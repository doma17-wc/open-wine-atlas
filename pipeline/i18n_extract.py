"""Collect every text of the interface that can be translated, into web/i18n/_keys.json.

The atlas is written in English. A text is translatable when it appears in web/index.src.html as
  t_("…") or N_("…")            in the script (every string literal of the first argument, so t_(a ? "x" : "y") counts)
  data-i18n                       on an HTML element (its text)
  data-i18n-title / -aria / -ph   on an HTML element (the attribute value)
plus the texts that come with the data and are shown as they are:
  tree.json      continent and group names (country names come from the browser)
  vintages.json  intro, note, scale and region names
  details-*.json type, outline, basis, atlas_note, irrigation, category, wine colour and category, bedrock

web/i18n/<lang>.json maps each English text to its translation. Run
  python pipeline/i18n_extract.py            # writes _keys.json and reports what each language is missing
  python pipeline/i18n_extract.py --prune    # also drops translations whose English text is gone
"""
import glob
import html as htmllib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
I18N = os.path.join(WEB, "i18n")


def js_unescape(s, q):
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            n = s[i + 1]
            out.append({"n": "\n", "t": "\t", "\\": "\\", '"': '"', "'": "'"}.get(n, n))
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def first_arg_literals(src, start):
    """String literals of the first argument of a call whose '(' is at src[start]."""
    depth, i, lits = 0, start, []
    while i < len(src):
        c = src[i]
        if c in "\"'`":
            q, j = c, i + 1
            while j < len(src) and src[j] != q:
                j += 2 if src[j] == "\\" else 1
            if depth == 1 and q != "`":
                lits.append(js_unescape(src[i + 1:j], q))
            i = j + 1
            continue
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
            if depth == 0:
                break
        elif c == "," and depth == 1:
            break
        i += 1
    return lits


def from_source(path):
    src = open(path, encoding="utf-8").read()
    keys = {}
    a = src.index("<script>\n(() => {")
    html, js = src[:a], src[a:]
    for m in re.finditer(r"\b(t_|N_)\(", js):
        if js[m.start() - 9:m.start()] == "function ":
            continue
        for lit in first_arg_literals(js, m.end() - 1):
            if re.search(r"[A-Za-z]", lit):
                keys.setdefault(lit, "interface")
    for m in re.finditer(r"<(\w+)([^<>]*)\bdata-i18n\b(?!-)[^<>]*>([^<]*)<", html):
        t = htmllib.unescape(m.group(3).strip())
        if t:
            keys.setdefault(t, "interface")
    for m in re.finditer(r'data-i18n-(?:title|aria|ph)="([^"]+)"', html):
        keys.setdefault(htmllib.unescape(m.group(1)), "interface")
    return keys


def from_data():
    keys = {}
    tree = json.load(open(os.path.join(WEB, "data", "tree.json"), encoding="utf-8"))
    for cont, _ in tree["roots"]:
        keys.setdefault(cont, "region names")
    for k, n in tree["nodes"].items():
        if k.startswith("g:") and n[0] and n[1] != "country":
            keys.setdefault(n[0], "region names")
    v = json.load(open(os.path.join(WEB, "data", "vintages.json"), encoding="utf-8"))
    for f in ("intro", "note", "scale"):
        if v.get(f):
            keys.setdefault(v[f], "vintage chart")
    for r in v.get("regions", []):
        keys.setdefault(r["name"], "vintage chart")
    for f in sorted(glob.glob(os.path.join(WEB, "data", "details-*.json"))):
        for d in json.load(open(f, encoding="utf-8")).values():
            for fld, ctx in (("type", "place types"), ("outline", "outline notes"), ("basis", "legal basis"), ("irrigation", "place types")):
                if d.get(fld) and d[fld] != "na":
                    keys.setdefault(d[fld], ctx)
            if d.get("atlas_note"):
                keys.setdefault(d["atlas_note"], "atlas notes")
            if d.get("category"):
                for x in re.split(r", |/", d["category"]):
                    if x.strip():
                        keys.setdefault(x.strip(), "wine categories")
            for b in d.get("bedrock") or []:
                keys.setdefault(b[0], "bedrock")
                keys.setdefault(re.sub(r" \(.*\)", "", b[0]), "bedrock")
            for w in d.get("wines") or []:
                for fld in ("colour", "category"):
                    if w.get(fld):
                        keys.setdefault(w[fld], "wine categories")
                if w.get("colour"):
                    keys.setdefault(w["colour"].lower(), "wine categories")
    return keys


def main():
    keys = from_source(os.path.join(WEB, "index.src.html"))
    for k, ctx in from_data().items():
        keys.setdefault(k, ctx)
    keys.pop("", None)
    os.makedirs(I18N, exist_ok=True)
    ordered = dict(sorted(keys.items(), key=lambda kv: (kv[1] != "interface", kv[1], kv[0].lower())))
    json.dump(ordered, open(os.path.join(I18N, "_keys.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    by = {}
    for k, ctx in ordered.items():
        by[ctx] = by.get(ctx, 0) + 1
    print(len(ordered), "texts:", ", ".join(f"{c} {n}" for c, n in by.items()))
    prune = "--prune" in sys.argv
    ph = re.compile(r"\{\w+\}")
    for f in sorted(glob.glob(os.path.join(I18N, "[a-z][a-z].json"))):
        tr = json.load(open(f, encoding="utf-8"))
        missing = [k for k in ordered if k not in tr]
        bad = [k for k, v in tr.items() if k in ordered and sorted(ph.findall(k)) != sorted(ph.findall(v))]
        stale = [k for k in tr if k not in ordered]
        if prune and stale:
            for k in stale:
                tr.pop(k)
            json.dump(tr, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
        print(os.path.basename(f), "missing", len(missing), "placeholder errors", len(bad), "stale", len(stale), "(pruned)" if prune and stale else "")
        for k in bad[:5]:
            print("   placeholder mismatch:", k[:70])


if __name__ == "__main__":
    main()
