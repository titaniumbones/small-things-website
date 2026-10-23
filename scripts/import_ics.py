#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["icalendar>=6", "recurring-ical-events>=3", "pyyaml", "requests"]
# ///
"""Import every event from the Hub's Outlook ICS feed into Hugo content files.

Reads the feed URL from hugo.toml (params.outlookFeed), expands recurring events
within a date window, and writes one Markdown file per occurrence. Outlook is the
only source of events: an event whose title starts with "Small Things:" goes to
content/events/small-things/, everything else to content/events/hiss/. Both folders
are regenerated on every run and are gitignored (except their _index.md).

A feed that cannot be fetched or is not an iCalendar file stops the import with a
non-zero exit, so the build fails and the last good deploy stays up.

Usage:
    uv run scripts/import_ics.py                 # fetch the feed and write files
    uv run scripts/import_ics.py --from path.ics # use a local file instead
    uv run scripts/import_ics.py --dry-run       # print what would be written
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
import unicodedata
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "hugo.toml"
EVENTS_DIR = ROOT / "content" / "events"
OUT_DIRS = {"hiss": EVENTS_DIR / "hiss", "small-things": EVENTS_DIR / "small-things"}
SMALL_THINGS_PREFIX = re.compile(r"^\s*small\s+things\s*:", re.I)
TORONTO = ZoneInfo("America/Toronto")

# Outlook writes Windows timezone names. Map the ones we expect to IANA zones;
# anything unknown falls back to Toronto, which is where every HISS event happens.
WINDOWS_TZ = {
    "Eastern Standard Time": "America/Toronto",
    "Eastern Daylight Time": "America/Toronto",
    "US Eastern Standard Time": "America/Indiana/Indianapolis",
    "Central Standard Time": "America/Chicago",
    "Mountain Standard Time": "America/Denver",
    "Pacific Standard Time": "America/Los_Angeles",
    "Atlantic Standard Time": "America/Halifax",
    "Newfoundland Standard Time": "America/St_Johns",
    "GMT Standard Time": "Europe/London",
    "UTC": "UTC",
}


def to_toronto(value, tzid: str | None = None) -> datetime:
    """Turn an ICS date or datetime into an aware datetime in Toronto time.

    Naive datetimes are interpreted in the zone named by ``tzid`` (a Windows or
    IANA name), or Toronto if none is given. All-day dates become 00:00 Toronto.
    """
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, date):
        dt = datetime.combine(value, time(0, 0))
    else:
        raise TypeError(f"unsupported date value: {value!r}")
    if dt.tzinfo is None:
        zone_name = WINDOWS_TZ.get(tzid or "", tzid or "America/Toronto")
        try:
            zone = ZoneInfo(zone_name)
        except Exception:
            zone = TORONTO
        dt = dt.replace(tzinfo=zone)
    return dt.astimezone(TORONTO)


def normalise_title(title: str) -> str:
    """Lower-case, strip accents and punctuation, collapse whitespace."""
    t = unicodedata.normalize("NFKD", title or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower().replace("&", " and ")
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def slugify(text: str, limit: int = 60) -> str:
    s = normalise_title(text).replace(" ", "-")
    return s[:limit].strip("-") or "event"


def read_feed_url(config: Path = CONFIG) -> str:
    with config.open("rb") as fh:
        data = tomllib.load(fh)
    url = data.get("params", {}).get("outlookFeed")
    if not url:
        raise SystemExit("hugo.toml has no params.outlookFeed; nothing to import")
    return url


def series_for_title(title: str) -> str:
    """Small Things episodes are the events whose title starts with "Small Things:"."""
    return "small-things" if SMALL_THINGS_PREFIX.match(title or "") else "hiss"


def occurrences(ics_bytes: bytes, start: date, end: date) -> list[dict]:
    """Expand the calendar into concrete occurrences between start and end."""
    import icalendar
    import recurring_ical_events

    try:
        cal = icalendar.Calendar.from_ical(ics_bytes)
    except ValueError as exc:
        raise SystemExit(f"the Outlook feed is not an iCalendar file ({exc}); not importing") from exc
    out = []
    for ev in recurring_ical_events.of(cal, skip_bad_series=True).between(start, end):
        dtstart = ev.get("DTSTART")
        if dtstart is None:
            continue
        tzid = dtstart.params.get("TZID") if hasattr(dtstart, "params") else None
        begin = to_toronto(dtstart.dt, tzid)
        dtend = ev.get("DTEND")
        finish = to_toronto(dtend.dt, dtend.params.get("TZID") if hasattr(dtend, "params") else None) if dtend is not None else None
        all_day = not isinstance(dtstart.dt, datetime)
        status = str(ev.get("STATUS", "CONFIRMED")).upper()
        out.append(
            {
                "uid": str(ev.get("UID", "")),
                "title": str(ev.get("SUMMARY", "Untitled event")).strip(),
                "start": begin,
                "end": finish,
                "all_day": all_day,
                "location": str(ev.get("LOCATION", "")).strip(),
                "description": str(ev.get("DESCRIPTION", "")).strip(),
                "url": str(ev.get("URL", "")).strip(),
                "cancelled": status == "CANCELLED",
            }
        )
    out.sort(key=lambda e: e["start"])
    return out


def clean_description(text: str) -> str:
    """Outlook descriptions arrive with CRLF and stray escapes; make them Markdown-safe."""
    text = text.replace("\r\n", "\n").replace("\\n", "\n").replace("\\,", ",").replace("\\;", ";")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def render_markdown(ev: dict) -> str:
    fm = {
        "title": ev["title"],
        "date": ev["start"].isoformat(),
        "status": "cancelled" if ev["cancelled"] else "confirmed",
        "imported": True,
        "uid": ev["uid"],
    }
    if ev["end"]:
        fm["end"] = ev["end"].isoformat()
    if ev["all_day"]:
        fm["allDay"] = True
    if ev["location"]:
        fm["location"] = ev["location"]
    if ev["url"]:
        fm["link"] = ev["url"]
    body = clean_description(ev["description"])
    front = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, default_flow_style=False).strip()
    return f"---\n{front}\n---\n\n{body}\n"


def filename_for(ev: dict) -> str:
    return f"{ev['start'].strftime('%Y-%m-%d')}-{slugify(ev['title'])}.md"


def write_events(events: list[dict], out_dirs: dict[str, Path] = OUT_DIRS, dry_run: bool = False) -> list[Path]:
    """Clear each series folder (keeping _index.md) and write one file per event into its series folder."""
    for d in out_dirs.values():
        d.mkdir(parents=True, exist_ok=True)
        if not dry_run:
            for old in d.glob("*.md"):
                if old.name != "_index.md":
                    old.unlink()
    written: list[Path] = []
    seen: set[Path] = set()
    for ev in events:
        out_dir = out_dirs[series_for_title(ev["title"])]
        name = filename_for(ev)
        stem, n = name[:-3], 2
        while out_dir / name in seen:
            name, n = f"{stem}-{n}.md", n + 1
        path = out_dir / name
        seen.add(path)
        if dry_run:
            print(f"would write {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}: {ev['title']} ({ev['start']:%Y-%m-%d %H:%M})")
        else:
            path.write_text(render_markdown(ev), encoding="utf-8")
        written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="source", help="local .ics file instead of the live feed")
    ap.add_argument("--past-days", type=int, default=400, help="keep events this many days back (default 400)")
    ap.add_argument("--future-days", type=int, default=400, help="keep events this many days ahead (default 400)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if args.source:
        ics = Path(args.source).read_bytes()
    else:
        import requests

        url = read_feed_url()
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        ics = resp.content

    today = datetime.now(TORONTO).date()
    events = occurrences(ics, today - timedelta(days=args.past_days), today + timedelta(days=args.future_days))
    written = write_events(events, dry_run=args.dry_run)
    print(f"{'would write' if args.dry_run else 'wrote'} {len(written)} event file(s) from {len(events)} occurrence(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
