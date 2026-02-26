import pytest
import sprint_hub.config as cfg_mod
import sprint_hub.capture as cap_mod

@pytest.fixture(autouse=True)
def patch_dirs(tmp_path, monkeypatch):
    cfg_dir = tmp_path / ".config" / "sprint-hub"
    monkeypatch.setattr(cfg_mod, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(cap_mod, "CONFIG_DIR", cfg_dir)

def test_tui_imports():
    from sprint_hub.tui import SprintHubApp
    assert SprintHubApp is not None

@pytest.mark.asyncio
async def test_tui_starts_without_active_sprint():
    from sprint_hub.tui import SprintHubApp
    app = SprintHubApp()
    async with app.run_test() as pilot:
        assert "no active sprint" in app.title.lower()
        await pilot.press("q")

@pytest.mark.asyncio
async def test_tui_delete_removes_selected_entry(tmp_path):
    from sprint_hub.tui import SprintHubApp
    from sprint_hub.capture import Buffer

    buf_path = tmp_path / ".config" / "sprint-hub" / "buffer.json"
    buf_path.parent.mkdir(parents=True, exist_ok=True)
    buf = Buffer(path=buf_path)
    buf.add("port_scan", "nmap output")
    buf.add("notes", "some notes")
    buf.save()

    cfg = cfg_mod.SprintConfig.create("sprint-test",
                                      config_dir=tmp_path / ".config" / "sprint-hub")
    cfg.save()
    cfg_mod.SprintConfig.set_active("sprint-test",
                                     config_dir=tmp_path / ".config" / "sprint-hub")

    app = SprintHubApp()
    async with app.run_test() as pilot:
        await pilot.press("d")
        buf2 = Buffer(path=buf_path)
        buf2.load()
        labels = [e.label for e in buf2.entries]
        assert "port_scan" not in labels
        assert "notes" in labels
        await pilot.press("q")


@pytest.mark.asyncio
async def test_tui_shows_buffer_entries(tmp_path):
    from sprint_hub.tui import SprintHubApp
    from sprint_hub.capture import Buffer, BufferEntry

    # Create a buffer with an entry
    buf_path = tmp_path / ".config" / "sprint-hub" / "buffer.json"
    buf_path.parent.mkdir(parents=True, exist_ok=True)
    buf = Buffer(path=buf_path)
    buf.add("test_entry", "some content here")
    buf.save()

    # Set up a minimal sprint config
    cfg = cfg_mod.SprintConfig.create("sprint-test",
                                      config_dir=tmp_path / ".config" / "sprint-hub")
    cfg.save()
    cfg_mod.SprintConfig.set_active("sprint-test",
                                     config_dir=tmp_path / ".config" / "sprint-hub")

    app = SprintHubApp()
    async with app.run_test() as pilot:
        assert "sprint-test" in app.title
        await pilot.press("q")
