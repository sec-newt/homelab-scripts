from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CONFIG_DIR = Path.home() / ".config" / "sprint-hub"
SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]


class GoogleAPI:
    def __init__(self, config_dir: Path = CONFIG_DIR):
        creds = self._get_credentials(config_dir)
        self.sheets = build("sheets", "v4", credentials=creds)
        self.docs   = build("docs",   "v1", credentials=creds)

    # ── auth ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _get_credentials(config_dir: Path) -> Credentials:
        """Load or refresh OAuth2 credentials. Token stored as JSON."""
        token_path = config_dir / "token.json"
        creds_path = config_dir / "credentials.json"
        creds: Optional[Credentials] = None

        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not creds_path.exists():
                    raise FileNotFoundError(
                        f"credentials.json not found at {creds_path}\n"
                        "See the Pre-Flight steps in the implementation plan."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(creds_path), SCOPES
                )
                creds = flow.run_local_server(port=0)

            config_dir.mkdir(parents=True, exist_ok=True)
            token_path.write_text(creds.to_json())
            token_path.chmod(0o600)

        return creds

    # ── sheets ────────────────────────────────────────────────────────────────

    def get_sheet_names(self, spreadsheet_id: str) -> list[str]:
        result = (
            self.sheets.spreadsheets()
            .get(spreadsheetId=spreadsheet_id, fields="sheets/properties/title")
            .execute()
        )
        return [s["properties"]["title"] for s in result.get("sheets", [])]

    def write_sheet_cell(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        cell: str,
        value: str,
    ) -> None:
        range_notation = f"{sheet_name}!{cell}"
        self.sheets.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_notation,
            valueInputOption="RAW",
            body={"values": [[value]]},
        ).execute()

    # ── docs ──────────────────────────────────────────────────────────────────

    def get_doc_headings(self, document_id: str) -> list[str]:
        doc = self.docs.documents().get(documentId=document_id).execute()
        headings = []
        for elem in doc.get("body", {}).get("content", []):
            para = elem.get("paragraph", {})
            style = para.get("paragraphStyle", {}).get("namedStyleType", "")
            if style.startswith("HEADING"):
                text = "".join(
                    r.get("textRun", {}).get("content", "")
                    for r in para.get("elements", [])
                ).strip()
                if text:
                    headings.append(text)
        return headings

    def append_to_heading(
        self,
        document_id: str,
        heading_text: str,
        content: str,
    ) -> None:
        """Append content after the first heading matching heading_text."""
        doc = self.docs.documents().get(documentId=document_id).execute()
        insert_index = self._find_heading_end_index(doc, heading_text)
        if insert_index is None:
            raise ValueError(f"Heading '{heading_text}' not found in document")

        self.docs.documents().batchUpdate(
            documentId=document_id,
            body={
                "requests": [{
                    "insertText": {
                        "location": {"index": insert_index},
                        "text": f"\n{content}",
                    }
                }]
            },
        ).execute()

    @staticmethod
    def _find_heading_end_index(doc: dict, heading_text: str) -> Optional[int]:
        for elem in doc.get("body", {}).get("content", []):
            para = elem.get("paragraph", {})
            style = para.get("paragraphStyle", {}).get("namedStyleType", "")
            if not style.startswith("HEADING"):
                continue
            text = "".join(
                r.get("textRun", {}).get("content", "")
                for r in para.get("elements", [])
            ).strip()
            if heading_text.lower() in text.lower():
                end = elem.get("endIndex")
                if end is not None:
                    return end
        return None

    # ── url parsing ───────────────────────────────────────────────────────────

    @staticmethod
    def extract_id_from_url(url: str) -> tuple[str, str]:
        """Return (doc_id, doc_type) where doc_type is 'doc' or 'sheet'.

        Raises ValueError if the URL is not a recognised Google Docs/Sheets URL.
        """
        sheet_match = re.search(r"docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)", url)
        if sheet_match:
            return sheet_match.group(1), "sheet"
        doc_match = re.search(r"docs\.google\.com/document/d/([a-zA-Z0-9_-]+)", url)
        if doc_match:
            return doc_match.group(1), "doc"
        raise ValueError(f"Could not extract a Google Docs or Sheets ID from: {url}")
