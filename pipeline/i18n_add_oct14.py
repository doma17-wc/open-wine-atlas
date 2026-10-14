"""One-off: translations for the texts added on 14 October 2026 (Where it is, stored terrain, Records).

Merges into web/i18n/<lang>.json without touching existing entries. Safe to rerun.
"""
import json
import os

I18N = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "i18n")
LANGS = ["fr", "it", "de", "es", "pt", "nl", "ja", "zh", "ko"]

T = {
    "No. {n}": ["N° {n}", "N. {n}", "Nr. {n}", "N.º {n}", "N.º {n}", "Nr. {n}", "第{n}位", "第{n}名", "{n}위"],
    # records: terrain records only for outlines drawn on the wine area
    "mean elevation, outlines drawn on the wine area only": ["altitude moyenne, périmètres tracés sur la zone viticole seulement", "quota media, solo perimetri tracciati sulla zona vitata", "mittlere Höhe, nur auf die Weinbaufläche gezeichnete Umrisse", "altitud media, solo contornos trazados sobre la zona vitícola", "altitude média, só contornos traçados sobre a zona vitícola", "gemiddelde hoogte, alleen omtrekken getekend op het wijngebied", "平均標高（産地そのものを描いた輪郭のみ）", "平均海拔（仅限按产区本身绘制的轮廓）", "평균 고도(산지 자체로 그린 경계만)"],
    "mean slope, outlines drawn on the wine area only": ["pente moyenne, périmètres tracés sur la zone viticole seulement", "pendenza media, solo perimetri tracciati sulla zona vitata", "mittlere Neigung, nur auf die Weinbaufläche gezeichnete Umrisse", "pendiente media, solo contornos trazados sobre la zona vitícola", "declive médio, só contornos traçados sobre a zona vitícola", "gemiddelde helling, alleen omtrekken getekend op het wijngebied", "平均傾斜（産地そのものを描いた輪郭のみ）", "平均坡度（仅限按产区本身绘制的轮廓）", "평균 경사(산지 자체로 그린 경계만)"],
    "Elevation and slope records use only outlines drawn on the wine area itself: French parcels, German vineyard sites, US AVAs and Australian subregions.": ["Les records d'altitude et de pente ne retiennent que les périmètres tracés sur la zone viticole elle-même : parcelles françaises, Lagen allemandes, AVA américaines et sous-régions australiennes.", "I primati di quota e pendenza usano solo perimetri tracciati sulla zona vitata stessa: particelle francesi, Lagen tedesche, AVA statunitensi e sottoregioni australiane.", "Höhen- und Neigungsrekorde berücksichtigen nur Umrisse, die auf die Weinbaufläche selbst gezeichnet sind: französische Parzellen, deutsche Einzellagen, US-AVAs und australische Subregionen.", "Los récords de altitud y pendiente solo usan contornos trazados sobre la propia zona vitícola: parcelas francesas, Lagen alemanas, AVA estadounidenses y subregiones australianas.", "Os recordes de altitude e declive só usam contornos traçados sobre a própria zona vitícola: parcelas francesas, Lagen alemãs, AVA norte-americanas e sub-regiões australianas.", "Hoogte- en hellingrecords gebruiken alleen omtrekken die op het wijngebied zelf getekend zijn: Franse percelen, Duitse Lagen, Amerikaanse AVA's en Australische subregio's.", "標高と傾斜の記録は、産地そのものを描いた輪郭のみを対象とします：フランスの区画、ドイツのLage、米国のAVA、オーストラリアのサブリージョン。", "海拔和坡度之最仅采用按产区本身绘制的轮廓：法国地块、德国单一园、美国AVA和澳大利亚子产区。", "고도와 경사 기록은 산지 자체로 그린 경계만 사용합니다: 프랑스 필지, 독일 Lage, 미국 AVA, 호주 하위 산지."],

    "{km} km {dir} of {town}": ["à {km} km de {town}, direction {dir}", "a {km} km a {dir} di {town}", "{km} km von {town} Richtung {dir}",
                                "a {km} km al {dir} de {town}", "a {km} km a {dir} de {town}", "{km} km van {town}, richting {dir}",
                                "{town}から{dir}へ{km} km", "{town}以{dir}{km}公里", "{town} 기준 {dir} {km} km"],
    "around the town of {town}": ["autour de la ville de {town}", "nei dintorni di {town}", "rund um den Ort {town}", "en torno a la localidad de {town}",
                                  "em redor da localidade de {town}", "rond de plaats {town}", "{town}の町の周辺", "{town}镇周边", "{town} 주변"],
    "next to {town}": ["tout près de {town}", "accanto a {town}", "direkt bei {town}", "junto a {town}", "junto a {town}", "vlak bij {town}",
                       "{town}のすぐ近く", "紧邻{town}", "{town} 바로 옆"],
    "It lies {a}.": ["Situation : {a}.", "Si trova {a}.", "Lage: {a}.", "Se encuentra {a}.", "Fica {a}.", "Ligging: {a}.", "位置：{a}。", "位置：{a}。", "위치: {a}."],
    "It lies {a} and {b}.": ["Situation : {a} et {b}.", "Si trova {a} e {b}.", "Lage: {a} und {b}.", "Se encuentra {a} y {b}.", "Fica {a} e {b}.",
                             "Ligging: {a} en {b}.", "位置：{a}、{b}。", "位置：{a}，{b}。", "위치: {a}, {b}."],
    "Where it is": ["Situation", "Dove si trova", "Lage", "Ubicación", "Localização", "Ligging", "位置", "位置", "위치"],
    "Nearest town": ["Ville la plus proche", "Centro più vicino", "Nächster Ort", "Localidad más cercana", "Localidade mais próxima", "Dichtstbijzijnde plaats",
                     "最寄りの町", "最近的城镇", "가장 가까운 마을"],
    "Nearest city": ["Grande ville la plus proche", "Città più vicina", "Nächste Stadt", "Ciudad más cercana", "Cidade mais próxima", "Dichtstbijzijnde stad",
                     "最寄りの都市", "最近的城市", "가장 가까운 도시"],
    "from the centre": ["depuis le centre", "dal centro", "vom Mittelpunkt", "desde el centro", "a partir do centro", "vanaf het midden", "中心から", "从中心起算", "중심 기준"],
    "{n} people": ["{n} habitants", "{n} abitanti", "{n} Einwohner", "{n} habitantes", "{n} habitantes", "{n} inwoners", "人口{n}人", "人口{n}", "인구 {n}명"],
    "To the sea": ["Distance à la mer", "Distanza dal mare", "Entfernung zum Meer", "Distancia al mar", "Distância ao mar", "Afstand tot de zee", "海までの距離", "距海距离", "바다까지 거리"],
    "Rivers nearby": ["Cours d'eau proches", "Fiumi vicini", "Flüsse in der Nähe", "Ríos cercanos", "Rios próximos", "Rivieren in de buurt", "近くの川", "附近河流", "인근 강"],
    "Lakes nearby": ["Lacs proches", "Laghi vicini", "Seen in der Nähe", "Lagos cercanos", "Lagos próximos", "Meren in de buurt", "近くの湖", "附近湖泊", "인근 호수"],
    "Same latitude, other continents": ["Même latitude, autres continents", "Stessa latitudine, altri continenti", "Gleiche Breite, andere Kontinente",
                                        "Misma latitud, otros continentes", "Mesma latitude, outros continentes", "Zelfde breedtegraad, andere continenten",
                                        "同じ緯度・他の大陸", "同纬度的其他大洲产区", "같은 위도, 다른 대륙"],
    "Distances from the centre of the place. Towns: GeoNames. Sea, rivers and lakes: Natural Earth.": [
        "Distances mesurées depuis le centre du lieu. Villes : GeoNames. Mer, cours d'eau et lacs : Natural Earth.",
        "Distanze misurate dal centro del luogo. Centri abitati: GeoNames. Mare, fiumi e laghi: Natural Earth.",
        "Entfernungen vom Mittelpunkt des Ortes. Orte: GeoNames. Meer, Flüsse und Seen: Natural Earth.",
        "Distancias desde el centro del lugar. Localidades: GeoNames. Mar, ríos y lagos: Natural Earth.",
        "Distâncias a partir do centro do local. Localidades: GeoNames. Mar, rios e lagos: Natural Earth.",
        "Afstanden vanaf het midden van de plek. Plaatsen: GeoNames. Zee, rivieren en meren: Natural Earth.",
        "距離は場所の中心から。町：GeoNames。海・川・湖：Natural Earth。",
        "距离从该地中心起算。城镇：GeoNames。海岸、河流和湖泊：Natural Earth。",
        "거리는 장소 중심 기준. 마을: GeoNames. 바다·강·호수: Natural Earth."],
    "Measured over the whole place on {n} elevation cells of about {res} m.": [
        "Mesuré sur l'ensemble du lieu, sur {n} cellules d'altitude d'environ {res} m.",
        "Misurato sull'intero luogo, su {n} celle di quota di circa {res} m.",
        "Für den ganzen Ort gemessen, auf {n} Höhenzellen von etwa {res} m.",
        "Medido en todo el lugar sobre {n} celdas de altitud de unos {res} m.",
        "Medido em todo o local sobre {n} células de altitude de cerca de {res} m.",
        "Gemeten over de hele plek op {n} hoogtecellen van ongeveer {res} m.",
        "場所全体を約{res} mの標高セル{n}個で計測。",
        "在整个地块上以约{res}米的{n}个高程单元测得。",
        "장소 전체를 약 {res} m 크기의 고도 셀 {n}개로 측정."],
    "Records": ["Records", "Primati", "Rekorde", "Récords", "Recordes", "Records", "記録", "之最", "기록"],
    "Highest": ["Les plus hauts", "I più alti", "Am höchsten", "Los más altos", "Os mais altos", "Hoogst gelegen", "最も高い", "海拔最高", "가장 높은 곳"],
    "Lowest": ["Les plus bas", "I più bassi", "Am tiefsten", "Los más bajos", "Os mais baixos", "Laagst gelegen", "最も低い", "海拔最低", "가장 낮은 곳"],
    "Steepest": ["Les plus pentus", "I più ripidi", "Am steilsten", "Los más empinados", "Os mais íngremes", "Steilst", "最も急斜面", "坡度最陡", "가장 가파른 곳"],
    "Largest": ["Les plus grands", "I più estesi", "Am größten", "Los más extensos", "Os mais extensos", "Grootst", "最も広い", "面积最大", "가장 넓은 곳"],
    "Smallest": ["Les plus petits", "I più piccoli", "Am kleinsten", "Los más pequeños", "Os mais pequenos", "Kleinst", "最も小さい", "面积最小", "가장 작은 곳"],
    "Most wineries mapped": ["Le plus de domaines cartographiés", "Più cantine mappate", "Die meisten kartierten Weingüter", "Más bodegas cartografiadas",
                             "Mais produtores cartografados", "Meeste wijnhuizen op de kaart", "地図上のワイナリーが最多", "已标注酒庄最多", "지도에 표시된 와이너리 최다"],
    "Farthest from the sea": ["Les plus éloignés de la mer", "I più lontani dal mare", "Am weitesten vom Meer", "Los más alejados del mar", "Os mais afastados do mar",
                              "Verst van zee", "海から最も遠い", "离海最远", "바다에서 가장 먼 곳"],
    "Farthest north": ["Les plus au nord", "I più a nord", "Am nördlichsten", "Los más septentrionales", "Os mais a norte", "Noordelijkst", "最北", "最北", "최북단"],
    "Farthest south": ["Les plus au sud", "I più a sud", "Am südlichsten", "Los más meridionales", "Os mais a sul", "Zuidelijkst", "最南", "最南", "최남단"],
    "area of the outline": ["superficie du périmètre", "superficie del perimetro", "Fläche des Umrisses", "superficie del contorno", "área do contorno",
                            "oppervlakte van de omtrek", "区域の面積", "轮廓面积", "경계 면적"],
    "measured area": ["superficie mesurée", "superficie misurata", "gemessene Fläche", "superficie medida", "área medida", "gemeten oppervlakte",
                      "計測面積", "实测面积", "측정 면적"],
    "OpenStreetMap wineries inside the outline": ["domaines OpenStreetMap dans le périmètre", "cantine OpenStreetMap all'interno del perimetro",
                                                  "OpenStreetMap-Weingüter im Umriss", "bodegas de OpenStreetMap dentro del contorno",
                                                  "produtores do OpenStreetMap dentro do contorno", "OpenStreetMap-wijnhuizen binnen de omtrek",
                                                  "区域内のOpenStreetMapのワイナリー", "轮廓内的OpenStreetMap酒庄", "경계 안의 OpenStreetMap 와이너리"],
    "from the centre to the nearest sea coast": ["du centre à la côte la plus proche", "dal centro alla costa più vicina", "vom Mittelpunkt zur nächsten Meeresküste",
                                                 "del centro a la costa más cercana", "do centro à costa mais próxima", "van het midden tot de dichtstbijzijnde kust",
                                                 "中心から最寄りの海岸まで", "从中心到最近海岸", "중심에서 가장 가까운 해안까지"],
    "latitude of the centre": ["latitude du centre", "latitudine del centro", "geografische Breite des Mittelpunkts", "latitud del centro", "latitude do centro",
                               "breedtegraad van het midden", "中心の緯度", "中心纬度", "중심의 위도"],
    "The records could not be loaded right now.": ["Les records n'ont pas pu être chargés pour le moment.", "Al momento non è possibile caricare i primati.",
                                                   "Die Rekorde konnten gerade nicht geladen werden.", "Ahora mismo no se han podido cargar los récords.",
                                                   "Não foi possível carregar os recordes neste momento.", "De records konden nu niet worden geladen.",
                                                   "現在、記録を読み込めません。", "暂时无法加载之最数据。", "지금은 기록을 불러올 수 없습니다."],
    "The extremes of the atlas, measured on the same open data for every place. Click a name to fly there.": [
        "Les extrêmes de l'atlas, mesurés avec les mêmes données ouvertes pour chaque lieu. Cliquez sur un nom pour vous y rendre.",
        "Gli estremi dell'atlante, misurati sugli stessi dati aperti per ogni luogo. Clicca un nome per volarci.",
        "Die Extreme des Atlas, für jeden Ort mit denselben offenen Daten gemessen. Ein Klick auf einen Namen fliegt dorthin.",
        "Los extremos del atlas, medidos con los mismos datos abiertos para cada lugar. Pulsa un nombre para volar hasta allí.",
        "Os extremos do atlas, medidos com os mesmos dados abertos para cada local. Clique num nome para voar até lá.",
        "De uitersten van de atlas, voor elke plek gemeten op dezelfde open data. Klik op een naam om erheen te vliegen.",
        "すべての場所を同じオープンデータで測ったアトラスの極値。名前をクリックするとその場所へ移動します。",
        "用同一套开放数据为每个地点测出的地图之最。点击名称即可飞往该地。",
        "모든 장소를 같은 공개 데이터로 측정한 아틀라스의 극값입니다. 이름을 누르면 그곳으로 이동합니다."],
    "The whole world": ["Le monde entier", "Tutto il mondo", "Die ganze Welt", "Todo el mundo", "O mundo inteiro", "De hele wereld", "全世界", "全世界", "전 세계"],
    "Regions are left out, and so are places drawn from the districts that contain them, because their outline is not the wine area. Outlines made of whole communes include land that is not vineyard.": [
        "Les régions sont exclues, de même que les lieux tracés d'après les circonscriptions qui les contiennent, car leur périmètre n'est pas la zone viticole. Les périmètres formés de communes entières incluent des terres qui ne sont pas des vignes.",
        "Sono escluse le regioni e i luoghi disegnati a partire dalle circoscrizioni che li contengono, perché il loro perimetro non è la zona vitivinicola. I perimetri formati da comuni interi includono terreni non vitati.",
        "Regionen sind ausgenommen, ebenso Orte, die nach den Verwaltungsbezirken gezeichnet sind, in denen sie liegen, weil ihr Umriss nicht das Weinbaugebiet ist. Umrisse aus ganzen Gemeinden enthalten auch Land ohne Reben.",
        "Se excluyen las regiones y los lugares trazados a partir de los distritos que los contienen, porque su contorno no es la zona vitícola. Los contornos formados por municipios enteros incluyen tierras sin viñedo.",
        "Excluem-se as regiões e os locais desenhados a partir dos distritos que os contêm, porque o seu contorno não é a zona vitícola. Os contornos formados por concelhos inteiros incluem terrenos sem vinha.",
        "Regio's zijn weggelaten, en ook plekken die getekend zijn naar de districten waarin ze liggen, omdat hun omtrek niet het wijngebied is. Omtrekken van hele gemeenten bevatten ook land zonder wijngaarden.",
        "地域、および含まれる行政区から描いた場所は除外しています。その輪郭はワイン産地そのものではないためです。市町村全体で描いた輪郭にはブドウ畑以外の土地も含まれます。",
        "不含大产区，也不含按所在行政区划绘制的地点，因为其轮廓并非葡萄酒产区本身。由整个市镇构成的轮廓包含非葡萄园土地。",
        "광역 산지와, 그 지점을 포함하는 행정 구역으로 그린 장소는 제외했습니다. 그 경계가 와인 산지 자체가 아니기 때문입니다. 시·군 전체로 그린 경계에는 포도밭이 아닌 땅도 포함됩니다."],
}


def main():
    for i, l in enumerate(LANGS):
        f = os.path.join(I18N, l + ".json")
        d = json.load(open(f, encoding="utf-8"))
        for en, tr in T.items():
            d.setdefault(en, tr[i])
        json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("added", len(T), "texts to", len(LANGS), "languages")


if __name__ == "__main__":
    main()
