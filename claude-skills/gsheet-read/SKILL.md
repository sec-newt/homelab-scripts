---
name: gsheet-read
description: Read the content of a Google Sheet by URL. Use when the user provides a Google Sheets URL and wants you to read its data. Optionally reads a specific sheet tab.
---

When the user provides a Google Sheets URL, run:

```bash
# Read all sheets:
gsheet-read <url>

# Read a specific sheet tab:
gsheet-read <url> "Sheet Name"
```

The script outputs tab-separated content with sheet names as headers. Read it and proceed with whatever the user asked you to do with it.

If the command fails with an auth error, tell the user to run:
```bash
python -c "from sprint_hub.google_api import GoogleAPI; GoogleAPI()"
```
to re-authenticate.
