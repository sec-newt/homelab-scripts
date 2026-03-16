---
name: gdoc-read
description: Read the full text content of a Google Doc. Use when the user provides a Google Docs URL and wants you to read it.
---

When the user provides a Google Docs URL, run:

```bash
gdoc-read <url>
```

The script outputs the full plain text of the document. Read it and proceed with whatever the user asked you to do with it.

If the command fails with an auth error, tell the user to run:
```bash
python -c "from sprint_hub.google_api import GoogleAPI; GoogleAPI()"
```
to re-authenticate.
