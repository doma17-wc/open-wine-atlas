"""Build web/data/study.json from the study paths in pipeline/study/*.json.

Each path file holds one path: lessons with sections, key facts and questions (see pipeline/study/README.md).
This script checks every path (place ids exist in the atlas, four distinct options, answer in range, no long dashes)
and adds the scope of each path: the atlas regions its drills and map quizzes draw from.

  python pipeline/study_build.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "pipeline", "study")
OUT = os.path.join(ROOT, "web", "data", "study.json")

ORDER = ["foundations", "bourgogne", "bordeaux", "north-france", "rhone-south", "italy", "iberia", "germany-austria", "usa", "southern"]
# tree keys (web/data/tree.json) the drills of each path use; foundations has none (theory only)
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
}
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
        p["scope"] = SCOPE.get(pid, [])
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
            for t in texts:
                if DASH.search(RANGE.sub("", t)):
                    errors.append(f"{w}: long dash in {t[:60]!r}")
        paths.append(p)
    out = {"version": 1, "paths": paths}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    nl = sum(len(p["lessons"]) for p in paths)
    nq = sum(len(l["questions"]) for p in paths for l in p["lessons"])
    print(f"study.json: {len(paths)} paths, {nl} lessons, {nq} questions, {os.path.getsize(OUT) // 1024} KB")
    for e in errors:
        print("  !", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
