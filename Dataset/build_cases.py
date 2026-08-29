"""
build_cases.py
Generates data/cases.csv for NetSage AI.

IMPORTANT — DATA PROVENANCE:
These cases are INSTRUCTOR-STYLE SYNTHETIC DATA authored to match realistic
Packet Tracer / Cisco IOS behavior (correct show-command syntax, correct
IP/VLAN logic, internally consistent topologies). They are NOT scraped or
copied from a real running network. This is documented in README.md and
in the Responsible AI log so the team can accurately state "synthetic,
not live-network" if asked during review.

Topologies used across the 30 cases (kept consistent so evidence lines up):
  A - SOHO Branch: R1-BR (router-on-a-stick) + SW1, VLANs 10/20/99
  B - Campus L3: SW-CORE (SVIs) + SW-DIST + SW-ACC, VLANs 30/40, DHCP relay
  C - WAN: R1(HQ) <-> R2(Branch), static + EIGRP + OSPF
  D - Internet Edge: R-EDGE, NAT/PAT, inside/outside, ACLs, DNS forwarding
  E - Wireless: WLC1 + AP1, Corporate SSID (VLAN10) + Guest SSID (VLAN50)
"""
import csv

cases = [
# ---------------- TOPOLOGY A: SOHO Branch ----------------
dict(case_id="C001",
 symptom="PC-ENG1 (VLAN 20 - Engineering) cannot reach any other host on the network, including its own default gateway.",
 topology_note="Topology A (SOHO Branch): R1-BR router-on-a-stick with sub-interfaces Gi0/0.10 (VLAN10, 10.10.10.1/24), Gi0/0.20 (VLAN20, 10.10.20.1/24), Gi0/0.99 (VLAN99 Servers, 10.10.99.1/24). SW1 access switch, PC-ENG1 physically on port Fa0/5, meant to be VLAN 20.",
 show_output="SW1# show interfaces fa0/5 switchport\nName: Fa0/5\nSwitchport: Enabled\nAdministrative Mode: static access\nOperational Mode: static access\nAdministrative Trunking Encapsulation: dot1q\nAccess Mode VLAN: 10 (VLAN0010)\nVoice VLAN: none\n\nSW1# show vlan brief\nVLAN Name                             Status    Ports\n---- -------------------------------- --------- -------------------------\n10   Sales                            active    Fa0/1, Fa0/2, Fa0/5\n20   Engineering                      active    Fa0/6, Fa0/7\n99   Servers                          active    Fa0/10\n\nPC-ENG1> ipconfig\nIP Address..............: 10.10.10.45\nSubnet Mask..............: 255.255.255.0\nDefault Gateway..........: 10.10.20.1\n\nPC-ENG1> ping 10.10.20.1\nRequest timed out. (4/4 packets lost)",
 expected_fault="Access port Fa0/5 is assigned to VLAN 10 instead of VLAN 20, so PC-ENG1 lands in the wrong IP subnet (10.10.10.x) while its default gateway is statically set for VLAN 20 (10.10.20.1), which is unreachable from VLAN 10.",
 osi_layer=2, concept_tag="vlan", severity="high",
 expected_next_command="show running-config interface fa0/5",
 expected_fix="On SW1, run: interface fa0/5 / switchport access vlan 20, then verify with 'show vlan brief' that Fa0/5 lists under VLAN 20."),

dict(case_id="C002",
 symptom="PC-SALES3 on VLAN 10 can ping its own subnet and other Sales PCs, but cannot reach anything outside VLAN 10, including the Servers VLAN.",
 topology_note="Topology A (SOHO Branch): PC-SALES3 statically configured, VLAN10 gateway on R1-BR is 10.10.10.1 via Gi0/0.10.",
 show_output="PC-SALES3> ipconfig\nIP Address..............: 10.10.10.52\nSubnet Mask..............: 255.255.255.0\nDefault Gateway..........: 10.10.10.254\n\nPC-SALES3> ping 10.10.10.1\nReply from 10.10.10.1: bytes=32 time=2ms TTL=255 (4/4 received)\n\nPC-SALES3> ping 10.10.99.10\nRequest timed out. (4/4 packets lost)\n\nR1-BR# show ip interface brief\nInterface              IP-Address      OK? Method Status                Protocol\nGigabitEthernet0/0.10   10.10.10.1      YES manual up                    up\nGigabitEthernet0/0.20   10.10.20.1      YES manual up                    up\nGigabitEthernet0/0.99   10.10.99.1      YES manual up                    up",
 expected_fault="PC-SALES3 is statically configured with default gateway 10.10.10.254, which does not exist on the VLAN 10 subnet (the real gateway is 10.10.10.1 on R1-BR sub-interface Gi0/0.10). Local-subnet traffic (to the gateway's own IP) works because ARP resolves it directly, but any traffic destined off-subnet is sent to a non-existent gateway and dropped.",
 osi_layer=3, concept_tag="gateway", severity="medium",
 expected_next_command="show running-config (verify no secondary gateway/HSRP exists at .254)",
 expected_fix="Reconfigure PC-SALES3's default gateway to 10.10.10.1 to match R1-BR's Gi0/0.10 address, then re-test connectivity to 10.10.99.10."),

dict(case_id="C003",
 symptom="Newly connected PC-SALES5 on VLAN 10 is not getting an IP address; it shows a 169.254.x.x self-assigned address.",
 topology_note="Topology A (SOHO Branch): R1-BR runs local DHCP pools for VLAN10 and VLAN20.",
 show_output="R1-BR# show ip dhcp pool\nPool VLAN10_POOL :\n Utilization mark (high/low)    : 100 / 0\n Subnet size (first/next)       : 0 / 0\n Total addresses                : 254\n Leased addresses               : 254\n Pending event                  : none\n\nR1-BR# show running-config | section dhcp pool VLAN10_POOL\nip dhcp pool VLAN10_POOL\n network 10.10.10.0 255.255.255.0\n default-router 10.10.10.1\n dns-server 10.10.99.20\n\nPC-SALES5> ipconfig\nIP Address..............: 169.254.34.12\nSubnet Mask..............: 255.255.0.0\nDefault Gateway..........: 0.0.0.0",
 expected_fault="DHCP pool VLAN10_POOL is fully exhausted (254/254 addresses leased), so no address remains to offer PC-SALES5. It falls back to an APIPA (169.254.x.x) address.",
 osi_layer=7, concept_tag="dhcp", severity="high",
 expected_next_command="show ip dhcp binding",
 expected_fix="Reclaim stale leases with 'clear ip dhcp binding *' after confirming they are no longer in use, or reduce the pool's excluded range so more usable addresses are available; consider shortening the lease time or expanding the subnet if exhaustion is a recurring pattern."),

dict(case_id="C004",
 symptom="Engineering (VLAN 20) users report they can browse the internal file share on their own VLAN but cannot reach Server1 (10.10.99.10) on the Servers VLAN, while Sales (VLAN 10) users can reach it fine.",
 topology_note="Topology A (SOHO Branch): R1-BR has ACL 101 applied inbound on Gi0/0.99 (Servers sub-interface) intended to restrict only guest/unknown traffic.",
 show_output="R1-BR# show access-lists 101\nExtended IP access list 101\n    10 deny ip 10.10.20.0 0.0.0.255 any\n    20 permit ip any any (142 matches)\n\nR1-BR# show ip interface gi0/0.99 | include access list\n  Inbound  access list is 101\n\nPC-ENG7> ping 10.10.99.10\nRequest timed out. (4/4 packets lost)\n\nPC-SALES2> ping 10.10.99.10\nReply from 10.10.99.10: bytes=32 time=3ms TTL=254 (4/4 received)",
 expected_fault="ACL 101 applied inbound on Gi0/0.99 explicitly denies all traffic from the Engineering subnet (10.10.20.0/24) before the permit-any statement is reached, blocking every Engineering host from reaching the Servers VLAN.",
 osi_layer=3, concept_tag="acl", severity="high",
 expected_next_command="show running-config interface gi0/0.99",
 expected_fix="Remove or correct ACL 101 line 10 (the deny for 10.10.20.0/24) if Engineering is supposed to have server access, or add a specific permit for the required service/ports above the deny if the restriction should be partial rather than total."),

dict(case_id="C005",
 symptom="Server1 (VLAN 99, Servers) is unreachable from every VLAN, and SW1's trunk to R1-BR shows VLAN 99 traffic being tagged incorrectly.",
 topology_note="Topology A (SOHO Branch): trunk link between SW1 and R1-BR carries VLAN10/20/99. Native VLAN should be consistent on both ends (VLAN 1 by convention here).",
 show_output="SW1# show interfaces trunk\nPort        Mode         Encapsulation  Status        Native vlan\nGi0/1       on           802.1q         trunking      1\n\nR1-BR# show interfaces gi0/0.99\nGigabitEthernet0/0.99 is up, line protocol is up\n  Encapsulation 802.1Q Virtual LAN, Vlan ID  99\n\nR1-BR# show interfaces gi0/0 | include Native\n(no output - Gi0/0 is the trunk parent, native VLAN configured under gi0/0.1 as 99)\n\nR1-BR# show running-config interface gi0/0.1\ninterface GigabitEthernet0/0.1\n encapsulation dot1Q 1 native",
 expected_fault="Native VLAN mismatch: SW1's trunk uses native VLAN 1 (the default), while R1-BR's trunk parent is configured with 'encapsulation dot1Q 1 native' — on closer inspection this actually matches, but the true root cause is that VLAN 99 is not included in R1-BR's dot1Q sub-interface for native traffic, meaning VLAN 99 traffic is being untagged and dropped or misassociated. Evidence is insufficient to confirm without 'show interfaces gi0/1 switchport' on SW1 to compare native VLAN configuration on both trunk ends directly.",
 osi_layer=2, concept_tag="vlan", severity="medium",
 expected_next_command="show interfaces gi0/1 switchport (on SW1) to directly compare native VLAN against R1-BR's trunk parent",
 expected_fix="Ensure both trunk ends agree on native VLAN (commonly VLAN 1, or a dedicated unused VLAN per security best practice) and that VLAN 99 is explicitly allowed and tagged (not native) on both ends: 'switchport trunk native vlan 1' on SW1 to match R1-BR, verified against 'show interfaces trunk' on both devices."),

dict(case_id="C006",
 symptom="All new Engineering (VLAN 20) hosts are receiving IP addresses in the 10.10.10.0/24 range (Sales subnet) instead of 10.10.20.0/24, causing gateway/subnet conflicts.",
 topology_note="Topology A (SOHO Branch): R1-BR has a dedicated DHCP pool VLAN20_POOL intended to serve VLAN 20 hosts via Gi0/0.20.",
 show_output="R1-BR# show running-config | section ip dhcp pool VLAN20_POOL\nip dhcp pool VLAN20_POOL\n network 10.10.10.0 255.255.255.0\n default-router 10.10.20.1\n dns-server 10.10.99.20\n\nPC-ENG9> ipconfig /release\nPC-ENG9> ipconfig /renew\nIP Address..............: 10.10.10.88\nSubnet Mask..............: 255.255.255.0\nDefault Gateway..........: 10.10.20.1",
 expected_fault="DHCP pool VLAN20_POOL has the wrong network statement (10.10.10.0/24, the Sales subnet) instead of 10.10.20.0/24. The pool hands out addresses from the wrong subnet while still pointing to the correct VLAN 20 default-router, producing a subnet mismatch that will break connectivity even though DHCP itself 'succeeds'.",
 osi_layer=7, concept_tag="dhcp", severity="high",
 expected_next_command="show ip dhcp pool VLAN20_POOL (confirm subnet after fix)",
 expected_fix="Correct the network statement to 'network 10.10.20.0 255.255.255.0' under pool VLAN20_POOL on R1-BR, then clear existing incorrect leases with 'clear ip dhcp binding *' and have affected clients renew."),

# ---------------- TOPOLOGY B: Campus L3 ----------------
dict(case_id="C007",
 symptom="HR department (VLAN 40) users on SW-ACC can reach each other but cannot reach any host on Finance (VLAN 30) or the server subnet, despite SW-CORE showing VLAN 40's SVI as up.",
 topology_note="Topology B (Campus L3): SW-CORE (SVIs for VLAN30/40), SW-DIST (distribution), SW-ACC (access, HR users). Trunk SW-DIST <-> SW-ACC should carry VLAN 30 and 40.",
 show_output="SW-DIST# show interfaces trunk\nPort        Mode   Encapsulation  Status        Native vlan\nGi0/1       on     802.1q         trunking      1\n\nSW-DIST# show interfaces gi0/1 switchport | include Allowed\nTrunking VLANs Allowed: 1,10,20,30\n\nSW-CORE# show interfaces vlan 40\nVlan40 is up, line protocol is up\n  Internet address is 172.16.40.1/24",
 expected_fault="The trunk on SW-DIST toward SW-ACC has an allowed-VLAN list of only 1,10,20,30 — VLAN 40 is not included, so HR traffic is dropped at the trunk before it ever reaches SW-CORE, even though the VLAN 40 SVI itself is up.",
 osi_layer=2, concept_tag="vlan", severity="high",
 expected_next_command="show running-config interface gi0/1 (on SW-DIST)",
 expected_fix="On SW-DIST, add VLAN 40 to the trunk: 'switchport trunk allowed vlan add 40' on the Gi0/1 interface, then confirm with 'show interfaces trunk' that VLAN 40 appears in the allowed and active list."),

dict(case_id="C008",
 symptom="HR (VLAN 40) PCs are not receiving IP addresses via DHCP; Finance (VLAN 30) PCs on the same core switch get addresses without issue.",
 topology_note="Topology B (Campus L3): DHCP is centralized on DHCP-SRV (172.16.99.10), reached via 'ip helper-address' configured on each VLAN's SVI on SW-CORE.",
 show_output="SW-CORE# show running-config interface vlan 30\ninterface Vlan30\n ip address 172.16.30.1 255.255.255.0\n ip helper-address 172.16.99.10\n\nSW-CORE# show running-config interface vlan 40\ninterface Vlan40\n ip address 172.16.40.1 255.255.255.0\n\nPC-HR2> ipconfig\nIP Address..............: 169.254.12.9\nSubnet Mask..............: 255.255.0.0\nDefault Gateway..........: 0.0.0.0",
 expected_fault="The Vlan40 SVI on SW-CORE is missing the 'ip helper-address 172.16.99.10' statement, so DHCP broadcast requests from HR clients are never relayed to the DHCP server, and clients fall back to APIPA.",
 osi_layer=7, concept_tag="dhcp", severity="high",
 expected_next_command="show ip interface vlan 40 (confirm helper-address after fix)",
 expected_fix="Add 'ip helper-address 172.16.99.10' under 'interface Vlan40' on SW-CORE, then have PC-HR2 release/renew and confirm it receives a 172.16.40.0/24 address."),

dict(case_id="C009",
 symptom="A Finance user can ping internal servers and external sites by IP address, but web browsing by hostname (e.g. intranet.corp.local) fails.",
 topology_note="Topology B (Campus L3): DNS resolution for the campus should point to internal DNS server 172.16.99.20, which forwards external queries upstream.",
 show_output="PC-FIN4> ipconfig /all\nIP Address..............: 172.16.30.55\nSubnet Mask..............: 255.255.255.0\nDefault Gateway..........: 172.16.30.1\nDNS Server...............: 172.16.99.200\n\nPC-FIN4> ping 172.16.99.20\nRequest timed out. (4/4 packets lost)\n\nPC-FIN4> ping 8.8.8.8\nReply from 8.8.8.8: bytes=32 time=40ms TTL=112 (4/4 received)\n\nPC-FIN4> nslookup intranet.corp.local\nDNS request timed out.",
 expected_fault="PC-FIN4's DNS server is configured as 172.16.99.200, a typo of the real DNS server address 172.16.99.20 (extra trailing zero, wrong host). Since that address doesn't respond, name resolution fails while direct IP-based connectivity (which doesn't depend on DNS) works normally.",
 osi_layer=7, concept_tag="dns", severity="medium",
 expected_next_command="show ip dhcp pool (to check whether the wrong DNS server is coming from a DHCP option, or was set statically)",
 expected_fix="Correct the DNS server entry to 172.16.99.20 on PC-FIN4 (statically or by fixing the DHCP pool's 'dns-server' option if it is centrally assigned), then re-test 'nslookup intranet.corp.local'."),

dict(case_id="C010",
 symptom="Finance (VLAN 30) can reach HR (VLAN 40) and other local campus subnets, but cannot reach the data center server subnet (172.16.99.0/24) reachable only via Edge-R1.",
 topology_note="Topology B (Campus L3): SW-CORE connects to Edge-R1 via a routed link; OSPF runs between SW-CORE and Edge-R1 to exchange the server subnet route.",
 show_output="SW-CORE# show ip route ospf\n(no output)\n\nSW-CORE# show ip ospf neighbor\n(no output - no neighbors found)\n\nSW-CORE# show ip protocols | include Routing Protocol\nRouting Protocol is \"ospf 1\"\n\nEdge-R1# show ip ospf interface brief\nInterface    PID   Area            IP Address/Mask    Cost  State Nbrs F/C\nGi0/1        1     0               172.16.250.1/30    1     DOWN  0/0",
 expected_fault="No OSPF adjacency exists between SW-CORE and Edge-R1 — Edge-R1's Gi0/1 OSPF interface is in a DOWN state, so the server subnet route (172.16.99.0/24) learned from further upstream is never advertised into the campus, and SW-CORE has no route to it.",
 osi_layer=3, concept_tag="routing", severity="high",
 expected_next_command="show running-config interface gi0/1 (on Edge-R1, confirm OSPF network statement/area and interface no-shutdown state)",
 expected_fix="Verify Gi0/1 on Edge-R1 is not administratively shut down and that it is included in the correct OSPF network statement/area matching SW-CORE's configuration, then confirm adjacency forms with 'show ip ospf neighbor' on both devices."),

dict(case_id="C011",
 symptom="A newly created VLAN 30 sub-network segment (Finance-Annex) cannot communicate with the rest of Finance VLAN 30 even though it was assigned VLAN 30 on its access switch.",
 topology_note="Topology B (Campus L3): a second instance of VLAN 30 was created locally on SW-ACC2 without syncing VTP/VLAN database with SW-CORE.",
 show_output="SW-ACC2# show vlan brief\nVLAN Name                             Status    Ports\n---- -------------------------------- --------- -------------------------\n30   VLAN0030                         active    Fa0/3, Fa0/4\n\nSW-CORE# show vlan brief | include 30\n30   Finance                          active    Gi0/2\n\nSW-ACC2# show interfaces vlan 30\n(vlan interface not configured on this switch - access layer only)",
 expected_fault="VLAN 30 exists independently on SW-ACC2 as an auto-created, unnamed VLAN (VLAN0030) rather than being learned consistently from the campus VLAN database used by SW-CORE (named 'Finance'). This points to inconsistent VLAN provisioning between switches (e.g. VTP mode/domain mismatch or manually created local VLAN), which can cause naming/scope inconsistencies even when the numeric VLAN ID matches.",
 osi_layer=2, concept_tag="vlan", severity="medium",
 expected_next_command="show vtp status (on both SW-ACC2 and SW-CORE, to compare VTP domain and mode)",
 expected_fix="Align VTP domain/mode across switches, or if VTP is not in use, manually ensure VLAN 30 is named and provisioned identically on every switch in the path, then re-verify end-to-end connectivity from Finance-Annex to the rest of VLAN 30."),

dict(case_id="C012",
 symptom="Multiple campus users intermittently report that internal hostnames resolve to the wrong IP addresses, sending them to a decommissioned server.",
 topology_note="Topology B (Campus L3): internal DNS server 172.16.99.20 hosts A records for internal services including 'fileserver.corp.local'.",
 show_output="PC-FIN9> nslookup fileserver.corp.local\nServer: 172.16.99.20\nAddress: 172.16.99.20\n\nName: fileserver.corp.local\nAddress: 172.16.99.99\n\nPC-FIN9> ping 172.16.99.99\nRequest timed out. (4/4 packets lost)\n\nAdmin note: fileserver.corp.local was migrated last month; its current address is 172.16.99.15.",
 expected_fault="The internal DNS server's A record for fileserver.corp.local is stale, still pointing to the decommissioned address 172.16.99.99 instead of the current 172.16.99.15, following a server migration that was not reflected in DNS.",
 osi_layer=7, concept_tag="dns", severity="medium",
 expected_next_command="show running-config (on DNS-SRV, or its management interface) to inspect the current A record entries for fileserver.corp.local",
 expected_fix="Update the A record for fileserver.corp.local on the internal DNS server to 172.16.99.15 and confirm propagation by re-running 'nslookup fileserver.corp.local' from an affected client."),

# ---------------- TOPOLOGY C: WAN (R1 HQ <-> R2 Branch) ----------------
dict(case_id="C013",
 symptom="PC-BR1 at the Branch site (connected to R2) cannot reach anything, not even its own default gateway.",
 topology_note="Topology C (WAN): R2 LAN interface Gi0/0 should be 192.168.2.1/24 serving PC-BR1's subnet.",
 show_output="PC-BR1> ipconfig\nIP Address..............: 192.168.2.50\nSubnet Mask..............: 255.255.255.0\nDefault Gateway..........: 192.168.2.254\n\nPC-BR1> ping 192.168.2.1\nRequest timed out. (4/4 packets lost)\n\nR2# show ip interface brief\nInterface              IP-Address      OK? Method Status                Protocol\nGigabitEthernet0/0      192.168.2.1     YES manual up                    up",
 expected_fault="PC-BR1 is statically configured with default gateway 192.168.2.254, which does not correspond to any interface on R2 (the actual LAN gateway is 192.168.2.1 on Gi0/0). Off-subnet traffic is sent to a non-existent gateway and dropped.",
 osi_layer=3, concept_tag="gateway", severity="high",
 expected_next_command="show arp (on R2, to confirm no device responds at .254)",
 expected_fix="Correct PC-BR1's default gateway to 192.168.2.1 to match R2's Gi0/0 address, then verify connectivity."),

dict(case_id="C014",
 symptom="HQ (behind R1, 192.168.1.0/24) cannot reach the Branch LAN (behind R2, 192.168.2.0/24), though R1 and R2 can ping each other across the WAN link.",
 topology_note="Topology C (WAN): R1 (HQ) <-> R2 (Branch) via point-to-point link 192.168.12.0/30. Static routing is used (no dynamic routing protocol configured).",
 show_output="R1# show ip route static\n(no output - no static routes configured)\n\nR1# ping 192.168.12.2\nReply from 192.168.12.2: bytes=32 time=1ms TTL=255 (4/4 received)\n\nPC-HQ3> ping 192.168.2.10\nRequest timed out. (4/4 packets lost)\n\nR1# show ip route\nGateway of last resort is not set\n     192.168.1.0/24 is directly connected, GigabitEthernet0/0\n     192.168.12.0/30 is directly connected, Serial0/0/0",
 expected_fault="R1 has no static route (or dynamic routing) configured for the Branch LAN subnet 192.168.2.0/24, so it has no way to forward HQ-to-Branch traffic even though the WAN link itself is up and reachable.",
 osi_layer=3, concept_tag="routing", severity="high",
 expected_next_command="show ip route (on R2, to confirm the reverse route toward 192.168.1.0/24 also needs checking)",
 expected_fix="Add a static route on R1: 'ip route 192.168.2.0 255.255.255.0 192.168.12.2', and confirm R2 has a corresponding route back to 192.168.1.0/24 via 192.168.12.1, then re-test end-to-end connectivity."),

dict(case_id="C015",
 symptom="R1 and R2 are both configured for EIGRP but never form a neighbor relationship; static routes were removed in favor of EIGRP and now HQ-Branch connectivity is down.",
 topology_note="Topology C (WAN): R1 and R2 connected via Serial0/0/0, both intended to run EIGRP for automatic route exchange.",
 show_output="R1# show ip eigrp neighbors\nEIGRP-IPv4 Neighbors for AS(100)\n(no neighbors found)\n\nR1# show running-config | section router eigrp\nrouter eigrp 100\n network 192.168.1.0\n network 192.168.12.0\n\nR2# show running-config | section router eigrp\nrouter eigrp 200\n network 192.168.2.0\n network 192.168.12.0",
 expected_fault="R1 and R2 are configured with mismatched EIGRP autonomous system numbers (AS 100 on R1 vs AS 200 on R2). EIGRP routers must use the same AS number to form a neighbor relationship, so no adjacency is established and no routes are exchanged.",
 osi_layer=3, concept_tag="routing", severity="high",
 expected_next_command="show ip eigrp neighbors (after fix, on both routers)",
 expected_fix="Change R2's EIGRP process to AS 100 to match R1: remove 'router eigrp 200' and configure 'router eigrp 100' with the same network statements, then verify the neighbor relationship forms and routes populate on both routers."),

dict(case_id="C016",
 symptom="PC-HQ7 lost connectivity to everything, including local HQ resources, right after a scheduled maintenance window on R1.",
 topology_note="Topology C (WAN): R1's Gi0/0 is the HQ LAN gateway interface (192.168.1.1/24).",
 show_output="R1# show ip interface brief\nInterface              IP-Address      OK? Method Status                Protocol\nGigabitEthernet0/0      192.168.1.1     YES manual administratively down down\n\nR1# show interfaces gi0/0 | include line protocol\nGigabitEthernet0/0 is administratively down, line protocol is down",
 expected_fault="R1's Gi0/0 interface (the HQ LAN gateway) is administratively shut down, most likely left disabled after maintenance. With the gateway interface down, all HQ hosts lose connectivity to anything beyond their own switch segment.",
 osi_layer=1, concept_tag="gateway", severity="high",
 expected_next_command="show running-config interface gi0/0 (confirm no other misconfiguration besides shutdown)",
 expected_fix="Re-enable the interface with 'no shutdown' under 'interface GigabitEthernet0/0' on R1, then confirm 'show ip interface brief' reports the interface as up/up and PC-HQ7 regains connectivity."),

dict(case_id="C017",
 symptom="R2's branch LAN hosts can reach R2 itself but nothing beyond it; R1 reports no route learned from R2 for the branch subnet even though OSPF is configured on both.",
 topology_note="Topology C (WAN): R1 and R2 run OSPF; R1 is in Area 0, R2's WAN-facing interface was configured in a non-backbone area by mistake.",
 show_output="R2# show ip ospf interface brief\nInterface    PID   Area            IP Address/Mask    Cost  State Nbrs F/C\nSe0/0/0      1     1               192.168.12.2/30    64    DOWN  0/0\n\nR1# show ip ospf interface brief\nInterface    PID   Area            IP Address/Mask    Cost  State Nbrs F/C\nSe0/0/0      1     0               192.168.12.1/30    64    DOWN  0/0",
 expected_fault="R1's WAN interface is in OSPF Area 0 while R2's matching WAN interface is in Area 1. OSPF requires both ends of a link to be in the same area to form an adjacency; the area mismatch prevents the neighbor relationship (and therefore route exchange) from ever forming.",
 osi_layer=3, concept_tag="routing", severity="high",
 expected_next_command="show ip ospf neighbor (confirm no adjacency exists, consistent with the area mismatch)",
 expected_fix="Change R2's Se0/0/0 OSPF area to 0 to match R1: under the OSPF network statement, correct 'area 1' to 'area 0' for the 192.168.12.0/30 network, then verify the neighbor forms and the branch subnet route appears in R1's routing table."),

dict(case_id="C018",
 symptom="PC-BR5 at the Branch can reach the Branch gateway and the WAN link, but not any HQ resources; other Branch PCs on the same switch work fine.",
 topology_note="Topology C (WAN): Branch LAN is 192.168.2.0/24 with a /24 mask; PC-BR5 was manually configured rather than via DHCP.",
 show_output="PC-BR5> ipconfig\nIP Address..............: 192.168.2.77\nSubnet Mask..............: 255.255.255.128\nDefault Gateway..........: 192.168.2.1\n\nPC-BR5> ping 192.168.2.1\nReply from 192.168.2.1: bytes=32 time=1ms TTL=255 (4/4 received)\n\nPC-BR5> ping 192.168.1.10\nRequest timed out. (4/4 packets lost)",
 expected_fault="PC-BR5 has an incorrect subnet mask (255.255.255.128 / a /25) instead of the network's actual 255.255.255.0 / /24. This puts PC-BR5 in a different logical subnet than the rest of 192.168.2.0/24, so while ARP for the directly-reachable gateway IP still happens to work, routing decisions based on the wrong local subnet boundary break off-subnet (HQ-bound) traffic.",
 osi_layer=3, concept_tag="gateway", severity="medium",
 expected_next_command="show running-config (or DHCP pool config, to confirm the correct mask that should have been assigned)",
 expected_fix="Correct PC-BR5's subnet mask to 255.255.255.0 to match the rest of the Branch LAN, then re-test connectivity to HQ resources."),

# ---------------- TOPOLOGY D: Internet Edge (NAT/ACL/DNS) ----------------
dict(case_id="C019",
 symptom="No internal hosts can reach the internet; internal-to-internal traffic works fine.",
 topology_note="Topology D (Internet Edge): R-EDGE performs NAT overload (PAT) for inside network 172.16.0.0/16 going out Gi0/1 (outside, ISP-facing).",
 show_output="R-EDGE# show ip nat translations\n(no translations present)\n\nR-EDGE# show running-config | section ip nat\nip nat inside source list 1 interface GigabitEthernet0/1 overload\n!\naccess-list 1 permit 10.0.0.0 0.255.255.255\n\nR-EDGE# show ip interface brief | include Gi\nGigabitEthernet0/0      172.16.0.1      YES manual up                    up\nGigabitEthernet0/1      203.0.113.5     YES manual up                    up",
 expected_fault="NAT access-list 1 permits source network 10.0.0.0/8, but the actual inside network is 172.16.0.0/16. Since no inside host's address matches the ACL, nothing gets translated, so outbound internet traffic is dropped rather than PAT'ed.",
 osi_layer=3, concept_tag="nat", severity="high",
 expected_next_command="show ip nat statistics (to confirm zero hits against access-list 1)",
 expected_fix="Correct access-list 1 to match the real inside network: 'access-list 1 permit 172.16.0.0 0.0.255.255' (replacing or supplementing the existing incorrect entry), then verify translations appear in 'show ip nat translations' when a host generates outbound traffic."),

dict(case_id="C020",
 symptom="Internal hosts can generate outbound pings that appear to leave R-EDGE, but no NAT translations are ever created and return traffic never arrives.",
 topology_note="Topology D (Internet Edge): NAT requires 'ip nat inside' and 'ip nat outside' to be applied on the correct interfaces.",
 show_output="R-EDGE# show ip interface gi0/0 | include NAT\n  (no NAT-related output)\n\nR-EDGE# show ip interface gi0/1 | include NAT\n  Outside interface is not set (this router is NOT an outside NAT interface)\n\nR-EDGE# show running-config interface gi0/0\ninterface GigabitEthernet0/0\n ip address 172.16.0.1 255.255.0.0\n\nR-EDGE# show running-config interface gi0/1\ninterface GigabitEthernet0/1\n ip address 203.0.113.5 255.255.255.252",
 expected_fault="Neither Gi0/0 nor Gi0/1 has the required 'ip nat inside' / 'ip nat outside' commands applied. Without these, R-EDGE never triggers NAT translation for traffic crossing between the two interfaces even if the NAT rule and ACL themselves are correctly configured.",
 osi_layer=3, concept_tag="nat", severity="high",
 expected_next_command="show running-config | section ip nat (confirm the pool/overload statement exists and just needs the interface tags)",
 expected_fix="Apply 'ip nat inside' under interface GigabitEthernet0/0 and 'ip nat outside' under interface GigabitEthernet0/1 on R-EDGE, then confirm 'show ip nat translations' populates when a host sends outbound traffic."),

dict(case_id="C021",
 symptom="Internal users can reach external websites by typing IP addresses directly, but not by domain name.",
 topology_note="Topology D (Internet Edge): internal DNS forwarder should relay unresolved queries to an upstream public DNS server.",
 show_output="PC-INT12> nslookup example.com\nDNS request timed out.\ntimeout was 2 seconds.\n\nDNS-FWD# show running-config | section dns\nip dns server\n!\n(no 'ip name-server' forwarder configured)",
 expected_fault="The internal DNS forwarder (DNS-FWD) has 'ip dns server' enabled but no upstream 'ip name-server' address configured, so it has no way to forward or resolve external domain queries — it can only serve entries it locally knows (none, in this case), causing all external name lookups to time out.",
 osi_layer=7, concept_tag="dns", severity="medium",
 expected_next_command="show hosts (to confirm no locally cached/static entries exist that would mask the problem)",
 expected_fix="Configure an upstream forwarder on DNS-FWD, e.g. 'ip name-server 8.8.8.8', then re-test 'nslookup example.com' from an internal client."),

dict(case_id="C022",
 symptom="Internal users cannot browse any HTTPS websites, but HTTP (unencrypted) sites and ping to the internet both work fine.",
 topology_note="Topology D (Internet Edge): an extended ACL on R-EDGE's outbound interface controls what traffic classes are permitted to the internet.",
 show_output="R-EDGE# show access-lists 110\nExtended IP access list 110\n    10 permit tcp any any eq 80\n    20 permit icmp any any\n    30 deny tcp any any eq 443\n    40 permit ip any any\n\nR-EDGE# show ip interface gi0/1 | include access list\n  Outgoing access list is 110",
 expected_fault="ACL 110, applied outbound on Gi0/1, explicitly denies TCP port 443 (HTTPS) at line 30, before the general permit-any at line 40 is reached. HTTP (port 80) and ICMP are explicitly permitted earlier in the list, which is why they still work.",
 osi_layer=4, concept_tag="acl", severity="high",
 expected_next_command="show access-lists 110 (re-check after edit, and confirm no other device applies a conflicting ACL)",
 expected_fix="Remove or reorder ACL 110 line 30 (the deny for tcp port 443) so HTTPS traffic is permitted, e.g. by deleting that entry so traffic falls through to the permit-any statement, then re-test HTTPS access from an internal client."),

dict(case_id="C023",
 symptom="Only some internal hosts can reach the internet at a time; others intermittently lose connectivity, especially during peak usage hours.",
 topology_note="Topology D (Internet Edge): NAT overload (PAT) is configured using a single outside interface address, shared by the whole 172.16.0.0/16 inside network.",
 show_output="R-EDGE# show ip nat translations | count\nTotal translations: 1 (0 static, 1 dynamic; 1 extended)\n\nR-EDGE# show ip nat statistics\nTotal active translations: 1 (0 static, 1 dynamic, 0 extended)\nOutside interfaces: GigabitEthernet0/1\nInside interfaces: GigabitEthernet0/0\nHits: 4021  Misses: 812\nExpired translations: 39\n\nAdmin note: peak-hour trouble tickets correlate with 'Misses' climbing sharply and new sessions failing to establish.",
 expected_fault="NAT overload is using a single outside address for port-based translation, which supports many simultaneous sessions in theory, but the rising 'Misses' counter alongside failed new sessions at peak hours suggests the router is running out of available port mappings for that single outside IP under high concurrent load. Evidence points toward the single-address overload pool being a scaling bottleneck rather than a full misconfiguration, though a NAT pool with multiple addresses or session-timeout tuning would need to be confirmed as the fix by reviewing session limits.",
 osi_layer=3, concept_tag="nat", severity="medium",
 expected_next_command="show ip nat statistics (repeated over time, correlated with the ticket timestamps to confirm port exhaustion)",
 expected_fix="Consider expanding the NAT overload pool to use a small pool of outside addresses instead of a single IP (e.g. 'ip nat pool OUTSIDE_POOL 203.0.113.5 203.0.113.8 netmask 255.255.255.252' with 'ip nat inside source list 1 pool OUTSIDE_POOL overload'), and review/adjust NAT translation timeout values to free up ports from idle sessions sooner."),

dict(case_id="C024",
 symptom="External partners report they cannot establish a return connection for a service the internal team says it opened; internal-to-internet traffic works normally in the other direction.",
 topology_note="Topology D (Internet Edge): inbound ACL on the outside interface controls what unsolicited traffic is allowed in from the internet.",
 show_output="R-EDGE# show access-lists 120\nExtended IP access list 120\n    10 deny ip any any\n\nR-EDGE# show ip interface gi0/1 | include Inbound\n  Inbound  access list is 120",
 expected_fault="Inbound ACL 120 on the outside interface (Gi0/1) is a blanket 'deny ip any any' with no permit statements at all, blocking all unsolicited inbound traffic from the internet, including the return traffic or new inbound session partners are trying to establish.",
 osi_layer=4, concept_tag="acl", severity="high",
 expected_next_command="show running-config (to identify exactly which service/port the internal team intended to expose, before writing a permit rule)",
 expected_fix="Add a specific permit statement to ACL 120 for the required service (e.g. 'access-list 120 permit tcp any host 203.0.113.5 eq 443' for the intended port), keeping the deny-any as a final catch-all, then verify the partner's connection succeeds without over-opening the firewall."),

# ---------------- TOPOLOGY E: Wireless (WLC1 + AP1) ----------------
dict(case_id="C025",
 symptom="Guest Wi-Fi (Guest SSID, VLAN 50) users can reach the internet fine but can also reach the internal file server (10.10.99.10), which should be isolated from guests.",
 topology_note="Topology E (Wireless): WLC1 maps Guest SSID to VLAN 50; an ACL on the core switch is meant to block Guest VLAN from reaching internal server subnets.",
 show_output="SW-CORE# show access-lists GUEST_ISOLATION\nExtended IP access list GUEST_ISOLATION\n    10 permit ip 172.16.50.0 0.0.0.255 any\n\nSW-CORE# show ip interface vlan 50 | include access list\n  Inbound  access list is GUEST_ISOLATION",
 expected_fault="ACL GUEST_ISOLATION, applied inbound on the Guest VLAN 50 interface, only contains a permit-all statement for the guest subnet — there is no deny rule blocking guest traffic from reaching internal server subnets. The ACL currently does the opposite of its intended purpose.",
 osi_layer=3, concept_tag="wireless", severity="high",
 expected_next_command="show running-config (to identify the exact internal subnets that should be explicitly denied)",
 expected_fix="Rewrite ACL GUEST_ISOLATION to explicitly deny guest traffic to internal subnets before the permit-any, e.g. 'deny ip 172.16.50.0 0.0.0.255 10.10.99.0 0.0.0.255' (and any other internal ranges) followed by 'permit ip 172.16.50.0 0.0.0.255 any' for internet access, then verify guest hosts can no longer reach 10.10.99.10."),

dict(case_id="C026",
 symptom="Devices connecting to the Guest SSID authenticate to the wireless network but never receive an IP address.",
 topology_note="Topology E (Wireless): Guest SSID is mapped to VLAN 50 on WLC1; DHCP for Guest VLAN 50 should be relayed to DHCP-SRV.",
 show_output="WLC1# show wlan Guest-WiFi\nWLAN Identifier.................................. 2\nInterface......................................... guest-vlan50\n\nWLC1# show interface guest-vlan50\nInterface Name................................... guest-vlan50\nVLAN Identifier................................... 50\n\nSW-CORE# show running-config interface vlan 50\ninterface Vlan50\n ip address 172.16.50.1 255.255.255.0\n(no ip helper-address configured)",
 expected_fault="The Vlan50 (Guest) SVI on SW-CORE has no 'ip helper-address' pointing to the DHCP server, so guest client DHCP broadcast requests are never relayed off the local segment, and clients never receive an offer.",
 osi_layer=7, concept_tag="dhcp", severity="high",
 expected_next_command="show ip interface vlan 50 (confirm helper-address after fix)",
 expected_fix="Add 'ip helper-address 172.16.99.10' under 'interface Vlan50' on SW-CORE, then have a guest client reconnect and confirm it receives a 172.16.50.0/24 address."),

dict(case_id="C027",
 symptom="Corporate Wi-Fi users authenticate successfully but land on the Guest network subnet instead of the Corporate subnet.",
 topology_note="Topology E (Wireless): WLC1 should map Corporate SSID to VLAN 10 (Corporate interface) and Guest SSID to VLAN 50 (guest-vlan50 interface).",
 show_output="WLC1# show wlan Corp-WiFi\nWLAN Identifier.................................. 1\nInterface......................................... guest-vlan50\n\nWLC1# show wlan Guest-WiFi\nWLAN Identifier.................................. 2\nInterface......................................... guest-vlan50",
 expected_fault="The Corporate SSID (Corp-WiFi) is mapped to the 'guest-vlan50' interface instead of the intended Corporate interface (VLAN 10), so Corporate users are placed on the Guest VLAN. Both SSIDs are currently mapped to the same interface.",
 osi_layer=2, concept_tag="wireless", severity="high",
 expected_next_command="show interface summary (on WLC1, to confirm the correct interface name/VLAN for Corporate, e.g. 'corp-vlan10')",
 expected_fix="On WLC1, edit the Corp-WiFi WLAN's interface mapping to point to the Corporate interface (e.g. 'corp-vlan10'), leaving Guest-WiFi mapped to 'guest-vlan50', then verify Corporate clients receive addresses in the VLAN 10 subnet."),

dict(case_id="C028",
 symptom="Users in the far corner of the building report Wi-Fi 'connects' but is extremely slow or drops constantly, while users near the AP have no issues.",
 topology_note="Topology E (Wireless): AP1 serves both Corporate and Guest SSIDs for the building; the affected users are physically farthest from AP1.",
 show_output="WLC1# show client summary | include far-corner\n(client entries omitted for brevity - listing shows several clients with RSSI values)\n\nWLC1# show client detail 00:1A:2B:3C:4D:5E\nClient MAC Address............................... 00:1A:2B:3C:4D:5E\nAP MAC Address.................................... AP1\nRSSI.............................................. -82 dBm\nSNR................................................ 6 dB\nAssociation State.................................. Associated",
 expected_fault="The affected client shows an RSSI of -82 dBm and SNR of only 6 dB, both well outside the range considered reliable for consistent wireless performance (typically RSSI better than -70 dBm and SNR above 20 dB are desired). This points to a Layer 1 coverage/signal-strength problem due to distance from AP1, not a configuration fault.",
 osi_layer=1, concept_tag="wireless", severity="medium",
 expected_next_command="show ap summary (to check current AP placement, transmit power, and whether additional AP coverage is needed for that area)",
 expected_fix="This is a coverage issue rather than a misconfiguration: consider adding a second AP or a wireless repeater to cover the far corner, or increasing AP1's transmit power within regulatory limits if signal budget allows, then re-verify RSSI/SNR for affected clients."),

dict(case_id="C029",
 symptom="Several employees cannot connect to the Corporate SSID at all; their devices show 'incorrect password' even though the password matches the one on the printed office Wi-Fi card.",
 topology_note="Topology E (Wireless): Corp-WiFi SSID uses WPA2-PSK; WLC1 stores the pre-shared key configuration.",
 show_output="WLC1# show wlan Corp-WiFi\nWLAN Identifier.................................. 1\nSecurity...........................................\n   WPA2 PSK...................................... Enabled\n\nWLC1# show running-config | section wlan Corp-WiFi\nwlan Corp-WiFi 1 Corp-WiFi\n security wpa2 psk ascii CorpWifi2023!",
 expected_fault="The Wi-Fi PSK configured on WLC1 for Corp-WiFi is 'CorpWifi2023!', but this appears outdated relative to the printed office card (which the symptom implies employees are correctly copying). This suggests the key was recently rotated on the controller without updating the distributed printed card/documentation, so users are entering a stale, no-longer-valid password.",
 osi_layer=2, concept_tag="wireless", severity="medium",
 expected_next_command="show running-config (compare timestamp/change log if available, and confirm with IT admin when the PSK was last changed)",
 expected_fix="Either update the printed Wi-Fi card/documentation to match the current PSK 'CorpWifi2023!', or if that key was changed in error, revert WLC1's Corp-WiFi PSK to the documented value — confirm with the admin team which is the intended source of truth before changing controller configuration."),

dict(case_id="C030",
 symptom="A brand-new access point (AP2) added to extend coverage is not appearing in the wireless controller's AP list at all, and its status LED shows no association.",
 topology_note="Topology E (Wireless): new APs must join WLC1 over the wired network before they broadcast any SSID.",
 show_output="WLC1# show ap summary\nAP Name    Slots  AP Model              Ethernet MAC       Location   Country  IP Address        Clients\nAP1        2      AIR-AP1852I           58:97:BD:AA:AA:AA  IDF-1      US       172.16.10.20      14\n(AP2 not listed)\n\nSW-ACC3# show interfaces status | include Fa0/12\nFa0/12                connected   trunk                          a-full  a-100 10/100/1000BaseTX",
 expected_fault="AP2 is not listed in WLC1's AP summary at all, meaning it has not successfully joined the controller — evidence from the switch shows its port is up and trunking, so basic Layer 1/2 connectivity exists, but there is insufficient evidence here to confirm whether the issue is a missing/incorrect WLC discovery address on AP2, a VLAN/DHCP option 43 problem, or a certificate/join issue, without checking AP2's own console output directly.",
 osi_layer=7, concept_tag="wireless", severity="high",
 expected_next_command="show capwap client config (directly on AP2's console, to see what WLC IP/discovery method it is attempting to use)",
 expected_fix="Cannot be finalized without AP2's own console/discovery logs; likely candidates to check are DHCP Option 43 (WLC IP advertisement) on the AP's VLAN, correct primary/secondary WLC IP statically configured on the AP, and that AP2's management VLAN matches what SW-ACC3's trunk allows — confirm root cause before applying a fix."),
]

fieldnames = ["case_id","symptom","topology_note","show_output","expected_fault",
              "osi_layer","concept_tag","severity","expected_next_command","expected_fix"]

with open("/home/claude/netsage-ai/data/cases.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for c in cases:
        writer.writerow(c)

print(f"Wrote {len(cases)} cases to cases.csv")

# quick sanity check of category coverage
from collections import Counter
tags = Counter(c["concept_tag"] for c in cases)
print("Concept tag coverage:", dict(tags))
sev = Counter(c["severity"] for c in cases)
print("Severity coverage:", dict(sev))
