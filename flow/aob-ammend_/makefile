# The amendments to the Allocation of Business Rules (orgpedia/doc: specs/aob.md §A5): input/*.pdf ->
# output/<name>.govdoc.json.zst, one document per notification, its ops as legal: relations. docflow keeps its
# working store in .storage/ (GovDoc files by id, the call cache, state); output/ links each file there by name.
# The ops come from Gemini on Vertex AI: set GOOGLE_CLOUD_PROJECT and log in with
# `gcloud auth application-default login`. Messages go to logs/info*.log, run logs to logs/run-*.jsonl.

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

studio:
	$(run) studio serve $(if $(DOCS),--docs $(DOCS)) $(if $(DOC),--doc $(DOC)) $(if $(DIR),--dir $(DIR))
