.DEFAULT_GOAL := help
SHELL := /bin/bash

SRC  := input/src
LOGS := input/logs
PY   := uv run python -u

# ---------------------------------------------------------------- ADAPT
NAME := cabsec_all
# collections every target works on; e.g. make download C=aob
C ?= council aob tob
# one archive.org collection for all three: opensource (Community Texts) until archive.org creates india-cabsec, then
#   make update_archive_metadata IA_COLLECTION=india-cabsec
IA_COLLECTION ?= opensource
# setup uploads only this many items of each of council, aob, tob to archive.org (enough to request a collection); empty = all
SETUP_ARCHIVE_LIMIT ?= 55
# 1 = setup links Wayback before uploading; 0 = leave Wayback to `backfill WHAT=wayback`
SETUP_WAYBACK ?= 0
# HF dataset the council files are seeded from (onetime_seed)
SEED_HF_REPO ?= Orgpedia/cabsec
SEED_DIR     ?= LFS/_seed/cabsec
# ----------------------------------------------------------------

# Max items per run and collection for download / link_wayback / upload_archive (empty = no limit)
LIMIT ?=
# new = only items first seen within NEW_WINDOW; all = everything pending
SCOPE ?= all
NEW_WINDOW ?= 7d
DOWNLOAD_DELAY ?= 1
# 1 = also retry downloads that failed with 404 / unknown type
RETRY_FAILED ?= 0
# Wayback SPN2: reuse an existing capture newer than this instead of re-capturing
WAYBACK_REUSE ?= 30d
# 0 = status skips the site vs archive.org search
IA_CHECK ?= 1

ifneq (,$(wildcard .env))
include .env
endif
HF_REPO := $(or $(HF_REPO_ID),Orgpedia/$(NAME))
ENV_FILE := $(if $(wildcard .env),--env-file .env)

LIMIT_ARG := $(if $(LIMIT),--limit $(LIMIT))
RETRY_ARG := $(if $(filter 1,$(RETRY_FAILED)),--retry-failed)
SCOPE_ARG = --scope $(SCOPE) --window $(NEW_WINDOW)
COLL_ARG := --collection $(IA_COLLECTION)

# $(call EACH,<script and args>): run once per collection in C,
# log to input/logs/<target>.<collection>.log; every collection runs, the target fails if any failed.
RUN_C = CABSEC_COLLECTION=$(1) $(PY) $(SRC)/$(2) 2>&1 | tee $(LOGS)/$@.$(1).log
EACH = mkdir -p $(LOGS); set -o pipefail; rc=0; \
	$(foreach c,$(C),echo "===== $(c)"; $(call RUN_C,$(c),$(1)) || rc=1;) exit $$rc
HF = mkdir -p $(LOGS); set -o pipefail; uv run $(ENV_FILE) hf $(1) 2>&1 | tee $(2)

.PHONY: help install discover discover_full onetime_seed download link_wayback upload_archive update_archive_metadata \
        show_metadata sync_hf_push hf_card import status setup update backfill

help:
	@echo "Usage: make <target> [C='council aob tob'] [VAR=value ...]   (see SPEC.md)"
	@echo ""
	@echo "Modes"
	@echo "  setup                    first time: discover_full onetime_seed download sync_hf_push hf_card upload_archive LIMIT=$(SETUP_ARCHIVE_LIMIT)"
	@echo "  update                   new items: discover download link_wayback upload_archive sync_hf_push status"
	@echo "  backfill WHAT=archive    upload the archive.org backlog              [C=... LIMIT=$(LIMIT)]"
	@echo "  backfill WHAT=wayback    capture the Wayback backlog, then refresh archive.org metadata"
	@echo ""
	@echo "Steps (each runs for every collection in C=$(C))"
	@echo "  install                  set up the uv environment"
	@echo "  discover                 record new entries from cabsec.gov.in in input/documents/<c>/items.json"
	@echo "  discover_full            walk the whole site: update changed entries, mark removed ones"
	@echo "  onetime_seed             council only: hf download $(SEED_HF_REPO) -> $(SEED_DIR), seed matching files"
	@echo "  download                 download missing files                       [SCOPE=$(SCOPE) LIMIT=$(LIMIT) RETRY_FAILED=$(RETRY_FAILED)]"
	@echo "  link_wayback             Wayback SPN2 captures                        [SCOPE=$(SCOPE) LIMIT=$(LIMIT) WAYBACK_REUSE=$(WAYBACK_REUSE)]"
	@echo "  upload_archive           upload to archive.org, oldest first          [SCOPE=$(SCOPE) LIMIT=$(LIMIT) IA_COLLECTION=$(IA_COLLECTION)]"
	@echo "  update_archive_metadata  re-apply changed metadata (incl. collection) [IA_COLLECTION=india-cabsec]"
	@echo "  show_metadata            print one item's archive.org metadata         [C=aob ID=386]"
	@echo "  sync_hf_push             hf upload: LFS/$(NAME)/<c>/pdfs -> $(HF_REPO) (unchanged files skipped)"
	@echo "  hf_card                  hf upload: input/hf/README.md -> $(HF_REPO)"
	@echo "  import                   hf download: $(HF_REPO) -> LFS/$(NAME), then relink"
	@echo "  status                   counts + site vs archive.org check           [IA_CHECK=$(IA_CHECK)]"
	@echo ""
	@echo "archive.org collection: $(IA_COLLECTION) (target: india-cabsec)"
	@echo "Credentials come from .env (see env.example)."

