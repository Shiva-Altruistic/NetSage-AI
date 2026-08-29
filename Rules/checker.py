#!/usr/bin/env python3
"""NetSage AI deterministic network rule checker.

Reads only the observed case fields (symptom, topology_note, show_output)
and applies deterministic heuristics/checks. It intentionally does not read
or use expected_fault/expected_fix so it can be used before AI diagnosis.
"""

from __future__ import annotations

import argparse
import csv
import ipaddress
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


@dataclass
class Finding:
    rule_id: str
    status: str  # PASS | FAIL | WARNING | NOT_APPLICABLE
    message: str
    evidence: str
    confidence: str = "High"


IPV4_RE = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
PORT_RE = re.compile(r"(Fa\d+/\d+|Gi\d+/\d+(?:\.\d+)?|Se\d+/\d+(?:/\d+)?|GigabitEthernet\d+/\d+(?:\.\d+)?)", re.I)


def normalize(text: str) -> str:
    return text.replace("\\n", "\n").replace("\r", "")


def ips(text: str) -> list[str]:
    return [m.group(0) for m in IPV4_RE.finditer(text)]


def valid_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def mask_to_prefix(mask: str) -> int | None:
    try:
        return ipaddress.IPv4Network(f"0.0.0.0/{mask}").prefixlen
    except ValueError:
        return None


def parse_ipconfig(text: str) -> list[dict[str, str]]:
    lines = [x.strip() for x in text.splitlines()]
    blocks: list[dict[str, str]] = []
    cur: dict[str, str] = {}
    for line in lines:
        m = re.search(r"IP Address\.*:\s*(\S+)", line, re.I)
        if m:
            if cur:
                blocks.append(cur)
            cur = {"ip": m.group(1)}
        m = re.search(r"Subnet Mask\.*:\s*(\S+)", line, re.I)
        if m and cur:
            cur["mask"] = m.group(1)
        m = re.search(r"Default Gateway\.*:\s*(\S+)", line, re.I)
        if m and cur:
            cur["gateway"] = m.group(1)
        m = re.search(r"DNS Server\.*:\s*(\S+)", line, re.I)
        if m and cur:
            cur["dns"] = m.group(1)
    if cur:
        blocks.append(cur)
    return blocks


def parse_show_ip_int_brief(text: str) -> list[dict[str, str]]:
    rows = []
    in_table = False
    for line in text.splitlines():
        if re.search(r"Interface\s+IP-Address\s+OK\?\s+Method\s+Status\s+Protocol", line, re.I):
            in_table = True
            continue
        if not in_table:
            continue
        parts = line.split()
        if len(parts) < 6:
            # Stop only when the next command begins; otherwise ignore prose.
            if re.match(r"^\S+#", line):
                in_table = False
            continue
        interface, ip, ok = parts[0], parts[1], parts[2]
        if ok.upper() != "YES":
            continue
        status, protocol = parts[-2].lower(), parts[-1].lower()
        if status not in {"up", "down", "administratively"} or protocol not in {"up", "down"}:
            continue
        if len(parts) >= 7 and parts[-3].lower() == "administratively" and parts[-2].lower() == "down":
            status = "administratively down"
            protocol = parts[-1].lower()
        rows.append({"interface": interface, "ip": ip, "status": status, "protocol": protocol})
    return rows


def parse_interface_blocks(text: str) -> dict[str, str]:
    blocks: dict[str, list[str]] = {}
    current = None
    for raw in text.splitlines():
        line = raw.rstrip()
        m = re.match(r"^interface\s+(\S+)", line, re.I)
        if m:
            current = m.group(1).lower()
            blocks[current] = []
            continue
        if current:
            if line and not line.startswith(" ") and not line.startswith("\t"):
                current = None
            else:
                blocks[current].append(line.strip())
    return {k: "\n".join(v) for k, v in blocks.items()}


def parse_acl_denies(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if re.search(r"\bdeny\b", line, re.I)]


