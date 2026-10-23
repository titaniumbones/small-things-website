# PRD: The HISS Research Hub website

- **Status:** Draft for discussion
- **Author:** Matt Price (drafted with Claude)
- **Implementer:** Kira Jensen
- **Date:** 2026-10-19

## Why

This repository currently builds a website for *Small Things*, the Hub's live-recorded podcast. The HISS Research Hub itself has no website. A site at hiss.utsc.utoronto.ca was planned but never built, although the current site links to it as if it existed.

We want to turn this site into the website of the whole Hub. *Small Things* becomes one page on it, next to the Hub's other programs.

## Who it is for

Faculty and undergraduate students at UTSC. They come for one of two reasons:

1. **To find events:** what is on this week, and how to get it into their calendar.
2. **To find out about the Hub:** what it is, which departments are in it, what it runs, and how to take part.

The home page should serve both: upcoming events near the top, with clear routes to the Hub's description and the department pages.

## Goals

1. **A site for the Hub, not the podcast.** The site's name, logo, home page and navigation all belong to the HISS Research Hub.

2. **Small Things as one page.** *Small Things* keeps a single page describing the series, its guests and its episodes. That page credits its funding (see *Funding acknowledgements*).

3. **Fuller descriptions of the Hub and its six departments.** One page on the Hub's scope of work: its research clusters, Conversations events and talk series. Then a short section or page for each department: Anthropology; Arts, Culture and Media; English; Geography; Historical and Cultural Studies; Language Studies.

4. **One calendar, maintained in Outlook.** Events are entered in the Hub's Outlook calendar. The site reads that calendar and shows the events. Nobody has to edit the repository to add an event.

5. **A way to propose an event.** Anyone can suggest an event through a link on the site. The suggestion goes to whoever maintains the Outlook calendar, who decides whether to add it. This must not require running a server.

6. **Easy to edit by hand.** Every piece of text on the site lives in a Markdown file that a non-programmer can find and change, in the GitHub web editor if need be.

7. **Easy to edit with Claude.** The README and a `CLAUDE.md` file explain where each kind of content lives and how to change it. Someone should be able to say "update the Geography description" or "add a page for the new cluster" to Claude Code and get a correct change.

8. **Looks like it belongs to U of T.** The visual style follows U of T's official brand at least loosely: its colours, its typography where it can be licensed or a close free substitute, and its general restraint.

## Non-goals

- **No server or database.** The site stays a static Hugo build, on GitHub Pages or Netlify (see Hosting).
- **No custom domain yet.** The site stays at `titaniumbones.github.io/small-things-website/` for now.
- **No sign-in or accounts** of any kind.
- **No podcast hosting.** Episode audio lives wherever it already lives. The site links to it.

## Anti-goals

These would make the project a failure even if everything else worked:

- **Text trapped in templates or settings.** If changing a sentence means editing a template, or a YAML field nested three levels deep, the site has failed goal 6. Prose goes in the body of Markdown files.
- **Two places to enter an event.** If people have to add an event to Outlook *and* to the repository, they will stop doing one of them and the two will drift apart.
- **Claims we cannot back up.** Every URL, program name and funding credit on the site has to be real. The current site links to a Hub website that does not exist. That must not happen again.

## Constraints

- **Static hosting.** GitHub Pages, built by the existing GitHub Actions workflow (`.github/workflows/deploy.yml`), or Netlify, built from `netlify.toml` (see Hosting).
- **Portable base URL.** The site must keep working if it moves to a custom domain, such as `hiss.hackinghistory.ca`. Moving it should take a change to `baseURL` in `hugo.toml` plus a DNS record, and nothing else. So: no hard-coded absolute URLs in templates or content.
- **Python through uv.** Any script runs with `uv run`, as the existing scripts do.
- **Outlook's published ICS feed** is the only machine-readable view of the calendar we have. Its URL is already in `hugo.toml` as `params.outlookFeed`.

## Hosting: GitHub Pages or Netlify

