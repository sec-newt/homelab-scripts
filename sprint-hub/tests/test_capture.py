from sprint_hub.capture import Buffer, BufferEntry

def test_add_entry(tmp_path):
    buf = Buffer(path=tmp_path / "buffer.json")
    buf.add("port_scan", "nmap output text")
    assert len(buf.entries) == 1
    assert buf.entries[0].label == "port_scan"

def test_buffer_persists(tmp_path):
    buf_path = tmp_path / "buffer.json"
    buf = Buffer(path=buf_path)
    buf.add("ffuf_output", "some ffuf results")
    buf.save()

    buf2 = Buffer(path=buf_path)
    buf2.load()
    assert buf2.entries[0].label == "ffuf_output"

def test_add_replaces_same_label(tmp_path):
    buf = Buffer(path=tmp_path / "buffer.json")
    buf.add("port_scan", "first")
    buf.add("port_scan", "second")
    assert len(buf.entries) == 1
    assert buf.entries[0].content == "second"

def test_remove_entry(tmp_path):
    buf = Buffer(path=tmp_path / "buffer.json")
    buf.add("port_scan", "nmap output")
    buf.add("ffuf_output", "ffuf output")
    buf.remove("port_scan")
    assert len(buf.entries) == 1
    assert buf.entries[0].label == "ffuf_output"

def test_clear_buffer(tmp_path):
    buf = Buffer(path=tmp_path / "buffer.json")
    buf.add("a", "text a")
    buf.add("b", "text b")
    buf.clear()
    assert buf.entries == []

def test_load_empty_when_no_file(tmp_path):
    buf = Buffer(path=tmp_path / "nonexistent.json")
    buf.load()  # should not raise
    assert buf.entries == []

def test_for_active_sprint_requires_explicit_load(tmp_path):
    """Verify that for_active_sprint + load() retrieves persisted entries."""
    import sprint_hub.capture as cap_mod
    original = cap_mod.CONFIG_DIR
    cap_mod.CONFIG_DIR = tmp_path

    # Write a buffer file
    buf1 = Buffer(path=tmp_path / "buffer.json")
    buf1.add("test_label", "test content")
    buf1.save()

    # Retrieve it via for_active_sprint
    buf2 = Buffer.for_active_sprint(config_dir=tmp_path)
    assert buf2.entries == []  # not loaded yet
    buf2.load()
    assert len(buf2.entries) == 1
    assert buf2.entries[0].label == "test_label"

    cap_mod.CONFIG_DIR = original
