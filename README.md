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

## Netlify: pull request previews and a second copy of the site

GitHub Pages is still the live site. Netlify runs alongside it, mainly so that every pull request gets its own preview address. This section explains how that works and where each setting lives.

### Where it lives

- **Account:** Matt's personal Netlify account (moptop99@gmail.com), team "moptop99's team", free plan.

- **Project:** `hiss-research-hub`. Dashboard: <https://app.netlify.com/projects/hiss-research-hub>.

- **Connection to GitHub:** through the Netlify GitHub app, which is installed on the `titaniumbones` account with access to selected repositories only. This repository is one of them. If Netlify ever stops seeing the repository, check GitHub → Settings → Applications → Netlify → Repository access.

- **Who can change it:** only Matt, for now. *(TODO (Matt): invite Kira to the Netlify team if she needs to read deploy logs or change settings.)*

### What triggers a build

| Event | What Netlify builds | Address |
| --- | --- | --- |
| A pull request is opened against `main`, or a new commit is pushed to its branch | A **deploy preview** of that branch | `https://deploy-preview-<PR number>--hiss-research-hub.netlify.app/` |
| A commit lands on `main` (usually by merging a pull request) | A **production** build | <https://hiss-research-hub.netlify.app/> |
| Every day at 10:00 UTC | A production rebuild, so new Outlook events appear | same as production |

When a preview finishes, Netlify posts a comment on the pull request with the preview link and a link to the deploy log, and adds a check called `netlify/hiss-research-hub/deploy-preview` to the pull request. A failed preview never touches the live site or the production copy.

Pushes to other branches are not built: in the project's settings only `main` is a branch Netlify deploys, so the `[context.branch-deploy]` block in `netlify.toml` is unused unless that setting changes.

The daily rebuild exists because Netlify only builds when the repository changes, and Outlook events change without any commit. `.github/workflows/netlify-daily.yml` runs on a schedule and sends a POST request to a Netlify **build hook**: a secret URL that starts a production build. The hook URL is stored as the repository secret `NETLIFY_BUILD_HOOK` (GitHub → Settings → Secrets and variables → Actions). GitHub runs scheduled workflows only from `main`, so the daily rebuild starts once that file is on `main`. You can also start it by hand from the Actions tab ("Daily Netlify rebuild" → "Run workflow").

### What a build does

`netlify.toml` holds the build. Netlify reads it from the branch being built, so a pull request can change its own build. Each build:

1. installs `uv` (Netlify's build image has Python but not uv);
2. runs `scripts/check_events.py`, the same event checks as on GitHub;
3. pulls events from the Outlook feed with `scripts/import_ics.py`;
4. runs the test suite (previews and production only);
5. builds the site with Hugo, setting `--baseURL` to the address of this particular deploy so that links and feeds point at the preview, not at the live site.

Netlify sets two variables the build uses: `URL`, the production address, and `DEPLOY_PRIME_URL`, the address of this deploy. Previews also set `HUGO_PARAMS_NOINDEX=true`, which adds a `noindex` tag to every page; Netlify itself also sends an `X-Robots-Tag: noindex` header on previews. Either keeps search engines from listing a preview.

### Settings that are not in the repository

Most of the build is in `netlify.toml`, but a few things are set in the Netlify dashboard (Project configuration):

- the production branch (`main`) and which branches deploy (only `main`);
- the environment variable `HUGO_VERSION` (also set in `netlify.toml`; the dashboard copy covers branches that do not have the file yet);
- the build hook "Daily rebuild (GitHub Actions)" (Build & deploy → Build hooks);
- deploy notifications, including the pull request comment.

### When a build fails

Open the deploy log from the link in the pull request comment, or from Deploys in the dashboard. The log shows each step above in order. The usual causes are an event file the checks reject, a failing test, or a Hugo template error, and the same failure shows up locally with `make check`, `make test` or `make build`. To rebuild without a new commit, use "Retry deploy" in the dashboard.

### Using the Netlify CLI on this repository

The Netlify CLI on Matt's Mac is logged in to a different account. For this repository it must use the moptop99 account. A local `.envrc` file (not committed; it needs [direnv](https://direnv.net/)) sets `NETLIFY_AUTH_TOKEN` from the macOS Keychain item `netlify-moptop99` whenever you are inside the repository; the CLI uses that token in preference to its own login. `netlify link` has already connected the folder to the project (stored in `.netlify/`, also not committed). Useful commands: `netlify status`, `netlify open`, `netlify logs --source deploy`, `netlify env:list`.

The token expires on 2027-01-21. To replace it, make a new one under Netlify → User settings → Applications → Personal access tokens, then store it with `security add-generic-password -U -s netlify-moptop99 -a moptop99 -w <token>`.

## Previewing another branch

The deploy workflow can publish a second branch alongside the live site at `/next/`, so two versions can be compared in a browser. The branch name is the `PREVIEW_BRANCH` setting at the top of `.github/workflows/deploy.yml`. The preview carries a `noindex` tag so search engines ignore it, and a failure to build it never blocks the main site. Set the value to an empty string to stop publishing the preview, for example once the branch has been merged.

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

- `hugo.toml`: site settings, menu, the Outlook feed URL, and the custom `.ics` and `.json` output formats.
- `layouts/`: templates. `home.html`, `calendar.html`, `events/section.html` (series pages), `events/page.html` (one event), and the `*.calendar.ics` and `home.eventsjson.json` feed templates. Shared pieces live in `layouts/partials/`.
- `assets/scss/main.scss`: all styles. Colours and type are set as variables at the top. Hugo compiles it; there is no npm.
- `assets/js/site.js`: the calendar's series filter. The page works without it.
- `static/fonts/`: Bricolage Grotesque, self-hosted.
- `scripts/import_ics.py`: the Outlook import. `scripts/check_events.py`: the validator that runs on pull requests.
- `tests/`: pytest suite for both scripts and a build smoke test.
- `.github/workflows/deploy.yml`: builds on push, pull request and a daily schedule; deploys to GitHub Pages.
- `netlify.toml`: the Netlify build, used for pull request previews. `.github/workflows/netlify-daily.yml` triggers a daily Netlify rebuild through a build hook.
- `docs/superpowers/specs/`: the design spec.

## Colours

The University of Toronto blue `#1e3765` is the ground. Each series has one colour: Small Things coral `#ff5c39`, Speakers' Corner yellow `#f5c400`, HISS Hub teal `#007fa3` (the UofT accent blue). Series colour is never the only signal; every chip also carries the series name.
