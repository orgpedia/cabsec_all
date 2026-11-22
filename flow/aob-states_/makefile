# The Rules after each amendment (doc/aob.md §A6), a data product: from the consolidated version
# upto 329 forward through the amendments' ops (../aob-ammend_/output/), checked against the consolidated versions
# (../aob-rules_/output/). Run those two tasks first. Writes output/states/<series>.json, output/problems.json
# and output/report.tsv (one row per amendment: its ops, those not applied, its differences from the version
# after it, and the states' drift from it).

run := uv run --no-sync

.PHONY: all states

all: states

states:
	$(run) docflow product src/states.yml
