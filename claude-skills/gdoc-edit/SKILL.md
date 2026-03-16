---
name: gdoc-edit
description: Read and edit the content of a Google Doc. Use when the user provides a Google Docs URL and wants to replace, update, or modify text in the document.
---

**Do NOT write a new Python script file or use google-api-python-client from scratch.** The `gdoc-edit` CLI command and `GoogleAPI` class are already set up with credentials. Use them directly.

Replace text in a Google Doc with one of two approaches depending on how many replacements you need.

## Single replacement — CLI

```bash
gdoc-edit <url> "old text" "new text"
```

Prints `Replaced N occurrence(s)` on success. If it prints `WARNING: 0 occurrences changed`, see the **Split Text Run** section below.

`replaceAllText` works across all tabs in the document — no tab targeting needed.

## Batch replacements — inline Python

When making multiple replacements, batch them into one API call to avoid round-trips:

```python
python3 - <<'EOF'
import sys; sys.path.insert(0, '.')
from sprint_hub.google_api import GoogleAPI

api = GoogleAPI()
doc_id = "YOUR_DOC_ID"   # extract from URL: /document/d/<ID>/

replacements = [
    ("old text 1", "new text 1"),
    ("old text 2", "new text 2"),
]

requests = [
    {"replaceAllText": {"containsText": {"text": old, "matchCase": True}, "replaceText": new}}
    for old, new in replacements
]

result = api.docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

for label, reply in zip([r[0] for r in replacements], result.get("replies", [])):
    count = reply.get("replaceAllText", {}).get("occurrencesChanged", 0)
    print(f"{'✓' if count else '✗'} {label[:50]} ({count})")
EOF
```

## Split Text Run (0 occurrences warning)

Google Docs stores text as a tree of runs, not a flat string. A phrase like `"Time to Recover (TTR)"` may be split across multiple runs — the API then finds 0 matches even though the text appears visibly in the doc.

**Diagnosis:** run `gdoc-read <url>` and search for the exact string in the output. If it appears in gdoc-read output but replaceAllText returns 0, the text is split across runs.

**Fix:** manually edit that specific paragraph in the browser, then re-read to confirm the new text, then you can use `gdoc-edit` on it from that point forward.

## Auth error

If either command fails with an auth error, re-authenticate:

```bash
python -c "from sprint_hub.google_api import GoogleAPI; GoogleAPI()"
```