def extract_vlan_numbers(text: str) -> set[int]:
    vals = set()
    for m in re.finditer(r"\bVLAN(?:\s+ID)?\s*[:=]?\s*(\d+)\b", text, re.I):
        vals.add(int(m.group(1)))
    for m in re.finditer(r"\bVlan(\d+)\b", text, re.I):
        vals.add(int(m.group(1)))
    for m in re.finditer(r"\b(?:VLAN|vlan)\s+(\d+)\b", text, re.I):
        vals.add(int(m.group(1)))
    return vals


def get_intended_vlan(topology: str, symptom: str) -> int | None:
    combined = f"{topology}\n{symptom}"
    patterns = [
        r"(?:meant|intended|should be|belongs to|in)\s+(?:be\s+)?VLAN\s*(\d+)",
        r"VLAN\s*(\d+)\s*[-–—:]\s*(?:Engineering|Sales|Finance|Guest|Servers|HR|Corporate)",
    ]
    for p in patterns:
        m = re.search(p, combined, re.I)
        if m:
            return int(m.group(1))
    return None


def rule_ip_config_sanity(text: str) -> list[Finding]:
    findings = []
    blocks = parse_ipconfig(text)
    if not blocks:
        return [Finding("IPCFG-001", "NOT_APPLICABLE", "No PC ipconfig-style block found.", "", "High")]
    for i, b in enumerate(blocks, 1):
        ip = b.get("ip")
        mask = b.get("mask")
        gw = b.get("gateway")
        if ip and not valid_ip(ip):
            findings.append(Finding("IPCFG-002", "FAIL", f"Host {i} has invalid IP address {ip}.", f"IP Address: {ip}"))
        if mask and mask_to_prefix(mask) is None:
            findings.append(Finding("IPCFG-003", "FAIL", f"Host {i} has invalid subnet mask {mask}.", f"Subnet Mask: {mask}"))
        if gw and gw != "0.0.0.0" and not valid_ip(gw):
            findings.append(Finding("IPCFG-004", "FAIL", f"Host {i} has invalid default gateway {gw}.", f"Default Gateway: {gw}"))
        if mask and ip and valid_ip(ip) and mask_to_prefix(mask) is not None:
            prefix = mask_to_prefix(mask)
            try:
                net = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)
                if gw and gw not in ("0.0.0.0",) and valid_ip(gw) and ipaddress.ip_address(gw) not in net:
                    findings.append(Finding("IPCFG-005", "FAIL", f"Host {i} default gateway {gw} is outside the host subnet {net}.", f"IP={ip}, Mask={mask}, Gateway={gw}"))
                else:
                    findings.append(Finding("IPCFG-006", "PASS", f"Host {i} IP/mask/gateway are internally consistent at the subnet level.", f"IP={ip}, Mask={mask}, Gateway={gw or 'not shown'}"))
            except ValueError:
                pass
    return findings


def rule_duplicate_ips(text: str) -> list[Finding]:
    # Do not count repeated references in configs/pings as duplicates. Look for
    # actual ARP evidence where the same IP maps to different MAC addresses.
    arp_pairs = re.findall(r"(?<![\d.])(\d{1,3}(?:\.\d{1,3}){3})\s+([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}|[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4})", text)
    macs_by_ip: dict[str, set[str]] = {}
    for ip, mac in arp_pairs:
        macs_by_ip.setdefault(ip, set()).add(mac.lower())
    duplicates = [ip for ip, macs in macs_by_ip.items() if len(macs) > 1]
    if duplicates:
        evidence = "; ".join(f"{ip} -> {sorted(macs_by_ip[ip])}" for ip in duplicates)
        return [Finding("IP-001", "FAIL", f"Potential duplicate IP(s) detected from conflicting ARP mappings: {', '.join(duplicates)}.", evidence)]
    return [Finding("IP-001", "PASS", "No conflicting IP-to-MAC mapping was detected in ARP-style evidence.", "ARP evidence checked for one IP resolving to multiple MAC addresses.")]


