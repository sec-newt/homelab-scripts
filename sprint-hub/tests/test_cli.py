import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
import sprint_hub.config as cfg_mod
import sprint_hub.capture as cap_mod
from sprint_hub.cli import init, capture, remove, relabel, edit_entry


@pytest.fixture(autouse=True)
def patch_dirs(tmp_path, monkeypatch):
    cfg_dir = tmp_path / ".config" / "sprint-hub"
    cfg_dir.mkdir(parents=True, exist_ok=True)

    # Patch module-level CONFIG_DIR variables
    monkeypatch.setattr(cfg_mod, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(cap_mod, "CONFIG_DIR", cfg_dir)

    # Wrap SprintConfig static/class methods to default to our cfg_dir.
    # Access the underlying functions via __dict__ to get the descriptors.
    _orig_set_active = cfg_mod.SprintConfig.__dict__["set_active"].__func__
    _orig_get_active = cfg_mod.SprintConfig.__dict__["get_active"].__func__
    _orig_load = cfg_mod.SprintConfig.__dict__["load"].__func__
    _orig_create = cfg_mod.SprintConfig.__dict__["create"].__func__
    _orig_for_active = cap_mod.Buffer.__dict__["for_active_sprint"].__func__

    def _set_active(sprint, config_dir=cfg_dir):
        return _orig_set_active(sprint, config_dir)

    def _get_active(config_dir=cfg_dir):
        return _orig_get_active(config_dir)

    def _load(cls, sprint, config_dir=cfg_dir):
        return _orig_load(cls, sprint, config_dir)

    def _create(cls, sprint, config_dir=cfg_dir):
        return _orig_create(cls, sprint, config_dir)

    def _for_active(cls, config_dir=cfg_dir):
        return _orig_for_active(cls, config_dir)

    monkeypatch.setattr(cfg_mod.SprintConfig, "set_active", staticmethod(_set_active))
    monkeypatch.setattr(cfg_mod.SprintConfig, "get_active", staticmethod(_get_active))
    monkeypatch.setattr(cfg_mod.SprintConfig, "load", classmethod(_load))
    monkeypatch.setattr(cfg_mod.SprintConfig, "create", classmethod(_create))
    monkeypatch.setattr(cap_mod.Buffer, "for_active_sprint", classmethod(_for_active))


def test_init_creates_sprint():
    runner = CliRunner()
    result = runner.invoke(init, ["--name", "sprint-test"])
    assert result.exit_code == 0, result.output
    assert "sprint-test" in result.output


def test_init_sets_active_sprint(tmp_path, monkeypatch):
    runner = CliRunner()
    runner.invoke(init, ["--name", "sprint-active"])
    # get_active is already patched by autouse fixture to use our cfg_dir
    active = cfg_mod.SprintConfig.get_active()
    assert active == "sprint-active"


def test_capture_from_pipe():
    runner = CliRunner()
    runner.invoke(init, ["--name", "sprint-test"])
    # Mock read_from_stdin so it returns content without consuming CliRunner's
    # stdin, leaving stdin available for the click.prompt("Label") call.
    with patch("sprint_hub.cli.read_from_stdin", return_value="test content\nline2"):
        result = runner.invoke(
            capture, ["--label", "my_output"],
            input="my_output\n",  # answer for the label prompt
        )
    assert result.exit_code == 0, result.output
    assert "my_output" in result.output


def test_capture_no_input_fails():
    runner = CliRunner()
    # Mock read_from_stdin to return None to simulate no piped input
    with patch("sprint_hub.cli.read_from_stdin", return_value=None):
        result = runner.invoke(capture, [])
    assert result.exit_code == 1
    assert "No input" in result.output


def test_capture_auto_suggest_from_label():
    runner = CliRunner()
    runner.invoke(init, ["--name", "sprint-test"])
    # Mock read_from_stdin so stdin is available for the click.prompt call.
    # suggest_label with no command/headings returns "capture".
    with patch("sprint_hub.cli.read_from_stdin", return_value="nmap output"):
        result = runner.invoke(
            capture, [],
            input="\n",  # accept the default label suggestion
        )
    assert result.exit_code == 0, result.output


def test_remove_deletes_buffer_entry(tmp_path):
    from sprint_hub.capture import Buffer, BufferEntry
    runner = CliRunner()
    runner.invoke(init, ["--name", "sprint-test"])

    buf_path = tmp_path / ".config" / "sprint-hub" / "buffer.json"
    buf = Buffer(path=buf_path)
    buf.add("port_scan", "nmap output")
    buf.add("notes", "some notes")
    buf.save()

    result = runner.invoke(remove, ["port_scan"])
    assert result.exit_code == 0, result.output
    assert "port_scan" in result.output

    buf2 = Buffer(path=buf_path)
    buf2.load()
    labels = [e.label for e in buf2.entries]
    assert "port_scan" not in labels
    assert "notes" in labels


def test_remove_nonexistent_label_exits_with_error():
    runner = CliRunner()
    runner.invoke(init, ["--name", "sprint-test"])
    result = runner.invoke(remove, ["nonexistent"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_relabel_renames_entry_in_place(tmp_path):
    from sprint_hub.capture import Buffer
    runner = CliRunner()
    runner.invoke(init, ["--name", "sprint-test"])

    buf_path = tmp_path / ".config" / "sprint-hub" / "buffer.json"
    buf = Buffer(path=buf_path)
    buf.add("old_name", "important content")
    buf.save()

    result = runner.invoke(relabel, ["old_name", "new_name"])
    assert result.exit_code == 0, result.output

    buf2 = Buffer(path=buf_path)
    buf2.load()
    labels = [e.label for e in buf2.entries]
    assert "old_name" not in labels
    assert "new_name" in labels
    assert buf2.entries[0].content == "important content"


def test_relabel_nonexistent_label_exits_with_error():
    runner = CliRunner()
    runner.invoke(init, ["--name", "sprint-test"])
    result = runner.invoke(relabel, ["ghost", "new_name"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_edit_entry_opens_editor_and_saves_result(tmp_path):
    from sprint_hub.capture import Buffer
    runner = CliRunner()
    runner.invoke(init, ["--name", "sprint-test"])

    buf_path = tmp_path / ".config" / "sprint-hub" / "buffer.json"
    buf = Buffer(path=buf_path)
    buf.add("notes", "original content")
    buf.save()

    with patch("sprint_hub.cli.click.edit", return_value="edited content"):
        result = runner.invoke(edit_entry, ["notes"])
    assert result.exit_code == 0, result.output

    buf2 = Buffer(path=buf_path)
    buf2.load()
    assert buf2.entries[0].content == "edited content"


def test_edit_entry_no_change_when_editor_returns_none(tmp_path):
    from sprint_hub.capture import Buffer
    runner = CliRunner()
    runner.invoke(init, ["--name", "sprint-test"])

    buf_path = tmp_path / ".config" / "sprint-hub" / "buffer.json"
    buf = Buffer(path=buf_path)
    buf.add("notes", "original content")
    buf.save()

    with patch("sprint_hub.cli.click.edit", return_value=None):
        result = runner.invoke(edit_entry, ["notes"])
    assert result.exit_code == 0, result.output
    assert "unchanged" in result.output.lower()

    buf2 = Buffer(path=buf_path)
    buf2.load()
    assert buf2.entries[0].content == "original content"


def test_edit_entry_nonexistent_label_exits_with_error():
    runner = CliRunner()
    runner.invoke(init, ["--name", "sprint-test"])
    result = runner.invoke(edit_entry, ["ghost"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_init_without_credentials_still_creates_sprint(tmp_path, monkeypatch):
    """When Google credentials are missing, sprint-init should still work with a manual label."""
    from unittest.mock import patch
    from sprint_hub.google_api import GoogleAPI
    import sprint_hub.config as cfg_mod2
    cfg_dir = tmp_path / ".config2" / "sprint-hub"
    monkeypatch.setattr(cfg_mod, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(cap_mod, "CONFIG_DIR", cfg_dir)

    runner = CliRunner()
    with patch.object(GoogleAPI, "__init__",
                      side_effect=FileNotFoundError("credentials.json not found")):
        result = runner.invoke(
            init,
            ["--name", "sprint-nocreds",
             "--url", "https://docs.google.com/document/d/abc123/edit"],
            input="Manual Label\n"   # response to the "Label (API unavailable)" prompt
        )
    assert result.exit_code == 0, result.output
    assert "sprint-nocreds" in result.output
