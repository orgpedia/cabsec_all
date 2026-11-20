"""The counts equal the states' evolution.json at its epochs (the copy of docflow's counting has not drifted)."""

from pathlib import Path

import pytest

from cells import count, read

STATES = Path(__file__).resolve().parents[2] / "aob-states_/output"
RULES = Path(__file__).resolve().parents[2] / "aob-rules_/output"


@pytest.mark.skipif(not (STATES / "evolution.json").exists(), reason="the states' output is not here")
def test_epochs_match_evolution():
  for e in read.evolution(STATES)["epochs"]:
    got = [u["size"] for u in count.units(read.base(RULES / f"{e['file']}.json"))["units"]]
    assert got == [u["count"] for u in e["units"]], e["label"]


def test_subjects_skip_omitted_and_unnumbered():
  unit = {"type": "ministry", "heading": "MINISTRY OF X", "children": [
    {"type": "entry", "num": "1", "text": "Roads."},
    {"type": "entry", "num": "2", "text": "Omitted."},
    {"type": "department", "heading": "A. DEPT", "children": [{"type": "entry", "num": "3A", "text": "Bridges."}]},
    {"type": "entry", "text": "An unnumbered note."}]}
  assert [e["text"] for e in count.subjects(unit)] == ["Roads.", "Bridges."]


def test_names_and_hindi():
  tree = {"children": [
    {"type": "schedule", "num": "1", "children": [
      {"type": "ministry", "num": "1", "heading": "Ministry of Coal", "heading_hi": "Koyala Mantralaya"}]},
    {"type": "schedule", "num": "2", "children": [
      {"type": "ministry", "heading": "MINISTRY OF COAL (KOYALA MANTRALAYA)",
       "children": [{"type": "entry", "num": "1", "text": "Coal."}]},
      {"type": "ministry", "heading": "Omitted.", "children": []}]}]}
  us = count.units(tree)["units"]
  assert [(u["name"], u["hindi"], u["size"]) for u in us] == [("Ministry of Coal", "Koyala Mantralaya", 1)]
