# The consolidated versions of the Allocation of Business Rules (orgpedia/doc: specs/aob.md §A5), the checkpoints:
# input/*.pdf -> output/<name>.govdoc.json.zst, and output/<name>.json, the version read into its tree of parts and
# its footnotes. docflow keeps its working store in .storage/; output/ links each file there by name.
# Messages go to logs/info*.log, run logs to logs/run-*.jsonl.

run := uv run --no-sync
docflow := $(run) docflow
flow := src/flow.yml --storage .storage
FILES ?=

.PHONY: all import flow validate issues expect studio

all: import flow validate issues

import: .storage/logs
	$(docflow) import $(flow) > logs/info.import.log

# FILES=<file of file ids, one a line>: only those (the samples)
flow: .storage/logs
	$(docflow) run $(flow) $(if $(FILES),--files $(FILES)) > logs/info.log
	$(docflow) link $(flow) >> logs/info.log

validate:
	$(docflow) validate $(flow) > logs/info.validate.log

issues:
	$(docflow) issues $(flow) > logs/info.issues.tsv

expect:
	$(docflow) expect $(flow)

.storage/logs:
	mkdir -p .storage logs
	ln -s ../logs .storage/logs

# a run from the studio may call Gemini (reviewer.md §R8): gcloud's project, unless one is set
studio: export GOOGLE_CLOUD_PROJECT ?= $(shell gcloud config get-value project 2>/dev/null)
studio:
	$(run) studio serve $(if $(DOCS),--docs $(DOCS)) $(if $(DOC),--doc $(DOC)) $(if $(DIR),--dir $(DIR))
