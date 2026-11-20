# The AoB's top-level units as cells, per amendment (requirements.md in this folder). Reads only the states' output
# JSON (../aob-states_/output/) and the 1961 Rules (../aob-rules_/output/); writes output/cells.json,
# output/cells-review.json and output/cells-review.html. Its code is in cells/ here: it imports nothing from docflow.
# Run aob-states_ first.

run := uv run --no-sync

.PHONY: all cells test

all: cells

cells:
	$(run) python -m cells src/cells.yml

test:
	$(run) --with pytest pytest -q tests
