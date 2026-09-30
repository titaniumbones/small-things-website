from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import import_ics as m

FIX = Path(__file__).parent / "fixtures" / "sample.ics"
TORONTO = ZoneInfo("America/Toronto")


def test_windows_tz_name_maps_to_toronto():
    dt = m.to_toronto(datetime(2026, 2, 5, 13, 0), "Eastern Standard Time")
    assert dt.tzinfo is not None
    assert dt.utcoffset().total_seconds() == -5 * 3600
    assert dt.hour == 13


def test_utc_datetime_is_converted_to_toronto():
    dt = m.to_toronto(datetime(2026, 4, 20, 15, 0, tzinfo=ZoneInfo("UTC")))
    assert dt.hour == 11  # EDT is UTC-4


def test_all_day_date_becomes_midnight_toronto():
    dt = m.to_toronto(date(2026, 10, 6))
    assert (dt.hour, dt.minute) == (0, 0)
    assert dt.tzinfo is not None


def test_normalise_title_treats_ampersand_as_and():
    assert m.normalise_title("Small Things: Bhavani Raman & Matt Price") == m.normalise_title(
        "Small Things: Bhavani Raman and Matt Price"
    )


def test_occurrences_expand_rrule_and_keep_status():
    evs = m.occurrences(FIX.read_bytes(), date(2026, 1, 1), date(2026, 12, 31))
    titles = [e["title"] for e in evs]
    assert titles.count("Centre for Ethnography Speakers Series") == 3
    cancelled = next(e for e in evs if e["title"] == "Cancelled Talk")
    assert cancelled["cancelled"] is True
    assert cancelled["start"].hour == 11
    launch = next(e for e in evs if e["title"].startswith("Book Launch"))
    assert launch["location"] == "HL348"
    assert launch["url"] == "https://example.org/launch"
    assert evs == sorted(evs, key=lambda e: e["start"])


def test_occurrences_respect_window():
    evs = m.occurrences(FIX.read_bytes(), date(2026, 3, 1), date(2026, 3, 31))
    assert {e["title"] for e in evs} == {"Centre for Ethnography Speakers Series"}


def test_write_events_skips_repo_titles_and_dedups_filenames(tmp_path):
    evs = m.occurrences(FIX.read_bytes(), date(2026, 1, 1), date(2026, 12, 31))
    skip = {m.normalise_title("Small Things: Bhavani Raman and Matt Price")}
    written = m.write_events(evs, out_dir=tmp_path, skip_titles=skip)
    names = sorted(p.name for p in written)
    assert not any("small-things" in n for n in names)
    assert len(names) == len(set(names)) == 5
    text = (tmp_path / next(n for n in names if "book-launch" in n)).read_text()
    assert "title: Book Launch, Donna Young" in text
    assert "imported: true" in text
    assert "link: https://example.org/launch" in text
    assert "Line one\nLine two, with comma" in text
    assert "date: '2026-04-01T13:00:00-04:00'" in text


def test_write_events_replaces_previous_output(tmp_path):
    (tmp_path / "stale.md").write_text("---\ntitle: old\n---\n")
    (tmp_path / "_index.md").write_text("---\ntitle: HISS Hub\n---\n")
    m.write_events([], out_dir=tmp_path)
    assert not (tmp_path / "stale.md").exists()
    assert (tmp_path / "_index.md").exists()


def test_repo_event_titles_reads_front_matter(tmp_path):
    d = tmp_path / "small-things"
    d.mkdir()
    (d / "_index.md").write_text("---\ntitle: Small Things\n---\n")
    (d / "x.md").write_text("---\ntitle: 'Ep 1: The Cup'\ndate: 2026-10-15T13:00:00-04:00\n---\n\nbody\n")
    assert m.repo_event_titles([d]) == {"ep 1 the cup"}
