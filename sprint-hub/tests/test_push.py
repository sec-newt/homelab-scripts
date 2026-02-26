import pytest
from unittest.mock import MagicMock
from sprint_hub.config import SprintConfig, Capture, SprintDoc
from sprint_hub.capture import Buffer, BufferEntry
from sprint_hub.push import push_all, push_entry

@pytest.fixture
def sample_config(tmp_path):
    cfg = SprintConfig.create("sprint-test", config_dir=tmp_path)
    cfg.add_doc(SprintDoc(id="sheet123", type="sheet", label="WS", added_chapter=1))
    cfg.add_capture("port_scan", Capture(
        destination_id="sheet123", type="sheet",
        sheet_name="Enumeration", cell="B4"
    ))
    cfg.add_doc(SprintDoc(id="doc456", type="doc", label="Report", added_chapter=2))
    cfg.add_capture("exec_summary", Capture(
        destination_id="doc456", type="doc", heading="Executive Summary"
    ))
    return cfg

def test_push_sheet_entry(sample_config):
    entry = BufferEntry(label="port_scan", content="nmap output", source="pipe")
    mock_api = MagicMock()
    push_entry(entry, sample_config, api=mock_api)
    mock_api.write_sheet_cell.assert_called_once_with(
        spreadsheet_id="sheet123",
        sheet_name="Enumeration",
        cell="B4",
        value="nmap output",
    )

def test_push_doc_entry(sample_config):
    entry = BufferEntry(label="exec_summary", content="Report content", source="clipboard")
    mock_api = MagicMock()
    push_entry(entry, sample_config, api=mock_api)
    mock_api.append_to_heading.assert_called_once_with(
        document_id="doc456",
        heading_text="Executive Summary",
        content="Report content",
    )

def test_push_unmapped_label_raises(sample_config):
    entry = BufferEntry(label="unknown_label", content="text", source="pipe")
    with pytest.raises(KeyError, match="unknown_label"):
        push_entry(entry, sample_config, api=MagicMock())

def test_push_all_returns_ok_for_each(sample_config, tmp_path):
    buf = Buffer(path=tmp_path / "buffer.json")
    buf.add("port_scan", "nmap output")
    results = push_all(buf, sample_config, api=MagicMock())
    assert results["port_scan"] == "ok"

def test_push_all_captures_errors(sample_config, tmp_path):
    buf = Buffer(path=tmp_path / "buffer.json")
    buf.add("bad_label", "some text")
    results = push_all(buf, sample_config, api=MagicMock())
    assert results["bad_label"].startswith("error:")

def test_push_all_continues_after_error(sample_config, tmp_path):
    buf = Buffer(path=tmp_path / "buffer.json")
    buf.add("bad_label", "text")
    buf.add("port_scan", "nmap output")
    results = push_all(buf, sample_config, api=MagicMock())
    assert results["bad_label"].startswith("error:")
    assert results["port_scan"] == "ok"
