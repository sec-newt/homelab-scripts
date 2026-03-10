---
name: nmap-interpreter
description: Use when the user pastes nmap scan output and wants findings explained, risk-rated, or turned into next steps for a pentest, CTF, or security assessment.
---

# Nmap Interpreter

## Overview
Turn raw nmap output into structured findings: what's open, what it means, what to try next.

## Workflow

1. **Parse the scan** — note host, open ports, services, versions, OS guess
2. **Categorize findings** by risk (High → Low)
3. **Flag quick wins** — known vulnerable versions, default creds, dangerous services
4. **Suggest follow-up** — specific commands for each finding

## Port / Service Risk Reference

### High Priority (investigate first)
| Port(s) | Service | Why it matters |
|---------|---------|----------------|
| 21 | FTP | Often anonymous login; plaintext creds |
| 22 | SSH | Version fingerprint; brute force if weak creds |
| 23 | Telnet | Plaintext — should not exist |
| 80/443/8080/8443 | HTTP/HTTPS | Web app attack surface |
| 445 | SMB | EternalBlue, relay attacks, share enumeration |
| 1433/3306/5432 | MSSQL/MySQL/Postgres | DB access, often over-permissioned |
| 3389 | RDP | BlueKeep if old; brute force |
| 5900 | VNC | Often weak/no auth |
| 6379 | Redis | Unauthenticated by default |
| 27017 | MongoDB | Unauthenticated by default |

### Medium Priority
| Port(s) | Service | Why it matters |
|---------|---------|----------------|
| 25/587 | SMTP | Open relay, info disclosure |
| 53 | DNS | Zone transfer attempt |
| 111/2049 | RPC/NFS | NFS share enumeration |
| 161/162 | SNMP | Community strings (public/private) |
| 389/636 | LDAP | User enumeration, null bind |
| 8080/8443 | Alt HTTP | Admin panels, dev services |

### Lower Priority (still document)
| Port(s) | Service | Why it matters |
|---------|---------|----------------|
| 7/9/13/17/19 | Legacy | Should not be open |
| 69 | TFTP | Unauthenticated file read/write |
| 179 | BGP | Routing attack surface |

## Version Flags (always check)
- Any version number → search for CVEs: `searchsploit <service> <version>` or check NVD
- `OpenSSH 7.x` → check for username enumeration
- `Apache 2.4.49` → CVE-2021-41773 (path traversal)
- `vsftpd 2.3.4` → backdoor (classic CTF)
- Outdated Samba → EternalBlue variants

## Script Output Interpretation

| NSE Script | What to look for |
|------------|-----------------|
| `http-title` | Login pages, default installs, admin panels |
| `smb-vuln-*` | Direct exploit confirmation |
| `ftp-anon` | `Anonymous FTP login allowed` = immediate access |
| `ssl-cert` | Hostname mismatches, expiry, self-signed |
| `http-auth` | Basic auth = brute force opportunity |
| `dns-zone-transfer` | If successful = full DNS map |

## Output Format

```
TARGET: 10.10.10.5  (Linux, TTL 64)

[HIGH] Port 21/tcp — vsftpd 2.3.4
  Anonymous login: No  |  Version: known backdoor (CVE-2011-2523)
  Next: Try backdoor trigger → metasploit: exploit/unix/ftp/vsftpd_234_backdoor

[HIGH] Port 80/tcp — Apache 2.4.49
  Title: "Apache2 Default Page"
  Next: Test path traversal (CVE-2021-41773): curl http://10.10.10.5/cgi-bin/.%2e/.%2e/etc/passwd

[MEDIUM] Port 22/tcp — OpenSSH 7.4
  Next: Try default/common creds; check for username enumeration (CVE-2018-15473)

[LOW] Port 443/tcp — nginx 1.18.0
  SSL cert: self-signed, expired 2022-01-01
  Next: Run nikto, gobuster; check for interesting directories
```

## Common Mistakes

- **Stopping at port list** — service version and script output are where findings live
- **Skipping UDP** — DNS (53), SNMP (161), TFTP (69) only show on `-sU`
- **Ignoring filtered ports** — firewall rules are themselves information about the network
- **Not correlating ports** — SMB on 445 + Kerberos on 88 + LDAP on 389 = domain controller
