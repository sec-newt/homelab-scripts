from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import yaml

CONFIG_DIR = Path.home() / ".config" / "sprint-hub"


@dataclass
class SprintDoc:
    id: str
    type: str          # "doc" or "sheet"
    label: str
    added_chapter: int


@dataclass
class Capture:
    destination_id: str
    type: str          # "doc" or "sheet"
    sheet_name: Optional[str] = None
    cell: Optional[str] = None
    heading: Optional[str] = None


@dataclass
class SprintConfig:
    sprint: str
    docs: list[SprintDoc] = field(default_factory=list)
    captures: dict[str, Capture] = field(default_factory=dict)
    _config_dir: Path = field(default_factory=lambda: CONFIG_DIR, repr=False)

    # ── persistence ──────────────────────────────────────────────────────────

    def save(self) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)
        path = self._config_dir / f"{self.sprint}.yaml"
        data = {
            "sprint": self.sprint,
            "docs": [
                {"id": d.id, "type": d.type,
                 "label": d.label, "added_chapter": d.added_chapter}
                for d in self.docs
            ],
            "captures": {
                name: {k: v for k, v in {
                    "destination_id": c.destination_id,
                    "type": c.type,
                    "sheet_name": c.sheet_name,
                    "cell": c.cell,
                    "heading": c.heading,
                }.items() if v is not None}
                for name, c in self.captures.items()
            },
        }
        path.write_text(yaml.safe_dump(data, default_flow_style=False))

    @classmethod
    def load(cls, sprint: str, config_dir: Path = CONFIG_DIR) -> "SprintConfig":
        path = config_dir / f"{sprint}.yaml"
        data = yaml.safe_load(path.read_text())
        docs = [SprintDoc(**d) for d in data.get("docs", [])]
        captures = {
            name: Capture(**vals)
            for name, vals in data.get("captures", {}).items()
        }
        cfg = cls(sprint=data["sprint"], docs=docs, captures=captures)
        cfg._config_dir = config_dir
        return cfg

    @classmethod
    def create(cls, sprint: str, config_dir: Path = CONFIG_DIR) -> "SprintConfig":
        cfg = cls(sprint=sprint)
        cfg._config_dir = config_dir
        return cfg

    # ── mutation ─────────────────────────────────────────────────────────────

    def add_doc(self, doc: SprintDoc) -> None:
        if not any(d.id == doc.id for d in self.docs):
            self.docs.append(doc)

    def add_capture(self, name: str, capture: Capture) -> None:
        self.captures[name] = capture

    # ── active sprint pointer ─────────────────────────────────────────────────

    @staticmethod
    def set_active(sprint: str, config_dir: Path = CONFIG_DIR) -> None:
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "active").write_text(sprint)

    @staticmethod
    def get_active(config_dir: Path = CONFIG_DIR) -> Optional[str]:
        path = config_dir / "active"
        return path.read_text().strip() if path.exists() else None
