# Small Things website. Everything Python runs through uv; the site builds with Hugo.

.PHONY: serve build import check test clean

serve:            ## run the dev server at http://localhost:1313/
	hugo server --disableFastRender

build: check      ## build into public/
	hugo --gc --minify

import:           ## pull HISS Hub events from the Outlook feed into content/events/hiss/
	uv run scripts/import_ics.py

check:            ## validate every event file
	uv run scripts/check_events.py

test:             ## run the Python tests (includes a Hugo build smoke test)
	uv run --group dev pytest -q

clean:
	rm -rf public resources/_gen
