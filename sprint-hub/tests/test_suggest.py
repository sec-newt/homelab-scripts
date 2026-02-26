from sprint_hub.suggest import suggest_label

def test_suggest_from_nmap():
    assert suggest_label("Starting Nmap 7.94...\n22/tcp open ssh", command="nmap") == "port_scan"

def test_suggest_from_ffuf():
    assert suggest_label("/admin [Status: 200]", command="ffuf") == "ffuf_output"

def test_suggest_from_gobuster():
    assert suggest_label("/admin (Status: 200)", command="gobuster") == "dir_scan"

def test_suggest_from_unknown_command():
    assert suggest_label("some output", command="mytool") == "mytool_output"

def test_suggest_from_clipboard_matches_heading():
    text = "## Executive Summary\n\nSome content here"
    headings = ["Executive Summary", "Attack Vectors", "Threat Actors"]
    assert suggest_label(text, headings=headings) == "executive_summary"

def test_suggest_fallback_is_capture():
    assert suggest_label("random text") == "capture"

def test_suggest_with_no_args_is_capture():
    assert suggest_label("") == "capture"

def test_suggest_does_not_match_partial_heading():
    """Short clipboard text should not match a longer heading it is contained in."""
    text = "Attack"
    headings = ["Attack Vectors", "Threat Actors"]
    # "Attack" is contained IN "Attack Vectors", but "Attack Vectors" is NOT in "Attack"
    # So this should return "capture" (no match), not "attack_vectors"
    result = suggest_label(text, headings=headings)
    assert result == "capture"
