from __future__ import annotations
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Label, ListItem, ListView

import sprint_hub.capture as _cap_mod
import sprint_hub.config as _cfg_mod
from sprint_hub.capture import Buffer
from sprint_hub.config import SprintConfig
from sprint_hub.push import push_all
from sprint_hub.google_api import GoogleAPI


class BufferPanel(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("── BUFFER ──")
        yield ListView(id="buffer-list")

    def refresh_entries(self, buffer: Buffer) -> None:
        lv = self.query_one("#buffer-list", ListView)
        lv.clear()
        for entry in buffer.entries:
            preview = entry.content[:60].replace("\n", " ")
            if len(entry.content) > 60:
                preview += "…"
            lv.append(ListItem(Label(f"[bold]{entry.label}[/bold]  {preview}")))


class SectionPanel(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("── SECTIONS ──")
        yield ListView(id="sections-list")

    def refresh_sections(self, items: list[str]) -> None:
        lv = self.query_one("#sections-list", ListView)
        lv.clear()
        for item in items:
            lv.append(ListItem(Label(item)))


class SprintHubApp(App):
    CSS = """
    Screen { layout: vertical; }
    Horizontal#panels { height: 1fr; }
    BufferPanel  { width: 1fr; border: solid $primary;   padding: 1; }
    SectionPanel { width: 1fr; border: solid $secondary; padding: 1; }
    #action-bar  { height: 3; layout: horizontal; align: center middle; }
    """

    BINDINGS = [
        Binding("q", "quit",         "Quit"),
        Binding("p", "push_all",     "Push All"),
        Binding("r", "refresh",      "Refresh"),
        Binding("d", "delete_entry", "Delete"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="panels"):
            yield BufferPanel()
            yield SectionPanel()
        with Horizontal(id="action-bar"):
            yield Button("Push All [P]", id="btn-push",    variant="success")
            yield Button("Refresh [R]",  id="btn-refresh", variant="default")
            yield Button("Quit [Q]",     id="btn-quit",    variant="error")
        yield Footer()

    def on_mount(self) -> None:
        self._load_state()

    def _load_state(self) -> None:
        config_dir = _cfg_mod.CONFIG_DIR
        active = SprintConfig.get_active(config_dir=config_dir)
        self.title = f"Sprint Hub — {active}" if active else "Sprint Hub — no active sprint"
        self._config = SprintConfig.load(active, config_dir=config_dir) if active else None
        self._buffer = Buffer.for_active_sprint(config_dir=_cap_mod.CONFIG_DIR)
        self._buffer.load()
        self.query_one(BufferPanel).refresh_entries(self._buffer)
        if self._config:
            self.query_one(SectionPanel).refresh_sections(
                list(self._config.captures.keys())
            )

    def action_delete_entry(self) -> None:
        lv = self.query_one("#buffer-list", ListView)
        idx = lv.index if lv.index is not None else 0
        if not self._buffer.entries or idx >= len(self._buffer.entries):
            self.notify("Nothing selected.", severity="warning")
            return
        label = self._buffer.entries[idx].label
        self._buffer.remove(label)
        self._buffer.save()
        self.notify(f"Deleted '{label}'.")
        self._load_state()

    def action_refresh(self) -> None:
        self._load_state()

    def action_push_all(self) -> None:
        if not self._config:
            self.notify("No active sprint.", severity="error")
            return
        self.notify("Pushing…")
        try:
            results = push_all(self._buffer, self._config, api=GoogleAPI())
            ok  = sum(1 for v in results.values() if v == "ok")
            err = sum(1 for v in results.values() if v != "ok")
            self.notify(f"Done: {ok} pushed, {err} errors.")
            if err == 0:
                self._buffer.clear()
                self._buffer.save()
                self._load_state()
        except Exception as e:
            # Strip extra quotes that KeyError.__str__ adds
            msg = str(e).strip('"')
            self.notify(msg, severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        actions = {
            "btn-push":    self.action_push_all,
            "btn-refresh": self.action_refresh,
            "btn-quit":    self.exit,
        }
        if event.button.id in actions:
            actions[event.button.id]()
