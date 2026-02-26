from __future__ import annotations
from sprint_hub.capture import Buffer, BufferEntry
from sprint_hub.config import SprintConfig
from sprint_hub.google_api import GoogleAPI


def push_entry(
    entry: BufferEntry,
    config: SprintConfig,
    api: GoogleAPI | None = None,
) -> None:
    """Push a single buffer entry to its mapped destination.

    Raises:
        KeyError: if the entry's label has no mapping in config.captures
        ValueError: if the capture type is unknown
    """
    if entry.label not in config.captures:
        raise KeyError(f"No mapping for '{entry.label}'. Add it to the sprint YAML.")

    if api is None:
        api = GoogleAPI()

    cap = config.captures[entry.label]

    if cap.type == "sheet":
        api.write_sheet_cell(
            spreadsheet_id=cap.destination_id,
            sheet_name=cap.sheet_name,
            cell=cap.cell,
            value=entry.content,
        )
    elif cap.type == "doc":
        api.append_to_heading(
            document_id=cap.destination_id,
            heading_text=cap.heading,
            content=entry.content,
        )
    else:
        raise ValueError(f"Unknown destination type: {cap.type}")


def push_all(
    buffer: Buffer,
    config: SprintConfig,
    api: GoogleAPI | None = None,
) -> dict[str, str]:
    """Push all buffer entries. Returns {label: 'ok' | 'error: ...'} for each.

    Never raises — errors are captured in the result dict so the full
    buffer is attempted even if some entries fail.
    """
    if api is None:
        api = GoogleAPI()

    results: dict[str, str] = {}
    for entry in buffer.entries:
        try:
            push_entry(entry, config, api=api)
            results[entry.label] = "ok"
        except Exception as e:
            results[entry.label] = f"error: {e}"
    return results
