# The AoB flows together (orgpedia/doc: specs/aob.md §A5-A6). After a correction in a studio, `make refresh` here
# brings it in and builds everything that follows from it, in order:
#   1. the versions and the amendments (aob-rules_, aob-ammend_): each file's edits, and the steps they change
#   2. the Rules' states (aob-states_): the changes applied, the problems found
#   3. both again, so their states_check raises the new problems as issues for the studios
# Then reload the studio. A word edit that reaches the ops step calls Gemini on Vertex AI: the project is gcloud's
# (`gcloud auth application-default login` once).

export GOOGLE_CLOUD_PROJECT ?= $(shell gcloud config get-value project 2>/dev/null)

.PHONY: refresh flows states report

refresh: flows states
	$(MAKE) -C aob-rules_ flow
	$(MAKE) -C aob-ammend_ flow
	@$(MAKE) --no-print-directory report

flows:
	$(MAKE) -C aob-rules_ flow
	$(MAKE) -C aob-ammend_ flow

states:
	$(MAKE) -C aob-states_ states

# what each run did, and the problems still open
report:
	@grep -h -E '^(ops|export|states_check) ' aob-ammend_/logs/info.log | sed 's/^/aob-ammend_  /'
	@grep -h -E '^(export|states_check) ' aob-rules_/logs/info.log | sed 's/^/aob-rules_   /'
	@tail -n +2 aob-states_/output/report.tsv | awk -F'\t' '{f += $$5; s += $$6} END {print "changes not applied: " f " (old), " s " (states only)"}'
