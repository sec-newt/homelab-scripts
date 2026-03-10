---
name: log-analyzer
description: Use when the user pastes or describes security log entries from auth.log, syslog, firewall logs, IDS/IPS alerts, or application logs and wants them parsed, annotated, or investigated.
---

# Log Analyzer

## Overview
Structure raw log output into findings with context, risk level, and next steps.

## Workflow

1. **Identify log type** — auth.log, syslog, firewall, web access, IDS alert, etc.
2. **Scan for anomalies** — use patterns below
3. **Cluster related events** — group by source IP / user / time window
4. **Assign risk level** — Low / Medium / High / Critical
5. **Recommend next steps** — specific, actionable

## Log Types and Key Patterns

### auth.log / secure
| Pattern | Meaning | Risk |
|---------|---------|------|
| `Failed password for` | Failed SSH/login attempt | Medium (single), High (repeated) |
| `Failed password for invalid user` | Brute force against non-existent accounts | High |
| `Accepted password for root` | Root login via password | High — should be key-only |
| `Accepted publickey` | Normal key-based login | Low |
| `session opened for user root` | Root session started | Medium — note who/when |
| `sudo: ... COMMAND=` | Privilege escalation | Note command; flag if unusual |
| `PAM: Authentication failure` | Failed auth (any PAM service) | See context |
| `POSSIBLE BREAK-IN ATTEMPT` | Reverse DNS mismatch | Investigate source IP |

### Firewall / iptables / ufw
| Pattern | Meaning | Risk |
|---------|---------|------|
| `[UFW BLOCK]` | Blocked connection attempt | Low-High depending on target port |
| High volume from single IP | Scanning or DoS | High |
| Outbound to unusual ports/IPs | Possible exfiltration or C2 | High |
| `DPT=22` blocked repeatedly | SSH scan | Medium |
| `DPT=3389` | RDP probe | High if internet-facing |

### Web Access Logs (Apache/Nginx)
| Pattern | Meaning | Risk |
|---------|---------|------|
| `404` flood | Directory scanning | Medium |
| `POST /xmlrpc.php`, `/wp-login.php` | WordPress brute force | High |
| SQL keywords in URL | SQLi probe | High |
| `../` in URL | Path traversal | High |
| Unusual user agent strings | Automated scanners | Medium |
| 4xx/5xx spike | Attack or misconfiguration | Investigate |

### Syslog / journald
| Pattern | Meaning | Risk |
|---------|---------|------|
| `Out of memory: Kill process` | OOM killer fired | Investigate cause |
| `segfault` | Crash — could indicate exploit | Investigate binary |
| `kernel: audit:` | Auditd event — check rule | Depends on rule |
| Repeated cron errors | Misconfigured job | Low |

## Brute Force Threshold (rough guides)
- **5+ failures in 1 minute** from same IP → High
- **Distributed** (many IPs, same username) → Credential stuffing
- **Many usernames, same IP** → Username enumeration

## Output Format

When presenting findings:

```
[HIGH] SSH brute force from 203.0.113.42
  Events: 47 failed password attempts for 'root' between 02:14–02:17
  Last entry: Mar 9 02:17:44 sshd[1234]
  Recommendation: Block IP at firewall; check if any attempt succeeded

[MEDIUM] Root login via password accepted
  Event: Accepted password for root from 192.168.1.10 port 52341
  Recommendation: Disable PasswordAuthentication for root in sshd_config; use keys only

[LOW] Normal user session
  4 successful logins for 'alice' via publickey — no action needed
```

## Common Mistakes

- **Treating every block as an alert** — internet-facing IPs get scanned constantly; volume and targeting matter
- **Missing the success after failures** — always check if a brute force attempt eventually succeeded
- **Ignoring timestamps** — correlate events by time window, not just event type
- **Forgetting outbound** — compromised hosts phone home; watch for unusual outbound traffic too
