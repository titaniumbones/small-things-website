"""Build the site into a temporary directory and check the important outputs.

Each build runs on a copy of the repository whose event folders hold only the events a
test supplies, so the results do not depend on what the live Outlook feed contains today.
"""

import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SERIES = ("hiss", "small-things")
SKIP = shutil.ignore_patterns(".git", "public", "resources", ".superpowers", ".netlify", "node_modules", "__pycache__", ".pytest_cache", ".venv")

pytestmark = pytest.mark.skipif(shutil.which("hugo") is None, reason="hugo not installed")


def event(series: str, title: str, when: datetime) -> tuple[str, str]:
    """An event file as the importer would write it: (series folder, file text)."""
    stamp = when.strftime("%Y-%m-%dT%H:%M:%S-04:00")
    return series, f"---\ntitle: '{title}'\ndate: '{stamp}'\nstatus: confirmed\nimported: true\nlocation: KW 130\n---\n\nAbout {title}.\n"


PAST_HUB = event("hiss", "Book Launch: Past Hub Event", datetime(2026, 4, 1, 13))
PAST_EPISODE = event("small-things", "Small Things: Bhavani Raman & Matt Price", datetime(2026, 2, 5, 13))


def build(tmp: Path, events=(PAST_HUB, PAST_EPISODE), env: dict | None = None, base: str = "https://example.org/") -> Path:
    src, out = tmp / "src", tmp / "out"
    shutil.copytree(ROOT, src, ignore=SKIP)
    for s in SERIES:
        for f in (src / "content" / "events" / s).glob("*.md"):
            if f.name != "_index.md":
                f.unlink()
    for i, (s, text) in enumerate(events):
        (src / "content" / "events" / s / f"event-{i}.md").write_text(text)
    run_env = {k: v for k, v in os.environ.items() if not k.startswith("HUGO_")}
    run_env.update(env or {})
    subprocess.run(["hugo", "--quiet", "-s", str(src), "-d", str(out), "--baseURL", base], check=True, env=run_env)
    return out


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    return build(tmp_path_factory.mktemp("site"))


def html_files(out: Path):
    return list(out.rglob("*.html"))


def test_pages_exist(site):
    for rel in [
        "index.html",
        "about/index.html",
        "departments/index.html",
        "events/index.html",
        "small-things/index.html",
        "contact/index.html",
        "calendar/index.html",  # alias redirect to /events/
        "what-we-do/index.html",  # alias redirect to /about/
    ]:
        assert (site / rel).exists(), rel


def test_feeds_exist_and_parse(site):
    icalendar = pytest.importorskip("icalendar")
    for rel in ["calendar.ics", "events/calendar.ics", "events/hiss/calendar.ics", "events/small-things/calendar.ics"]:
        raw = (site / rel).read_bytes()
        assert b"\r\n" in raw, f"{rel} should use CRLF line endings"
        icalendar.Calendar.from_ical(raw)
    assert icalendar.Calendar.from_ical((site / "calendar.ics").read_bytes()).walk("VEVENT")


def test_events_json(site):
    data = json.loads((site / "events.json").read_text())
    assert data["events"]
    for key in ("title", "start", "series", "seriesName", "status", "url"):
        assert key in data["events"][0]


def test_home_links_to_feed(site):
    html = (site / "index.html").read_text()
    assert 'type="text/calendar"' in html
    assert "calendar.ics" in html


def test_title_is_hub(site):
    title = re.search(r"<title>(.*?)</title>", (site / "index.html").read_text(), re.S).group(1)
    assert "HISS Research Hub" in title


def test_no_dead_hub_links(site):
    for f in html_files(site):
        assert "hiss.utsc.utoronto.ca" not in f.read_text(), f


def test_links_respect_subpath(tmp_path):
    out = build(tmp_path, base="https://example.org/sub/")
    for f in [out / "index.html", out / "about" / "index.html", out / "events" / "index.html"]:
        for url in re.findall(r'(?:href|src)="?(/[^"\s>]*)', f.read_text()):
            assert url.startswith("/sub/"), f"{f.relative_to(out)}: {url}"
