import pytest
from unittest.mock import MagicMock, patch
from sprint_hub.google_api import GoogleAPI

@patch("sprint_hub.google_api.build")
def test_write_sheet_cell(mock_build):
    api = GoogleAPI.__new__(GoogleAPI)
    api.sheets = mock_build.return_value
    api.docs = MagicMock()

    api.write_sheet_cell(
        spreadsheet_id="sheet123",
        sheet_name="Enumeration",
        cell="B4",
        value="nmap output here"
    )

    mock_build.return_value.spreadsheets.return_value \
        .values.return_value.update.assert_called_once()

@patch("sprint_hub.google_api.build")
def test_get_sheet_structure(mock_build):
    mock_sheet = mock_build.return_value
    mock_sheet.spreadsheets.return_value.get.return_value.execute.return_value = {
        "sheets": [
            {"properties": {"title": "Enumeration"}},
            {"properties": {"title": "Attack Vectors"}},
        ]
    }
    api = GoogleAPI.__new__(GoogleAPI)
    api.sheets = mock_sheet

    result = api.get_sheet_names("sheet123")
    assert result == ["Enumeration", "Attack Vectors"]

@patch("sprint_hub.google_api.build")
def test_get_doc_headings(mock_build):
    mock_doc = mock_build.return_value
    mock_doc.documents.return_value.get.return_value.execute.return_value = {
        "body": {
            "content": [
                {"paragraph": {
                    "paragraphStyle": {"namedStyleType": "HEADING_1"},
                    "elements": [{"textRun": {"content": "Executive Summary\n"}}]}},
                {"paragraph": {
                    "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                    "elements": [{"textRun": {"content": "Body text\n"}}]}},
                {"paragraph": {
                    "paragraphStyle": {"namedStyleType": "HEADING_2"},
                    "elements": [{"textRun": {"content": "Attack Vectors\n"}}]}},
            ]
        }
    }
    api = GoogleAPI.__new__(GoogleAPI)
    api.docs = mock_doc

    headings = api.get_doc_headings("doc123")
    assert "Executive Summary" in headings
    assert "Attack Vectors" in headings
    assert "Body text" not in headings

def test_extract_id_from_sheet_url():
    url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdK/edit#gid=0"
    doc_id, doc_type = GoogleAPI.extract_id_from_url(url)
    assert doc_id == "1BxiMVs0XRA5nFMdK"
    assert doc_type == "sheet"

def test_extract_id_from_doc_url():
    url = "https://docs.google.com/document/d/1abc123xyz/edit"
    doc_id, doc_type = GoogleAPI.extract_id_from_url(url)
    assert doc_id == "1abc123xyz"
    assert doc_type == "doc"

def test_extract_id_raises_on_bad_url():
    with pytest.raises(ValueError):
        GoogleAPI.extract_id_from_url("https://evil.com/spreadsheets/d/FAKEID/edit")
    with pytest.raises(ValueError):
        GoogleAPI.extract_id_from_url("https://google.com/notadoc")

@patch("sprint_hub.google_api.build")
def test_append_to_heading(mock_build):
    mock_doc_service = mock_build.return_value
    mock_doc_service.documents.return_value.get.return_value.execute.return_value = {
        "body": {
            "content": [
                {
                    "endIndex": 20,
                    "paragraph": {
                        "paragraphStyle": {"namedStyleType": "HEADING_1"},
                        "elements": [{"textRun": {"content": "Executive Summary\n"}}],
                    },
                }
            ]
        }
    }
    mock_doc_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

    api = GoogleAPI.__new__(GoogleAPI)
    api.docs = mock_doc_service

    api.append_to_heading("doc123", "Executive Summary", "Some content")

    call_args = mock_doc_service.documents.return_value.batchUpdate.call_args
    requests = call_args.kwargs["body"]["requests"]
    assert len(requests) == 1
    insert = requests[0]["insertText"]
    assert insert["location"]["index"] == 20   # endIndex unmodified, NOT endIndex - 1
    assert "Some content" in insert["text"]

def test_find_heading_end_index_returns_endIndex():
    doc = {
        "body": {
            "content": [
                {
                    "endIndex": 20,
                    "paragraph": {
                        "paragraphStyle": {"namedStyleType": "HEADING_1"},
                        "elements": [{"textRun": {"content": "Executive Summary\n"}}],
                    },
                }
            ]
        }
    }
    result = GoogleAPI._find_heading_end_index(doc, "Executive Summary")
    assert result == 20   # must equal endIndex exactly

def test_find_heading_end_index_returns_none_when_missing():
    doc = {"body": {"content": []}}
    assert GoogleAPI._find_heading_end_index(doc, "Missing Heading") is None
