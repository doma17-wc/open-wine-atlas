"""One-off: translations for the texts added on 21 October 2026 (producers and wines from LWIN).

Merges into web/i18n/<lang>.json without touching existing entries. Safe to rerun.
"""
import json
import os

I18N = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "i18n")
LANGS = ["fr", "it", "de", "es", "pt", "nl", "ja", "zh", "ko"]

T = {
    "Producer": ["Producteur", "Produttore", "Erzeuger", "Productor", "Produtor", "Producent", "生産者", "生产商", "생산자"],
    "Producers · {n}": ["Producteurs · {n}", "Produttori · {n}", "Erzeuger · {n}", "Productores · {n}", "Produtores · {n}", "Producenten · {n}",
                        "生産者 · {n}", "生产商 · {n}", "생산자 · {n}"],
    "Producers and wines:": ["Producteurs et vins :", "Produttori e vini:", "Erzeuger und Weine:", "Productores y vinos:", "Produtores e vinhos:",
                             "Producenten en wijnen:", "生産者とワイン：", "生产商与葡萄酒：", "생산자와 와인:"],
    "by Liv-ex": ["de Liv-ex", "di Liv-ex", "von Liv-ex", "de Liv-ex", "da Liv-ex", "van Liv-ex", "（Liv-ex）", "（Liv-ex）", "(Liv-ex)"],
    "Wines from": ["Vins de", "Vini da", "Weine aus", "Vinos de", "Vinhos de", "Wijnen uit", "ワインの産地：", "葡萄酒产自", "와인 산지:"],
    "Wines · {n}": ["Vins · {n}", "Vini · {n}", "Weine · {n}", "Vinos · {n}", "Vinhos · {n}", "Wijnen · {n}", "ワイン · {n}", "葡萄酒 · {n}", "와인 · {n}"],
    "wine": ["vin", "vino", "Wein", "vino", "vinho", "wijn", "ワイン", "款葡萄酒", "와인"],
    "wines": ["vins", "vini", "Weine", "vinos", "vinhos", "wijnen", "ワイン", "款葡萄酒", "와인"],
    "1 wine": ["1 vin", "1 vino", "1 Wein", "1 vino", "1 vinho", "1 wijn", "1本のワイン", "1款葡萄酒", "와인 1종"],
    "{n} wines": ["{n} vins", "{n} vini", "{n} Weine", "{n} vinos", "{n} vinhos", "{n} wijnen", "{n}本のワイン", "{n}款葡萄酒", "와인 {n}종"],
    "place on the map": ["lieu sur la carte", "luogo sulla mappa", "Ort auf der Karte", "lugar en el mapa", "lugar no mapa", "plek op de kaart",
                         "地図上の場所", "地图上的地点", "지도 위 장소"],
    "places on the map": ["lieux sur la carte", "luoghi sulla mappa", "Orte auf der Karte", "lugares en el mapa", "lugares no mapa", "plekken op de kaart",
                          "地図上の場所", "地图上的地点", "지도 위 장소"],
    "Where the wines come from · {n}": ["D'où viennent les vins · {n}", "Da dove vengono i vini · {n}", "Woher die Weine kommen · {n}",
                                        "De dónde vienen los vinos · {n}", "De onde vêm os vinhos · {n}", "Waar de wijnen vandaan komen · {n}",
                                        "ワインの産地 · {n}", "葡萄酒产地 · {n}", "와인 산지 · {n}"],
    "Place not given": ["Lieu non précisé", "Luogo non indicato", "Ort nicht angegeben", "Lugar no indicado", "Lugar não indicado", "Plaats niet opgegeven",
                        "産地の記載なし", "未注明产地", "산지 미기재"],
    "Sparkling": ["Effervescent", "Spumante", "Schaumwein", "Espumoso", "Espumante", "Mousserend", "スパークリング", "起泡酒", "스파클링"],
    "Fortified": ["Muté", "Fortificato", "Likörwein", "Generoso", "Fortificado", "Versterkt", "酒精強化", "加强酒", "주정 강화"],
    "Sweet": ["Liquoreux", "Dolce", "Süß", "Dulce", "Doce", "Zoet", "甘口", "甜型", "스위트"],
    "The records of these wines name the country only, so they are not placed on the map.": [
        "Les fiches de ces vins ne donnent que le pays : ils ne sont donc pas placés sur la carte.",
        "Le schede di questi vini indicano solo il paese, perciò non sono collocati sulla mappa.",
        "Die Einträge dieser Weine nennen nur das Land, deshalb stehen sie nicht auf der Karte.",
        "Los registros de estos vinos solo indican el país, así que no están situados en el mapa.",
        "Os registos destes vinhos só indicam o país, por isso não estão no mapa.",
        "De gegevens van deze wijnen noemen alleen het land, dus ze staan niet op de kaart.",
        "これらのワインの記録には国名しかないため、地図上には配置されていません。",
        "这些葡萄酒的记录只写了国家，因此未在地图上标出。",
        "이 와인들의 기록에는 나라만 적혀 있어 지도에 표시되지 않습니다."],
    "Names as Liv-ex publishes them. The atlas places each wine on the site, appellation or region its record names; the number next to a wine is its LWIN.": [
        "Noms tels que Liv-ex les publie. L'atlas place chaque vin sur le lieu-dit, l'appellation ou la région que nomme sa fiche ; le numéro à côté d'un vin est son LWIN.",
        "Nomi come li pubblica Liv-ex. L'atlante colloca ogni vino sul vigneto, la denominazione o la regione indicati nella sua scheda; il numero accanto a un vino è il suo LWIN.",
        "Namen so, wie Liv-ex sie veröffentlicht. Der Atlas setzt jeden Wein auf die Lage, Appellation oder Region, die sein Eintrag nennt; die Zahl neben einem Wein ist sein LWIN.",
        "Nombres tal como los publica Liv-ex. El atlas sitúa cada vino en el pago, la denominación o la región que indica su registro; el número junto a un vino es su LWIN.",
        "Nomes tal como a Liv-ex os publica. O atlas coloca cada vinho na vinha, denominação ou região que o seu registo indica; o número junto a um vinho é o seu LWIN.",
        "Namen zoals Liv-ex ze publiceert. De atlas plaatst elke wijn op de wijngaard, appellatie of regio die het gegeven noemt; het nummer naast een wijn is de LWIN.",
        "名称はLiv-exの公開どおりです。アトラスは各ワインを記録に記された畑・アペラシオン・地域に配置しています。ワインの横の番号はLWINです。",
        "名称按Liv-ex发布的原样。地图集把每款葡萄酒放在其记录所写的园地、产区或地区；葡萄酒旁的数字是它的LWIN。",
        "이름은 Liv-ex가 공개한 그대로입니다. 아틀라스는 각 와인을 기록에 적힌 밭, 원산지 명칭 또는 지역에 배치합니다. 와인 옆 번호는 LWIN입니다."],
    "{w} wines in the LWIN database by Liv-ex (CC BY 4.0) name this place or a place inside it. The number is how many.": [
        "{w} vins de la base LWIN de Liv-ex (CC BY 4.0) nomment ce lieu ou un lieu qu'il contient. Le chiffre indique combien.",
        "{w} vini del database LWIN di Liv-ex (CC BY 4.0) indicano questo luogo o un luogo al suo interno. Il numero dice quanti.",
        "{w} Weine der LWIN-Datenbank von Liv-ex (CC BY 4.0) nennen diesen Ort oder einen Ort darin. Die Zahl sagt, wie viele.",
        "{w} vinos de la base LWIN de Liv-ex (CC BY 4.0) indican este lugar o un lugar dentro de él. El número dice cuántos.",
        "{w} vinhos da base LWIN da Liv-ex (CC BY 4.0) indicam este lugar ou um lugar dentro dele. O número diz quantos.",
        "{w} wijnen uit de LWIN-database van Liv-ex (CC BY 4.0) noemen deze plek of een plek erbinnen. Het getal zegt hoeveel.",
        "Liv-exのLWINデータベース（CC BY 4.0）で、この場所またはその中の場所を記すワインは{w}本。数字は本数です。",
        "Liv-ex的LWIN数据库（CC BY 4.0）中有{w}款葡萄酒注明此地或其内的地点。数字表示款数。",
        "Liv-ex의 LWIN 데이터베이스(CC BY 4.0)에서 이곳 또는 그 안의 장소를 적은 와인은 {w}종입니다. 숫자는 종 수입니다."],
    "Search Barolo, Musigny, Louis Roederer, Cristal…": [
        "Chercher Barolo, Musigny, Louis Roederer, Cristal…", "Cerca Barolo, Musigny, Louis Roederer, Cristal…", "Barolo, Musigny, Louis Roederer, Cristal suchen…",
        "Buscar Barolo, Musigny, Louis Roederer, Cristal…", "Pesquisar Barolo, Musigny, Louis Roederer, Cristal…", "Zoek Barolo, Musigny, Louis Roederer, Cristal…",
        "Barolo、Musigny、Louis Roederer、Cristalを検索…", "搜索 Barolo、Musigny、Louis Roederer、Cristal…", "Barolo, Musigny, Louis Roederer, Cristal 검색…"],
    "Search wine places, producers and wines": [
        "Chercher des lieux, producteurs et vins", "Cerca luoghi, produttori e vini", "Weinorte, Erzeuger und Weine suchen", "Buscar lugares, productores y vinos",
        "Pesquisar lugares, produtores e vinhos", "Zoek wijnplekken, producenten en wijnen", "産地・生産者・ワインを検索", "搜索产地、生产商和葡萄酒", "산지, 생산자, 와인 검색"],
    "Loading the wines…": ["Chargement des vins…", "Caricamento dei vini…", "Weine werden geladen…", "Cargando los vinos…", "A carregar os vinhos…",
                           "Wijnen laden…", "ワインを読み込み中…", "正在加载葡萄酒…", "와인을 불러오는 중…"],
    "Search in": ["Chercher dans", "Cerca in", "Suchen in", "Buscar en", "Pesquisar em", "Zoeken in", "検索対象", "搜索范围", "검색 대상"],
    "Choose what the search looks for": ["Choisir ce que la recherche couvre", "Scegli cosa cercare", "Wählen, wonach gesucht wird", "Elegir qué busca la búsqueda",
                                         "Escolher o que a pesquisa procura", "Kies waar de zoekfunctie naar zoekt", "検索する対象を選ぶ", "选择搜索的内容", "검색할 항목 선택"],
    "Places and regions": ["Lieux et régions", "Luoghi e regioni", "Orte und Regionen", "Lugares y regiones", "Lugares e regiões", "Plekken en regio's",
                           "産地と地域", "产地与地区", "산지와 지역"],
    "Producers": ["Producteurs", "Produttori", "Erzeuger", "Productores", "Produtores", "Producenten", "生産者", "生产商", "생산자"],
    "Wines": ["Vins", "Vini", "Weine", "Vinos", "Vinhos", "Wijnen", "ワイン", "葡萄酒", "와인"],
    "Nothing found. Some kinds are switched off under the filter button.": [
        "Aucun résultat. Certains types sont désactivés sous le bouton de filtre.", "Nessun risultato. Alcuni tipi sono spenti nel pulsante filtro.",
        "Nichts gefunden. Einige Arten sind unter dem Filterknopf ausgeschaltet.", "Sin resultados. Algunos tipos están desactivados en el botón de filtro.",
        "Nada encontrado. Alguns tipos estão desligados no botão de filtro.", "Niets gevonden. Sommige soorten staan uit onder de filterknop.",
        "見つかりません。フィルターボタンで一部の種類がオフになっています。", "未找到。筛选按钮中关闭了部分类型。", "결과가 없습니다. 필터 버튼에서 일부 항목이 꺼져 있습니다."],
}


def main():
    for i, lang in enumerate(LANGS):
        path = os.path.join(I18N, lang + ".json")
        d = json.load(open(path, encoding="utf-8"))
        n = 0
        for en, tr in T.items():
            if en not in d:
                d[en] = tr[i]
                n += 1
        json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(lang, n)


if __name__ == "__main__":
    main()
