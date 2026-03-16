# Claude / OpenClaw Skills

Reference skills for Claude Code and OpenClaw — security-focused tools for homelab and CTF work, plus Google Docs/Sheets API integration.

Skills are markdown documents loaded automatically by Claude when the task matches the skill's trigger. They encode proven workflows so you don't repeat the same instructions every session.

## Skills

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `docker-compose-helper` | Generating or auditing Docker Compose files | Security audit checklist + secure-by-default template |
| `log-analyzer` | Pasting security log entries | Parses auth.log, firewall, web logs — risk levels and next steps |
| `nmap-interpreter` | Pasting nmap scan output | Rates findings, flags vulnerable versions, suggests follow-up |
| `pcap-analyzer` | Pasting Wireshark/tshark output | tshark one-liners, pattern reference, writeup structure |
| `gdoc-read` | User provides a Google Docs URL to read | Runs `gdoc-read <url>`, returns full document text |
| `gsheet-read` | User provides a Google Sheets URL to read | Runs `gsheet-read <url>`, returns tab-separated sheet data |
| `gdoc-edit` | User wants to replace or update text in a Google Doc | Single replacement via CLI or batched via inline Python |

## Installation

### Claude Code

```bash
# Each skill goes in its own directory under ~/.claude/skills/
cp -r docker-compose-helper ~/.claude/skills/
cp -r log-analyzer ~/.claude/skills/
cp -r nmap-interpreter ~/.claude/skills/
cp -r pcap-analyzer ~/.claude/skills/
cp -r gdoc-read ~/.claude/skills/
cp -r gsheet-read ~/.claude/skills/
cp -r gdoc-edit ~/.claude/skills/
```

### OpenClaw

Each skill needs a `_meta.json` alongside the `SKILL.md`:

```bash
for skill in docker-compose-helper log-analyzer nmap-interpreter pcap-analyzer gdoc-read gsheet-read gdoc-edit; do
  mkdir -p ~/.openclaw/workspace/skills/$skill
  cp $skill/SKILL.md ~/.openclaw/workspace/skills/$skill/
  echo "{\"ownerId\":\"local\",\"slug\":\"$skill\",\"version\":\"1.0.0\",\"publishedAt\":$(date +%s%3N)}" \
    > ~/.openclaw/workspace/skills/$skill/_meta.json
done
```

## Skill Format

Each skill is a `SKILL.md` with YAML frontmatter:

```yaml
---
name: skill-name
description: Use when [specific triggering conditions]
---
```

The `description` is what Claude reads to decide whether to load the skill. Keep it starting with "Use when..." and describe the situation, not the skill's process.
