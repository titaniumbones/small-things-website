"""Build the site into a temporary directory and check the important outputs exist."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.skipif(shutil.which("hugo") is None, reason="hugo not installed")


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    out = tmp_path_factory.mktemp("public")
    subprocess.run(["hugo", "--quiet", "-s", str(ROOT), "-d", str(out), "--baseURL", "https://example.org/"], check=True)
    return out


def test_pages_exist(site):
    for rel in [
        "index.html",
        "calendar/index.html",
        "about/index.html",
        "events/small-things/index.html",
        "events/speakers-corner/index.html",
        "events/hiss/index.html",
    ]:
        assert (site / rel).exists(), rel


def test_feeds_exist_and_parse(site):
    icalendar = pytest.importorskip("icalendar")
    for rel in ["calendar.ics", "events/small-things/calendar.ics", "events/speakers-corner/calendar.ics"]:
        raw = (site / rel).read_bytes()
        assert b"\r\n" in raw, f"{rel} should use CRLF line endings"
        cal = icalendar.Calendar.from_ical(raw)
        assert cal.walk("VEVENT"), f"{rel} has no events"


def test_events_json(site):
    data = json.loads((site / "events.json").read_text())
    assert data["events"], "no events in events.json"
    e = data["events"][0]
    for key in ("title", "start", "series", "seriesName", "status", "url"):
        assert key in e


def test_home_links_to_feed(site):
    html = (site / "index.html").read_text()
    assert 'type="text/calendar"' in html
    assert "calendar.ics" in html
