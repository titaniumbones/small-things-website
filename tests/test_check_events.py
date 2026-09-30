from pathlib import Path

import check_events as c

GOOD = """---
title: "Episode 1: The cup"
date: 2026-10-15T13:00:00-04:00
end: 2026-10-15T14:30:00-04:00
location: "KW 130"
status: tbc
speakers:
  - "Someone"
episode: 1
audio: ""
---

Body.
"""


def run(text: str, folder: str = "small-things") -> list[str]:
    path = c.EVENTS_DIR / folder / "x.md"
    return c.check_event(path, text)


def test_good_file_has_no_problems():
    assert run(GOOD) == []


def test_missing_front_matter():
    assert "start with a line containing only ---" in run("title: nope\n")[0]


def test_bad_yaml_is_reported_plainly():
    problems = run('---\ntitle: "unclosed\ndate: 2026-10-15T13:00:00-04:00\n---\n')
    assert any("not valid YAML" in p for p in problems)


def test_missing_title_and_date():
    problems = run("---\nlocation: KW 130\n---\n")
    assert any(p.startswith("title is missing") for p in problems)
    assert any(p.startswith("date is missing") for p in problems)


def test_unreadable_date():
    problems = run("---\ntitle: x\ndate: next thursday\n---\n")
    assert any("not a date I can read" in p for p in problems)


def test_end_before_start():
    problems = run("---\ntitle: x\ndate: 2026-10-15T13:00:00-04:00\nend: 2026-10-15T12:00:00-04:00\n---\n")
    assert any("ends before it starts" in p for p in problems)


def test_unknown_status():
    problems = run("---\ntitle: x\ndate: 2026-10-15T13:00:00-04:00\nstatus: maybe\n---\n")
    assert any("status 'maybe' is not one of" in p for p in problems)


def test_series_set_by_hand_is_rejected():
    problems = run("---\ntitle: x\ndate: 2026-10-15T13:00:00-04:00\nseries: hiss\n---\n")
    assert any("folder the file sits in decides" in p for p in problems)


def test_speakers_must_be_list():
    problems = run("---\ntitle: x\ndate: 2026-10-15T13:00:00-04:00\nspeakers: Someone\n---\n")
    assert any("speakers must be a list" in p for p in problems)


def test_bad_urls_and_episode():
    problems = run("---\ntitle: x\ndate: 2026-10-15T13:00:00-04:00\naudio: not-a-url\nepisode: three\n---\n")
    assert any(p.startswith("audio must be a full URL") for p in problems)
    assert any(p.startswith("episode must be a whole number") for p in problems)


def test_unknown_folder():
    problems = run(GOOD, folder="podcasts")
    assert any("not a known series" in p for p in problems)


def test_real_repo_events_pass():
    for path in c.event_files([]):
        assert c.check_event(path) == [], path
