# Data schema

Every place on the map is a GeoJSON feature with the same small set of properties.
Facts that vary by country go into a separate details record, keyed by the same `id`.

## Feature properties

| Field | Type | Example | Notes |
|---|---|---|---|
| `id` | string | `fr-inao-d2911` | `<country>-<source>-<source id>`, lowercase, never reused |
| `name` | string | `Gevrey-Chambertin premier cru Clos Saint-Jacques` | Official name in the local language. Alternatives separated by " ou ", " / " are shortened to the first form; the full form stays in details |
| `country` | string | `FR` | ISO 3166-1 alpha-2 |
| `level` | enum | `vineyard` | `region`, `appellation`, `subzone`, `vineyard`, `vineyard_area` |
| `rank` | enum | `premier_cru` | `grand_cru`, `premier_cru`, `docg`, `doca`, `pago`, or empty |
| `parent` | string | `Gevrey-Chambertin` | Name of the place this one sits inside, or empty |
| `src` | string | `inao` | Key in `sources.json` |
| `ol` | enum | `approx` | Optional. Outline precision for places outside the EU and the US: `legal` (union of the units the law names, or an official outline), `approx` (units that contain the area; drawn dashed), `point` (marker at the namesake town, the geometry is a Point) |

### Levels

| Level | Meaning | Examples |
|---|---|---|
| `region` | Wine-growing region that groups appellations | Mosel, Rheingau (Anbaugebiete) |
| `appellation` | Protected designation of origin | Barolo, Rioja, Chablis, AOC Valais |
| `subzone` | Named part of an appellation that can appear on the label | Côtes de Bordeaux Blaye, Gevrey-Chambertin premier cru, Großlage Bernkasteler Kurfürstlay |
| `vineyard` | Named site | Clos Saint-Jacques, Les Bressandes, Wehlener Sonnenuhr, Cannubi |
| `vineyard_area` | Planted area without legal standing | OSM `landuse=vineyard` |

## Details record (`details-<cc>.json`)

Free-form, but use these keys when the source has them:

`type`, `official_name`, `registered`, `category`, `grapes` (slash separated), `max_yield_hl_ha`,
`max_yield_kg_ha`, `min_planting_density`, `area_ha`, `outline_area_ha`, `communes` (list),
`region`, `bereich`, `grosslage`, `register_no`, `eu_register` (URL), `source_date`, `note`.

Places built by `world.py` also use `basis` (legal basis), `outline` and `outline_quality` (how the outline was
drawn), `admin_units` (list), `outline_source` (`{name, licence, source}`), `register_ref` (legal act),
`also_registered` (smaller GIs inside that are not mapped yet), `state`, `lat`, `lon`.

## Geometry

WGS84 (EPSG:4326), Polygon or MultiPolygon (Point for `ol: point`), coordinates rounded to 6 decimals (about 0.1 m).
Simplify only to remove survey noise (1 m in a metric projection). Generalisation for small
zoom levels is done by the tile builder, never in the stored data.
