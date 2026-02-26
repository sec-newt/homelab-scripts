from __future__ import annotations
import re
from typing import Optional

_COMMAND_MAP: dict[str, str] = {
    "nmap":      "port_scan",
    "masscan":   "port_scan",
    "ffuf":      "ffuf_output",
    "gobuster":  "dir_scan",
    "dirsearch": "dir_scan",
    "nikto":     "vuln_scan",
    "sqlmap":    "sqli_output",
    "hydra":     "brute_force",
    "hashcat":   "hash_crack",
    "john":      "hash_crack",
    "wfuzz":     "ffuf_output",
    "curl":      "curl_output",
    "wget":      "wget_output",
}


def suggest_label(
    text: str,
    command: Optional[str] = None,
    headings: Optional[list[str]] = None,
) -> str:
    """Return a snake_case label suggestion.

    Priority: command map -> heading match -> 'capture'.
    """
    if command:
        base = command.split("/")[-1].split()[0].lower()
        return _COMMAND_MAP.get(base, _to_snake(f"{base}_output"))

    if headings:
        first_line = text.strip().splitlines()[0] if text.strip() else ""
        clean = re.sub(r"^#+\s*", "", first_line).strip()
        for heading in headings:
            if heading.lower() in clean.lower():
                return _to_snake(heading)

    return "capture"


def _to_snake(text: str) -> str:
    text = re.sub(r"[^\w\s]", "_", text)
    text = re.sub(r"\s+", "_", text.strip())
    text = re.sub(r"_+", "_", text)
    return text.lower().strip("_")
