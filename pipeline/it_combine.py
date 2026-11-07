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
    load = lambda n: json.load(open(os.path.join(d, n), encoding="utf-8"))
    pa, pc, tt = load("piemonte_appellations.json"), load("piemonte_crus.json"), load("toscana.json")
    out = {
        "_note": ("Piemonte and Toscana in depth (pipeline/it_deep.py), merged by pipeline/it_combine.py from three research files. "
                  "Figures carry their source on each record; open questions are listed in doubts."),
        "sources": pa.get("sources", []) + pc.get("sources", []) + tt.get("sources", []),
        "doubts": ["Piemonte appellations: " + x for x in pa.get("doubts", [])] + ["Langhe and Roero crus: " + x for x in pc.get("doubts", [])]
                  + ["Toscana: " + x for x in tt.get("doubts", [])],
        "commune_alias": COMMUNE_ALIAS,
        "regions": {
            "piemonte": {"region": pa.get("region", {}), "groups": [{"name": n, "members": m} for n, m in GROUPS["piemonte"]],
                         "appellations": pa["appellations"], "communes": pc.get("communes", {}), "subzones": {}},
            "toscana": {"region": tt.get("region", {}), "groups": [{"name": n, "members": m} for n, m in GROUPS["toscana"]],
                        "appellations": tt["appellations"], "subzones": tt.get("subzones", {})},
        },
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
