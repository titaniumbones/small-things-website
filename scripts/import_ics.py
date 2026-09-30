#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["icalendar>=6", "recurring-ical-events>=3", "pyyaml", "requests"]
# ///
"""Import HISS Hub events from the Hub's Outlook ICS feed into Hugo content files.

Reads the feed URL from hugo.toml (params.outlookFeed), expands recurring events
within a date window, and writes one Markdown file per occurrence into
content/events/hiss/. The folder is regenerated on every run and is gitignored.

Events whose title matches an event that already lives in the repo (Small Things,
Speakers' Corner) are skipped, so the same event never appears twice.

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
OUT_DIR = ROOT / "content" / "events" / "hiss"
REPO_EVENT_DIRS = [ROOT / "content" / "events" / "small-things", ROOT / "content" / "events" / "speakers-corner"]
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


def repo_event_titles(dirs=REPO_EVENT_DIRS) -> set[str]:
    """Normalised titles of every hand-written event in the repo."""
    titles: set[str] = set()
    for d in dirs:
        if not d.exists():
            continue
        for path in d.glob("*.md"):
            if path.name == "_index.md":
                continue
            fm = parse_front_matter(path.read_text(encoding="utf-8"))
            if fm and fm.get("title"):
                titles.add(normalise_title(str(fm["title"])))
    return titles


def parse_front_matter(text: str) -> dict | None:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return None
    return yaml.safe_load(m.group(1)) or {}


def occurrences(ics_bytes: bytes, start: date, end: date) -> list[dict]:
    """Expand the calendar into concrete occurrences between start and end."""
    import icalendar
    import recurring_ical_events

    cal = icalendar.Calendar.from_ical(ics_bytes)
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


def write_events(events: list[dict], out_dir: Path = OUT_DIR, skip_titles: set[str] | None = None, dry_run: bool = False) -> list[Path]:
    skip_titles = skip_titles or set()
    out_dir.mkdir(parents=True, exist_ok=True)
    if not dry_run:
        for old in out_dir.glob("*.md"):
            if old.name != "_index.md":
                old.unlink()
    written: list[Path] = []
    seen: set[str] = set()
    for ev in events:
        if normalise_title(ev["title"]) in skip_titles:
            continue
        name = filename_for(ev)
        stem, n = name[:-3], 2
        while name in seen:
            name, n = f"{stem}-{n}.md", n + 1
        seen.add(name)
        path = out_dir / name
        if dry_run:
            print(f"would write {path.relative_to(ROOT)}: {ev['title']} ({ev['start']:%Y-%m-%d %H:%M})")
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
    written = write_events(events, skip_titles=repo_event_titles(), dry_run=args.dry_run)
    print(f"{'would write' if args.dry_run else 'wrote'} {len(written)} event file(s) to {OUT_DIR.relative_to(ROOT)} from {len(events)} occurrence(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
