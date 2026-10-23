from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

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


def test_series_for_title():
    for t in ["Small Things: Bhavani Raman & Matt Price", "small things:x", "  Small  Things :  x"]:
        assert m.series_for_title(t) == "small-things", t
    for t in ["Small Things - x", "A talk on small things: y", "Lunch with Leanne"]:
        assert m.series_for_title(t) == "hiss", t


def _dirs(tmp_path):
    return {"hiss": tmp_path / "hiss", "small-things": tmp_path / "small-things"}


def test_write_events_routes_by_series(tmp_path):
    dirs = _dirs(tmp_path)
    for d in dirs.values():
        d.mkdir()
        (d / "_index.md").write_text("---\ntitle: x\n---\n")
        (d / "stale.md").write_text("---\ntitle: old\n---\n")
    evs = m.occurrences(FIX.read_bytes(), date(2026, 1, 1), date(2026, 12, 31))
    written = m.write_events(evs, out_dirs=dirs)
    small = sorted(p.name for p in written if p.parent == dirs["small-things"])
    hiss = sorted(p.name for p in written if p.parent == dirs["hiss"])
    assert len(small) == 1 and "bhavani-raman" in small[0]
    assert len(hiss) == len(set(hiss)) == 5
    for d in dirs.values():
        assert (d / "_index.md").exists()
        assert not (d / "stale.md").exists()
    text = (dirs["hiss"] / next(n for n in hiss if "book-launch" in n)).read_text()
    assert "title: Book Launch, Donna Young" in text
    assert "imported: true" in text
    assert "link: https://example.org/launch" in text
    assert "Line one\nLine two, with comma" in text
    assert "date: '2026-04-01T13:00:00-04:00'" in text


def test_empty_feed_writes_nothing_and_succeeds(tmp_path):
    empty = b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//x//EN\r\nEND:VCALENDAR\r\n"
    evs = m.occurrences(empty, date(2026, 1, 1), date(2026, 12, 31))
    assert m.write_events(evs, out_dirs=_dirs(tmp_path)) == []


def test_main_fails_on_bad_feed(tmp_path):
    bad = tmp_path / "bad.ics"
    bad.write_text("<html>not a calendar</html>")
    with pytest.raises(SystemExit) as exc:
        m.main(["--from", str(bad)])
    assert exc.value.code not in (0, None)


def test_write_events_replaces_previous_output(tmp_path):
    (tmp_path / "stale.md").write_text("---\ntitle: old\n---\n")
    (tmp_path / "_index.md").write_text("---\ntitle: HISS Hub\n---\n")
    m.write_events([], out_dirs={"hiss": tmp_path})
    assert not (tmp_path / "stale.md").exists()
    assert (tmp_path / "_index.md").exists()


def test_small_things_episodes_are_kept_however_old():
    ics = (FIX.read_bytes())
    # A window that starts long after the 2026-02-05 episode still keeps it; Hub events outside the window go.
    evs = m.occurrences(ics, date(2028, 1, 1), date(2028, 12, 31), keep_series={"small-things"})
    assert [e["title"] for e in evs] == ["Small Things: Bhavani Raman & Matt Price"]


def test_feed_with_no_events_at_all_fails(tmp_path):
    empty = tmp_path / "empty.ics"
    empty.write_bytes(b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//x//EN\r\nEND:VCALENDAR\r\n")
    with pytest.raises(SystemExit) as exc:
        m.main(["--from", str(empty), "--dry-run"])
    assert exc.value.code not in (0, None)