def rule_subnet_mask_consistency(text: str, topology: str) -> list[Finding]:
    # Compare an observed host mask with an explicitly stated intended mask in topology.
    intended_masks = re.findall(r"(?:actual|intended|should be|network[’']?s actual)\s+(?:subnet\s+)?mask[^0-9]*(255\.\d+\.\d+\.\d+)", topology, re.I)
    if not intended_masks:
        intended_masks = re.findall(r"(?:/\d+)\s*\((255\.\d+\.\d+\.\d+)\)", topology, re.I)
    observed = re.findall(r"Subnet Mask\.*:\s*(255\.\d+\.\d+\.\d+)", text, re.I)
    if not observed or not intended_masks:
        return [Finding("IPCFG-007", "NOT_APPLICABLE", "No explicit observed-vs-intended subnet mask comparison can be made.", "", "High")]
    intended = intended_masks[0]
    bad = [m for m in observed if m != intended]
    if bad:
        return [Finding("IPCFG-007", "FAIL", f"Observed subnet mask(s) {sorted(set(bad))} differ from explicitly stated intended mask {intended}.", f"Observed={sorted(set(observed))}; intended={intended}")]
    return [Finding("IPCFG-007", "PASS", "Observed subnet mask matches the explicitly stated intended mask.", f"Observed={sorted(set(observed))}; intended={intended}")]


def rule_interface_status(text: str) -> list[Finding]:
    rows = parse_show_ip_int_brief(text)
    if not rows:
        return [Finding("IF-001", "NOT_APPLICABLE", "No 'show ip interface brief' table found.", "", "High")]
    bad = [r for r in rows if r["status"] == "administratively down" or (r["status"] == "down" and r["protocol"] == "down")]
    if bad:
        evidence = "; ".join(f"{r['interface']} {r['status']}/{r['protocol']}" for r in bad)
        return [Finding("IF-001", "FAIL", "One or more interfaces are down in the supplied interface summary.", evidence)]
    return [Finding("IF-001", "PASS", "No administratively-down/down interface was found in the supplied summary.", "All parsed interfaces are operational.")]


def rule_wrong_access_vlan(text: str, topology: str, symptom: str) -> list[Finding]:
    intended = get_intended_vlan(topology, symptom)
    if intended is None:
        return [Finding("VLAN-001", "NOT_APPLICABLE", "No explicit intended VLAN could be inferred from the case context.", "", "High")]
    m_port = re.search(r"(?:Name:|interface\s+)(\S+)\n(?:.*\n){0,8}.*Access Mode VLAN:\s*(\d+)", text, re.I)
    if not m_port:
        m_port = re.search(r"(?:Access Mode VLAN|Access VLAN):\s*(\d+)", text, re.I)
        if m_port:
            actual = int(m_port.group(1)); port = "access port"
        else:
            return [Finding("VLAN-001", "NOT_APPLICABLE", "No access-port VLAN assignment was found.", "", "High")]
    else:
        port, actual = m_port.group(1), int(m_port.group(2))
    if actual != intended:
        return [Finding("VLAN-001", "FAIL", f"Access {port} is in VLAN {actual}, but case context indicates VLAN {intended}.", f"Access Mode VLAN: {actual}; intended VLAN: {intended}")]
    return [Finding("VLAN-001", "PASS", f"Parsed access VLAN {actual} matches intended VLAN {intended}.", f"Access VLAN: {actual}")]


def rule_dhcp_pool(text: str) -> list[Finding]:
    matches = re.findall(r"Total addresses\s*:\s*(\d+)\s+Leased addresses\s*:\s*(\d+)", text, re.I | re.S)
    if not matches:
        return [Finding("DHCP-001", "NOT_APPLICABLE", "No DHCP pool utilization block found.", "", "High")]
    exhausted = [(int(t), int(l)) for t, l in matches if int(l) >= int(t) and int(t) > 0]
    if exhausted:
        return [Finding("DHCP-001", "FAIL", "At least one DHCP pool is exhausted.", "; ".join(f"total={t}, leased={l}" for t, l in exhausted))]
    return [Finding("DHCP-001", "PASS", "Parsed DHCP pools have available addresses.", "; ".join(f"total={t}, leased={l}" for t, l in matches))]


