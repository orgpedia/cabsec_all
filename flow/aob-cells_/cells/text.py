"""Text helpers, copied from docflow (products/states.py, tasks/schedules.py, products/bridge.py) so that this
folder stands alone. tests/test_count.py checks the counts against the states' evolution.json, so a drift shows."""

import re
import unicodedata
from typing import Any, Optional

SMALL = {"ministry", "department", "of", "and", "the", "for", "&", "in", "on", "with", "a", "an"}
BRACKETED = re.compile(r"\s*\((?:[^()]|\([^()]*\))*\)$")
HW = r"(?:mant[a-z]{0,4}l?a?ya|vibhag|sachivalaya|karyalaya|aa?yog)\b"
HINDI_WORD = re.compile(r"(?i)" + HW)  # "Mantralya", "Mantralalya" too
_H = r"(?i:mant[a-z]{0,3}l?a?ya|vibhag|sachivalaya|karyalaya|aa?yog)"
MISREAD_CLOSE = re.compile(r"(\([^()]*" + _H + r")\s*[}\]](?=[\s.;,:]*$)")
LOST_CLOSE = re.compile(r"(\([^()]*" + _H + r")(?=[\s.;,:]*$)")
MISREAD_OPEN = re.compile(r"[{\[](?=[^(){}\[\]]*" + _H + r"\)[\s.;,:]*$)")
MARK = re.compile(r"(?<=[\w.)\]])\s+\d{1,3}(?=\s*[.;,:]|\s+(?:note|omitted|provided)\b)", re.I)


def key(s: Optional[str]) -> str:
  """Letters and digits only, lower case, a footnote's number printed full size off."""
  s = unicodedata.normalize("NFKC", s or "").lower().replace("&", " and ").strip()
  s = re.sub(r"(?<=[.)])\s*\d{1,3}$|(?<=omitted)\s*\.?\s*\d{1,3}$", "", s)
  return re.sub(r"[^a-z0-9]", "", s)


def closed(s: str) -> str:
  return LOST_CLOSE.sub(r"\1)", MISREAD_CLOSE.sub(r"\1)", MISREAD_OPEN.sub("(", s)))


def hkey(s: Optional[str]) -> str:
  """A heading for comparing: its English name, without a Hindi name in brackets."""
  s = re.sub(r"[\s\-–—_.;,:\"'”’]+$", "", closed(s or ""))
  s = re.sub(r"\s+\d{1,2}$", "", s)
  if (m := BRACKETED.search(s)) and HINDI_WORD.search(m.group(0)):
    s = s[:m.start()]
  s = re.sub(r"(?i)\b(\w+)(?:\s+\1\b)+", r"\1", s)
  return key(re.sub(r"\s+\d{1,2}$", "", re.sub(r"\s*\([^()]*\)$", "", s)))


def own(n: dict[str, Any]) -> str:
  return n.get("heading") or n.get("text") or ""


def full(n: dict[str, Any]) -> str:
  """A part's text with all inside it, each item with its number."""
  def label(c: dict[str, Any]) -> str:
    return f"({c['num']}) " if c.get("type") == "item" and c.get("num") else ""
  return " ".join([own(n)] + [label(c) + full(c) for c in n.get("children", [])])


def unmarked(s: str) -> str:
  return MARK.sub("", s)


def name(heading: Optional[str]) -> str:
  """A heading as a person reads it: the Hindi name in brackets off, a broken word joined, capitals as a title."""
  s = re.sub(r"(\w)- (\w)", r"\1\2", (heading or "").strip())
  s = re.sub(r"^[^\w(]+", "", s)  # a footnote's mark before it: "* Ministry of Tourism and Civil Aviation"
  if (m := BRACKETED.search(s)) and HINDI_WORD.search(m.group(0)):
    s = s[:m.start()]
  s = re.sub(r"[\s.,;:\"”'\-]+$", "", s)  # "Ministry of Industry and Supply :-"
  s = re.sub(r"\s+\d{1,3}$", "", s)  # a footnote's number
  s = re.sub(r"^[A-Z]\.\s+(?=Ministry|Department)", "", s)  # a misread label: "A. Ministry of Supply"
  if (m := BRACKETED.search(s)) and HINDI_WORD.search(m.group(0)):
    s = s[:m.start()]
  s = re.sub(r"\s*\([^()]*" + HW + r"[^()]*\)", "", s, flags=re.I)  # one in the middle too
  if s.isupper():
    small = {"of", "and", "the", "for", "in", "on", "with", "to"}
    s = " ".join(w.lower() if w.lower() in small and i else w.capitalize() for i, w in enumerate(s.split()))
  return s


def hindi_in(heading: Optional[str]) -> Optional[str]:
  """The Hindi name a heading carries in brackets ("… (Krishi Mantralaya)"), else None."""
  s = re.sub(r"(\w)- (\w)", r"\1\2", re.sub(r"[\s.;,:\"”']+$", "", closed(heading or "")))
  m = BRACKETED.search(s)
  if m and HINDI_WORD.search(m.group(0)):
    return re.sub(r"\s+", " ", m.group(0).strip()[1:-1]).strip()
  m = re.search(r"\(([^()]*" + HW + r"[^()]*)\)", s, flags=re.I)
  return re.sub(r"\s+", " ", m.group(1)).strip() if m else None


def plain(s: Optional[str]) -> str:
  """A name for telling a rename from a spelling: no brackets at all, letters only."""
  return key(re.sub(r"\([^()]*\)?", "", name(s)))


def words(name_: str) -> set[str]:
  return {w for w in re.findall(r"[a-z]+", name_.lower()) if w not in SMALL}


def similar(a: str, b: str) -> float:
  wa, wb = words(a), words(b)
  return len(wa & wb) / len(wa | wb) if wa and wb else 0.0
