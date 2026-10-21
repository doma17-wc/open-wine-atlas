"""Check one or more study path files without building web/data/study.json.

  python3 pipeline/study_check.py pipeline/study/path-bourgogne.json [...]

Checks what study_build.py checks (place ids exist, four distinct options, answer in range, unique ids, no long
dashes) plus the flashcards: every card has a front "f" and a back "b", fronts are unique inside a lesson, an
optional "place" exists in the atlas. Prints counts per lesson and every problem; exit code 1 on problems.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASH = re.compile("[—–]")
RANGE = re.compile(r"\d–\d")


def check(path, ids):
    errors = []
    p = json.load(open(path, encoding="utf-8"))
    print(f"{p['id']}: {p['title']}")
    for l in p["lessons"]:
        w = f"{p['id']}/{l['id']}"
        texts = [l["title"], l.get("intro", "")] + l.get("key", [])
        for s in l["sections"]:
            texts += [s["h"]] + s.get("p", [])
            errors += [f"{w}: unknown place {x}" for x in s.get("places", []) if x not in ids]
        qids = set()
        for q in l["questions"]:
            qw = f"{w}/{q.get('id')}"
            if q["id"] in qids:
                errors.append(f"{qw}: duplicate question id")
            qids.add(q["id"])
            if len(q["options"]) != 4 or len(set(q["options"])) != 4:
                errors.append(f"{qw}: needs four distinct options")
            if not (0 <= q["answer"] < len(q["options"])):
                errors.append(f"{qw}: answer out of range")
            if q.get("place") and q["place"] not in ids:
                errors.append(f"{qw}: unknown place {q['place']}")
            texts += [q["q"], q.get("explain", "")] + q["options"]
        fronts = set()
        for i, c in enumerate(l.get("cards", [])):
            cw = f"{w}/card {i + 1}"
            if not c.get("f") or not c.get("b"):
                errors.append(f"{cw}: needs f and b")
                continue
            if c["f"] in fronts:
                errors.append(f"{cw}: duplicate front {c['f'][:40]!r}")
            fronts.add(c["f"])
            if c.get("place") and c["place"] not in ids:
                errors.append(f"{cw}: unknown place {c['place']}")
            if len(c["b"]) > 220:
                errors.append(f"{cw}: back longer than 220 characters")
            texts += [c["f"], c["b"]]
        for t in texts:
            if DASH.search(RANGE.sub("", t)):
                errors.append(f"{w}: long dash in {t[:60]!r}")
        print(f"  {l['id']}: {len(l['questions'])} questions, {len(l.get('cards', []))} cards")
    return errors


def main(paths):
    ids = {r[1] for r in json.load(open(os.path.join(ROOT, "web", "data", "search.json"), encoding="utf-8"))}
    errors = []
    for f in paths:
        errors += check(f, ids)
    for e in errors:
        print("  !", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
