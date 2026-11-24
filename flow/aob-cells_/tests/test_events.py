"""One small case for each kind of event."""

from cells import events as ev, match
from cells.text import hkey


def U(name, texts):
  return {"name": name, "heading": name, "hkey": hkey(name), "hindi": None, "size": len(texts), "texts": texts}


def run(a, b):
  peer = {j: i for j, u in enumerate(b) for i, p in enumerate(a) if p["hkey"] == u["hkey"]}
  ids = ev.Ids()
  a_ids = [ids.new() for _ in a]
  b_ids, evs = ev.step(a, a_ids, b, match.flows(a, b, peer), ids, 3, 0.2)
  return a_ids, b_ids, {(e["kind"], tuple(e["from"]), tuple(e["to"])) for e in evs}


S = [f"Subject number {w} of the list." for w in "alpha beta gamma delta epsilon zeta eta theta iota kappa".split()]
T = [f"Topic about {w} matters." for w in "red blue green yellow orange purple".split()]


def test_split():
  _, _, got = run([U("Ministry of Steel, Mines and Fuel", S)],
                  [U("Ministry of Steel", S[:5]), U("Ministry of Fuel", S[5:])])
  assert ("split", (0,), (0, 1)) in got


def test_merged():
  _, _, got = run([U("Ministry of A", S[:5]), U("Ministry of B", S[5:])], [U("Ministry of C", S)])
  assert ("merged", (0, 1), (0,)) in got


def test_absorbed_keeps_the_id():
  a_ids, b_ids, got = run([U("Ministry of Works", T), U("Ministry of Rehabilitation", S)],
                          [U("Ministry of Works", T + S)])
  assert ("absorbed", (1,), (0,)) in got and b_ids[0] == a_ids[0]


def test_spun_off():
  _, _, got = run([U("Ministry of Agriculture", S + T)], [U("Ministry of Agriculture", S), U("Ministry of Cooperation", T)])
  assert ("spun_off", (0,), (1,)) in got


def test_renamed_keeps_the_id():
  a_ids, b_ids, got = run([U("Ministry of Irrigation and Power", S)], [U("Ministry of Energy", S)])
  assert ("renamed", (0,), (0,)) in got and b_ids == a_ids


def test_spelling_is_not_a_rename():
  _, _, got = run([U("Ministry of Environment. and Forest", S)], [U("Ministry of Environment and Forests", S)])
  assert not any(k == "renamed" for k, _, _ in got)


def test_born_ended_grew_shrank_moved():
  _, _, got = run([U("Ministry of A", S), U("Ministry of B", T), U("Ministry of Gone", ["Old thing one.", "x y z."])],
                  [U("Ministry of A", S[:6]), U("Ministry of B", T + S[6:]),
                   U("Ministry of New", ["Fresh work one.", "Fresh work two.", "Fresh work three."])])
  assert ("moved", (0,), (1,)) in got
  assert ("born", (), (2,)) in got and ("ended", (2,), ()) in got
  _, _, got = run([U("Ministry of A", S[:5])], [U("Ministry of A", S)])
  assert ("grew", (0,), (0,)) in got
  _, _, got = run([U("Ministry of A", S)], [U("Ministry of A", S[:5])])
  assert ("shrank", (0,), (0,)) in got


def test_touched_by_path_and_number():
  firsts = [[{"num": "14", "heading": "Ministry of Steel, Mines and Fuel"}]]
  ch = [{"before": [{"path": "schedule 1 › ministry 14"}], "after": []},
        {"before": [{"path": "schedule 2"}], "after": [{"path": "schedule 2 › ministry MINISTRY OF LAW. › department B"}]}]
  assert ev.touched(ch, firsts) == {hkey("Ministry of Steel, Mines and Fuel"), hkey("MINISTRY OF LAW")}


def test_renamed_and_moved_is_not_a_split():
  # a unit renamed while a part of its work goes to a unit that stays (2021, Heavy Industries and Public Enterprises)
  a_ids, b_ids, got = run([U("Ministry of Heavy Industries and Public Enterprises", S), U("Ministry of Finance", T)],
                          [U("Ministry of Heavy Industries", S[:6]), U("Ministry of Finance", T + S[6:])])
  assert not any(k == "split" for k, _, _ in got)
  assert ("renamed", (0,), (0,)) in got and ("moved", (0,), (1,)) in got
  assert b_ids == a_ids


def test_a_unit_ending_into_a_new_unit_is_absorbed():
  # 1979: Education and Social Welfare splits into Education and Culture and Social Welfare; the Department of
  # Culture's subjects go to Education and Culture, which the split makes
  edu = [f"Education subject {w}." for w in "a b c d e f g h".split()]
  sw = [f"Welfare subject {w}." for w in "a b c d".split()]
  cul = [f"Culture subject {w}." for w in "a b c d e".split()]
  _, _, got = run([U("Ministry of Education and Social Welfare", edu + sw), U("Department of Culture", cul)],
                  [U("Ministry of Education and Culture", edu + cul), U("Ministry of Social Welfare", sw)])
  assert any(k == "split" for k, _, _ in got)
  assert ("absorbed", (1,), (0,)) in got


def test_a_small_part_of_a_split_is_one_of_its_parts():
  # 1971: a unit splits, and a third, smaller unit gets a share of its subjects too small for the split to count
  big = [f"Subject {w} of the old ministry." for w in "a b c d e f g h i j k l m n o p q r s t".split()]
  _, b_ids, got = run([U("Ministry of Education and Youth Services", big)],
                      [U("Ministry of Education and Social Welfare", big[:9]), U("Department of Culture", big[9:17]),
                       U("Department of Science and Technology", big[17:])])
  split = [x for x in got if x[0] == "split"]
  assert split and set(split[0][2]) == {0, 1, 2}