def rule_dhcp_helper(text: str, symptom: str) -> list[Finding]:
    if not re.search(r"dhcp|169\.254\.|IP address", symptom, re.I):
        return [Finding("DHCP-002", "NOT_APPLICABLE", "Case symptom does not clearly indicate DHCP provisioning trouble.", "", "Medium")]
    blocks = parse_interface_blocks(text)
    if not blocks and "ip helper-address" not in text.lower():
        return [Finding("DHCP-002", "WARNING", "DHCP-related symptom detected, but no interface configuration block was supplied.", "No ip helper-address evidence available.", "Medium")]
    has_helper = bool(re.search(r"ip helper-address\s+\d+\.\d+\.\d+\.\d+", text, re.I))
    if "169.254." in text and not has_helper:
        return [Finding("DHCP-002", "FAIL", "DHCP-related evidence shows APIPA and no ip helper-address is present in supplied configuration.", "APIPA 169.254.x.x + no ip helper-address")]
    return [Finding("DHCP-002", "PASS", "No deterministic missing-helper condition was established from the supplied evidence.", "Helper configuration evidence is present or case is not a relay case.", "Medium")]


def rule_trunk_allowed(text: str, symptom: str, topology: str) -> list[Finding]:
    m = re.search(r"Trunking VLANs Allowed:\s*([^\n]+)", text, re.I)
    if not m:
        return [Finding("TRUNK-001", "NOT_APPLICABLE", "No explicit trunk allowed-VLAN list found.", "", "High")]
    allowed = {int(x) for x in re.findall(r"\b\d+\b", m.group(1))}
    vlan_candidates = extract_vlan_numbers(f"{symptom}\n{topology}")
    # Focus on non-default VLANs mentioned in the case context.
    relevant = sorted(v for v in vlan_candidates if v not in {1})
    missing = [v for v in relevant if v not in allowed]
    if missing:
        return [Finding("TRUNK-001", "FAIL", f"Referenced VLAN(s) {missing} are not in the trunk allowed list.", f"Allowed={sorted(allowed)}; referenced={relevant}")]
    return [Finding("TRUNK-001", "PASS", "No referenced non-default VLAN was found missing from the parsed trunk list.", f"Allowed={sorted(allowed)}")]


def rule_missing_route(text: str, symptom: str) -> list[Finding]:
    if not re.search(r"cannot reach|cannot access|no route|remote|branch|server|outside vlan|another vlan", symptom, re.I):
        return [Finding("ROUTE-001", "NOT_APPLICABLE", "Symptom does not clearly indicate a routed-connectivity problem.", "", "Medium")]
    if re.search(r"show ip route static\s*\n\s*\(no output|no static routes configured", text, re.I) or re.search(r"show ip route\s*\n\s*\(no output", text, re.I):
        return [Finding("ROUTE-001", "FAIL", "Routing evidence contains an empty route view for a case describing remote connectivity failure.", "No route/static route output shown.")]
    if re.search(r"show ip route ospf\s*\n\s*\(no output", text, re.I) and re.search(r"show ip ospf neighbor\s*\n\s*\(no output", text, re.I):
        return [Finding("ROUTE-001", "FAIL", "No OSPF routes and no OSPF neighbors are shown for a routed case.", "No OSPF route + no OSPF neighbor")]
    return [Finding("ROUTE-001", "PASS", "No deterministic missing-route signature was found in the supplied route evidence.", "Route output does not show the empty/no-neighbor signatures used by this rule.", "Medium")]


def rule_acl_blocks(text: str) -> list[Finding]:
    denies = parse_acl_denies(text)
    if not denies:
        return [Finding("ACL-001", "NOT_APPLICABLE", "No ACL deny entries found.", "", "High")]
    if any(re.search(r"deny\s+ip\s+any\s+any", d, re.I) for d in denies):
        return [Finding("ACL-001", "FAIL", "An explicit deny ip any any appears in the supplied ACL evidence.", "; ".join(denies))]
    return [Finding("ACL-001", "WARNING", "ACL deny entries exist; deterministic checker cannot prove whether they block the affected flow without full traffic context.", "; ".join(denies), "Medium")]


