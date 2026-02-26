from __future__ import annotations
import json
import sys
import subprocess
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.home() / ".config" / "sprint-hub"


@dataclass
class BufferEntry:
    label: str
    content: str
    source: str = "unknown"


@dataclass
class Buffer:
    path: Path
    entries: list[BufferEntry] = field(default_factory=list)

    def load(self) -> None:
        if self.path.exists():
            data = json.loads(self.path.read_text())
            self.entries = [BufferEntry(**e) for e in data]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([asdict(e) for e in self.entries], indent=2))

    def add(self, label: str, content: str, source: str = "unknown") -> None:
        self.entries = [e for e in self.entries if e.label != label]
        self.entries.append(BufferEntry(label=label, content=content, source=source))

    def remove(self, label: str) -> None:
        self.entries = [e for e in self.entries if e.label != label]

    def clear(self) -> None:
        self.entries = []

    @classmethod
    def for_active_sprint(cls, config_dir: Path = CONFIG_DIR) -> "Buffer":
        """Return a Buffer pointed at the active sprint's buffer file.

        Note: does NOT auto-load entries. Call .load() after to get persisted data:
            buf = Buffer.for_active_sprint()
            buf.load()
        """
        return cls(path=config_dir / "buffer.json")


def read_from_clipboard() -> str:
    """Read text from Wayland clipboard using wl-paste."""
    result = subprocess.run(
        ["wl-paste", "--no-newline"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"wl-paste failed: {result.stderr.strip()}")
    return result.stdout


def read_from_stdin() -> Optional[str]:
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return None
