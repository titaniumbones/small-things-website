# Small Things

The website for *Small Things*, a live-recorded podcast from the Humanities and Interpretive Social Sciences (HISS) Research Hub at the University of Toronto Scarborough, with a shared calendar for Small Things, HISS Hub events and HCS Speakers' Corner.

Live site: https://titaniumbones.github.io/small-things-website/

It is a static site built with [Hugo](https://gohugo.io). Every event is one Markdown file. Nothing else is needed to add or change an event.

## Add an event in five steps

You can do all of this in the GitHub web editor. No software to install.

1. Open the folder for the series: `content/events/small-things/` or `content/events/speakers-corner/`. (HISS Hub events come from the Hub's Outlook calendar automatically; see below.)

2. Click **Add file → Create new file**. Name it `YYYY-MM-DD-short-name.md`, for example `2026-11-12-tanya-titchkosky-cane.md`.

3. Paste this and fill it in:

   ```yaml
   ---
   title: "Tanya Titchkosky: a white cane"
   date: 2026-11-12T13:00:00-05:00
   end: 2026-11-12T14:30:00-05:00
   location: "KW 130"
   status: confirmed
   speakers:
     - "Tanya Titchkosky"
   # Small Things episodes only:
   episode: 2
   object: "A white cane"
   department: "Anthropology"
   audio: ""
   ---

   A sentence or two about the event. This is what people see on the event page.
   ```

   The time needs Toronto's offset: `-04:00` from mid-March to early November, `-05:00` the rest of the year. `status` is `confirmed`, `tbc` (date not yet fixed) or `cancelled`.

4. Click **Commit changes**, choose **Create a new branch and start a pull request**, and open the pull request.

5. Wait a minute. A check runs and tells you in plain words if anything is wrong with the file. When it is green, merge. The site rebuilds and deploys itself.

To change an event, open its file and edit it the same way. To publish an episode recording, put the audio file's URL in `audio`.

## The three series

| Series | Folder | Where events come from |
| --- | --- | --- |
| Small Things | `content/events/small-things/` | Files in this repo |
| Speakers' Corner | `content/events/speakers-corner/` | Files in this repo |
| HISS Hub | `content/events/hiss/` | Imported from the HISS Hub Outlook calendar at build time |

Each folder has an `_index.md` with the series description. Edit it to change the text on the series page.

HISS Hub events are pulled from the Outlook feed named in `hugo.toml` by `scripts/import_ics.py`, once a day and on every push. The imported files are not committed. To change a HISS Hub event, change it in the Outlook calendar. If a Hub event is also a Small Things or Speakers' Corner event, give the repo file the same title and the import skips the duplicate.

## Calendar feeds

The site publishes iCalendar feeds anyone can subscribe to:

- `/calendar.ics`: everything
- `/events/small-things/calendar.ics`, `/events/speakers-corner/calendar.ics`, `/events/hiss/calendar.ics`: one series each
- every event page has its own `calendar.ics` for "add to my calendar"
- `/events.json`: the same data for scripts

## Working locally

You need [Hugo](https://gohugo.io/installation/) (extended edition) and [uv](https://docs.astral.sh/uv/).

```sh
make import     # optional: pull HISS Hub events from Outlook
make serve      # http://localhost:1313/
make check      # validate event files
make test       # Python tests plus a Hugo build smoke test
make build      # production build into public/
```

`hugo new events/small-things/2026-11-12-short-name.md` creates a new event file from the template in `archetypes/events.md`.

## How it is put together

Five pages: home, **About Us**, **Events**, **What we do** and **Contact**. The look is clean and modern: white paper, near-black type in Plus Jakarta Sans, soft rounded panels, pill buttons, hairline section breaks, and a circle with a small dot standing for the object on the table. No photographs. The home page is the pitch to prospective guests; its copy lives in the front matter of `content/_index.md`.

- `hugo.toml`: site settings, the menu, contact details, the Outlook feed URL, and the custom `.ics` and `.json` output formats.
- `layouts/`: templates. `home.html`, `about.html`, `what-we-do.html`, `contact.html`, `events/section.html` (the Events list with its series filter), `events/page.html` (one event), and the `*.calendar.ics` and `home.eventsjson.json` feed templates. Shared pieces live in `layouts/partials/`.
- `content/about.md`, `content/what-we-do.md`, `content/contact.md`: page copy. About Us and the "Take part" block are lists of labelled sections in the front matter; each `body` is Markdown.
- `content/events/_index.md`: the Events page. When nothing is scheduled it shows the `notice` ("Coming soon… to be announced!") instead of a list, and past events are not listed.
- `content/events/<series>/_index.md`: each series' description, one-line `short`, `headline`, and the `facts` shown on What we do. Series pages have no HTML of their own; they are listed on Events and What we do and keep only their `.ics` feed.
- `assets/scss/main.scss`: all styles. Colours and type are set as variables at the top. Hugo compiles it; there is no npm.
- `assets/js/site.js`: the Events page's series filter. The page works without it.
- `static/fonts/`: Plus Jakarta Sans (SIL Open Font License, licence text alongside), self-hosted.
- `scripts/import_ics.py`: the Outlook import. `scripts/check_events.py`: the validator that runs on pull requests.
- `tests/`: pytest suite for both scripts and a build smoke test.
- `.github/workflows/deploy.yml`: builds on push, pull request and a daily schedule; deploys to GitHub Pages.
- `docs/superpowers/specs/`: the design spec.

## Colours

Black and white, with one accent. Paper is `#ffffff`, ink is `#0b0b0b`. University of Toronto blue `#1e3765` is the only colour and is reserved for links and hover states on buttons, so a visitor's eye is pulled to exactly one thing at a time. Series are told apart by their written name, never by colour.
