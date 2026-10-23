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


def test_todos_hidden_in_production(site):
    for f in html_files(site):
        text = f.read_text()
        assert 'class="todo"' not in text and "TODO" not in text, f


def test_todos_shown_on_previews(tmp_path):
    out = build(tmp_path, env={"HUGO_PARAMS_SHOWTODOS": "true"})
    assert 'class="todo"' in (out / "about" / "index.html").read_text()


def test_page_sections_render_from_markdown(site):
    html = (site / "about" / "index.html").read_text()
    assert html.count('class="section section-line"') >= 3
    assert re.search(r'<h2[^>]*class="?h-md', html)


TOMORROW = datetime.now() + timedelta(days=1)


def test_empty_state_when_no_upcoming(site):
    for rel in ["index.html", "events/index.html"]:
        assert "Nothing is on the calendar yet" in (site / rel).read_text(), rel


def test_past_events_still_listed(site):
    assert "Past Hub Event" in (site / "events" / "index.html").read_text()


def test_upcoming_event_listed(tmp_path):
    out = build(tmp_path, events=(PAST_HUB, event("hiss", "Tomorrow Talk", TOMORROW)))
    for rel in ["index.html", "events/index.html"]:
        html = (out / rel).read_text()
        assert "Tomorrow Talk" in html, rel
        assert "Nothing is on the calendar yet" not in html, rel


def test_propose_link(site):
    assert "mailto:matt.price@utoronto.ca?subject=Event%20proposal" in (site / "index.html").read_text()
    assert "Propose an event" in (site / "events" / "index.html").read_text()


def test_small_things_lists_episode(site):
    html = (site / "small-things" / "index.html").read_text()
    assert "Bhavani Raman" in html
    assert "Small Things: Bhavani" not in html


def test_departments_page_has_six_sections(site):
    html = (site / "departments" / "index.html").read_text()
    for name in ["Anthropology", "Arts, Culture and Media", "English", "Human Geography", "Historical and Cultural Studies", "Language Studies"]:
        assert name in html, name
    assert html.count('class="section section-line"') == 6


def alias_target(out: Path, rel: str) -> str:
    m = re.search(r'http-equiv="?refresh"? content="?0; url=([^"\s>]+)', (out / rel).read_text())
    assert m, f"{rel} is not an alias redirect"
    return m.group(1)


def test_old_urls_redirect(site):
    assert alias_target(site, "calendar/index.html").endswith("/events/")
    assert alias_target(site, "what-we-do/index.html").endswith("/about/")
    assert alias_target(site, "events/small-things/index.html").endswith("/small-things/")
    assert alias_target(site, "events/hiss/index.html").endswith("/events/")
    assert alias_target(site, "events/speakers-corner/index.html").endswith("/about/")


def test_content_pages_publish_no_calendar(site):
    for rel in ["about", "departments", "contact", "small-things"]:
        assert not (site / rel / "calendar.ics").exists(), rel
        assert "text/calendar" not in (site / rel / "index.html").read_text(), rel


def test_hidden_rows_are_hidden_by_css(site):
    css = next((site / "scss").glob("main*.css")).read_text()
    assert re.search(r"\[hidden\]\s*\{\s*display:\s*none\s*!important", css)


def test_site_feed_is_named_for_the_hub(site):
    raw = (site / "calendar.ics").read_text()
    assert "X-WR-CALNAME:HISS Research Hub" in raw
    assert "Small Things, HISS Hub and Speakers" not in raw
    assert "PRODID:-//HISS Research Hub//" in raw
