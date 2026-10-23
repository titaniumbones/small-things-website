# CLAUDE.md

Guidance for Claude Code in this repository: the website of the HISS Research Hub at UTSC.

## Read the design documents first

Before planning or changing anything structural (page layout, navigation, the event pipeline, deployment, styling), read the design documents in `docs/`:

- `docs/prd/2026-10-19-hiss-hub-site.md`: product requirements for the Hub site.

- `docs/superpowers/specs/2026-10-23-hiss-hub-redesign-design.md`: decisions made since the PRD (Kira's design, events only from Outlook, TODO placeholders). Where it and the PRD disagree, it wins.

- `docs/superpowers/specs/`: earlier design specs. Where an older spec and a newer document disagree, the newer one wins.

If a change you are asked to make contradicts one of these documents, say so before making it. If the change is agreed, update the document in the same commit so it stays true.

## Content map

| What | File |
| --- | --- |
| Home page text and headline | `content/_index.md` |
| About the Hub | `content/about.md` |
| Departments (one `##` section each) | `content/departments.md` |
| Calendar page text | `content/events/_index.md` |
| Small Things page, guest steps, episode details table | `content/small-things.md` |
| Contact | `content/contact.md` |
| Site name, footer line, contact email, propose-event form URL, Outlook feed URL, menu | `hugo.toml` |
| Events | the Hub's Outlook calendar, imported into `content/events/hiss/` and `content/events/small-things/` (generated, not committed) |

## Rules

- **Outlook is the only source of events.** Never add event files to the repository. A `Small Things:` title prefix in Outlook puts an event in the Small Things series (`scripts/import_ics.py`, `series_for_title`).
- **Prose stays out of templates and front matter.** Page text goes in the Markdown body under `##` headings; each heading becomes a section (`layouts/partials/content-parts.html`, `sections.html`). Front matter holds only title, description, aliases, layout, and one-line labels such as `headline` or `badge`.
- **Every URL must be real.** Check a link resolves before adding it. Write site links as `/about/`; the link render hook adds the base path.
- **Unconfirmed facts go in a placeholder:** `{{< todo >}}(Matt) what is needed{{< /todo >}}`. It shows on previews and `hugo server`, not on the live site. `make todos` lists them.
- **Python always runs through `uv run`.**

## Commands

See the `Makefile`: `make import` (pull events from Outlook), `make serve`, `make check` (validate events, list TODOs), `make todos`, `make test`, `make build`.

Pull requests get a Netlify deploy preview; the README's Netlify section explains the setup.
