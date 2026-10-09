"""Download the open source files used by world.py and osm.py into raw/.

Everything comes from GitHub-hosted mirrors so the build works from restricted networks:
  geoBoundaries gbOpen (Runfola et al. 2020), simplified admin boundaries, per-file licence in the meta CSV
  adynak/WineRegions, Australian GI outlines (stopgap until the Wine Australia layer is committed, see README)
  openhistorymap/openwinemap, OpenStreetMap wine POIs per country (ODbL)

Run: python pipeline/fetch_world.py
"""
import os
import sys
import urllib.request

from common import RAW

GB = "https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/main/releaseData/gbOpen/{iso}/{adm}/geoBoundaries-{iso}-{adm}_simplified.geojson"
GB_META = "https://raw.githubusercontent.com/wmgeolab/geoBoundaries/main/releaseData/geoBoundariesOpen-meta.csv"
ADYNAK = "https://raw.githubusercontent.com/adynak/WineRegions/master/Australia/{path}"
OWM = "https://raw.githubusercontent.com/openhistorymap/openwinemap/main/data/countries/{cc}.geojson"

# admin layers used by pipeline/world_specs.py
GB_FILES = [
    ("AUS", "ADM1"), ("NZL", "ADM2"), ("ZAF", "ADM1"), ("ZAF", "ADM3"), ("CHL", "ADM3"), ("ARG", "ADM2"),
    ("BRA", "ADM2"), ("URY", "ADM1"), ("CAN", "ADM2"), ("CAN", "ADM3"), ("MEX", "ADM2"), ("GEO", "ADM2"),
    ("MDA", "ADM1"), ("UKR", "ADM1"), ("UKR", "ADM2"), ("ARM", "ADM1"), ("TUR", "ADM1"), ("ISR", "ADM2"),
    ("LBN", "ADM2"), ("SRB", "ADM1"), ("SRB", "ADM2"), ("MKD", "ADM2"), ("MNE", "ADM1"), ("BIH", "ADM3"),
    ("JPN", "ADM1"), ("CHN", "ADM2"), ("IND", "ADM2"),
]

# adynak/WineRegions Australian files (state folder / file name)
AU_FILES = """Queensland/Granite_Belt Queensland/South_Burnett Western_Australia/Albany Western_Australia/Great_Southern
Western_Australia/Perth_Hills Western_Australia/Peel Western_Australia/Pemberton Western_Australia/Porongurup
Western_Australia/Swan_District Western_Australia/Frankland_River Western_Australia/Mount_Barker
Western_Australia/Greater_Perth Western_Australia/Blackwood_Valley
Western_Australia/West_Australian_South_East_Coastal Western_Australia/Swan_Valley Western_Australia/Denmark
Western_Australia/Eastern_Plains,_Inland_and_North_of_Western_Australia Western_Australia/Margaret_River
Western_Australia/Geographe Western_Australia/South_West_Australia Western_Australia/Central_Western_Australia
Western_Australia/Manjimup Victoria/Sunbury Victoria/Grampians Victoria/Upper_Goulburn Victoria/Alpine_Valleys
Victoria/Great_Western Victoria/Geelong Victoria/Gippsland Victoria/Beechworth Victoria/Strathbogie_Ranges
Victoria/Glenrowan Victoria/Murray_Darling Victoria/Henty Victoria/Heathcote Victoria/North_East_Victoria
Victoria/Rutherglen Victoria/Swan_Hill Victoria/Bendigo Victoria/Goulburn_Valley Victoria/Nagambie_Lakes
Victoria/Western_Victoria Victoria/Macedon_Ranges Victoria/King_Valley Victoria/Central_Victoria
Victoria/Pyrenees Victoria/Yarra_Valley Victoria/Mornington_Peninsula Australia/Australia
New_South_Wales/Riverina New_South_Wales/Gundagai New_South_Wales/Canberra_District
New_South_Wales/Hastings_River New_South_Wales/Hunter New_South_Wales/Cowra New_South_Wales/Northern_Slopes
New_South_Wales/Tumbarumba New_South_Wales/Western_Plains New_South_Wales/Perricoota
New_South_Wales/Broke_Fordwich New_South_Wales/Hilltops New_South_Wales/Murray_Darling
New_South_Wales/Big_Rivers New_South_Wales/Swan_Hill New_South_Wales/Hunter_Valley New_South_Wales/South_Coast
New_South_Wales/New_England_Australia New_South_Wales/Shoalhaven_Coast New_South_Wales/Orange
New_South_Wales/Northern_Rivers New_South_Wales/Pokolbin New_South_Wales/Central_Ranges
New_South_Wales/Upper_Hunter_Valley New_South_Wales/Mudgee New_South_Wales/Southern_Highlands
South_Australia/Mount_Gambier South_Australia/McLaren_Vale South_Australia/Currency_Creek
South_Australia/Eden_Valley South_Australia/Barossa_Valley South_Australia/Langhorne_Creek
South_Australia/Fleurieu South_Australia/Riverland South_Australia/Southern_Flinders_Ranges
South_Australia/High_Eden South_Australia/The_Peninsulas South_Australia/Robe South_Australia/Padthaway
South_Australia/Kangaroo_Island South_Australia/Southern_Fleurieu South_Australia/Clare_Valley
South_Australia/Mount_Benson South_Australia/Piccadilly_Valley South_Australia/Far_North
South_Australia/Lenswood South_Australia/Barossa South_Australia/Limestone_Coast
South_Australia/Adelaide_Hills South_Australia/Adelaide_Plains South_Australia/Wrattonbully
South_Australia/Coonawarra South_Australia/Mount_Lofty_Ranges""".split()

# every country file in openwinemap (data/manifest.json, 2026-10-04)
OWM_COUNTRIES = ("FR IT ES PT DE AT CH GR HU RO BG HR SI SK CZ LU RS MK ME BA AL MD UA GE AM TR CY LB IL MA TN ZA US CA MX "
                 "AR CL UY BR AU NZ JP CN GB").split()


def get(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 200:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".part"
    with urllib.request.urlopen(url, timeout=300) as r, open(tmp, "wb") as f:
        f.write(r.read())
    if os.path.getsize(tmp) < 200:
        raise RuntimeError(f"too small (Git LFS pointer?): {url}")
    os.replace(tmp, path)
    print("  got", os.path.relpath(path, RAW))


def main():
    jobs = [(GB_META, os.path.join(RAW, "geoboundaries", "meta.csv"))]
    jobs += [(GB.format(iso=i, adm=a), os.path.join(RAW, "geoboundaries", f"{i}-{a}.geojson")) for i, a in GB_FILES]
    jobs += [(ADYNAK.format(path=p + ".geojson"), os.path.join(RAW, "au", p.replace("/", "__") + ".geojson")) for p in AU_FILES]
    jobs += [(OWM.format(cc=c), os.path.join(RAW, "osm", f"{c}.geojson")) for c in OWM_COUNTRIES]
    failed = []
    for url, path in jobs:
        try:
            get(url, path)
        except Exception as e:
            failed.append((url, str(e)))
    for u, e in failed:
        print("FAILED", u, e, file=sys.stderr)
    print(f"{len(jobs) - len(failed)}/{len(jobs)} files present")


if __name__ == "__main__":
    main()
