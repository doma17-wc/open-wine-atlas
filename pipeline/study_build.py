"""Build web/data/study.json from the study paths in pipeline/study/*.json.

Each path file holds one path: lessons with sections, key facts, questions and flashcards (see pipeline/study/README.md).
This script checks every path (place ids exist in the atlas, four distinct options, answer in range, no long dashes;
every card has a front and a back, fronts are unique in a lesson, backs stay short) and adds the scope of each path:
the atlas regions its drills and map quizzes draw from. A path with an empty scope is theory only (no drills).

  python pipeline/study_build.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "pipeline", "study")
OUT = os.path.join(ROOT, "web", "data", "study.json")

ORDER = ["foundations", "bourgogne", "bordeaux", "north-france", "rhone-south", "italy", "iberia", "germany-austria", "usa", "southern",
         "vine-wine", "sparkling-sweet-fortified", "central-east"]
# tree keys (web/data/tree.json) the drills of each path use; foundations, vine-wine and sparkling-sweet-fortified have
# none (theory only)
SCOPE = {
    "bourgogne": ["g:FR/bourgogne"],
    "bordeaux": ["g:FR/bordeaux", "g:FR/sud-ouest"],
    "north-france": ["g:FR/champagne", "g:FR/alsace", "g:FR/vallee-de-la-loire"],
    "rhone-south": ["g:FR/vallee-du-rhone", "g:FR/provence", "g:FR/languedoc", "g:FR/roussillon"],
    "italy": ["g:IT"],
    "iberia": ["g:ES", "g:PT"],
    "germany-austria": ["g:DE", "g:AT"],
    "usa": ["g:US/CA", "g:US/OR", "g:US/WA", "g:US/NY"],
    "southern": ["g:AU", "g:NZ", "g:ZA", "g:CL", "g:AR"],
    "vine-wine": [],
    "sparkling-sweet-fortified": [],
    "central-east": ["g:CH", "g:HU", "g:GR", "g:SI", "g:HR", "g:GE", "g:AM", "g:MK"],
}
CARD_BACK_MAX = 220
DASH = re.compile("[—–]")  # long dash, and the en dash outside number ranges
RANGE = re.compile(r"\d–\d")


def main():
    ids = {r[1] for r in json.load(open(os.path.join(ROOT, "web", "data", "search.json"), encoding="utf-8"))}
    tree = json.load(open(os.path.join(ROOT, "web", "data", "tree.json"), encoding="utf-8"))["nodes"]
    errors, paths = [], []
    files = {os.path.splitext(f)[0].replace("path-", ""): f for f in os.listdir(SRC) if f.endswith(".json")}
    for pid in [p for p in ORDER if p in files] + sorted(set(files) - set(ORDER)):
        p = json.load(open(os.path.join(SRC, files[pid]), encoding="utf-8"))
        where = pid
        for k in SCOPE.get(pid, []):
            if k not in tree:
                errors.append(f"{where}: scope {k} is not in the tree")
        # keys missing from the tree are left out: the drills draw from the regions that are there
        p["scope"] = [k for k in SCOPE.get(pid, []) if k in tree]
        seen_l = set()
        for l in p["lessons"]:
            w = f"{where}/{l.get('id')}"
            if l["id"] in seen_l:
                errors.append(f"{w}: duplicate lesson id")
            seen_l.add(l["id"])
            texts = [l["title"], l.get("intro", "")] + l.get("key", [])
            for s in l["sections"]:
                texts += [s["h"]] + s.get("p", [])
                bad = [x for x in s.get("places", []) if x not in ids]
                if bad:
                    errors.append(f"{w}: unknown places {bad}")
                    s["places"] = [x for x in s["places"] if x in ids]
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
                    q.pop("place")
                texts += [q["q"], q.get("explain", "")] + q["options"]
            fronts, cards = set(), []
            for i, c in enumerate(l.get("cards", [])):
                cw = f"{w}/card {i + 1}"
                if not isinstance(c, dict) or not c.get("f") or not c.get("b"):
                    errors.append(f"{cw}: needs f and b")
                    continue
                if c["f"] in fronts:
                    errors.append(f"{cw}: duplicate front {c['f'][:40]!r}")
                    continue
                fronts.add(c["f"])
                if c.get("place") and c["place"] not in ids:
                    errors.append(f"{cw}: unknown place {c['place']}")
                    c.pop("place")
                if len(c["b"]) > CARD_BACK_MAX:
                    errors.append(f"{cw}: back longer than {CARD_BACK_MAX} characters")
                texts += [c["f"], c["b"]]
                cards.append({k: c[k] for k in ("f", "b", "place") if c.get(k)})
            if "cards" in l:
                l["cards"] = cards
            for t in texts:
                if DASH.search(RANGE.sub("", t)):
                    errors.append(f"{w}: long dash in {t[:60]!r}")
        paths.append(p)
    out = {"version": 1, "paths": paths}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    nl = sum(len(p["lessons"]) for p in paths)
    nq = sum(len(l["questions"]) for p in paths for l in p["lessons"])
    nc = sum(len(l.get("cards", [])) for p in paths for l in p["lessons"])
    print(f"study.json: {len(paths)} paths, {nl} lessons, {nq} questions, {nc} flashcards, {os.path.getsize(OUT) // 1024} KB")
    for p in paths:
        print(f"  {p['id']}: {len(p['lessons'])} lessons, {sum(len(l['questions']) for l in p['lessons'])} questions, "
              f"{sum(len(l.get('cards', [])) for l in p['lessons'])} cards" + ("" if p["scope"] else ", theory only"))
    for e in errors:
        print("  !", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
