"""All EU wine PDOs outside the French INAO file (21 countries): EU wine PDO boundaries (Candiago et al. 2022, Scientific Data, CC BY 4.0).

Boundaries follow the municipalities listed in each product specification, so they are
appellation outlines, not vineyard plots. France uses the more precise INAO data instead.

Input : raw/eupdo/eu_pdo_wgs84.geojson, raw/eupdo/PDO_EU_id.csv
Output: build/eu_appellations.geojsonl, build/eu_details.json
"""
import json
import os

import pandas as pd
import pyogrio
import shapely

from common import BUILD, RAW, norm, round_geom, write_details, write_features

# every country in the inventory; FR only for PDOs missing from the INAO parcel file (e.g. Champagne)
COUNTRIES = {"IT", "ES", "DE", "FR", "AT", "PT", "GR", "HU", "RO", "BG", "HR", "SI", "CZ", "SK", "BE", "CY", "NL", "GB",
             "MT", "DK", "LU"}
TYPE = {"IT": "DOP (DOC/DOCG)", "ES": "DOP", "DE": "g.U. (PDO)", "FR": "AOP", "AT": "g.U. (DAC / Qualitätswein)",
        "PT": "DOP (DOC)", "GR": "ΠΟΠ (PDO)", "HU": "OEM (PDO)", "RO": "DOC (PDO)", "BG": "ЗНП (PDO)", "HR": "ZOI (PDO)",
        "SI": "ZGP (PDO)", "CZ": "CHOP (PDO)", "SK": "CHOP (PDO)", "BE": "BOB / AOP (PDO)", "CY": "ΠΟΠ (PDO)",
        "NL": "BOB (PDO)", "GB": "PDO", "MT": "DOK (PDO)", "DK": "BOB (PDO)", "LU": "AOP (PDO)"}
SRC = "eupdo"
HERE = os.path.dirname(os.path.abspath(__file__))


def load_list(name):
    path = os.path.join(HERE, "lists", name)
    return {norm(line.split("(")[0]) for line in open(path, encoding="utf-8")
            if line.strip() and not line.startswith("#")}


def main():
    gdf = pyogrio.read_dataframe(os.path.join(RAW, "eupdo", "eu_pdo_wgs84.geojson"), on_invalid="fix")
    meta = pd.read_csv(os.path.join(RAW, "eupdo", "PDO_EU_id.csv"), encoding_errors="replace")
    gdf = gdf.merge(meta, on="PDOid", how="left")
    gdf = gdf[gdf["Country"].isin(COUNTRIES)].copy()
    # France: keep only PDOs that the INAO parcel file does not cover
    inao_path = os.path.join(BUILD, "fr_details.json")
    if os.path.exists(inao_path):
        inao = json.load(open(inao_path, encoding="utf-8"))
        have = set()
        for v in inao.values():
            for n in str(v.get("official_name", "")).split(" ou "):
                have.add(norm(n))
        keep = [c != "FR" or not ({norm(x) for x in str(n).split(" / ")} & have) for c, n in zip(gdf["Country"], gdf["PDOnam"])]
        gdf = gdf[keep].copy()
        print("FR PDOs added from the EU inventory:", sorted(gdf.loc[gdf["Country"] == "FR", "PDOnam"]))
    else:
        gdf = gdf[gdf["Country"] != "FR"].copy()
    print("PDOs:", gdf["Country"].value_counts().to_dict())

    docg = load_list("it_docg.txt")
    pago = load_list("es_pago.txt")
    doca = {norm("Rioja"), norm("Priorat")}
    de_regions = load_list("de_anbaugebiete.txt")

    def first_name(n):
        # multilingual names are "A / B"; use the first for the map label
        return str(n).split(" / ")[0].strip()

    names, ranks, levels = [], [], []
    for r in gdf.itertuples():
        full = str(r.PDOnam)
        keys = {norm(p) for p in full.split(" / ")}
        name = first_name(full)
        rank = ""
        if r.Country == "IT" and keys & docg:
            rank = "docg"
        elif r.Country == "ES" and keys & doca:
            rank = "doca"
        elif r.Country == "ES" and (keys & pago or any(("pago " + k) in pago or k.replace("pago ", "") in pago for k in keys)):
            rank = "pago"
        level = "appellation"
        if r.Country == "DE":
            level = "region" if keys & de_regions else "vineyard"
        names.append(name); ranks.append(rank); levels.append(level)
    gdf["name"], gdf["rank"], gdf["level"] = names, ranks, levels
    gdf["id"] = [f"{c.lower()}-eupdo-{p}" for c, p in zip(gdf["Country"], gdf["PDOid"])]
    gdf["country"] = gdf["Country"]
    gdf["parent"] = ""
    gdf["src"] = SRC
    gdf["geometry"] = [None if g is None else round_geom(shapely.make_valid(g), 5) for g in gdf.geometry]
    missing = gdf[gdf.geometry.isna() | gdf.geometry.is_empty]
    if len(missing):
        print("no outline in the inventory:", sorted(missing["name"]))
    gdf = gdf[~(gdf.geometry.isna() | gdf.geometry.is_empty)].copy()

    # German single-vineyard PDOs sit inside an Anbaugebiet: find it spatially
    regions = gdf[(gdf["country"] == "DE") & (gdf["level"] == "region")]
    for i, r in gdf[(gdf["country"] == "DE") & (gdf["level"] == "vineyard")].iterrows():
        hit = regions[regions.intersects(r.geometry.representative_point())]
        if len(hit):
            gdf.at[i, "parent"] = hit.iloc[0]["name"]

    matched_docg = sorted(gdf.loc[gdf["rank"] == "docg", "name"])
    print(f"DOCG matched {len(matched_docg)}; pagos matched {sum(gdf['rank'] == 'pago')}; "
          f"DOCa {list(gdf.loc[gdf['rank'] == 'doca', 'name'])}")

    details = {}
    area = gdf.to_crs(3035).geometry.area / 10000
    for (i, r), a in zip(gdf.iterrows(), area):
        def val(c):
            v = r.get(c)
            return None if pd.isna(v) else v
        details[r["id"]] = {
            "type": TYPE.get(r["country"], "PDO"),
            "official_name": r["PDOnam"],
            "registered": val("Registration"),
            "category": val("Category_of_wine_product"),
            "grapes": val("Varieties_OIV"),
            "grapes_other": val("Varieties_Other"),
            "max_yield_hl_ha": val("Maximum_yield_hl"),
            "max_yield_kg_ha": val("Maximum_yield_kg"),
            "min_planting_density": val("Minimum_planting_density"),
            "irrigation": val("Irrigation"),
            "communes": [c.strip() for c in str(val("Municip_nam") or "").split("/") if c.strip()][:400],
            "eu_register": val("PDOinfo"),
            "outline_area_ha": round(float(a)),
        }
        details[r["id"]] = {k: v for k, v in details[r["id"]].items() if v not in (None, "", [])}

    cols = ["id", "name", "country", "level", "rank", "parent", "src"]
    write_features(os.path.join(BUILD, "eu_appellations.geojsonl"), gdf, cols)
    write_details(os.path.join(BUILD, "eu_details.json"), details)


if __name__ == "__main__":
    main()
