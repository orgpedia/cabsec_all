# The AoB's top-level units as cells, per amendment (requirements.md in this folder). Reads only the states' output
# JSON (../aob-states_/output/) and the 1961 Rules (../aob-rules_/output/); writes output/cells.json,
# output/cells-review.json and output/cells-review.html (and cells-2004*, from series 271 on). Its code is in cells/ here: it imports nothing from docflow.
# Run aob-states_ first.

run := uv run --no-sync

.PHONY: all cells cells-2004 timeline site page-images video test

all: cells cells-2004 timeline

cells:
	$(run) python -m cells src/cells.yml

# the same from the 2004 re-issue (series 271) on: output/cells-2004.json
cells-2004:
	$(run) python -m cells src/cells-2004.yml

# what the chart and the video read (ui-requirements U30): ui/timeline.json (from 1947); ui/timeline-2004.json is no longer read
timeline: cells cells-2004
	$(run) python -m cells.timeline src/cells.yml
	$(run) python -m cells.timeline src/cells-2004.yml

# the web page, copied to its GitHub Pages repository (orgpedia/site.cabsec-aob, next to cabsec_all); commit and push there
SITE ?= ../../../site.cabsec-aob
site:
	rsync -a --delete --exclude .DS_Store ui/people/ $(SITE)/people/
	rsync -a --exclude .DS_Store ui/assets/ $(SITE)/assets/
	cp ui/index.html ui/engine.js ui/l-en.svg ui/timeline.json $(SITE)/
	$(run) python -m cells.site src/cells.yml $(SITE)

# the amendments' page images (ui-requirements U49): WebP from the PDFs in ../aob-ammend_/input, made once (pages
# already made are kept); PAGES_LIMIT=500 makes at most that many in one run
page-images:
	$(run) python -m cells.pageimages src/cells.yml $(SITE)

# the 4:5 videos (ui-requirements U32), rendered from the site in headless Chrome (Playwright + ffmpeg): X at 2x
# (2:04, under X's 2:20), LinkedIn at 1.5x (2:44); an .srt of the captions beside each. Run make site first.
video:
	$(run) python -m cells.video --site $(SITE) --speed 2 --out output/video/ministries-1947-2026-x.mp4
	$(run) python -m cells.video --site $(SITE) --speed 1.5 --out output/video/ministries-1947-2026-linkedin.mp4

test:
	$(run) --with pytest pytest -q tests
