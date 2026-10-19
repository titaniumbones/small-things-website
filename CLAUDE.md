# CLAUDE.md

Guidance for Claude Code in this repository.

## Read the design documents first

Before planning or changing anything structural (page layout, navigation, the event pipeline, deployment, styling), read the design documents in `docs/`:

- `docs/prd/` holds product requirements. The current one is `docs/prd/2026-10-19-hiss-hub-site.md`, which turns this site from the *Small Things* podcast site into the HISS Research Hub website.

- `docs/superpowers/specs/` holds earlier design specs. Where an older spec and a newer PRD disagree, the newer document wins.

If a change you are asked to make contradicts one of these documents, say so before making it. If the change is agreed, update the document in the same commit so it stays true.

## Commands

See the `Makefile`: `make serve`, `make build`, `make check`, `make test`, `make import`. Python always runs through `uv run`.
