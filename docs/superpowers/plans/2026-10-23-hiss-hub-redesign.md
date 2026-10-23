# HISS Hub Site on Kira's Redesign: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the Small Things site into the HISS Research Hub website, wearing Kira's `redesign/minimal` look, with every event from Outlook and every sentence in a Markdown body.

**Architecture:** Hugo static site. `scripts/import_ics.py` writes Outlook events into one folder per series (`content/events/hiss/`, `content/events/small-things/`), both generated and gitignored; the folder decides the series, as today. Kira's SCSS, fonts and visual partials are copied in once. Prose pages render through one partial that turns each `##` section of the Markdown body into one of Kira's two-column sections, so no prose lives in templates or front matter. A `todo` shortcode shows placeholders on previews and hides them on production.

**Tech Stack:** Hugo 0.152.2 (extended), Python 3.11+ via `uv run`, pytest, icalendar, Netlify + GitHub Pages.

**Spec:** `docs/superpowers/specs/2026-10-23-hiss-hub-redesign-design.md` (builds on `docs/prd/2026-10-19-hiss-hub-site.md`).

## Global Constraints

- Python only through `uv run`; scripts keep their PEP 723 headers.
- No absolute URLs to this site in templates or content (`relURL`/`RelPermalink` only); `baseURL` change must be the only step to move domains.
- Prose only in Markdown bodies under `##` headings. Front matter: `title`, `description`, `weight`/menu, `aliases`, and short labels a template positions (≤ 1 line each).
- Visual style: Kira's `redesign/minimal` (Space Grotesk, JetBrains Mono, zinc greys, dark gridded hero, `#1e3765` accent).
- Small Things episodes: Outlook titles starting `Small Things:`.
- "Propose an event": `params.proposeEventUrl` if set, else `mailto:` `params.contactEmail` (`matt.price@utoronto.ca`).
- TODO placeholders: `{{< todo >}}…{{< /todo >}}`; shown when `hugo.IsServer` or `site.Params.showTodos`; Netlify `deploy-preview` context sets `HUGO_PARAMS_SHOWTODOS=true`.
- A failed Outlook import fails the build (Netlify and GitHub Actions).
- `/calendar.ics` keeps its path; moved pages get `aliases`.
- No links to `hiss.utsc.utoronto.ca`; no `hubUrl` param.

## Review Focus