def rule_nat_roles(text: str) -> list[Finding]:
    if "ip nat" not in text.lower():
        return [Finding("NAT-001", "NOT_APPLICABLE", "No NAT configuration evidence found.", "", "High")]
    inside = bool(re.search(r"ip nat inside", text, re.I))
    outside = bool(re.search(r"ip nat outside", text, re.I))
    if not inside or not outside:
        missing = []
        if not inside: missing.append("ip nat inside")
        if not outside: missing.append("ip nat outside")
        return [Finding("NAT-001", "FAIL", "NAT configuration is missing one or more required interface roles.", ", ".join(missing))]
    return [Finding("NAT-001", "PASS", "Both NAT inside and outside roles appear in the supplied configuration.", "ip nat inside + ip nat outside")]


def rule_nat_acl_alignment(text: str) -> list[Finding]:
    m_nat = re.search(r"ip nat inside source list\s+(\d+)\b", text, re.I)
    if not m_nat:
        return [Finding("NAT-002", "NOT_APPLICABLE", "No NAT source-list configuration found.", "", "High")]
    acl_num = m_nat.group(1)
    acl_match = re.search(rf"access-list\s+{re.escape(acl_num)}\s+permit\s+[^\n]*?(\d+\.\d+\.\d+\.\d+)\s+([0-9.]+)", text, re.I)
    if not acl_match:
        return [Finding("NAT-002", "WARNING", f"NAT references ACL {acl_num}, but a parsable permit network was not found.", f"ip nat inside source list {acl_num}", "Medium")]
    permit_net, wildcard = acl_match.group(1), acl_match.group(2)
    inside_ips = []
    blocks = parse_ipconfig(text)
    inside_ips.extend(b.get("ip", "") for b in blocks)
    if inside_ips:
        try:
            wc_int = int(ipaddress.IPv4Address(wildcard))
            netmask_int = 0xFFFFFFFF ^ wc_int
            prefix = bin(netmask_int).count("1")
            net = ipaddress.IPv4Network(f"{permit_net}/{prefix}", strict=False)
            outside = [ip for ip in inside_ips if valid_ip(ip) and ipaddress.ip_address(ip) not in net]
            if outside:
                return [Finding("NAT-002", "FAIL", f"Observed host IP(s) are outside NAT ACL {acl_num}'s permitted network.", f"ACL network={net}; host IPs={outside}")]
        except ValueError:
            pass
    return [Finding("NAT-002", "PASS", f"NAT source ACL {acl_num} has a parsable permit network; no deterministic mismatch proven.", f"Permit network={permit_net} wildcard={wildcard}", "Medium")]


def rule_ospf_area_mismatch(text: str) -> list[Finding]:
    areas = re.findall(r"^\s*(?:Se|Gi|GigabitEthernet|FastEthernet)\S+\s+\d+\s+(\d+)\s+\S+", text, re.I | re.M)
    if len(set(areas)) >= 2:
        return [Finding("OSPF-001", "WARNING", f"Multiple OSPF areas appear in the supplied interface summaries: {sorted(set(areas))}.", f"Areas={sorted(set(areas))}", "Medium")]
    configs = re.findall(r"network\s+[^\n]+\s+area\s+(\d+)", text, re.I)
    if len(set(configs)) >= 2:
        return [Finding("OSPF-001", "WARNING", f"Multiple OSPF areas are configured: {sorted(set(configs))}; this is not by itself an error.", f"Configured areas={sorted(set(configs))}", "Low")]
    return [Finding("OSPF-001", "NOT_APPLICABLE", "No multi-end OSPF area mismatch signature detected.", "", "High")]


def rule_eigrp_as_mismatch(text: str) -> list[Finding]:
    ases = [int(x) for x in re.findall(r"router\s+eigrp\s+(\d+)", text, re.I)]
    if len(ases) >= 2 and len(set(ases)) > 1:
        return [Finding("EIGRP-001", "FAIL", f"Different EIGRP autonomous-system numbers are shown: {sorted(set(ases))}.", f"EIGRP AS values={ases}")]
    if ases:
        return [Finding("EIGRP-001", "PASS", "Only one EIGRP AS value is visible in the supplied evidence.", f"EIGRP AS values={ases}")]
    return [Finding("EIGRP-001", "NOT_APPLICABLE", "No EIGRP configuration evidence found.", "", "High")]


