---
name: pcap-analyzer
description: Use when the user pastes Wireshark output, tshark summaries, or describes packet capture findings and wants them analyzed, explained, or structured for a writeup.
---

# PCAP Analyzer

## Overview
Structure packet capture observations into findings: what protocols, what behaviour, what's suspicious, what to include in a report or CTF writeup.

## Workflow

1. **Identify what you have** — full pcap file, tshark output, Wireshark screenshot, or verbal description
2. **Find the conversation** — who is talking to whom? On what protocol?
3. **Flag anomalies** — anything that shouldn't be there, or that deviates from normal
4. **Extract artifacts** — credentials, files, flags, commands
5. **Structure the writeup**

## Useful tshark One-Liners (to suggest to user)

```bash
# Protocol summary
tshark -r capture.pcap -q -z io,phs

# All conversations (IP pairs)
tshark -r capture.pcap -q -z conv,tcp

# HTTP requests
tshark -r capture.pcap -Y http.request -T fields -e http.host -e http.request.uri

# DNS queries
tshark -r capture.pcap -Y dns.qry.type==1 -T fields -e dns.qry.name

# Follow TCP stream (stream index 0)
tshark -r capture.pcap -q -z follow,tcp,ascii,0

# Extract files (HTTP objects)
tshark --export-objects http,./extracted/ -r capture.pcap

# Credentials in cleartext
tshark -r capture.pcap -Y "ftp || http.authbasic || telnet" -T fields -e text
```

## Common Findings and What They Mean

### Cleartext Credentials
| Protocol | What to look for |
|----------|-----------------|
| FTP | `USER` / `PASS` commands in TCP stream |
| HTTP Basic Auth | Base64 in `Authorization:` header — decode it |
| Telnet | Keystrokes visible in follow stream |
| SMTP AUTH PLAIN | Base64 encoded user:pass |
| LDAP | Bind request with password |

### Suspicious Traffic Patterns
| Pattern | Meaning |
|---------|---------|
| Many SYN, few SYN-ACK | Port scan (SYN scan) |
| ICMP to many hosts | Ping sweep / host discovery |
| DNS queries for unusual TLDs | DNS exfiltration or C2 beaconing |
| Long DNS TXT records | DNS tunneling (iodine, dnscat2) |
| Periodic outbound connections | C2 beaconing — check interval |
| Large outbound transfer, encrypted | Possible exfiltration |
| Cleartext POST with sensitive fields | Credential or data exposure |
| ARP for many IPs | ARP scan / network reconnaissance |

### CTF-Specific Patterns
| Artifact | How to find it |
|----------|----------------|
| Flag in HTTP response | Follow TCP/HTTP stream; search for flag format |
| Flag in DNS query | Filter `dns` — check query names |
| File embedded in pcap | Export Objects (File → Export Objects → HTTP/SMB/etc.) |
| Flag in ICMP payload | Follow ICMP stream or check Data field |
| Encoded data | Base64, hex, or custom encoding in any stream |

## Writeup Format

```
## Network Capture Analysis

### Overview
- Capture duration: X minutes
- Packets: N
- Protocols: TCP, HTTP, DNS, ...
- Notable hosts: 192.168.1.10 (attacker), 192.168.1.1 (gateway)

### Finding 1: Cleartext FTP Credentials [HIGH]
Stream 3 shows FTP login to 192.168.1.50:
  USER: admin
  PASS: password123
Extracted via: Follow TCP Stream → Stream 3

### Finding 2: Port Scan Detected [MEDIUM]
Host 192.168.1.10 sent SYN packets to 192.168.1.50 on ports 20–1024
between 10:02:14–10:02:17. No established connections (all RST).

### Artifacts Recovered
- Credential: admin:password123 (FTP)
- File: invoice.pdf extracted from HTTP stream 7
- Flag: CTF{pcap_1s_fun} found in ICMP echo payload (packet 142)
```

## Common Mistakes

- **Only looking at one protocol** — cross-correlate (DNS resolves the IP that HTTP then hits)
- **Missing encrypted traffic context** — TLS won't show content, but metadata (SNI, cert CN, timing) still tells a story
- **Not following streams** — packet-by-packet is harder than Follow Stream for understanding sessions
- **Overlooking non-standard ports** — HTTP often runs on 8080, 8443, 9000; filter by protocol decode not just port
