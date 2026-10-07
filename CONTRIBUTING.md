# Contributing

Thank you for helping map the world's vineyards. There are three ways to help.

## 1. Report or suggest a fix

On the map, open a place and press **Suggest a correction**, or use **Suggest a place**.
Write what should change and name your source (a law, a disciplinare, a cahier des charges,
an official register, a producer's own documentation). Suggestions go into a review queue.

## 2. Add a single place by hand

Add a GeoJSON file to `contrib/<country>/` that follows [SCHEMA.md](SCHEMA.md). Rules:

* One feature per file, named after its `id`, for example `contrib/it/it-contrib-barolo-cannubi.geojson`.
* `src` is `contrib` and the feature has a `source` property with a link to the document that defines the boundary.
* Draw from an official map or a public-domain base, never trace a copyrighted atlas or book.
* Your contribution is published under CC BY 4.0.

## 3. Add a whole dataset

This is the most valuable contribution. Write `pipeline/<source>.py` that:

1. Reads the official file from `raw/<source>/` (document the download URL and licence in `sources.json`).
2. Converts each feature into the schema, with stable ids.
3. Writes `build/<source>.geojsonl` and `build/<source>_details.json` with the helpers in `common.py`.
4. Registers the new files in `build_tiles.py`.

Only use data whose licence allows redistribution and commercial reuse with attribution
(Licence Ouverte, CC BY, CC0, dl-de/by, ODbL, government open data). If you are unsure, open an issue first.

## Review

Every change is checked by a maintainer against its source before it is merged.
Classifications (DOCG, grand cru, Pago, MGA, Lage) must cite the legal text.
