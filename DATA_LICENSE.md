# Data licences

The code in this repository is released under the MIT licence (see LICENSE).

The map data is derived from the sources below. Each derived layer keeps the licence of its
source, and anyone who reuses it must give the attribution shown here.

| Layer | Licence | Attribution |
|---|---|---|
| France appellations and dénominations | Licence Ouverte 2.0 | Institut national de l'origine et de la qualité (INAO), Délimitation parcellaire des AOC viticoles, 2026-08-31 |
| Italy, Spain, Germany appellation outlines | CC BY 4.0 | Candiago et al. (2022), A geospatial inventory of regulatory information for wine protected designations of origin in Europe, Scientific Data |
| Germany Einzellagen and Großlagen | dl-de/by-2-0 | © Landwirtschaftskammer Rheinland-Pfalz |
| Switzerland cantonal outlines | Open use with attribution | Bundesamt für Statistik (BFS), GEOSTAT / swisstopo |
| Wineries, Swiss vineyard areas, rivers, lakes | ODbL 1.0 | © OpenStreetMap contributors |
| Country borders | Public domain | Natural Earth |
| United States AVAs | CC0 1.0 | UC Davis Library, AVA Digitizing Project |
| Australia GI outlines | CC BY 4.0 | Geographical Indications of Australia, © Wine Australia (outlines via adynak/WineRegions, published there as CC0) |
| Outlines built from administrative units (Chile, Argentina, South Africa, New Zealand, Brazil, Uruguay, Canada, Mexico, Georgia, Moldova, Ukraine, Armenia, Türkiye, Israel, Lebanon, Serbia, North Macedonia, Montenegro, Bosnia and Herzegovina, Japan, China, India, Tasmania) | Licence of each geoBoundaries layer, shown on every place: CC BY 3.0 IGO, CC BY 4.0, CC BY 2.5, ODbL, CC BY-SA 2.0 (Türkiye, share-alike), OGL-Canada 2.0, PDDL, CC0 or public domain | geoBoundaries gbOpen, Runfola et al. (2020), and the national sources it lists |
| Which units make up each place (`pipeline/world_specs.py`, `pipeline/world/`) and marker positions | CC BY 4.0 | Open Wine Atlas contributors, compiled from the wine laws and registers cited on each place |
| Editorial vintage chart (`web/data/vintages.json`) and editorial notes (`pipeline/notes/`) | CC BY 4.0 | Open Wine Atlas contributors |
| Climate (read live, not stored) | CC BY 4.0 | Open-Meteo, ERA5 / ERA5-Land (Copernicus Climate Change Service) |
| Soil (read live, not stored) | CC BY 4.0 | ISRIC SoilGrids 2.0 |
| Satellite base map (read live) | CC BY-NC-SA 4.0 | Sentinel-2 cloudless by EOX IT Services; IGN France, swisstopo, IGN España orthophotos |
| Topographic base map (read live) | CC BY-SA | OpenTopoMap, © OpenStreetMap contributors |
| Relief and terrain figures (computed in the browser, not stored) | Open licences of each elevation model | © Mapterhorn and its sources, see https://mapterhorn.com/attribution (IGN, German Länder survey offices, swisstopo, IGN España, Copernicus) |
| Community contributions in `contrib/` | CC BY 4.0 | Open Wine Atlas contributors |

Because the OpenStreetMap layers are under ODbL, a database that combines them with other
layers must keep them as separate, clearly attributed layers, as this project does.