install: pyproject.toml
	uv sync

# ---------------------------------------------------------------- steps

discover:
	$(call EACH,discover.py)

discover_full:
	$(call EACH,discover.py --full)

# Downloads the old dataset (~2.3 GB) once; the files are hardlinked into LFS/$(NAME). Delete $(SEED_DIR) afterwards if you like.
onetime_seed:
	$(call HF,download $(SEED_HF_REPO) --repo-type dataset --include "pdfs/**/*.pdf" --local-dir $(SEED_DIR),$(LOGS)/onetime_seed_hf.log)
	mkdir -p $(LOGS); set -o pipefail; $(call RUN_C,council,onetime_seed.py --seed-dir $(SEED_DIR))

download:
	$(call EACH,download.py $(SCOPE_ARG) --delay $(DOWNLOAD_DELAY) $(RETRY_ARG) $(LIMIT_ARG))

link_wayback:
	$(call EACH,link_wayback.py $(SCOPE_ARG) --reuse $(WAYBACK_REUSE) $(LIMIT_ARG))

upload_archive:
	$(call EACH,upload_archive.py $(SCOPE_ARG) $(LIMIT_ARG) $(COLL_ARG))

update_archive_metadata:
	$(call EACH,upload_archive.py --update-metadata $(COLL_ARG))

show_metadata:
	@test -n "$(ID)" || { echo ">>> usage: make show_metadata C=aob ID=386"; exit 1; }
	@for c in $(C); do CABSEC_COLLECTION=$$c $(PY) $(SRC)/upload_archive.py --show "$(ID)" || true; done

# Unchanged files are skipped and nothing is deleted on HF; the dataset is created (public) on the first push.
sync_hf_push:
	mkdir -p $(LOGS); set -o pipefail; rc=0; \
	$(foreach c,$(C),if [ -d LFS/$(NAME)/$(c)/pdfs ]; then \
	  uv run $(ENV_FILE) hf upload $(HF_REPO) LFS/$(NAME)/$(c)/pdfs $(c)/pdfs --repo-type dataset \
	    --exclude "*.part" --exclude ".DS_Store" --commit-message "sync $(c) files" 2>&1 | tee $(LOGS)/$@.$(c).log || rc=1; \
	else echo "*** no files in LFS/$(NAME)/$(c)/pdfs, nothing to push"; fi;) \
	exit $$rc

hf_card:
	$(call HF,upload $(HF_REPO) input/hf/README.md README.md --repo-type dataset --commit-message "dataset card",$(LOGS)/$@.log)

import:
	$(call HF,download $(HF_REPO) --repo-type dataset --local-dir LFS/$(NAME) $(foreach c,$(C),--include "$(c)/pdfs/**"),$(LOGS)/$@.log)
	$(MAKE) --no-print-directory download

status:
	$(call EACH,status.py $(if $(filter 0,$(IA_CHECK)),--no-ia))

# ---------------------------------------------------------------- modes
# Every step runs even if an earlier one failed; the mode exits non-zero at the end.

setup: install
	@rc=0; \
	$(MAKE) --no-print-directory discover_full || rc=1; \
	$(if $(filter council,$(C)),$(MAKE) --no-print-directory onetime_seed || rc=1;) \
	$(MAKE) --no-print-directory download || rc=1; \
	$(MAKE) --no-print-directory sync_hf_push || rc=1; \
	$(MAKE) --no-print-directory hf_card || rc=1; \
	if [ "$(SETUP_WAYBACK)" = 1 ]; then $(MAKE) --no-print-directory link_wayback || rc=1; fi; \
	$(MAKE) --no-print-directory upload_archive SCOPE=all LIMIT=$(SETUP_ARCHIVE_LIMIT) || rc=1; \
	$(MAKE) --no-print-directory status || rc=1; \
	exit $$rc

update:
	@rc=0; \
	$(MAKE) --no-print-directory discover || rc=1; \
	$(MAKE) --no-print-directory download SCOPE=new || rc=1; \
	$(MAKE) --no-print-directory link_wayback SCOPE=new || rc=1; \
	$(MAKE) --no-print-directory upload_archive SCOPE=new || rc=1; \
	$(MAKE) --no-print-directory sync_hf_push || rc=1; \
	$(MAKE) --no-print-directory status IA_CHECK=0 || rc=1; \
	exit $$rc

backfill:
	@case "$(WHAT)" in \
	  archive) rc=0; \
	    $(MAKE) --no-print-directory upload_archive SCOPE=all || rc=1; \
	    $(MAKE) --no-print-directory status || rc=1; exit $$rc ;; \
	  wayback) rc=0; \
	    $(MAKE) --no-print-directory link_wayback SCOPE=all || rc=1; \
	    $(MAKE) --no-print-directory update_archive_metadata || rc=1; \
	    $(MAKE) --no-print-directory status || rc=1; exit $$rc ;; \
	  *) echo ">>> usage: make backfill WHAT=archive|wayback [C=council|aob|tob] [LIMIT=n]"; exit 1 ;; \
	esac
