from __future__ import annotations
import click
from pathlib import Path

from sprint_hub.config import SprintConfig, SprintDoc, Capture
from sprint_hub.capture import Buffer, read_from_clipboard, read_from_stdin
from sprint_hub.suggest import suggest_label


@click.command("sprint-init")
@click.option("--name", prompt="Sprint name (e.g. sprint-11)")
@click.option("--url", default=None, help="Google Doc or Sheet URL (optional)")
def init(name: str, url: str | None):
    """Create a new sprint. Run once at the start of each sprint."""
    cfg = SprintConfig.create(name)
    if url:
        _add_url_to_config(cfg, url, chapter=1)
    cfg.save()
    SprintConfig.set_active(name)
    click.echo(f"Sprint '{name}' created and set as active.")


@click.command("sprint-add")
@click.option("--url", prompt="Google Doc or Sheet URL")
@click.option("--chapter", default=None, type=int)
def add(url: str, chapter: int | None):
    """Add a new document to the active sprint."""
    active = SprintConfig.get_active()
    if not active:
        click.echo("No active sprint. Run sprint-init first.", err=True)
        raise SystemExit(1)
    cfg = SprintConfig.load(active)
    chapter = chapter or (max((d.added_chapter for d in cfg.docs), default=0) + 1)
    _add_url_to_config(cfg, url, chapter=chapter)
    cfg.save()
    click.echo(f"Added to sprint '{active}'.")


@click.command("sprint-capture")
@click.option("--from-clipboard", "from_clip", is_flag=True)
@click.option("--label", default=None)
@click.option("--command", default=None, help="Hint for auto-suggest (e.g. nmap)")
def capture(from_clip: bool, label: str | None, command: str | None):
    """Capture text into the buffer.

    Pipe from terminal:   nmap -sV 10.0.0.1 | sprint-capture
    From clipboard:       sprint-capture --from-clipboard
    """
    if from_clip:
        content = read_from_clipboard()
        source = "clipboard"
    else:
        content = read_from_stdin()
        if content is None:
            click.echo("No input. Pipe something or use --from-clipboard.", err=True)
            raise SystemExit(1)
        source = "pipe"

    headings: list[str] = []
    active = SprintConfig.get_active()
    if active:
        try:
            cfg = SprintConfig.load(active)
            headings = list(cfg.captures.keys())
        except Exception:
            pass

    suggestion = label or suggest_label(content, command=command, headings=headings)
    final_label = click.prompt("Label", default=suggestion)

    buf = Buffer.for_active_sprint()
    buf.load()
    buf.add(final_label, content, source=source)
    buf.save()
    click.echo(f"Captured {content.count(chr(10)) + 1} lines as '{final_label}'.")


@click.command("sprint-remove")
@click.argument("label")
def remove(label: str):
    """Remove a labeled entry from the buffer."""
    buf = Buffer.for_active_sprint()
    buf.load()
    if not any(e.label == label for e in buf.entries):
        click.echo(f"Label '{label}' not found in buffer.", err=True)
        raise SystemExit(1)
    buf.remove(label)
    buf.save()
    click.echo(f"Removed '{label}' from buffer.")


@click.command("sprint-relabel")
@click.argument("old_label")
@click.argument("new_label")
def relabel(old_label: str, new_label: str):
    """Rename a buffer entry label without changing its content."""
    buf = Buffer.for_active_sprint()
    buf.load()
    entry = next((e for e in buf.entries if e.label == old_label), None)
    if entry is None:
        click.echo(f"Label '{old_label}' not found in buffer.", err=True)
        raise SystemExit(1)
    entry.label = new_label
    buf.save()
    click.echo(f"Renamed '{old_label}' → '{new_label}'.")


@click.command("sprint-edit")
@click.argument("label")
def edit_entry(label: str):
    """Open a buffer entry's content in $EDITOR."""
    buf = Buffer.for_active_sprint()
    buf.load()
    entry = next((e for e in buf.entries if e.label == label), None)
    if entry is None:
        click.echo(f"Label '{label}' not found in buffer.", err=True)
        raise SystemExit(1)
    updated = click.edit(entry.content)
    if updated is None:
        click.echo("Unchanged.")
        return
    entry.content = updated
    buf.save()
    click.echo(f"Updated '{label}'.")


@click.command("sprint-hub")
def hub():
    """Open the Sprint Hub TUI."""
    from sprint_hub.tui import SprintHubApp
    SprintHubApp().run()


# ── helpers ───────────────────────────────────────────────────────────────────

def _add_url_to_config(cfg: SprintConfig, url: str, chapter: int) -> None:
    from sprint_hub.google_api import GoogleAPI   # lazy import: not needed by capture/hub
    doc_id, doc_type = GoogleAPI.extract_id_from_url(url)
    try:
        api = GoogleAPI()
        if doc_type == "sheet":
            sheets = api.get_sheet_names(doc_id)
            label = click.prompt("Label for this spreadsheet",
                                 default=sheets[0] if sheets else "Worksheet")
            _prompt_sheet_captures(cfg, doc_id, sheets)
        else:
            headings = api.get_doc_headings(doc_id)
            label = click.prompt("Label for this document", default="Report")
            _prompt_doc_captures(cfg, doc_id, headings)
    except FileNotFoundError as e:
        click.echo(str(e), err=True)
        label = click.prompt("Label (API unavailable, enter manually)")
    cfg.add_doc(SprintDoc(id=doc_id, type=doc_type, label=label, added_chapter=chapter))


def _prompt_sheet_captures(cfg: SprintConfig, doc_id: str, sheets: list[str]) -> None:
    click.echo("\nSheets: " + ", ".join(sheets))
    click.echo("Enter captures as  name=CELL  pairs, comma-separated.")
    click.echo("Example:  port_scan=B4, ffuf_output=C2   (or press Enter to skip)\n")
    for sheet in sheets:
        raw = click.prompt(f"  {sheet}", default="", show_default=False)
        for part in raw.split(","):
            part = part.strip()
            if "=" not in part:
                continue
            name, cell = [x.strip() for x in part.split("=", 1)]
            cfg.add_capture(name, Capture(
                destination_id=doc_id, type="sheet",
                sheet_name=sheet, cell=cell
            ))


def _prompt_doc_captures(cfg: SprintConfig, doc_id: str, headings: list[str]) -> None:
    click.echo("\nHeadings found:")
    for i, h in enumerate(headings, 1):
        click.echo(f"  {i}. {h}")
    click.echo("Enter captures as  name=NUMBER  pairs.")
    click.echo("Example:  exec_summary=1, solutions=3   (or press Enter to skip)\n")
    raw = click.prompt("Captures", default="", show_default=False)
    for part in raw.split(","):
        part = part.strip()
        if "=" not in part:
            continue
        name, idx_str = [x.strip() for x in part.split("=", 1)]
        try:
            idx = int(idx_str) - 1
            if idx < 0 or idx >= len(headings):
                raise IndexError
            heading = headings[idx]
            cfg.add_capture(name, Capture(
                destination_id=doc_id, type="doc", heading=heading
            ))
        except (ValueError, IndexError):
            click.echo(f"Skipping '{name}' — bad index '{idx_str}'", err=True)
