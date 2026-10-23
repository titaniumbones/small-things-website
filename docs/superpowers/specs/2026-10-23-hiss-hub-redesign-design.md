# Design: HISS Research Hub site on Kira's redesign

- **Date:** 2026-10-23

- **Builds on:** the PRD `docs/prd/2026-10-19-hiss-hub-site.md`. Read it first. This note records decisions made since, and where it disagrees with the PRD, this note wins (the PRD is updated in the same branch).

- **Branch:** `hiss-hub`, started from `main` after the Netlify setup (PR #3) merged, so it gets a Netlify deploy preview. Its pull request targets `main`.

## Intent

The site stops being the *Small Things* podcast site and becomes the website of the HISS Research Hub at UTSC. Kira Jensen's redesign on `redesign/minimal` (published at `/next/` on GitHub Pages) is the visual starting point. Matt wants to switch to it. *Small Things* becomes one page of the Hub site.

The people it serves are UTSC faculty and undergraduates who come either to find events or to find out about the Hub (PRD, *Who it is for*).

## What changed since the PRD

1. **Visual style is Kira's design, not the U of T brand.** Space Grotesk for display and body, JetBrains Mono for labels and numbers, zinc greys on white, a near-black hero with a faint grid and a navy glow, U of T blue (`#1e3765`) as the link and accent colour. This replaces PRD goal 8 and the *Visual style* section, which treated `redesign/minimal` as "a reference for layout, not for brand". Accessible contrast and a phone layout still apply.

2. **No logo yet.** Matt could not find the official HISS logo. The header uses a text wordmark ("HISS Research Hub"). A visible `TODO (Matt): official HISS logo` sits in the README and in the TODO check output (not on the public page). Swapping in a logo later should mean adding a file and changing one partial.

3. **The repository's own events are deleted, not migrated to Outlook.** The PRD planned to export the ten repo events and have Matt import them into Outlook. Nine of them are placeholders ("Guest and object to be announced", "Speaker to be announced"), and some dates have passed. Importing them would put fake events into the real calendar. The tenth, the Bhavani Raman episode, is already in the Outlook feed. So the files under `content/events/small-things/` and `content/events/speakers-corner/` that are events go, and so does the duplicate-title check in `scripts/import_ics.py` that existed only to avoid doubles with them. No `.ics` export is needed.

4. **The calendar is empty for now, and the site must look right empty.** The Outlook feed's newest event is 2026-04-15. Kira will keep the calendar up to date going forward. Until she adds events, every place that lists upcoming events shows a short empty-state message with the "Propose an event" link, and past events stay visible below so the site does not look abandoned.

5. **Small Things episodes are recognised by title prefix.** The published ICS feed carries no categories (checked 2026-10-23: 20 events, 0 `CATEGORIES` lines). It already uses the prefix `Small Things:` for the one episode. Convention: an Outlook event whose title starts with `Small Things:` is a *Small Things* episode. This answers PRD open question 1.

6. **Episode details live in the Small Things page's Markdown.** Object, guest, department and audio link for each episode go in a Markdown table in the body of the Small Things page file. One row today (Bhavani Raman). This answers PRD open question 2.

7. **"Propose an event" is a `mailto:` link for now** to `params.contactEmail` (`matt.price@utoronto.ca`), because no Microsoft Form exists yet. The form-URL parameter from the PRD is added to `hugo.toml` empty, so filling it in later switches the link with no template change. PRD open question 3 (who owns the form) stays open.

8. **TODO notes show on previews and are hidden on the live site** (Matt, 2026-10-23). In Markdown a placeholder is written so a template or render hook can find it (builder's call how: a shortcode such as `{{< todo >}}…{{< /todo >}}` is one option). Netlify deploy previews and local `hugo server` show it, highlighted; production builds (Netlify production and GitHub Pages) drop it. The TODO check lists every one and does not fail the build, so the site can merge while drafts are still being rewritten.

9. **Kira switches to this branch.** She is still working on `redesign/minimal` but will move to `hiss-hub` (Matt, 2026-10-23). So her design is copied into `hiss-hub` once, not merged, and `redesign/minimal` is frozen. `PREVIEW_BRANCH` in `deploy.yml` is set to `""` in this branch, so `/next/` stops publishing her old Small Things version once this merges. Netlify previews replace it.

## Goals

As in the PRD, with the changes above. In short:

- The site's name, wordmark, home page and navigation belong to the Hub.

- Pages: Home, About the Hub, Departments, Calendar, Small Things, Contact (PRD *Pages* table).

- Every event comes from the Outlook feed. Adding an event in Outlook puts it on the site after the next daily build.

- Every piece of visible prose can be changed by editing one Markdown file, in the body under `##` headings.

- No link points to a site that does not exist. Remaining TODOs are listed by a check.

## Anti-goals

From the PRD, restated because Kira's branch currently breaks the first one:

- **Text trapped in templates or settings.** `redesign/minimal` keeps most page prose in front matter (`pitch.body`, `steps[].body`, `sections[].body`, `takePart[].body`). That has to move into Markdown bodies. Front matter keeps only what templates need: title, one-line description, menu weight, and short labels the template positions (for example the hero pill). If a template needs structure (numbered steps, a department list), it gets it from ordinary Markdown in the body (an ordered list, a bulleted list of links) styled by CSS, not from YAML.

- **Two places to enter an event.** Gone once the repo event files are deleted.

- **Claims we cannot back up.** Every URL, program name and funding credit has to be real or marked TODO.

## Pages and content

| Page | File | Contents |
| --- | --- | --- |
| Home | `content/_index.md` | One paragraph on what the Hub is; the next three upcoming events (or the empty state); links to About, Departments, Calendar; a short pointer to *Small Things*. |
| About the Hub | `content/about.md` | Scope of work: research clusters, Research Conversations, the talk series (with Speakers' Corner as a paragraph), who runs it, how to get involved, funding. |
| Departments | `content/departments.md` | One page, six `##` sections, each a short paragraph and a link to the department's own site. *(Builder's call per the PRD: one page, because six short pages would each be a paragraph.)* |
| Calendar | `content/events/_index.md` | Upcoming events from Outlook (or the empty state), past events, subscribe links, "Propose an event". Stays at `/events/`; `/calendar/` stays an alias. |
| Small Things | `content/small-things.md` (or the series section page, builder's call) | What it is, how to be a guest (Kira's five steps, as a Markdown ordered list), the episodes found by title prefix, the episode details table, funding acknowledgement. Kira's guest pitch and "Looking for 2026–2027 guests" pill move here from the home page. |
| Contact | `content/contact.md` | Who to write to, for what. |

Kira's `what-we-do` page is folded into About (series, how to take part) and removed; give it an alias to `/about/`. Its "Add an event: one file on GitHub" item is wrong after this change and must not survive.

**Sources for first drafts.** Matt's earlier site `~/UTSC/HISS/hiss-website/content/` (mission, department list, contact); `~/UTSC/HISS/MPF-2026/Research-Clusters-Report.md` and `MPF-Application-Draft.md` (clusters, Conversations); `~/UTSC/HISS/RIE-proposal/RIE-Application-Draft.md` (Research Conversations series, funding). These are proposals and drafts, not facts: cluster names are preliminary, grant outcomes unknown. Anything taken from them is marked `TODO (Matt): confirm …` in the text. Do not use `hiss@utsc.utoronto.ca` from the old site; it is unverified. Department URLs from Kira's branch are the ones to use; check each resolves before relying on it.

## Calendar and events

- `scripts/import_ics.py` remains the only way events enter the site. It assigns `series: small-things` to events whose title starts with `Small Things:` and `series: hiss` to the rest. *(Builder decides whether to strip the prefix from the displayed title on the Small Things page.)*

- **A failed import fails the build** (PRD, builder's call, now decided). Remove the `|| echo …` fallback in `netlify.toml` and the equivalent in `.github/workflows/deploy.yml`, so a broken feed leaves the last good deploy in place.

- Speakers' Corner has no page or menu entry. Its feed `events/speakers-corner/calendar.ics` and section go. Old per-series feeds can go except `/calendar.ics` (PRD, *Old URLs*). Moved pages get Hugo `aliases`.

- Empty state wording, in Markdown or a single short front-matter label: "Nothing is on the calendar yet. Have an idea? Propose an event."

- The README gets an "Adding an event" section written for Kira: add it to the Hub's Outlook calendar; start *Small Things* episode titles with `Small Things:`; it appears within a day; add the episode's details row to the Small Things page.

## Cleanup

- Remove `params.hubUrl` and every link to hiss.utsc.utoronto.ca.

- Rename `title`, `description` and README from *Small Things* to the Hub.

- In `deploy.yml`, change only the import (fail loudly) and set `PREVIEW_BRANCH: ""`. Whether GitHub Pages is retired is Matt's open hosting decision (PRD *Hosting*).

- `CLAUDE.md` gains the content map, rules and commands the PRD lists.

## Checks and tests

- A TODO check (a `make todos` target, also run by `make check`) lists every TODO marker in `content/`, `hugo.toml` and the README. It reports; it does not fail.

- Tests: update `tests/test_build.py` to the new page set and feeds; add tests for the title-prefix series assignment and for the import failing loudly; keep the existing import and check tests passing. A build with zero upcoming events must succeed and show the empty state (test it).

## Left to the builder

Template structure, how the `##` sections of a page map onto Kira's visual sections, CSS changes needed for body-rendered content, the exact empty-state markup, file names, and whether Small Things is a plain page or the series section page.

## Done means

PRD *Done means*, except: "with the HISS logo" becomes "with a HISS wordmark (logo pending)", and "U of T–like styling" becomes "Kira's redesign".
