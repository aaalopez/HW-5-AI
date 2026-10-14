"""Append-only audit trail at output/audit_trail.json.

Never truncated or wiped between runs — each call reads whatever is already
there, appends, and writes the full array back, so a history of every agent
loop step accumulates across runs.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

AUDIT_PATH = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> list:
    if not AUDIT_PATH.exists():
        return []
    try:
        data = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def append_audit(entry: dict) -> None:
    """Add one entry to the audit trail without wiping existing history."""
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    entries = _load()
    entries.append(entry)
    AUDIT_PATH.write_text(json.dumps(entries, indent=2, default=str), encoding="utf-8")
