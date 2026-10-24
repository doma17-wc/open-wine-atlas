"""Merge regional research files into pipeline/lists/ch_regions.json.

Each file holds {"cantons": {...}, "places": [...], "gaps": [...]} in the format of ch_regions.json. Cantons that
the atlas has no record for yet are keyed "NEW:<name>" and become entries of "new_cantons", drawn from the BFS
canton boundary. Places of a canton are replaced as a whole (by id prefix), so a file can be merged again.

  python pipeline/ch_combine.py path/to/vs.json path/to/ti.json ...
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST = os.path.join(ROOT, "pipeline", "lists", "ch_regions.json")
# BFS canton numbers (swiss-maps cantons.shp ids) and the wine region group of the explorer
BFS = {"zürich": 1, "zurich": 1, "bern": 2, "berne": 2, "luzern": 3, "uri": 4, "schwyz": 5, "obwalden": 6, "nidwalden": 7,
       "glarus": 8, "zug": 9, "fribourg": 10, "freiburg": 10, "solothurn": 11, "basel-stadt": 12, "basel-landschaft": 13,
       "schaffhausen": 14, "appenzell ausserrhoden": 15, "appenzell innerrhoden": 16, "st. gallen": 17, "graubünden": 18,
       "aargau": 19, "thurgau": 20, "ticino": 21, "vaud": 22, "valais": 23, "neuchâtel": 24, "genève": 25, "jura": 26}
REGION = {2: "Trois-Lacs", 10: "Trois-Lacs", 26: "Trois-Lacs"}  # everything else new is German-speaking Switzerland

# free-text rule fields of the research files -> rows of d["rules"] [label, text]
RULE_KEYS = [("gc_rule", "Grand cru"), ("grand_cru_rule", "Grand cru"), ("traditional_names", "Traditional names"),
             ("nostrano_rule", "Nostrano"), ("americana_note", "Americana"), ("bianco_di_merlot_note", "Bianco di Merlot"),
             ("rules_note", "Production rules"), ("grapes_note", "Grapes"), ("growers_note", "Growers"), ("harvest_note", "Harvest")]


def tidy(s):
    """Swiss number style to the atlas style: 2'411'897 -> 2,411,897; a stray apostrophe after a year -> colon."""
    if not isinstance(s, str):
        return s
    s = re.sub(r"(?<=\d)'(?=\d{3}\b)", ",", s)
    s = re.sub(r"(?<=\d)'(?=\d{3}\b)", ",", s)
    s = re.sub(r"\b((?:19|20)\d\d)' ", r"\1: ", s)
    return s.replace(" — ", ", ").replace("—", ", ")


def normalize(d):
    d = {k: (tidy(v) if isinstance(v, str) else v) for k, v in d.items()}
    rules = list(d.get("rules", []))
    for k, label in RULE_KEYS:
        if d.get(k):
            rules.append([label, d.pop(k)])
    if isinstance(d.get("specialities"), list):
        rules += [[n, tidy(t)] for n, t in d.pop("specialities")]
    if d.get("grape_ha_note") and not d.get("grape_share_note"):
        d["grape_share_note"] = d.pop("grape_ha_note")
    d.pop("grape_ha_note", None)
    if rules:
        d["rules"] = rules
    return d


def main(paths):
    spec = json.load(open(LIST, encoding="utf-8"))
    spec.setdefault("new_cantons", {})
    gaps = spec.setdefault("_gaps", {})
    for path in paths:
        src = json.load(open(path, encoding="utf-8"))
        key = os.path.splitext(os.path.basename(path))[0]
        new_places = src.get("places", [])
        prefixes = {re.match(r"ch-reg-([a-z]+)-", p["id"]).group(1) for p in new_places}
        spec["places"] = [p for p in spec["places"] if re.match(r"ch-reg-([a-z]+)-", p["id"]).group(1) not in prefixes]
        for p in new_places:
            p["d"] = normalize(p.get("d", {}))
            spec["places"].append(p)
        for cid, c in src.get("cantons", {}).items():
            c = normalize(c)
            if cid.startswith("NEW:"):
                nm = cid[4:].strip()
                n = BFS[nm.lower().split(" / ")[0]]
                # the map name is the short legal one, "AOC <canton>"; Fribourg has no cantonal AOC and keeps its own
                off = c.get("official_name") or ""
                name = "AOC " + nm if "AOC" in off or "KUB" in off or not off else re.sub(r"\s*\(.*\)\s*$", "", off)
                spec["new_cantons"]["ch-canton-" + str(n)] = {"bfs": n, "name": name, "region": REGION.get(n, "Deutschschweiz"), "d": c}
            else:
                spec["cantons"][cid] = c
        if src.get("gaps"):
            gaps[key] = src["gaps"]
        print(f"  {key}: {len(new_places)} places, cantons {list(src.get('cantons', {}))}")
    # place names must be unique in Switzerland: children find their parent by name
    seen = {}
    for p in spec["places"]:
        assert p["name"] not in seen, f"two places named {p['name']}: {seen[p['name']]} and {p['id']}"
        seen[p["name"]] = p["id"]
    open(LIST, "w", encoding="utf-8").write(json.dumps(spec, ensure_ascii=False, indent=1) + "\n")
    print(f"  ch_regions.json: {len(spec['places'])} places, {len(spec['new_cantons'])} new cantons")


if __name__ == "__main__":
    main(sys.argv[1:])
