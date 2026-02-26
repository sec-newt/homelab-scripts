# sprint-hub

A Hyprland-integrated CLI + TUI that captures labeled text from any source
(terminal output, browser clipboard) and pushes it to the correct Google
Docs/Sheets cell in one keypress.

Built to eliminate copy-paste errors and window-switching friction when working
at high screen magnification (4–5×). Each capture is held in a local buffer
until you're ready to push everything to Google at once.

---

## The problem

Working at high zoom means losing your place every time you switch windows.
Copying nmap output into a spreadsheet cell requires: zoom out → switch to
browser → find the right cell → paste → zoom back in → find where you were.

Sprint Hub collapses that to: pipe output → press `Super+F12` → press `P`.

---

## Architecture

```
sprint_hub/
├── config.py      — per-sprint YAML config (doc URLs, label→cell mappings)
├── capture.py     — JSON buffer with add/remove/persist
├── suggest.py     — auto-label heuristics (nmap → port_scan, ffuf → directory_scan)
├── google_api.py  — OAuth2 wrapper for Docs and Sheets APIs
├── push.py        — buffer → Google routing logic
├── cli.py         — Click entry points (sprint-init, sprint-capture, etc.)
└── tui.py         — Textual TUI scratchpad
```

Config lives in `~/.config/sprint-hub/`. One YAML file per sprint, plus a
`buffer.json` holding queued captures and an `active` pointer file.

---

## Installation

**Requires:** Python 3.12+, `pipx`, a Wayland compositor (for clipboard capture)

```bash
git clone https://github.com/sec-newt/homelab-scripts.git
cd homelab-scripts/sprint-hub
pipx install .
```

Verify:
```bash
sprint-capture --help
```

---

## First-time setup

### 1. Google Cloud credentials (once per Google account)

You need OAuth credentials to write to Google Docs/Sheets.

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → **APIs & Services → Library** → enable:
   - Google Docs API
   - Google Sheets API
3. **APIs & Services → OAuth consent screen**
   - User Type: External
   - Add scopes: `documents`, `spreadsheets`, `drive.readonly`
   - Add your Google account as a test user
4. **Credentials → Create Credentials → OAuth client ID**
   - Application type: Desktop app
5. Download the JSON → save as `~/.config/sprint-hub/credentials.json`

### 2. Initialise a sprint

```bash
sprint-init --name sprint-5
```

Paste a Google Doc or Sheets URL when prompted. The tool fetches the document
structure (headings for Docs, sheet names for Sheets) and asks you to map
capture labels to destinations:

```
Sheets: Enumeration, Exploitation, Loot
  Enumeration: port_scan=B4, service_scan=C4
  Exploitation: ffuf_output=B2
```

---

## Daily usage

### Capture from the terminal

```bash
nmap -sV 10.0.0.1 | sprint-capture
ffuf -w wordlist.txt -u http://target/FUZZ | sprint-capture
cat output.txt | sprint-capture --label loot
```

The label is auto-suggested from the command name. You can accept it (Enter)
or type a different one.

### Capture from the browser (Hyprland)

```
Super + Shift + X   →  captures clipboard → saves with auto-label
```

See [Fixing a wrong label](#fixing-a-wrong-label) if the auto-label is wrong.

### Push to Google

```
Super + F12   →  opens TUI
P             →  push all buffered entries to Google
```

Or from the terminal: `sprint-hub` then press `P`.

### Mid-sprint: new document unlocked

```bash
sprint-add --url "https://docs.google.com/spreadsheets/d/..."
```

Merges the new document into the existing sprint config without losing prior
mappings.

---

## Fixing a wrong label

| Situation | Command |
|-----------|---------|
| Label is wrong, content is fine | `sprint-relabel wrong correct` |
| Need to edit the captured text | `sprint-edit label` — opens in `$EDITOR` |
| Delete the entry entirely | `sprint-remove label` (or `D` in TUI) |
| Delete and re-capture from clipboard | `sprint-remove label` then `sprint-capture --from-clipboard --label correct` |

---

## All commands

| Command | What it does |
|---------|-------------|
| `sprint-init --name NAME` | Create sprint config, map docs interactively |
| `sprint-add --url URL` | Add a newly-unlocked doc mid-sprint |
| `sprint-capture` | Capture piped text with auto-suggested label |
| `sprint-capture --from-clipboard` | Capture Wayland clipboard |
| `sprint-capture --label NAME` | Capture with explicit label (skips auto-suggest) |
| `sprint-remove LABEL` | Delete buffer entry |
| `sprint-relabel OLD NEW` | Rename label in-place (content unchanged) |
| `sprint-edit LABEL` | Edit entry content in `$EDITOR` |
| `sprint-hub` | Open Textual TUI scratchpad |

---

## Hyprland integration (optional)

Add to `~/.config/hypr/conf.d/40-binds.conf`:

```conf
# Sprint Hub scratchpad
bind = $mainMod, F12, togglespecialworkspace, sprint-hub
bind = $mainMod SHIFT, X, exec, sprint-capture --from-clipboard
```

Add to `~/.config/hypr/conf.d/20-autostart.conf`:

```conf
exec-once = [workspace special:sprint-hub silent] sprint-hub
```

Change `F12` / `SHIFT+X` if those conflict with existing binds.

---

## Running tests

```bash
cd sprint-hub
pip install -e ".[dev]"
pytest tests/ -v
```

51 tests covering config persistence, buffer operations, Google API (mocked),
push routing, label auto-suggest, CLI commands, and the Textual TUI.

---

## Config file format

`~/.config/sprint-hub/sprint-N.yaml`:

```yaml
sprint: sprint-5
docs:
  - id: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
    type: sheet
    label: Worksheet
    added_chapter: 1
captures:
  port_scan:
    destination_id: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
    type: sheet
    sheet_name: Enumeration
    cell: B4
  exec_summary:
    destination_id: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
    type: doc
    heading: Executive Summary
```

Labels are arbitrary — use whatever makes sense for your workflow.

---

## Skills demonstrated

Python · Textual TUI · Google Docs/Sheets API · OAuth2 · Click CLI ·
Wayland clipboard (wl-paste) · Hyprland scratchpad integration · pipx packaging ·
YAML config · pytest + unittest.mock · accessible UI design (high-zoom workflow)
