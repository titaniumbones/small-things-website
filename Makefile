# HISS Research Hub website. Everything Python runs through uv; the site builds with Hugo.

.PHONY: serve build import check todos test clean

serve:            ## run the dev server at http://localhost:1313/
	hugo server --disableFastRender

build: check      ## build into public/
	hugo --gc --minify

import:           ## pull every event from the Outlook feed into content/events/
	uv run scripts/import_ics.py

check:            ## validate every event file and list the TODOs still in the text
	uv run scripts/check_events.py
	uv run scripts/list_todos.py

todos:            ## list every TODO placeholder still in the text
	uv run scripts/list_todos.py

test:             ## run the Python tests (includes a Hugo build smoke test)
	uv run --group dev pytest -q

clean:
	rm -rf public resources/_gen