def rule_wireless_signal(text: str) -> list[Finding]:
    rssi = re.search(r"RSSI\.*\s*([-\d]+)\s*dBm", text, re.I)
    snr = re.search(r"SNR\.*\s*(\d+)\s*dB", text, re.I)
    if not rssi and not snr:
        return [Finding("WIFI-001", "NOT_APPLICABLE", "No wireless RSSI/SNR evidence found.", "", "High")]
    bad = []
    if rssi and int(rssi.group(1)) <= -80:
        bad.append(f"RSSI {rssi.group(1)} dBm")
    if snr and int(snr.group(1)) < 10:
        bad.append(f"SNR {snr.group(1)} dB")
    if bad:
        return [Finding("WIFI-001", "FAIL", "Wireless signal metrics indicate poor link quality.", "; ".join(bad))]
    return [Finding("WIFI-001", "PASS", "Wireless signal metrics are not below the severe threshold used by this rule.", f"RSSI={rssi.group(1) if rssi else 'n/a'}, SNR={snr.group(1) if snr else 'n/a'}")]


def rule_dns_config(text: str, symptom: str) -> list[Finding]:
    if not re.search(r"dns|name resolution|nslookup|domain", symptom + "\n" + text, re.I):
        return [Finding("DNS-001", "NOT_APPLICABLE", "No DNS-related evidence found.", "", "High")]
    if re.search(r"DNS Server\.*:\s*(?:$|0\.0\.0\.0)|DNS Server\.*:\s*$", text, re.I | re.M):
        return [Finding("DNS-001", "FAIL", "Client DNS server setting appears missing/empty.", "DNS Server field is empty or 0.0.0.0")]
    if re.search(r"ip dns server", text, re.I) and not re.search(r"ip name-server\s+\d+\.\d+\.\d+\.\d+", text, re.I):
        return [Finding("DNS-001", "FAIL", "DNS forwarding/server configuration lacks an upstream ip name-server entry in the supplied evidence.", "ip dns server present; no ip name-server")]
    return [Finding("DNS-001", "WARNING", "DNS evidence is present, but this checker cannot fully validate record correctness without a DNS zone/database view.", "DNS/lookup evidence supplied", "Medium")]



def rule_gateway_against_router(text: str) -> list[Finding]:
    blocks = parse_ipconfig(text)
    if not blocks:
        return [Finding("GW-001", "NOT_APPLICABLE", "No PC ipconfig block found.", "", "High")]
    router_rows = parse_show_ip_int_brief(text)
    router_ips = {r["ip"] for r in router_rows if valid_ip(r["ip"])}
    if not router_ips:
        return [Finding("GW-001", "NOT_APPLICABLE", "No router interface IPs were available for gateway comparison.", "", "High")]
    for b in blocks:
        ip, mask, gw = b.get("ip"), b.get("mask"), b.get("gateway")
        if not (ip and mask and gw and valid_ip(ip) and valid_ip(gw) and mask_to_prefix(mask) is not None):
            continue
        if gw in router_ips:
            return [Finding("GW-001", "PASS", f"Observed gateway {gw} matches a router interface IP in the supplied evidence.", f"Gateway={gw}; router IPs={sorted(router_ips)}")]
        prefix = mask_to_prefix(mask)
        net = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)
        if ipaddress.ip_address(gw) in net:
            return [Finding("GW-001", "FAIL", f"Observed gateway {gw} does not match any supplied router interface IP in the host subnet.", f"Host subnet={net}; gateway={gw}; router IPs={sorted(router_ips)}")]
    return [Finding("GW-001", "WARNING", "A host gateway was present, but the supplied router evidence was insufficient for a definitive comparison.", f"Router IPs={sorted(router_ips)}", "Medium")]


