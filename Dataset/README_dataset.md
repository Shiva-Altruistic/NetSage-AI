# NetSage AI — Dataset (cases.csv)

## Provenance
These 30 cases are **synthetic, instructor-style troubleshooting scenarios** —
written to match realistic Cisco IOS `show`-command syntax and internally
consistent topology/IP/VLAN logic. They are **not** captured from a live
network or a real Packet Tracer session. This is disclosed here and should
be repeated in your project's Responsible AI documentation and README, since
your rubric requires evidence to be traceable and honest about its source.

If you have time before the deadline, replace some or all of these with
cases captured directly from Packet Tracer (see the base topologies below —
they were designed so you can rebuild them in PT and swap in real `show`
output without changing the CSV schema).

## Topologies used (5 total, 6 cases each except Wireless which has 6→ adjusted to 6/6/6/6/6=30)
| ID | Name | Devices | Subnets |
|---|---|---|---|
| A | SOHO Branch | R1-BR (router-on-a-stick), SW1 | VLAN10 10.10.10.0/24, VLAN20 10.10.20.0/24, VLAN99 10.10.99.0/24 |
| B | Campus L3 | SW-CORE (SVIs), SW-DIST, SW-ACC/SW-ACC2 | VLAN30 172.16.30.0/24, VLAN40 172.16.40.0/24, servers 172.16.99.0/24 |
| C | WAN | R1 (HQ), R2 (Branch) | 192.168.1.0/24, 192.168.2.0/24, link 192.168.12.0/30 |
| D | Internet Edge | R-EDGE | inside 172.16.0.0/16, outside 203.0.113.4/30 |
| E | Wireless | WLC1, AP1 (+AP2) | Corporate VLAN10, Guest VLAN50 172.16.50.0/24 |

## Coverage
- **Fault categories**: vlan (4), gateway (4), dhcp (4), dns (3), routing (4), acl (3), nat (3), wireless (5) — all 8 required categories present.
- **Severity**: currently high/medium only — no "low" severity cases. Recommend adding 3-5 low-severity cases (e.g. minor DNS staleness, single-client RSSI dip) before submission so the dashboard's severity chart isn't skewed.
- Case C005 and C023 and C030 are intentionally written as "insufficient evidence, needs one more command" cases — useful for testing that your AI prompt correctly says "possible/unknown" instead of forcing a confident diagnosis. Good candidates to feature in your Responsible AI log.

## Schema
`case_id, symptom, topology_note, show_output, expected_fault, osi_layer, concept_tag, severity, expected_next_command, expected_fix`

`expected_fault`, `expected_next_command`, `expected_fix` are your **ground truth** for evaluation — not what the AI should be shown. Feed the AI only `symptom`, `topology_note`, and `show_output`, then compare its output against these fields.
