"""Trace storage.

Traces are stored as directories:
  .agent-traces/
    <session-id>/
      meta.json       # session metadata
      events.ndjson   # newline-delimited JSON events

NDJSON is append-only. No database. No dependencies. Just files.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from .models import EventType, SessionMeta, TraceEvent

DEFAULT_TRACE_DIR = ".agent-traces"


class TraceStore:
    def __init__(self, base_dir: str | Path = DEFAULT_TRACE_DIR):
        self.base_dir = Path(base_dir)

    def _session_dir(self, session_id: str) -> Path:
        if not session_id or ".." in session_id or "/" in session_id or "\x00" in session_id:
            raise ValueError(f"Invalid session ID: {session_id!r}")
        return self.base_dir / session_id

    def create_session(self, meta: SessionMeta) -> Path:
        d = self._session_dir(meta.session_id)
        d.mkdir(parents=True, exist_ok=True)
        (d / "meta.json").write_text(meta.to_json())
        # create empty events file
        (d / "events.ndjson").touch()
        return d

    def append_event(self, session_id: str, event: TraceEvent) -> None:
        f = self._session_dir(session_id) / "events.ndjson"
        with open(f, "a") as fh:
            fh.write(event.to_json() + "\n")

    def update_meta(self, meta: SessionMeta) -> None:
        f = self._session_dir(meta.session_id) / "meta.json"
        f.write_text(meta.to_json())

    def load_meta(self, session_id: str) -> SessionMeta | None:
        f = self._session_dir(session_id) / "meta.json"
        try:
            return SessionMeta.from_json(f.read_text())
        except FileNotFoundError:
            return None

    def stream_events(self, session_id: str):
        """Yield TraceEvents one at a time without loading the entire file."""
        f = self._session_dir(session_id) / "events.ndjson"
        with open(f) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield TraceEvent.from_json(line)

    def load_events(self, session_id: str) -> list[TraceEvent]:
        return list(self.stream_events(session_id))

    def list_sessions(self) -> list[SessionMeta]:
        if not self.base_dir.exists():
            return []
        sessions = []
        for d in sorted(self.base_dir.iterdir(), reverse=True):
            meta_file = d / "meta.json"
            if meta_file.exists():
                try:
                    sessions.append(SessionMeta.from_json(meta_file.read_text()))
                except json.JSONDecodeError as e:
                    sys.stderr.write(f"[agent-trace] Warning: corrupted file {meta_file}: {e}\n")
                    continue
                except TypeError:
                    continue
        return sessions

    def get_latest_session_id(self) -> str | None:
        sessions = self.list_sessions()
        if not sessions:
            return None
        return sessions[0].session_id

    def session_exists(self, session_id: str) -> bool:
        try:
            return (self._session_dir(session_id) / "meta.json").exists()
        except ValueError:
            return False

    def find_session(self, prefix: str) -> str | None:
        """Find a session by prefix match. Raises ValueError if multiple match."""
        if not self.base_dir.exists():
            return None
        sessions = self.list_sessions()
        matches = [s.session_id for s in sessions if s.session_id.startswith(prefix)]
        if len(matches) == 0:
            return None
        if len(matches) > 1:
            raise ValueError(f"Ambiguous session prefix '{prefix}' matches: {', '.join(matches[:5])}")
        return matches[0]

    def annotations_path(self, session_id: str) -> Path:
        """Return the path to the annotations sidecar file."""
        return self._session_dir(session_id) / "annotations.jsonl"