def rule_vlan_presence(text: str, topology: str, symptom: str) -> list[Finding]:
    m = re.search(r"(?:cannot reach|cannot connect|VLAN|belongs to|in)\D{0,40}VLAN\s*(\d+)", symptom + "\n" + topology, re.I)
    if not m:
        return [Finding("VLAN-002", "NOT_APPLICABLE", "No single required VLAN could be inferred from the case context.", "", "High")]
    vlan = int(m.group(1))
    # Look for an actual show vlan brief table and its VLAN entries.
    if not re.search(r"show vlan brief", text, re.I):
        return [Finding("VLAN-002", "NOT_APPLICABLE", "No 'show vlan brief' output available for VLAN-presence validation.", "", "High")]
    present = {int(x) for x in re.findall(r"^\s*(\d+)\s+\S+\s+active", text, re.I | re.M)}
    if vlan not in present:
        return [Finding("VLAN-002", "FAIL", f"VLAN {vlan} is referenced by the case but is absent from the supplied 'show vlan brief' output.", f"Required VLAN={vlan}; present VLANs={sorted(present)}")]
    return [Finding("VLAN-002", "PASS", f"VLAN {vlan} is present in the supplied VLAN table.", f"Present VLANs={sorted(present)}")]


def rule_evidence_sufficiency(symptom: str, text: str) -> list[Finding]:
    if re.search(r"insufficient evidence|cannot confirm|need.*additional|without.*checking|not enough evidence", symptom + "\n" + text, re.I):
        return [Finding("EVID-001", "WARNING", "The case explicitly states that evidence is insufficient for confirmation; AI should not overstate a diagnosis.", "Case contains an uncertainty statement.", "High")]
    return [Finding("EVID-001", "PASS", "No explicit uncertainty statement was found in the supplied case evidence.", "Evidence-sufficiency wording checked.", "Medium")]

def check_case(row: dict[str, str]) -> list[Finding]:
    symptom = normalize(row.get("symptom", ""))
    topology = normalize(row.get("topology_note", ""))
    output = normalize(row.get("show_output", ""))
    combined = f"{symptom}\n{topology}\n{output}"

    findings: list[Finding] = []
    findings += rule_ip_config_sanity(output)
    findings += rule_subnet_mask_consistency(output, topology)
    findings += rule_duplicate_ips(output)
    findings += rule_gateway_against_router(output)
    findings += rule_vlan_presence(output, topology, symptom)
    findings += rule_evidence_sufficiency(symptom, output)
    findings += rule_interface_status(output)
    findings += rule_wrong_access_vlan(output, topology, symptom)
    findings += rule_dhcp_pool(output)
    findings += rule_dhcp_helper(output, symptom)
    findings += rule_trunk_allowed(output, symptom, topology)
    findings += rule_missing_route(output, symptom)
    findings += rule_acl_blocks(output)
    findings += rule_nat_roles(output)
    findings += rule_nat_acl_alignment(combined)
    findings += rule_ospf_area_mismatch(output)
    findings += rule_eigrp_as_mismatch(output)
    findings += rule_wireless_signal(output)
    findings += rule_dns_config(output, symptom)
    return findings


def summarize(findings: Iterable[Finding]) -> str:
    fails = [f for f in findings if f.status == "FAIL"]
    warns = [f for f in findings if f.status == "WARNING"]
    if fails:
        return "FAIL"
    if warns:
        return "WARNING"
    return "PASS"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic NetSage AI rules against cases.csv")
    parser.add_argument("--csv", required=True, help="Path to cases.csv")
    parser.add_argument("--output", default="rule_results.csv", help="Output CSV path")
    args = parser.parse_args()

    source = Path(args.csv)
    rows = []
    with source.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"case_id", "symptom", "topology_note", "show_output"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"Missing required observed-data columns: {sorted(missing)}")
        for row in reader:
            rows.append(row)

    out_path = Path(args.output)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "case_id", "rule_id", "status", "message", "evidence", "confidence"
        ])
        writer.writeheader()
        for row in rows:
            findings = check_case(row)
            for finding in findings:
                writer.writerow({"case_id": row["case_id"], **asdict(finding)})

    # Human-readable summary without relying on ground truth columns.
    case_summaries = []
    for row in rows:
        fs = check_case(row)
        case_summaries.append((row["case_id"], summarize(fs), sum(f.status == "FAIL" for f in fs), sum(f.status == "WARNING" for f in fs)))

    print("NetSage deterministic rule checker")
    print(f"Cases checked: {len(rows)}")
    print(f"Detailed results: {out_path}")
    print("\nCase summary:")
    for cid, status, fails, warns in case_summaries:
        print(f"  {cid}: {status} (fails={fails}, warnings={warns})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