Matt is willing to move the site to Netlify if that simplifies things. Netlify is now set up alongside GitHub Pages (2026-10-23): the project `hiss-research-hub` on Matt's personal Netlify account builds every pull request against `main` from `netlify.toml` and posts a preview link on the pull request. GitHub Pages is still the live site. *(TODO (Matt): decide whether and when production moves to Netlify. Moving means pointing people at `hiss-research-hub.netlify.app` or a custom domain, then retiring `deploy.yml`.)* The two options, for the decision:

- **GitHub Pages (what we have).** Free, and already working. Pull requests get checked but not previewed. The only preview is the one-branch `/next/` workaround in `deploy.yml`.
- **Netlify.** Every pull request gets its own preview URL automatically, so the `/next/` workaround can go. **Netlify Forms** can take event proposals through a form on the site itself, with submissions emailed to the organiser. No server is involved, and the free tier allows 100 submissions a month. Costs: one more account to manage, and Kira and Matt both need access to it. The daily Outlook rebuild uses a Netlify build hook, triggered by `.github/workflows/netlify-daily.yml` (the hook URL is the repository secret `NETLIFY_BUILD_HOOK`). The build installs `uv` in Netlify's build image.

Either way, the static-site constraint stands, and so does the portable base URL.

## Decisions already made

- **Outlook is the source of truth for events.** The site imports the feed. It does not keep its own copy of events.
- **The existing Hugo site is the starting point, not a fresh build.** Keep what works: the Outlook import (`scripts/import_ics.py`), the ICS subscription feeds, the event checks (`scripts/check_events.py`), the tests and the deploy workflow. Replace the identity, navigation and page structure.
- **Preview before merging.** Build this work on a branch and preview it before merging to `main`. On Netlify, every pull request gets a preview automatically (this is now set up). On GitHub Pages, point `PREVIEW_BRANCH` in `deploy.yml` (on `main`) at the new branch. That replaces the `redesign/minimal` preview, which this work supersedes. Start the new branch from `main`. Borrow layout ideas from `redesign/minimal` where they are useful.
- **Speakers' Corner joins the Hub's talk series.** It no longer has a page or menu entry of its own. Its talks are listed with the rest of the talk series, on the About page and in the calendar. Its current description (`content/events/speakers-corner/_index.md`) can become a paragraph in the talk-series section.
- **Logo:** the official HISS Research Hub logo. *(Matt is locating the file; it will be added to `static/` or `assets/`.)*

## Pages

This is a starting structure. The builder can adjust it.

| Page | Contents |
| --- | --- |
| Home | One paragraph on what the Hub is; the next few upcoming events; links to the Hub, department and calendar pages. |
| About the Hub | The Hub's scope of work: research clusters, Conversations events, the talk series, who runs it, how to get involved. |
| Departments | A short description of each of the six departments and its connection to the Hub, linking to the department's own site. One page with six sections, or six short pages: builder's call. |
| Calendar | Every upcoming event, from the Outlook feed. Subscribe links. A "Propose an event" link. |
| Small Things | The podcast: what it is, how to be a guest, the season's episodes, funding acknowledgement. |
| Contact | Who to write to, for what. |

## Content and editing

- **One page, one Markdown file.** Each file's text is plain Markdown under clear `##` headings. Front matter holds only what templates need (title, a one-line description, menu weight) and no prose.
- **Placeholders are visible.** Where the facts are not yet known, the draft says so in the text, for example `TODO (Matt): confirm cluster names`, so nobody mistakes a guess for a fact. A check should list the remaining TODOs.
- **The first drafts will need rewriting.** Claude will write first drafts of the Hub and department descriptions. Expect Matt and others to rewrite them. Keep each section short and self-contained so a person can replace one paragraph without touching the rest.
- **`README.md`** is for people: how to change text, how events get onto the site, how to preview, how to deploy.
- **`CLAUDE.md`** is for Claude Code: the content map (which file holds what), the rules (Outlook is the source of events; prose stays out of templates; every URL must be real), and the commands to build and check the site.

## Calendar

