# The AoB's top-level units as cells, per amendment (requirements.md in this folder). Reads only the states' output
# JSON (../aob-states_/output/) and the 1961 Rules (../aob-rules_/output/); writes output/cells.json,
# output/cells-review.json and output/cells-review.html (and cells-2004*, from series 271 on). Its code is in cells/ here: it imports nothing from docflow.
# Run aob-states_ first.

run := uv run --no-sync

.PHONY: all cells cells-2004 timeline test

all: cells cells-2004 timeline

cells:
	$(run) python -m cells src/cells.yml

# the same from the 2004 re-issue (series 271) on: output/cells-2004.json
cells-2004:
	$(run) python -m cells src/cells-2004.yml

# what the chart and the video read (ui-requirements U30): ui/timeline.json (from 1961) and ui/timeline-2004.json
timeline: cells cells-2004
	$(run) python -m cells.timeline src/cells.yml
	$(run) python -m cells.timeline src/cells-2004.yml

test:
	$(run) --with pytest pytest -q tests
