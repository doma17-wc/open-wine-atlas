"""Merge the research files for Piemonte and Toscana into pipeline/lists/it_deep.json (read by it_deep.py).

  python pipeline/it_combine.py <research dir>

Inputs, one per research brief: piemonte_appellations.json (region and appellations), piemonte_crus.json (communes of
Barolo, Barbaresco and Roero with their MGA, multi-commune MGA), toscana.json (region, appellations, sub-zones).
The groups of each region are set here; an appellation in no group stops the build in it_deep.py.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "pipeline", "lists", "it_deep.json")

GROUPS = {
    "piemonte": [
        ("Regional appellations", ["Piemonte", "Langhe", "Monferrato"]),
        ("Langhe and Roero", ["Barolo", "Barbaresco", "Roero", "Dogliani", "Dolcetto di Diano d'Alba / Diano d'Alba", "Alta Langa", "Alba",
                              "Barbera d'Alba", "Dolcetto d'Alba", "Nebbiolo d'Alba", "Verduno Pelaverga / Verduno"]),
        ("Asti and Monferrato", ["Asti", "Barbera d'Asti", "Nizza", "Barbera del Monferrato Superiore", "Barbera del Monferrato",
                                 "Brachetto d'Acqui / Acqui", "Dolcetto di Ovada Superiore / Ovada", "Dolcetto di Ovada", "Gavi / Cortese di Gavi",
                                 "Ruchè di Castagnole Monferrato", "Terre Alfieri", "Albugnano", "Calosso", "Cisterna d'Asti", "Colli Tortonesi",
                                 "Cortese dell'Alto Monferrato", "Dolcetto d'Acqui", "Dolcetto d'Asti", "Freisa d'Asti", "Gabiano",
                                 "Grignolino d'Asti", "Grignolino del Monferrato Casalese", "Loazzolo",
                                 "Malvasia di Casorzo d'Asti / Malvasia di Casorzo / Casorzo", "Malvasia di Castelnuovo Don Bosco",
                                 "Rubino di Cantavenna", "Strevi"]),
        ("Alto Piemonte", ["Gattinara", "Ghemme", "Boca", "Bramaterra", "Colline Novaresi", "Coste della Sesia", "Fara", "Lessona", "Sizzano",
                           "Valli Ossolane"]),
        ("Turin, Canavese and Pinerolese", ["Erbaluce di Caluso / Caluso", "Canavese", "Carema", "Collina Torinese", "Freisa di Chieri",
                                            "Pinerolese", "Valsusa", "Colline Saluzzesi"]),
    ],
    "toscana": [
        ("Regional appellations", ["Colli dell'Etruria Centrale", "Vin Santo del Chianti"]),
        ("Chianti and central Tuscany", ["Chianti", "Chianti Classico", "Vernaccia di San Gimignano", "Vin Santo del Chianti Classico", "Pomino",
                                         "Bianco dell'Empolese", "Val d'Arno di Sopra / Valdarno di Sopra", "San Gimignano", "Terre di Casole",
                                         "Val d'Arbia", "Terre di Pisa"]),
        ("Montalcino, Montepulciano and southern Tuscany", ["Brunello di Montalcino", "Vino Nobile di Montepulciano", "Rosso di Montalcino",
                                                            "Moscadello di Montalcino", "Sant'Antimo", "Rosso di Montepulciano",
                                                            "Vin Santo di Montepulciano", "Orcia", "Cortona", "Valdichiana toscana", "Grance Senesi"]),
        ("Maremma and the coast", ["Bolgheri", "Bolgheri Sassicaia", "Morellino di Scansano", "Montecucco Sangiovese", "Montecucco",
                                   "Maremma toscana", "Suvereto", "Val di Cornia Rosso / Rosso della Val di Cornia", "Val di Cornia",
                                   "Elba Aleatico Passito / Aleatico Passito dell'Elba", "Elba", "Montescudaio", "Terratico di Bibbona",
                                   "Monteregio di Massa Marittima", "Ansonica Costa dell'Argentario", "Capalbio", "Parrina", "Sovana",
                                   "Bianco di Pitigliano"]),
        ("Northern Tuscany", ["Carmignano", "Barco Reale di Carmignano", "Vin Santo di Carmignano", "Montecarlo", "Colline Lucchesi", "Valdinievole",
                              "Candia dei Colli Apuani", "San Torpè"]),
    ],
}
# merged communes: the name in a specification -> the ISTAT name today
COMMUNE_ALIAS = {
    "Calliano": "Calliano Monferrato", "Casorzo": "Casorzo Monferrato", "Grana": "Grana Monferrato", "Montemagno": "Montemagno Monferrato",
    "Moransengo": "Moransengo-Tonengo", "Tonengo": "Moransengo-Tonengo", "Murisengo": "Murisengo Monferrato", "Pont-Canavese": "Pont Canavese",
    "Barberino Val d'Elsa": "Barberino Tavarnelle", "Tavarnelle Val di Pesa": "Barberino Tavarnelle",
}


def main():
    d = sys.argv[1]
    def load(n):  # the checked second round when it exists
        v2 = os.path.join(d, n.replace(".json", "_v2.json"))
        return json.load(open(v2 if os.path.exists(v2) else os.path.join(d, n), encoding="utf-8"))
    pa, pc, tt = load("piemonte_appellations.json"), load("piemonte_crus.json"), load("toscana.json")
    cx_path = os.path.join(d, "regions_context.json")
    cx = json.load(open(cx_path, encoding="utf-8")) if os.path.exists(cx_path) else {}
    regional = {reg: set(dict(GROUPS[reg])["Regional appellations"]) for reg in GROUPS}

    def app_rec(reg, name, v):
        v = dict(v)
        v["deep_level"] = "regional" if name in regional[reg] else ("docg" if v.get("rank") == "docg" else "doc")
        if v.get("vine_area_year") and str(v["vine_area_year"]) not in v.get("vine_area_src", ""):
            v["vine_area_src"] = v.get("vine_area_src", "") + f" ({v['vine_area_year']})"
        if v.get("vine_area_kind") == "secondary" and "secondary" not in v.get("vine_area_src", "").lower():
            v["vine_area_src"] = v.get("vine_area_src", "") + " (secondary source)"
        if v.get("production"):
            v["rules"] = list(v.get("rules", [])) + [["Production", str(v["production"]) + (" (" + v["production_src"] + ")" if v.get("production_src") else "")]]
        return v

    # Piemonte: one record per commune; the MGA of each appellation listed on its sheet, notes for the best known
    p_apps = {k: app_rec("piemonte", k, v) for k, v in pa["appellations"].items()}
    communes = {}
    mga_of = {}  # appellation -> [[MGA, commune]]
    for cname, cv in pc["communes"].items():
        of = cv["of"]
        rec = {"of": of, "partial": of if cv.get("partial") else [], "mga": cv.get("mga", {}),
               "vine_area_ha": cv.get("vine_area_ha", {}), "vine_area_src": cv.get("vine_area_src", ""),
               "atlas_note": cv.get("atlas_note"), "refs": cv.get("refs")}
        rules = {}
        for a, lab in (cv.get("menzione_comunale") or {}).items():
            rules.setdefault(a, []).append(["Commune name on the label", lab])
        for a, n in (cv.get("mga_count") or {}).items():
            rules.setdefault(a, []).append(["MGA in this commune", str(n)])
        rec["rules"] = rules
        communes[cname] = rec
        for a, ms in cv.get("mga", {}).items():
            for m in ms:
                mga_of.setdefault(a, []).append([m, cname])
    notes = {}  # appellation -> [[MGA, note]]
    for key, sv in pc.get("subzones", {}).items():
        if sv.get("type") == "MGA" and sv.get("atlas_note"):
            notes.setdefault(sv["of"], []).append([key.split(" / ", 1)[-1], sv["atlas_note"]])
    mga = pc.get("mga", {})

    def mga_extra(a, m, with_communes, commune=None):
        r = mga.get(a + " / " + m) or (mga.get(f"{a} / {m} ({commune})") if commune else None) or {}
        bits = [", ".join(r.get("communes") or [])] if with_communes and r.get("communes") else []
        if r.get("vine_area_ha"):
            bits.append(f"{r['vine_area_ha']:g} ha")
        elif r.get("area_ha"):  # press figures, not a registered area
            bits.append(f"about {r['area_ha']:g} ha")
        if r.get("altitude_m"):
            bits.append(f"{r['altitude_m'][0]} to {r['altitude_m'][1]} m")
        if r.get("aspect"):
            bits.append(str(r["aspect"]))
        return bits
    for key, r in mga.items():
        physical = any(r.get(f) for f in ("altitude_m", "aspect", "soil", "area_ha"))
        if r.get("atlas_note") and physical and not any(n[0] == key.split(" / ", 1)[-1] for n in notes.get(r["of"], [])):
            notes.setdefault(r["of"], []).append([key.split(" / ", 1)[-1], r["atlas_note"]])
    for cname, rec in communes.items():
        rec["mga_items"] = {a: [[m, " · ".join(mga_extra(a, m, False, cname))] for m in ms] for a, ms in rec["mga"].items()}
    for a, items in list(mga_of.items()):
        merged = {}
        for m, c in items:  # an MGA across two communes is one name
            merged.setdefault(m, []).append(c)
        items = mga_of[a] = sorted([[m, " · ".join([", ".join(cs)] + mga_extra(a, m, False))] for m, cs in merged.items()],
                                   key=lambda x: x[0].lower())
        p_apps[a]["named_sites"] = {"kind": "MGA", "items": items, "notes": sorted(notes.get(a, []))}
    for cname, rec in communes.items():
        for a in rec["of"]:
            if notes.get(a):
                rec.setdefault("mga_notes", {})[a] = [n for n in notes[a] if n[0] in rec["mga"].get(a, [])]

    # Toscana: sub-zones drawn on whole communes, else a marker on their village; Pievi without a location listed only
    t_apps = {k: app_rec("toscana", k, v) for k, v in tt["appellations"].items()}
    subs, pievi = {}, []
    for name, sv in tt.get("subzones", {}).items():
        sv = dict(sv)
        sv["display"] = name
        if sv["type"] == "Pieve":
            pievi.append([name, sv.get("village") if sv.get("village") and sv.get("village") != name else ""])
        if sv["type"] == "UGA" and sv.get("vine_area_ha"):
            sv["vine_area_note"] = ("The eleven UGA figures add up to about 9,800 ha, more than the area registered for Chianti Classico: "
                                    "read them as the vineyard area of each UGA, not as Chianti Classico hectares.")
        if sv["type"] == "Sottozona" or (sv["type"] == "UGA" and sv.get("whole_communes")):
            sv["draw"] = "communes"
        elif sv.get("lat") is None:
            continue
        subs[name] = sv
    if pievi:
        t_apps["Vino Nobile di Montepulciano"]["named_sites"] = {"kind": "Pieve", "items": sorted(pievi)}

    # regional context: the region, its areas on their group or key appellation
    AREA_TO = {
        "Langhe": "g:IT/piemonte/langhe-and-roero", "Roero": "g:IT/piemonte/langhe-and-roero",
        "Monferrato (Astigiano and Casalese)": "g:IT/piemonte/asti-and-monferrato", "Gavi and Colli Tortonesi": "g:IT/piemonte/asti-and-monferrato",
        "Alto Piemonte (Novara and Vercelli hills)": "g:IT/piemonte/alto-piemonte", "Canavese and Carema": "g:IT/piemonte/turin-canavese-and-pinerolese",
        "Chianti Classico": "Chianti Classico", "Chianti (outer zones)": "Chianti", "Montalcino": "Brunello di Montalcino",
        "Montepulciano": "Vino Nobile di Montepulciano", "San Gimignano": "Vernaccia di San Gimignano",
        "Bolgheri and the Etruscan coast": "Bolgheri", "Maremma (Scansano, Montecucco)": "g:IT/toscana/maremma-and-the-coast",
        "Carmignano": "Carmignano", "Rufina": "it-deep-chianti-rufina",
    }
    context = {}
    sec = lambda x: " (secondary source)" if (x or {}).get("src_kind") == "secondary" else ""

    def norm_ctx(c):
        """The research record as the sheet shows it: plain text, [label, text] pairs and strings."""
        o = {}
        if c.get("atlas_note"):
            o["atlas_note"] = c["atlas_note"]
        g = c.get("geology") or {}
        if isinstance(g, dict):
            o["geology"] = ([g["summary"]] if g.get("summary") else []) + [
                [f["name"] + (" (" + f["age"] + ")" if f.get("age") else ""), (f.get("note") or "") + sec(f)] for f in g.get("formations") or []]
        cl = c.get("climate") or {}
        if isinstance(cl, dict):
            items = [["Type", cl["type"]]] if cl.get("type") else []
            for st in cl.get("stations") or []:
                v = ", ".join(x for x in [f"{st['mean_temp_c']} °C mean" if st.get("mean_temp_c") is not None else "",
                                         f"{st['rain_mm']:,} mm rain a year" if st.get("rain_mm") else ""] if x)
                lab = st.get("station", "") + (" · " + st["period"] if st.get("period") and st["period"] != "not stated" else "")
                items.append([lab, (v + ". " if v else "") + (st.get("note") or "") + sec(st)])
            for f in cl.get("influences") or []:
                items.append([f.get("factor", ""), (f.get("note") or "") + sec(f)])
            o["climate"] = items
        al = c.get("altitude_m")
        if isinstance(al, dict) and al.get("min") is not None and al.get("max") is not None:
            o["altitude_m"] = [al["min"], al["max"]]
            if al.get("text"):
                o["altitude_text"] = al["text"]
        o["history"] = [[str(h.get("year", "")), h.get("fact", "") + sec(h)] for h in c.get("history") or []]
        o["grapes"] = [[x.get("grape", ""), x.get("fact", "") + sec(x)] for x in c.get("grapes") or []]
        o["study_points"] = [x.get("point", "") + sec(x) if isinstance(x, dict) else x for x in c.get("study_points") or []]
        o["refs"] = c.get("refs") or []
        return o

    def put(target, title, c):
        c = {k: v for k, v in c.items() if v}
        if c:
            context.setdefault(target, []).append({"title": title, **c})
    for reg, R in (cx.get("regions") or {}).items():
        base = {"piemonte": pa, "toscana": tt}[reg].get("region", {})
        r = norm_ctx(R)
        facts = []
        if base.get("vine_area_ha"):
            facts.append(["Vineyard area", f"{base['vine_area_ha']:,} ha. " + base.get("vine_area_src", "")])
        if base.get("grape_share"):
            facts.append(["Main grapes", ", ".join(f"{g} {p}%" for g, p in base["grape_share"][:8]) + ". " + base.get("grape_share_note", "")])
        r["grapes"] = facts + r.get("grapes", [])
        put("g:IT/" + reg, {"piemonte": "Piemonte", "toscana": "Toscana"}[reg], r)
    for area, A in (cx.get("areas") or {}).items():
        t = AREA_TO.get(area)
        if not t:
            print("  context area not placed:", area)
            continue
        put(t, area, norm_ctx(A))

    out = {
        "_note": ("Piemonte and Toscana in depth (pipeline/it_deep.py), merged by pipeline/it_combine.py from three research files. "
                  "Figures carry their source on each record; open questions are listed in doubts."),
        "sources": pa.get("sources", []) + pc.get("sources", []) + tt.get("sources", []),
        "doubts": ["Piemonte appellations: " + x for x in pa.get("doubts", [])] + ["Langhe and Roero crus: " + x for x in pc.get("doubts", [])]
                  + ["Toscana: " + x for x in tt.get("doubts", [])],
        "changes": [x for f in (pa, pc, tt) for x in f.get("changes", [])],
        "commune_alias": COMMUNE_ALIAS,
        "context": context,
        "regions": {
            "piemonte": {"region": pa.get("region", {}), "groups": [{"name": n, "members": m} for n, m in GROUPS["piemonte"]],
                         "appellations": p_apps, "communes": communes, "subzones": {}},
            "toscana": {"region": tt.get("region", {}), "groups": [{"name": n, "members": m} for n, m in GROUPS["toscana"]],
                        "appellations": t_apps, "subzones": subs},
        },
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
