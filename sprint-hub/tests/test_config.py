import pytest
from pathlib import Path
from sprint_hub.config import SprintConfig, Capture, SprintDoc

def test_create_new_sprint(tmp_path):
    cfg = SprintConfig.create("sprint-11", config_dir=tmp_path)
    assert cfg.sprint == "sprint-11"
    assert cfg.docs == []
    assert cfg.captures == {}

def test_save_and_load(tmp_path):
    cfg = SprintConfig.create("sprint-11", config_dir=tmp_path)
    cfg.add_doc(SprintDoc(id="abc123", type="sheet", label="Worksheet", added_chapter=1))
    cfg.add_capture("port_scan", Capture(
        destination_id="abc123", type="sheet",
        sheet_name="Enumeration", cell="B4"
    ))
    cfg.save()

    loaded = SprintConfig.load("sprint-11", config_dir=tmp_path)
    assert loaded.sprint == "sprint-11"
    assert loaded.docs[0].id == "abc123"
    assert loaded.captures["port_scan"].cell == "B4"

def test_add_doc_does_not_overwrite_captures(tmp_path):
    cfg = SprintConfig.create("sprint-11", config_dir=tmp_path)
    cfg.add_capture("ffuf_output", Capture(
        destination_id="abc123", type="sheet",
        sheet_name="Attack Vectors", cell="C2"
    ))
    cfg.add_doc(SprintDoc(id="newdoc", type="doc", label="Report", added_chapter=4))
    cfg.save()

    loaded = SprintConfig.load("sprint-11", config_dir=tmp_path)
    assert "ffuf_output" in loaded.captures
    assert len(loaded.docs) == 1

def test_get_active_sprint(tmp_path):
    SprintConfig.create("sprint-11", config_dir=tmp_path).save()
    SprintConfig.set_active("sprint-11", config_dir=tmp_path)
    assert SprintConfig.get_active(config_dir=tmp_path) == "sprint-11"
