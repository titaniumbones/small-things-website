#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Check every event file under content/events/ before Hugo builds the site.

Prints one line per problem, in plain English, naming the file and the field.
Exits 1 if anything is wrong, so a pull request cannot merge a broken event.

Usage:
    uv run scripts/check_events.py            # check the whole tree
    uv run scripts/check_events.py file.md    # check specific files
"""

from __future__ import annotations

import re
import sys
from datetime import date, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
EVENTS_DIR = ROOT / "content" / "events"
KNOWN_SERIES = {"small-things", "speakers-corner", "hiss"}
KNOWN_STATUS = {"confirmed", "tbc", "cancelled"}
URL_RE = re.compile(r"^https?://\S+$")


def split_front_matter(text: str) -> tuple[dict | None, str | None]:
    """Return (front matter dict, error message)."""
    if not text.startswith("---"):
        return None, "the file must start with a line containing only --- (the front matter opener)"
    m = re.match(r"^---\s*\n(.*?)\n---\s*(\n|$)", text, re.S)
    if not m:
        return None, "could not find the closing --- line of the front matter"
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError as exc:
        return None, f"the front matter is not valid YAML ({str(exc).splitlines()[0]}); check quotes and indentation"
    if data is None:
        return {}, None
    if not isinstance(data, dict):
        return None, "the front matter must be key: value lines"
    return data, None


def as_datetime(value) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def check_event(path: Path, text: str | None = None) -> list[str]:
    """Return a list of problems for one event file. Empty means it is fine."""
    problems: list[str] = []
    text = text if text is not None else path.read_text(encoding="utf-8")
    fm, err = split_front_matter(text)
    if err:
        return [err]
    assert fm is not None

    title = fm.get("title")
    if not title or not str(title).strip():
        problems.append("title is missing")

    start = fm.get("date")
    if start is None:
        problems.append("date is missing (start time, for example 2026-10-15T13:00:00-04:00)")
    else:
        start_dt = as_datetime(start)
        if start_dt is None:
            problems.append(f"date {start!r} is not a date I can read; use 2026-10-15T13:00:00-04:00")
        elif isinstance(start_dt, datetime) and start_dt.tzinfo is None and isinstance(start, str):
            problems.append("date has no timezone offset; add -04:00 (summer) or -05:00 (winter)")
        end = fm.get("end")
        if end not in (None, ""):
            end_dt = as_datetime(end)
            if end_dt is None:
                problems.append(f"end {end!r} is not a date I can read")
            elif start_dt is not None and (end_dt.tzinfo is None) == (start_dt.tzinfo is None) and end_dt < start_dt:
                problems.append("end is before date (the event ends before it starts)")

    status = fm.get("status", "confirmed")
    if status not in KNOWN_STATUS:
        problems.append(f"status {status!r} is not one of: {', '.join(sorted(KNOWN_STATUS))}")

    if "series" in fm:
        problems.append("series should not be set by hand; the folder the file sits in decides the series")

    speakers = fm.get("speakers")
    if speakers is not None and not isinstance(speakers, list):
        problems.append("speakers must be a list (one name per line, each starting with '- ')")

    for field in ("link", "audio"):
        v = fm.get(field)
        if v not in (None, "") and not URL_RE.match(str(v)):
            problems.append(f"{field} must be a full URL starting with http:// or https://")

    ep = fm.get("episode")
    if ep not in (None, "") and not (isinstance(ep, int) and not isinstance(ep, bool) and ep >= 0):
        problems.append("episode must be a whole number (0 for the pilot)")

    if path.parent != EVENTS_DIR and path.parent.name not in KNOWN_SERIES and EVENTS_DIR in path.parents:
        problems.append(f"folder {path.parent.name!r} is not a known series; use one of {', '.join(sorted(KNOWN_SERIES))}")

    return problems


def event_files(paths: list[str]) -> list[Path]:
    if paths:
        return [Path(p).resolve() for p in paths]
    return sorted(p for p in EVENTS_DIR.rglob("*.md") if p.name != "_index.md")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    bad = 0
    files = event_files(argv)
    for path in files:
        for problem in check_event(path):
            bad += 1
            try:
                shown = path.relative_to(ROOT)
            except ValueError:
                shown = path
            print(f"{shown}: {problem}")
    if bad:
        print(f"\n{bad} problem(s) in event files. Fix them and run again.")
        return 1
    print(f"Checked {len(files)} event file(s): all good.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