- The daily scheduled build already pulls the Outlook feed. Keep it, so new Outlook events appear on the site within a day without anyone touching the repository.
- Keep the ICS subscription feeds so people can add the Hub calendar to their own calendar app.
- **Moving the repository's own events into Outlook.** Ten events live as files in the repo today: seven *Small Things* episodes and three Speakers' Corner talks. They have to be in Outlook before their files are deleted, or they vanish from the site. The site already publishes them as ICS. The builder exports those feeds as one `.ics` file. Matt imports it into the Hub's Outlook calendar and confirms the events show up in the published feed. Only then are the files and the duplicate-title check in `scripts/import_ics.py` removed. *(TODO (Matt): can the HCS organisers of Speakers' Corner add events to the Hub calendar, or do they send them to the calendar's owner?)*
- **If the Outlook import fails** *(builder's call)*: now that Outlook is the only source of events, a failed import should fail the build and leave the last good deploy in place. Today's build publishes with no events instead.
- **Old URLs** *(my call; no posters or QR codes are known to point at the current site)*: keep the site-wide feed at its current path (`/calendar.ics`). Give moved pages Hugo `aliases` so their old URLs still lead somewhere. Old per-series feeds can go.
- **Proposing an event.** The recommended mechanism is a Microsoft Form on U of T's Microsoft 365. It needs no server, and people sign in with their U of T account, which they already have. Submissions arrive with whoever owns the form, who adds accepted events to Outlook by hand. The form's URL goes in `hugo.toml` as a parameter. If the parameter is empty, the link falls back to a `mailto:` link to the contact address.
  - We rejected GitHub issue forms because most faculty and students do not have GitHub accounts.

## Funding acknowledgements

The *Small Things* page acknowledges:

- **Research for Inclusive Excellence (RIE) funds** from UTSC. *(TODO (Matt): confirm the exact grant name and the office that awards it.)*
- **The CoP project.** *(TODO (Matt): exact name, funder and wording; Matt is locating the documents.)*

The current About page also credits the Mentoring Partnership Fund and the six founding departments. *(TODO (Matt): keep or drop?)*

## Visual style

- Follow the U of T brand guidelines (brand.utoronto.ca): U of T blue as the primary colour, a restrained palette and a clean sans-serif. *(Builder: check the current guidelines for the exact colour values and typefaces, and use a free web font where the official face is not licensed for the web.)*
- The current branch `redesign/minimal` has a minimal design with Space Grotesk. Treat it as a reference for layout, not for brand.
- Accessible contrast and a layout that works on a phone.

## Cleanup

- Remove `params.hubUrl` from `hugo.toml` and every link to hiss.utsc.utoronto.ca.
- Rename the site's `title`, `description` and README from *Small Things* to the Hub.
- Decide whether the repository itself gets renamed. Renaming changes the GitHub Pages URL. *(TODO (Matt).)*

## Open questions

1. **How series events are told apart.** Once every event comes from Outlook, the site needs a way to know which events are *Small Things* episodes, for that page's list. The likeliest options are a title prefix (`Small Things: …`) or a marker line in the Outlook event's description. The builder should check what the published ICS feed actually carries, such as whether Outlook categories survive into it, and propose a convention for Matt to approve.
2. **Small Things episode details.** Each episode currently has a repository file holding its object, guest, department and audio link. If events come only from Outlook, where do those details go? A table on the Small Things page is the simplest option.
3. **Who owns the event-proposal form** and receives its submissions.

## Done means

- The site at the current URL presents the HISS Research Hub, with the HISS logo, U of T–like styling, and pages for the Hub, the departments, the calendar, *Small Things* and contact.
- Every event on the site comes from the Outlook feed. Adding an event in Outlook puts it on the site after the next daily build, with no repository change.
- A "Propose an event" link works and needs no server.
- Every piece of visible text can be changed by editing one Markdown file. The README and `CLAUDE.md` say which file.
- No link points to a site that does not exist. Remaining TODOs are listed by a check, not hidden.
- The existing tests pass, and new tests cover the page structure and the calendar import.