- **Empty calendar** (today's real state: newest Outlook event 2026-04-15): home and calendar must render the empty-state line and the propose link, and past events must still list. Test: Task 1 `test_empty_feed_writes_nothing_and_succeeds`; Task 4 `test_empty_state_when_no_upcoming`.
- **Feed unreachable or not iCalendar**: import must exit non-zero, not write an empty site. Test: Task 1 `test_main_fails_on_bad_feed`.
- **Title prefix variants** (`Small Things:` with odd spacing/case, `Small Things - …`, a title merely containing "small things"): only a leading `small things:` (case-insensitive, whitespace-tolerant) counts. Test: Task 1 `test_series_for_title`.
- **TODO leaking to production**: a production build must contain no `TODO (` text. Test: Task 3 `test_todos_hidden_in_production`.
- **Hugo base path on GitHub Pages** (`/small-things-website/` subpath): nav, CSS, fonts and feed links must resolve under a subpath. Test: Task 2 `test_links_respect_subpath`.

---

### Task 1: Import writes per-series folders; repo events go; failures are loud

**Files:**
- Modify: `scripts/import_ics.py`, `scripts/check_events.py` (KNOWN_SERIES), `netlify.toml`, `.github/workflows/deploy.yml`, `.gitignore`
- Delete: every non-`_index.md` file in `content/events/small-things/`; the whole `content/events/speakers-corner/` folder
- Test: `tests/test_import_ics.py`, `tests/test_check_events.py`

**Interfaces:**
- Produces: `series_for_title(title: str) -> str` returning `"small-things"` or `"hiss"`; `OUT_DIRS: dict[str, Path]` (`{"hiss": content/events/hiss, "small-things": content/events/small-things}`); `write_events(events, out_dirs=OUT_DIRS, dry_run=False) -> list[Path]` (no `skip_titles`); `main()` returns non-zero (or raises `SystemExit` with a message) when the feed cannot be fetched or parsed.
- Removes: `repo_event_titles`, `REPO_EVENT_DIRS`, `skip_titles`.

- [ ] **Step 1: Write failing tests** in `tests/test_import_ics.py`:
  - `test_series_for_title`: `"Small Things: Bhavani Raman & Matt Price"`, `"small things:x"`, `"  Small  Things :  x"` → `"small-things"`; `"Small Things - x"`, `"A talk on small things: y"`, `"Lunch with Leanne"` → `"hiss"`.
  - `test_write_events_routes_by_series(tmp_path)`: fixture occurrences → the Small Things one lands in `tmp_path/"small-things"`, the other five in `tmp_path/"hiss"`; each dir's `_index.md` survives; stale `.md` files in both are removed.
  - `test_empty_feed_writes_nothing_and_succeeds(tmp_path)`: a `VCALENDAR` with no `VEVENT` → `write_events` returns `[]`, no error.
  - `test_main_fails_on_bad_feed(tmp_path)`: `main(["--from", <file containing "not a calendar">])` raises `SystemExit` with a non-zero code or returns non-zero.
  - Replace `test_write_events_skips_repo_titles_and_dedups_filenames` and `test_repo_event_titles_reads_front_matter` with the routing test above (keep the filename de-dup and Markdown-content assertions inside it).
- [ ] **Step 2:** `uv run --group dev pytest tests/test_import_ics.py -q` → new tests FAIL.
- [ ] **Step 3: Implement** in `scripts/import_ics.py`. Prefix match: `re.match(r"^\s*small\s+things\s*:", title, re.I)`. `write_events` clears and writes each folder in `out_dirs`. Wrap `icalendar.Calendar.from_ical` failure into `SystemExit("…not an iCalendar file…")`. Update the module docstring (no more skipping repo titles; per-series folders).
- [ ] **Step 4:** Delete the placeholder/repo event files. `.gitignore`: add `content/events/small-things/*` and `!content/events/small-things/_index.md`. `check_events.py`: `KNOWN_SERIES = {"small-things", "hiss"}`; remove the speakers-corner fixtures/expectations from `tests/test_check_events.py` if any.
- [ ] **Step 5:** `netlify.toml` (all three contexts) and `deploy.yml`: run `uv run scripts/import_ics.py` with no `|| echo` fallback; in `deploy.yml` set `PREVIEW_BRANCH: ""`; in `netlify.toml` `[context.deploy-preview.environment]` add `HUGO_PARAMS_SHOWTODOS = "true"`.
- [ ] **Step 6:** `uv run --group dev pytest -q` → import/check tests PASS (build tests may fail until Task 2).
- [ ] **Step 7: Commit** `git commit -m "Route Outlook events by title prefix and drop repo event files"`

### Task 2: Kira's design and the Hub identity

**Files:**
- Copy from `origin/redesign/minimal` (`git checkout origin/redesign/minimal -- <paths>`): `assets/scss/main.scss`, `static/fonts/` (Space Grotesk, JetBrains Mono + OFL texts), `static/favicon.svg`, `layouts/baseof.html`, `layouts/partials/{head,header,footer,event-row,event-when,series-chip}.html`, `layouts/events/page.html`, `layouts/list.calendar.ics`
- Delete: `static/fonts/BricolageGrotesque-*`, `layouts/calendar.html`, `layouts/partials/subscribe.html` (if unused after copy)
- Modify: `hugo.toml`, `layouts/partials/header.html`, `layouts/partials/footer.html`, `layouts/partials/head.html`
- Test: `tests/test_build.py`

**Interfaces:**
- Produces: `hugo.toml` `title = "HISS Research Hub"`; params `description`, `contactEmail`, `proposeEventUrl = ""`, `utscUrl`, `outlookFeed`, `upcomingOnHome = 3`, `showTodos = false`; no `hubUrl`, `hubName`, `hcsUrl` unless a template still needs them. Menu (weights): About 10 `/about`, Departments 20 `/departments`, Calendar 30 `/events`, Small Things 40 `/small-things`, Contact 50 `/contact` (identifier `contact`).
- Produces: partial `propose-link.html` → returns the propose URL string (form URL or `mailto:` with subject "Event proposal").

- [ ] **Step 1: Rewrite `tests/test_build.py`** for the new site: `test_pages_exist` for `index.html`, `about/`, `departments/`, `events/`, `small-things/`, `contact/`, and alias redirects `calendar/`, `what-we-do/`; `test_feeds_exist_and_parse` for `calendar.ics`, `events/calendar.ics`, `events/hiss/calendar.ics`, `events/small-things/calendar.ics` (may be empty calendars); `test_no_dead_hub_links`: no built HTML contains `hiss.utsc.utoronto.ca`; `test_links_respect_subpath`: build with `--baseURL https://example.org/sub/` and assert every `href`/`src` starting with `/` starts with `/sub/`; `test_title_is_hub`: `<title>` on home contains `HISS Research Hub`. Drop `test_events_json`'s non-empty assertion (the feed may be empty) but keep the key check when events exist.
- [ ] **Step 2:** `uv run --group dev pytest tests/test_build.py -q` → FAIL.
- [ ] **Step 3:** Copy Kira's files; header wordmark text "HISS Research Hub" with `aria-label="HISS Research Hub home"` and the logo partial slot (`<span class="logo">` stays as the placeholder mark); footer: one line on the Hub at UTSC from `site.Params.description`, menu links, calendar feed link, contact email; no `hubUrl`, no "Events are edited on GitHub". `head.html` keeps the noindex block from `main`.
- [ ] **Step 4:** Tests from Step 1 that depend only on identity/assets pass (page-existence ones pass after Task 4).
- [ ] **Step 5: Commit** `git commit -m "Adopt Kira's redesign and the HISS Research Hub identity"`

### Task 3: Sectioned pages, the TODO shortcode and the TODO check

**Files:**
- Create: `layouts/partials/sections.html`, `layouts/shortcodes/todo.html`, `scripts/list_todos.py`
- Modify: `layouts/page.html`, `assets/scss/main.scss` (`.todo` style; body-rendered sections), `Makefile` (`todos` target; `check` runs it)
- Test: `tests/test_build.py`, `tests/test_list_todos.py`

**Interfaces:**
- Produces: `partial "sections.html" .Content` → splits rendered HTML at each `<h2`; text before the first `<h2>` renders as the page lede; each section renders as Kira's `section.section.section-line > .wrap.two-col` with the `h2` (class `h-md`) left and the rest in `.prose` right.
- Produces: `{{< todo >}}text{{< /todo >}}` → `<mark class="todo">TODO: text</mark>` when shown, empty string otherwise. Authors write `{{< todo >}}(Matt) confirm cluster names{{< /todo >}}`.
- Produces: `scripts/list_todos.py` → prints `path:line: text` for every `{{< todo >}}` in `content/` and every `TODO (` in `hugo.toml`, `README.md`; always exits 0; `main(argv) -> int`, `find_todos(paths: list[Path]) -> list[tuple[Path, int, str]]`.

- [ ] **Step 1: Failing tests.** `tests/test_list_todos.py::test_finds_shortcode_and_plain_todos(tmp_path)` (one shortcode in a `.md`, one `TODO (Matt)` in a `.toml` → two results with correct line numbers). In `test_build.py`: `test_todos_hidden_in_production` (default build: no `TODO` in any HTML under the build dir) and `test_todos_shown_on_previews` (build with env `HUGO_PARAMS_SHOWTODOS=true`: `class="todo"` appears in `about/index.html`).
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement the shortcode, partial, script, Makefile target; `layouts/page.html` = Kira's page head (eyebrow `site.Title`, `h1` title, `.Description` lede) + `partial "sections.html" .Content`.
- [ ] **Step 4:** Run → PASS (the shown/hidden tests pass once Task 4's About page exists; temporarily verify with a fixture page if executing strictly in order).
- [ ] **Step 5: Commit** `git commit -m "Render Markdown sections in Kira's layout; add TODO placeholders and check"`

### Task 4: Pages and their content

**Files:**
- Create/replace: `content/_index.md`, `content/about.md`, `content/departments.md`, `content/small-things.md`, `content/contact.md`, `content/events/_index.md`, `content/events/hiss/_index.md`, `content/events/small-things/_index.md`
- Create/replace templates: `layouts/home.html`, `layouts/events/section.html`, `layouts/small-things.html` (or `layout: small-things` on the page), `layouts/partials/empty-state.html`
- Delete: Kira's `what-we-do` page/layout (alias `/what-we-do/` on `about.md`), any Speakers' Corner page
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: `sections.html`, `todo` shortcode, `propose-link.html`, `all-events.html`, `event-row.html`.
- Produces: `partial "empty-state.html" .` → `<p class="notice">` "Nothing is on the calendar yet." + link "Have an idea? Propose an event" to the propose URL.

Content rules: each page's prose under `##` headings; first drafts from the spec's sources; any fact not confirmed by Matt in a `todo` shortcode. Exact copy fixed by the spec: empty state "Nothing is on the calendar yet. Have an idea? Propose an event." Department sites (use these URLs; check each returns 200 with `curl -sI`): Anthropology `https://www.utsc.utoronto.ca/anthropology/`, Arts, Culture and Media `https://www.utsc.utoronto.ca/acm/`, English `https://www.utsc.utoronto.ca/engdept/`, Geography `https://www.utsc.utoronto.ca/geography/`, Historical and Cultural Studies `https://www.utsc.utoronto.ca/hcs/`, Language Studies `https://www.utsc.utoronto.ca/dls/`.

- **Home:** hero (front matter short labels: `headline`, `lede`), body `##` sections (what the Hub is; pointer to Small Things), then upcoming events (first `upcomingOnHome`) or the empty state, then links to About / Departments / Calendar.
- **About:** `##` What the Hub does; Research clusters (preliminary names from the MPF draft, in `todo`); Research Conversations; Talk series (Speakers' Corner paragraph from the old `_index.md`); Who runs it; Get involved; Funding (in `todo`). `aliases: ["/what-we-do/"]`.
- **Departments:** six `##` sections, each one paragraph + link; anything beyond the department's name and URL in `todo`.
- **Calendar (`events/_index.md`):** short intro; template shows upcoming (month list, series filter for Hub/Small Things) or empty state, then "Past events" (most recent first, last 12 months), subscribe band, propose link. `aliases: ["/calendar/"]`.
- **Small Things:** `##` What it is; Be a guest (Kira's five steps as an ordered list); Episodes (template lists `small-things` series events, newest first, strip the `Small Things:` prefix in display); Episode details (Markdown table: Date | Guest | Department | Object | Audio; one row for 2026-02-05 Bhavani Raman, unknown cells `todo`); Funding (`todo`). Front matter `badge: "Looking for 2026–2027 guests"`. `aliases: ["/events/small-things/"]` only if that path no longer renders a page.
- **Contact:** `##` sections: general (contactEmail), propose an event, Small Things guests, where (campus address).

- [ ] **Step 1: Failing tests** in `test_build.py`: `test_empty_state_when_no_upcoming` (build with `content/events/hiss/` and `small-things/` holding only `_index.md`: `index.html` and `events/index.html` contain "Nothing is on the calendar yet"); `test_upcoming_event_listed` (write a fixture event dated tomorrow into a temp copy of the site, or use `--source` of a copied tree: home lists its title, no empty state); `test_propose_link` (home contains `mailto:matt.price@utoronto.ca`); `test_small_things_lists_episode` (fixture Small Things event appears on `small-things/index.html` without the `Small Things:` prefix).
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Write templates and content.
- [ ] **Step 4:** `make import && make check && uv run --group dev pytest -q && hugo --gc --minify` → all PASS; `hugo server` and eyeball each page at phone and desktop widths.
- [ ] **Step 5: Commit** `git commit -m "Add the Hub's pages with first-draft content"`

### Task 5: Documentation, PRD, PR

**Files:**
- Modify: `README.md`, `CLAUDE.md`, `docs/prd/2026-10-19-hiss-hub-site.md`

- [ ] **Step 1:** README: retitle to the Hub; "Changing text" (which file holds each page; `##` sections; the `todo` shortcode and `make todos`); "Adding an event" for Kira (Outlook; `Small Things:` prefix; appears within a day; add a details row on the Small Things page); remove Small Things/Speakers' Corner per-series feed list and the `/next/` section; keep the Netlify section; list the missing logo as a TODO.
- [ ] **Step 2:** CLAUDE.md: content map (page → file), rules (Outlook is the only event source; prose stays out of templates; every URL must be real; TODOs via the shortcode), commands (`make serve|check|todos|test|build|import`).
- [ ] **Step 3:** PRD: goal 8 and *Visual style* → Kira's design; logo → wordmark pending; *Moving the repository's own events* → deleted, not migrated (2026-10-23); open questions 1–2 answered; point to the design note.
- [ ] **Step 4:** `make check && uv run --group dev pytest -q && make todos` → PASS, TODO list printed.
- [ ] **Step 5:** Commit, push, `gh pr create --base main --head hiss-hub`; wait for the Netlify preview; fetch the preview and confirm the home page title, the empty state, a visible `TODO` highlight, and `noindex`.
