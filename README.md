# HISS Research Hub website

The website of the Humanities and Interpretive Social Sciences (HISS) Research Hub at the University of Toronto Scarborough: what the Hub is, its six departments, its calendar of events, and its podcast *Small Things*.

Live site: https://titaniumbones.github.io/small-things-website/

It is a static site built with [Hugo](https://gohugo.io). Every page's text is a Markdown file you can edit in the GitHub web editor. Every event comes from the Hub's Outlook calendar.

*TODO (Matt): add the official HISS logo. The header shows a text wordmark until then; the logo goes in `layouts/partials/header.html` and `footer.html`.*

## Adding an event

Add it to the Hub's Outlook calendar. That is all. The site reads the calendar's published feed once a day (and on every change to the repository), so a new event appears on the site within a day. To change or cancel an event, change it in Outlook.

- **Small Things recordings:** start the Outlook title with `Small Things:`, for example `Small Things: Bhavani Raman & Matt Price`. That puts the event in the *Small Things* series and on the Small Things page. Then add a row for the episode (guest, department, object, audio link) to the "Episode details" table in `content/small-things.md`.

- **Everything else** (talks, Research Conversations, Speakers' Corner, screenings, launches) needs no prefix.

- **Location and a link:** fill in Outlook's location field, and put a web address in the event if there is one. Both show on the site.

People who want to suggest an event use the "Propose an event" link, which emails `params.contactEmail` (or goes to the form in `params.proposeEventUrl`, once there is one) in `hugo.toml`.

## Changing the text of a page

Each page is one Markdown file. Its text is under `##` headings; each heading becomes one section of the page. Change the words, commit, and the site rebuilds.

| Page | File |
| --- | --- |
| Home | `content/_index.md` (the big headline is `headline:` at the top) |
| About the Hub | `content/about.md` |
| Departments | `content/departments.md` |
| Calendar | `content/events/_index.md` (the event list itself comes from Outlook) |
| Small Things | `content/small-things.md` (the "Looking for guests" badge is `badge:` at the top) |
| Contact | `content/contact.md` |
| Footer line | `description` in `hugo.toml` |

In the GitHub web editor: open the file, click the pencil, edit, then **Commit changes → Create a new branch and start a pull request**. The pull request gets a Netlify preview link (see below) so you can check the page before merging.

### Placeholders

Where a fact is not known yet, the text marks it like this:

```
Four clusters are forming. {{< todo >}}(Matt) confirm the cluster names{{< /todo >}}
```

The placeholder shows, highlighted in yellow, on pull request previews and when you run the site locally. The live site leaves it out. To replace it, write the real fact and delete the whole `{{< todo >}}…{{< /todo >}}`. `make todos` lists every placeholder left.

## Calendar feeds

The site publishes iCalendar feeds anyone can subscribe to:

- `/calendar.ics`: every event
- `/events/hiss/calendar.ics` and `/events/small-things/calendar.ics`: one series each
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

## Working locally

You need [Hugo](https://gohugo.io/installation/) (extended edition) and [uv](https://docs.astral.sh/uv/).

```sh
make import     # pull every event from Outlook (without it the calendar is empty)
make serve      # http://localhost:1313/small-things-website/, placeholders shown
make check      # validate imported event files and list placeholders
make todos      # list placeholders only
make test       # Python tests plus Hugo build tests
make build      # production build into public/
```

If the Outlook feed cannot be fetched or is not a calendar, the import stops with an error and the build fails, so the live site keeps its last good version instead of publishing with no events.

## How it is put together

- `hugo.toml`: site settings, menu, the Outlook feed URL, and the custom `.ics` and `.json` output formats.
- `layouts/`: templates. `home.html`, `page.html` (About, Departments, Contact), `small-things.html`, `events/section.html` (the calendar), `events/page.html` (one event), and the `*.calendar.ics` and `home.eventsjson.json` feed templates. `partials/content-parts.html` and `partials/sections.html` turn a page's `##` headings into sections; `shortcodes/todo.html` is the placeholder. No page text lives in templates.
- `assets/scss/main.scss`: all styles. Colours and type are set as variables at the top. Hugo compiles it; there is no npm.
- `assets/js/site.js`: the calendar's series filter. The page works without it.
- `static/fonts/`: Space Grotesk and JetBrains Mono, self-hosted (OFL).
- `scripts/import_ics.py`: the Outlook import, which writes `content/events/hiss/` and `content/events/small-things/` (not committed). `scripts/check_events.py`: checks those files. `scripts/list_todos.py`: lists placeholders.
- `tests/`: pytest suite for the scripts, and build tests that run Hugo on a copy of the site with known events.
- `.github/workflows/deploy.yml`: builds on push, pull request and a daily schedule; deploys to GitHub Pages.
- `netlify.toml`: the Netlify build, used for pull request previews. `.github/workflows/netlify-daily.yml` triggers a daily Netlify rebuild through a build hook.
- `docs/prd/`: product requirements. `docs/superpowers/specs/` and `docs/superpowers/plans/`: design notes and implementation plans.

## Look

The design is Kira Jensen's: Space Grotesk for text, JetBrains Mono for small labels, zinc greys on white, a near-black hero with a faint grid, and University of Toronto blue `#1e3765` for links and accents. Colours and type are variables at the top of `assets/scss/main.scss`. Series are told apart by name on every event, not by colour alone.
