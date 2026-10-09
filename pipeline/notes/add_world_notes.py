"""Append editorial notes for wine places outside the EU and the US to editorial.json (idempotent).

General wine knowledge, CC BY 4.0, Open Wine Atlas contributors. Check facts against the
official register before reuse.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
NOTES = [
    # Australia
    ("AU", "Barossa Valley", "Warm valley north-east of Adelaide, settled by Silesian Lutherans in the 1840s. Some of the oldest Shiraz, Grenache and Mataro vines in the world survive here on their own roots, because phylloxera never reached South Australia."),
    ("AU", "Eden Valley", "The higher, cooler hills east of the Barossa Valley, on granite and schist. Known for taut, lime-scented Riesling and for Shiraz from a few historic vineyards."),
    ("AU", "McLaren Vale", "Maritime region south of Adelaide between the Mount Lofty Ranges and the Gulf St Vincent. Shiraz and Grenache dominate, and the region has mapped dozens of distinct geologies across its districts."),
    ("AU", "Clare Valley", "A series of narrow valleys north of Adelaide, warm by day and cool at night. With Eden Valley it is Australia's classic home of dry Riesling."),
    ("AU", "Coonawarra", "A strip about 12 to 15 km long of red terra rossa over limestone in the flat south-east of South Australia. It made its name with Cabernet Sauvignon."),
    ("AU", "Adelaide Hills", "Cool, high part of the Mount Lofty Ranges just east of Adelaide. Sauvignon Blanc, Chardonnay and Pinot Noir, and a base for sparkling wine."),
    ("AU", "Margaret River", "Region in Western Australia between the Indian Ocean and the Leeuwin Ridge, planted from the late 1960s. The ocean keeps the climate mild; Cabernet Sauvignon and Chardonnay are its best-known wines."),
    ("AU", "Yarra Valley", "Cool region east of Melbourne, one of the first vineyard areas of Victoria in the 1830s. Chardonnay, Pinot Noir and sparkling wine, with Shiraz on warmer sites."),
    ("AU", "Mornington Peninsula", "Maritime peninsula south of Melbourne with small vineyards, surrounded by sea on three sides. Pinot Noir and Chardonnay."),
    ("AU", "Heathcote", "Central Victorian region on red Cambrian soils along the Mount Camel Range, best known for dense Shiraz."),
    ("AU", "Rutherglen", "North-east Victoria, hot and dry, famous for fortified Muscat and Topaque aged for decades in a solera-like system."),
    ("AU", "Great Southern", "Australia's largest wine region, on the south coast of Western Australia. Five subregions: Albany, Denmark, Frankland River, Mount Barker and Porongurup. Riesling, Shiraz and Cabernet Sauvignon."),
    ("AU", "Tasmania", "The island state is a single wine GI. Australia's coolest wine region, increasingly important for sparkling wine, Pinot Noir and Chardonnay."),
    ("AU", "Canberra District", "Cool upland region around the national capital, mostly in New South Wales. Known for Shiraz, often co-fermented with a little Viognier, and for Riesling."),
    ("AU", "Hunter", "One of Australia's oldest wine regions, north of Sydney. Humid and warm, it makes a unique style of low-alcohol Semillon that ages for decades, and medium-bodied Shiraz."),
    ("AU", "Orange", "High-altitude region on the slopes of the extinct volcano Mount Canobolas in New South Wales. Its lower boundary is set at 600 m."),
    ("AU", "Riverland", "Irrigated region along the Murray River, one of the largest sources of Australian wine by volume."),
    # New Zealand
    ("NZ", "Marlborough", "At the north-east tip of the South Island, New Zealand's largest wine region. Its pungent Sauvignon Blanc, first planted in the 1970s, put the country on the wine map. The Wairau and Awatere valleys are its main parts."),
    ("NZ", "Central Otago", "The world's most southerly major wine region, inland on the South Island with a continental climate. Pinot Noir on schist-derived soils is its signature."),
    ("NZ", "Hawke's Bay", "East coast of the North Island, warm and sunny, the country's second-largest region. Syrah and Bordeaux varieties, notably from the Gimblett Gravels, an old riverbed."),
    ("NZ", "Wairarapa", "Region in the south-east of the North Island, including Martinborough. Small producers, best known for Pinot Noir."),
    ("NZ", "Martinborough", "Small town and terrace of free-draining gravels in the Wairarapa, among New Zealand's first Pinot Noir areas in the 1980s."),
    ("NZ", "Waiheke Island", "Island in the Hauraki Gulf off Auckland with a warm, maritime climate, known for Bordeaux-style reds and Syrah."),
    ("NZ", "Gisborne", "On the east coast of the North Island, warm and fertile, long known for Chardonnay."),
    ("NZ", "Nelson", "Sunny region at the top of the South Island, west of Marlborough. Aromatic whites and Pinot Noir from the Waimea Plains and the Moutere Hills."),
    ("NZ", "North Canterbury", "The main wine area of Canterbury, centred on the Waipara Valley north of Christchurch. Riesling, Pinot Noir and Chardonnay on limestone and gravel."),
    # South Africa
    ("ZA", "Stellenbosch", "The heart of South African wine, east of Cape Town between the Simonsberg, Helderberg and Jonkershoek mountains. Cabernet Sauvignon, Bordeaux blends, Pinotage and Chenin Blanc on granite and sandstone soils. The district is divided into wards."),
    ("ZA", "Swartland", "Rolling wheat and vine country north of Cape Town, dry-farmed bush vines on shale and granite. Since the 2000s a centre of old-vine Chenin Blanc and Rhône-style blends."),
    ("ZA", "Constantia", "The oldest wine area of the Cape, on the slopes of the Constantiaberg south of Cape Town. Its sweet Vin de Constance was famous in 18th- and 19th-century Europe."),
    ("ZA", "Franschhoek", "Valley settled by French Huguenots in the late 17th century, enclosed by mountains east of Paarl."),
    ("ZA", "Walker Bay", "Cool maritime district around Hermanus, including the Hemel-en-Aarde wards, known for Pinot Noir and Chardonnay."),
    ("ZA", "Elgin", "Cool, high apple-growing basin in the Overberg, a source of Sauvignon Blanc, Chardonnay and Pinot Noir."),
    ("ZA", "Paarl", "Large district around the town of Paarl and its granite domes, north of Stellenbosch, home of the KWV for most of the 20th century."),
    ("ZA", "Robertson", "Warm, dry Breede River valley district on lime-rich soils, known for Chardonnay and sparkling Cap Classique."),
    ("ZA", "Coastal Region", "Wine of Origin region that groups the districts close to the Atlantic and False Bay, including Stellenbosch, Paarl, Swartland and Cape Town."),
    # Chile
    ("CL", "Valle del Maipo", "The valley around Santiago, cradle of Chilean wine in the 19th century. Alto Maipo, at the foot of the Andes, is known for Cabernet Sauvignon."),
    ("CL", "Valle de Colchagua", "Part of the Rapel Valley, warm and sunny, best known for Carmenère, Cabernet Sauvignon and blends. Apalta, a horseshoe of hillside vineyards, is its most famous sector."),
    ("CL", "Valle de Casablanca", "Coastal valley between Santiago and Valparaíso, cooled by the Pacific and the Humboldt current. Planted from the 1980s with Sauvignon Blanc, Chardonnay and Pinot Noir."),
    ("CL", "Valle de Leyda", "Coastal zone of the San Antonio Valley, a few kilometres from the ocean, for cool-climate Sauvignon Blanc and Pinot Noir."),
    ("CL", "Valle del Maule", "Chile's largest wine-growing valley by area, with old dry-farmed Carignan and País vines in its coastal hills."),
    ("CL", "Valle del Itata", "One of the oldest vineyard areas of Chile, in the south, with dry-farmed old País, Muscat and Cinsault vines on granite slopes."),
    ("CL", "Valle del Elqui", "Northern valley in the Andes foothills, very dry and clear, best known for pisco but also for high-altitude Syrah and Sauvignon Blanc."),
    ("CL", "Valle del Aconcagua", "Valley north of Santiago, warm inland, with coastal vineyards reaching towards the Pacific."),
    ("CL", "Apalta", "Horseshoe of steep hillsides in the Colchagua Valley on the north bank of the Tinguiririca river, home to some of Chile's best-known reds."),
    # Argentina
    ("AR", "Mendoza", "Argentina's main wine province, producing most of the country's wine in an irrigated high desert at the foot of the Andes. Malbec is its signature."),
    ("AR", "Luján de Cuyo", "Department south of Mendoza city with some of the oldest Malbec vineyards, between about 900 and 1,100 m. It holds one of Argentina's two DOCs."),
    ("AR", "Valle de Uco", "High valley south-west of Mendoza (Tupungato, Tunuyán and San Carlos), with vineyards from about 900 m to over 1,500 m. Cool nights and alluvial soils."),
    ("AR", "Paraje Altamira", "Alluvial fan of the Tunuyán river in San Carlos, Valle de Uco, at around 1,000 to 1,100 m. Stony, calcareous soils; registered as an IG in 2013 and enlarged in 2017."),
    ("AR", "Los Chacayes", "High IG in Tunuyán, Valle de Uco, on stony alluvial soils up towards the Andes."),
    ("AR", "Agrelo", "District of Luján de Cuyo with deep clay-loam soils, widely planted with Malbec and Cabernet Sauvignon."),
    ("AR", "San Juan", "Hot, dry province north of Mendoza, Argentina's second wine region by volume. Syrah does well here, especially in the Tulum and Pedernal valleys."),
    ("AR", "Salta", "Northern province whose Calchaquí valleys hold some of the highest vineyards in the world, above 2,000 m in places. Torrontés and intense Malbec."),
    ("AR", "Cafayate - Valle de Cafayate", "The best-known part of the Calchaquí valleys, around 1,700 m, sandy and dry. Home of aromatic Torrontés."),
    ("AR", "Patagonia - Patagonia Argentina", "The southern wine regions along the Río Negro and Neuquén valleys and further south, cool and windy, for Pinot Noir and Malbec."),
    # Brazil, Uruguay
    ("BR", "Vale dos Vinhedos", "Valley in the Serra Gaúcha of Rio Grande do Sul, settled by Italian immigrants in the 1870s. Brazil's first wine IP (2002) and first DO (2012)."),
    ("BR", "Campanha Gaúcha", "Plains along the Uruguayan border in Rio Grande do Sul, drier and sunnier than the Serra Gaúcha."),
    ("BR", "Vale do São Francisco", "Tropical irrigated vineyards around Petrolina at about 9° south, which can harvest more than once a year."),
    ("UY", "Metropolitana", "The departments around Montevideo, chiefly Canelones, where most Uruguayan wine is made. Tannat is the national grape."),
    # Canada
    ("CA", "Niagara Peninsula", "Ontario's main wine area, between Lake Ontario and Lake Erie, moderated by the lakes and sheltered by the Niagara Escarpment. Icewine, Riesling, Chardonnay and Cabernet Franc."),
    ("CA", "Okanagan Valley", "Long valley of glacial lakes in British Columbia, semi-desert in the south around Osoyoos and Oliver, cooler in the north."),
    ("CA", "Prince Edward County", "Limestone peninsula in Lake Ontario where vines are buried in winter to survive the cold. Pinot Noir and Chardonnay."),
    # Georgia, Moldova, Lebanon, Israel, Turkey
    ("GE", "Kakheti", "Eastern Georgia along the Alazani valley, where most of the country's wine is made, including amber wines fermented with skins in buried clay qvevri, a method inscribed by UNESCO in 2013."),
    ("GE", "Tsinandali", "Village appellation in Kakheti for a dry white blend of Rkatsiteli and Mtsvane, named after the village of Tsinandali, home of the estate of the poet Alexander Chavchavadze."),
    ("GE", "Mukuzani", "Appellation in Kakheti for dry red Saperavi from the right bank of the Alazani."),
    ("GE", "Kindzmarauli", "Appellation in Kvareli, Kakheti, for semi-sweet red Saperavi."),
    ("GE", "Khvanchkara", "Appellation in Racha, western Georgia, for naturally semi-sweet red wine from Aleksandrouli and Mujuretuli."),
    ("MD", "Codru", "The central, wooded hill region of Moldova around Chișinău, with the country's large underground cellars at Cricova and Mileștii Mici."),
    ("LB", "Bekaa Valley", "High plateau between the Lebanon and Anti-Lebanon mountains at about 1,000 m, where nearly all Lebanese wine is made."),
    ("IL", "Galilee", "Israel's northern wine region, highest and coolest, including Upper Galilee."),
    ("TR", "Thrace-Marmara", "European Turkey and the Sea of Marmara coast, one of the country's main wine areas, second in output to the Aegean."),
    ("TR", "Central Anatolia (Cappadocia)", "Volcanic high plateau around Nevşehir where vines have been grown for thousands of years. Native grapes such as Emir in Cappadocia and Kalecik Karası from Kalecik near Ankara."),
    # Asia
    ("JP", "Yamanashi", "Prefecture west of Tokyo and the centre of Japanese wine since the 19th century. Its signature is Koshu, a pink-skinned grape for delicate dry whites."),
    ("JP", "Hokkaido", "Japan's northern island, cool enough for Pinot Noir and German varieties, with fast-growing plantings."),
    ("CN", "Helan Mountain East (Ningxia)", "Desert foothills of the Helan Mountains in Ningxia, sheltered from Gobi winds. Vines are buried each winter against the cold. China's best-known region for Cabernet Sauvignon."),
    ("CN", "Yantai", "Coastal area of Shandong where Changyu founded China's first modern winery in 1892."),
    ("IN", "Nashik Valley", "Plateau north-east of Mumbai at 500 to 700 m that produces most of India's wine. Vines are pruned so that the harvest falls in the dry winter months."),
]


def main():
    path = os.path.join(HERE, "editorial.json")
    data = json.load(open(path, encoding="utf-8"))
    have = {(n.get("country"), n.get("name")) for n in data["notes"]}
    add = [{"country": c, "name": n, "note": t} for c, n, t in NOTES if (c, n) not in have]
    data["notes"] += add
    # same layout as the hand-written file: one note per line
    head = {k: v for k, v in data.items() if k != "notes"}
    lines = ["{"] + ["  " + json.dumps(k) + ": " + json.dumps(v, ensure_ascii=False) + "," for k, v in head.items()] + ['  "notes": [']
    lines += ["    " + json.dumps(n, ensure_ascii=False) + ("," if i < len(data["notes"]) - 1 else "") for i, n in enumerate(data["notes"])]
    lines += ["  ]", "}"]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"added {len(add)} notes, total {len(data['notes'])}")


if __name__ == "__main__":
    main()
