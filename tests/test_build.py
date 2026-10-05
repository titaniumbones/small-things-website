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
        "about/index.html",
        "events/index.html",
        "what-we-do/index.html",
        "contact/index.html",
        "calendar/index.html",  # alias redirect to /events/
        "events/small-things/2026-02-05-bhavani-raman/index.html",
    ]:
        assert (site / rel).exists(), rel


def test_feeds_exist_and_parse(site):
    icalendar = pytest.importorskip("icalendar")
    # Every feed must exist and parse; a series with nothing scheduled yet publishes an empty feed.
    for rel in ["calendar.ics", "events/calendar.ics", "events/small-things/calendar.ics", "events/speakers-corner/calendar.ics", "events/hiss/calendar.ics"]:
        raw = (site / rel).read_bytes()
        assert b"\r\n" in raw, f"{rel} should use CRLF line endings"
        icalendar.Calendar.from_ical(raw)
    all_events = icalendar.Calendar.from_ical((site / "calendar.ics").read_bytes())
    assert all_events.walk("VEVENT"), "calendar.ics has no events"


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


def test_series_pages_have_no_html(site):
    # Series are listed on /events/ and /what-we-do/; each series keeps only its .ics feed.
    for rel in ["events/small-things/index.html", "events/speakers-corner/index.html", "events/hiss/index.html"]:
        assert not (site / rel).exists(), rel


def test_nav_has_the_four_pages(site):
    html = (site / "index.html").read_text()
    for name in ("About Us", "Events", "What we do", "Contact"):
        assert name in html, name


def test_events_page_says_coming_soon_when_nothing_is_scheduled(site):
    html = (site / "events/index.html").read_text()
    assert "Coming soon" in html


def test_home_pitches_guests(site):
    html = (site / "index.html").read_text()
    assert "Propose an object" in html
    assert "mailto:" in html


def test_no_escaped_feed_links(site):
    # Hugo gives calendar feeds a webcal:// address, which Go templates blank out as "#ZgotmplZ".
    # Feed links must use relative paths so the subscribe buttons work.
    for rel in ["index.html", "events/index.html", "contact/index.html"]:
        html = (site / rel).read_text()
        assert "ZgotmplZ" not in html, rel
        assert "calendar.ics" in html, rel
