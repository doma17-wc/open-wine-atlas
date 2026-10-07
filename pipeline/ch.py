"""Switzerland: cantonal wine appellations.

Swiss AOCs are defined canton by canton, so the canton boundary is used as the appellation
outline until the official cantonal vineyard cadastres (Rebbaukataster) are added.
Canton boundaries: BFS GEOSTAT / swisstopo generalised boundaries 2024 (via the swiss-maps package).

Output: build/ch_appellations.geojsonl, build/ch_details.json
"""
import os

import pyogrio
import shapely

from common import BUILD, RAW, round_geom, write_details, write_features

# canton id -> (appellation name, Swiss wine region)
WINE_CANTONS = {
    23: ("AOC Valais", "Valais"),
    22: ("AOC Vaud", "Vaud"),
    25: ("AOC Genève", "Genève"),
    24: ("AOC Neuchâtel", "Trois-Lacs"),
    21: ("DOC Ticino", "Ticino"),
    1: ("AOC Zürich", "Deutschschweiz"),
    14: ("AOC Schaffhausen", "Deutschschweiz"),
    19: ("AOC Aargau", "Deutschschweiz"),
    18: ("AOC Graubünden", "Deutschschweiz"),
    20: ("AOC Thurgau", "Deutschschweiz"),
    17: ("AOC St. Gallen", "Deutschschweiz"),
    13: ("AOC Basel-Landschaft", "Deutschschweiz"),
    3: ("AOC Luzern", "Deutschschweiz"),
}


def main():
    path = os.path.join(RAW, "basemap", "swiss", "package", "2024", "cantons.shp")
    df = pyogrio.read_dataframe(path, encoding="utf-8")
    df = df[df["id"].astype(int).isin(WINE_CANTONS)].copy()
    df["geometry"] = shapely.make_valid(df.geometry.simplify(20, preserve_topology=True))
    df = df.set_crs(2056, allow_override=True).to_crs(4326)
    df["geometry"] = [round_geom(g, 5) for g in df.geometry]
    info = [WINE_CANTONS[int(i)] for i in df["id"]]
    df["name"] = [a for a, _ in info]
    df["parent"] = [r for _, r in info]
    df["id"] = ["ch-canton-" + str(int(i)) for i in df["id"]]
    df["country"], df["level"], df["rank"], df["src"] = "CH", "appellation", "", "bfs"
    details = {r.id: {"type": "Cantonal AOC", "wine_region": r.parent,
                      "note": "Outline follows the canton boundary. Vineyard plots will come from the cantonal Rebbaukataster."}
               for r in df.itertuples()}
    cols = ["id", "name", "country", "level", "rank", "parent", "src"]
    write_features(os.path.join(BUILD, "ch_appellations.geojsonl"), df, cols)
    write_details(os.path.join(BUILD, "ch_details.json"), details)


if __name__ == "__main__":
    main()
