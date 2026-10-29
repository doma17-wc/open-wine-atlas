"""One-off: translations for the Champagne and Bordeaux Deep Regions of 29 October 2026 (pipeline/champagne.py,
pipeline/bordeaux_deep.py).

Merges into web/i18n/<lang>.json without touching existing entries. Safe to rerun.
Order of each list: fr, it, de, es, pt, nl, ja, zh, ko.
"""
import json
import os

I18N = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "i18n")
LANGS = ["fr", "it", "de", "es", "pt", "nl", "ja", "zh", "ko"]

T = {
    "Champagne in depth": ["La Champagne en profondeur", "Champagne in profondità", "Die Champagne im Detail", "Champagne en profundidad",
                           "Champagne em profundidade", "Champagne in detail", "シャンパーニュを深く", "深入香槟", "샹파뉴 깊이 보기"],
    "Bordeaux in depth": ["Bordeaux en profondeur", "Bordeaux in profondità", "Bordeaux im Detail", "Burdeos en profundidad",
                          "Bordéus em profundidade", "Bordeaux in detail", "ボルドーを深く", "深入波尔多", "보르도 깊이 보기"],
    "Champagne in full depth": ["La Champagne en profondeur", "La Champagne in profondità", "Die Champagne im ganzen Detail", "Champagne en profundidad",
                                "A Champagne em profundidade", "Champagne tot in detail", "シャンパーニュを隅々まで", "全面深入香槟", "샹파뉴를 깊이"],
    "Bordeaux in full depth": ["Bordeaux en profondeur", "Bordeaux in profondità", "Bordeaux im ganzen Detail", "Burdeos en profundidad",
                               "Bordéus em profundidade", "Bordeaux tot in detail", "ボルドーを隅々まで", "全面深入波尔多", "보르도를 깊이"],
    "Champagne · 4 levels": ["Champagne · 4 niveaux", "Champagne · 4 livelli", "Champagne · 4 Ebenen", "Champagne · 4 niveles", "Champagne · 4 níveis",
                             "Champagne · 4 niveaus", "シャンパーニュ · 4つの階層", "香槟 · 4个层级", "샹파뉴 · 4단계"],
    "Bordeaux · 4 levels": ["Bordeaux · 4 niveaux", "Bordeaux · 4 livelli", "Bordeaux · 4 Ebenen", "Burdeos · 4 niveles", "Bordéus · 4 níveis",
                            "Bordeaux · 4 niveaus", "ボルドー · 4つの階層", "波尔多 · 4个层级", "보르도 · 4단계"],
    "Other villages": ["Autres villages", "Altri villaggi", "Andere Dörfer", "Otros pueblos", "Outras aldeias", "Andere dorpen", "その他の村", "其他村庄", "기타 마을"],
    "Vineyard zone": ["Zone viticole", "Zona viticola", "Weinbauzone", "Zona vitícola", "Zona vitícola", "Wijnbouwzone", "ブドウ栽培地区", "葡萄园区", "포도밭 지구"],
    "Classified estate": ["Cru classé", "Cru classificato", "Klassifiziertes Weingut", "Finca clasificada", "Propriedade classificada",
                          "Geklasseerd wijngoed", "格付けシャトー", "列级酒庄", "등급 샤토"],
    "Communal appellation": ["Appellation communale", "Denominazione comunale", "Gemeindeappellation", "Denominación comunal", "Denominação comunal",
                             "Gemeentelijke appellatie", "村名アペラシオン", "村庄级产区", "마을 아펠라시옹"],
    "Sub-regional appellation": ["Appellation sous-régionale", "Denominazione sottoregionale", "Subregionale Appellation", "Denominación subregional",
                                 "Denominação sub-regional", "Subregionale appellatie", "地区アペラシオン", "次产区级产区", "하위 지역 아펠라시옹"],
    "Échelle des crus": ["Échelle des crus"] * 6 + ["エシェル・デ・クリュ", "Échelle des crus（村庄评级）", "에셸 데 크뤼"],
    "Classification": ["Classement", "Classificazione", "Klassifizierung", "Clasificación", "Classificação", "Classificatie", "格付け", "分级", "등급"],
    "Classified estates · {n}": ["Crus classés · {n}", "Cru classificati · {n}", "Klassifizierte Weingüter · {n}", "Fincas clasificadas · {n}",
                                 "Propriedades classificadas · {n}", "Geklasseerde wijngoederen · {n}", "格付けシャトー · {n}", "列级酒庄 · {n}", "등급 샤토 · {n}"],
    "Grand cru village": ["Village grand cru", "Villaggio grand cru", "Grand-Cru-Gemeinde", "Pueblo grand cru", "Aldeia grand cru", "Grand-crudorp",
                          "グラン・クリュの村", "特级园村庄", "그랑 크뤼 마을"],
    "Premier cru village": ["Village premier cru", "Villaggio premier cru", "Premier-Cru-Gemeinde", "Pueblo premier cru", "Aldeia premier cru",
                            "Premier-crudorp", "プルミエ・クリュの村", "一级园村庄", "프르미에 크뤼 마을"],
    "Champagne village": ["Village de Champagne", "Villaggio della Champagne", "Champagner-Gemeinde", "Pueblo de Champagne", "Aldeia de Champagne",
                          "Champagnedorp", "シャンパーニュの村", "香槟村庄", "샹파뉴 마을"],
    "Appellation": ["Appellation", "Denominazione", "Appellation", "Denominación", "Denominação", "Appellatie", "アペラシオン", "产区", "아펠라시옹"],
    "Every Champagne village with its cru rating, in its vineyard zone": [
        "Chaque village de Champagne avec son classement de cru, dans sa zone viticole",
        "Ogni villaggio della Champagne con la sua classe di cru, nella sua zona viticola",
        "Jede Champagner-Gemeinde mit ihrer Cru-Einstufung, in ihrer Weinbauzone",
        "Cada pueblo de Champagne con su categoría de cru, en su zona vitícola",
        "Cada aldeia de Champagne com a sua classificação de cru, na sua zona vitícola",
        "Elk Champagnedorp met zijn cru-klasse, in zijn wijnbouwzone",
        "シャンパーニュのすべての村とそのクリュ格付け、栽培地区ごとに", "香槟每个村庄及其园级，按葡萄园区划分", "샹파뉴의 모든 마을과 크뤼 등급, 포도밭 지구별로"],
    "Every Bordeaux appellation with its hectares, and the classified estates": [
        "Chaque appellation de Bordeaux avec ses hectares, et les crus classés",
        "Ogni denominazione di Bordeaux con i suoi ettari, e i cru classificati",
        "Jede Bordeaux-Appellation mit ihren Hektar, und die klassifizierten Weingüter",
        "Cada denominación de Burdeos con sus hectáreas, y las fincas clasificadas",
        "Cada denominação de Bordéus com os seus hectares, e as propriedades classificadas",
        "Elke Bordeaux-appellatie met haar hectares, en de geklasseerde wijngoederen",
        "ボルドーのすべてのアペラシオンと面積、そして格付けシャトー", "波尔多每个产区及其公顷数，以及列级酒庄", "보르도의 모든 아펠라시옹과 면적, 그리고 등급 샤토"],
    "Every village of the appellation with its cru rating and planted hectares, in its vineyard zone.": [
        "Chaque village de l'appellation avec son classement de cru et ses hectares plantés, dans sa zone viticole.",
        "Ogni villaggio della denominazione con la sua classe di cru e i suoi ettari vitati, nella sua zona viticola.",
        "Jede Gemeinde der Appellation mit ihrer Cru-Einstufung und ihrer Rebfläche, in ihrer Weinbauzone.",
        "Cada pueblo de la denominación con su categoría de cru y sus hectáreas plantadas, en su zona vitícola.",
        "Cada aldeia da denominação com a sua classificação de cru e os seus hectares plantados, na sua zona vitícola.",
        "Elk dorp van de appellatie met zijn cru-klasse en aangeplante hectares, in zijn wijnbouwzone.",
        "アペラシオンのすべての村、そのクリュ格付けと植栽面積を栽培地区ごとに。",
        "产区内每个村庄及其园级和种植面积，按葡萄园区划分。",
        "아펠라시옹의 모든 마을과 크뤼 등급, 재배 면적을 포도밭 지구별로."],
    "Every appellation with its hectares, and the estates of the 1855, Graves and Saint-Émilion classifications.": [
        "Chaque appellation avec ses hectares, et les crus des classements de 1855, des Graves et de Saint-Émilion.",
        "Ogni denominazione con i suoi ettari, e le tenute delle classificazioni del 1855, delle Graves e di Saint-Émilion.",
        "Jede Appellation mit ihren Hektar, und die Weingüter der Klassifizierungen von 1855, der Graves und von Saint-Émilion.",
        "Cada denominación con sus hectáreas, y las fincas de las clasificaciones de 1855, de Graves y de Saint-Émilion.",
        "Cada denominação com os seus hectares, e as propriedades das classificações de 1855, de Graves e de Saint-Émilion.",
        "Elke appellatie met haar hectares, en de wijngoederen van de classificaties van 1855, Graves en Saint-Émilion.",
        "すべてのアペラシオンとその面積、1855年・グラーヴ・サンテミリオン格付けのシャトー。",
        "每个产区及其公顷数，以及1855年、格拉夫和圣埃美隆分级的酒庄。",
        "모든 아펠라시옹과 면적, 1855년·그라브·생테밀리옹 등급의 샤토."],
    "Free preview: Champagne place {n} of {free}. A free account opens all {total}.": [
        "Aperçu gratuit : lieu de Champagne {n} sur {free}. Un compte gratuit ouvre les {total}.",
        "Anteprima gratuita: luogo della Champagne {n} di {free}. Un account gratuito li apre tutti e {total}.",
        "Kostenlose Vorschau: Champagne-Ort {n} von {free}. Ein kostenloses Konto öffnet alle {total}.",
        "Vista previa gratuita: lugar de Champagne {n} de {free}. Una cuenta gratuita abre los {total}.",
        "Pré-visualização gratuita: local de Champagne {n} de {free}. Uma conta gratuita abre os {total}.",
        "Gratis voorproefje: Champagneplaats {n} van {free}. Een gratis account opent ze alle {total}.",
        "無料プレビュー：シャンパーニュの場所 {n}/{free}。無料アカウントで{total}か所すべてが開きます。",
        "免费预览：香槟地点 {n}/{free}。免费账户可打开全部{total}个。",
        "무료 미리보기: 샹파뉴 장소 {n}/{free}. 무료 계정으로 {total}곳 모두 열립니다."],
    "Free preview: Bordeaux place {n} of {free}. A free account opens all {total}.": [
        "Aperçu gratuit : lieu de Bordeaux {n} sur {free}. Un compte gratuit ouvre les {total}.",
        "Anteprima gratuita: luogo di Bordeaux {n} di {free}. Un account gratuito li apre tutti e {total}.",
        "Kostenlose Vorschau: Bordeaux-Ort {n} von {free}. Ein kostenloses Konto öffnet alle {total}.",
        "Vista previa gratuita: lugar de Burdeos {n} de {free}. Una cuenta gratuita abre los {total}.",
        "Pré-visualização gratuita: local de Bordéus {n} de {free}. Uma conta gratuita abre os {total}.",
        "Gratis voorproefje: Bordeauxplaats {n} van {free}. Een gratis account opent ze alle {total}.",
        "無料プレビュー：ボルドーの場所 {n}/{free}。無料アカウントで{total}か所すべてが開きます。",
        "免费预览：波尔多地点 {n}/{free}。免费账户可打开全部{total}个。",
        "무료 미리보기: 보르도 장소 {n}/{free}. 무료 계정으로 {total}곳 모두 열립니다."],
    "You have explored {n} Champagne places for free. A free account opens all {total}: every premier cru and village of every zone, with its cru rating, hectares, terrain, soils and producers.": [
        "Vous avez exploré {n} lieux de Champagne gratuitement. Un compte gratuit ouvre les {total} : chaque premier cru et village de chaque zone, avec son classement de cru, ses hectares, son terrain, ses sols et ses producteurs.",
        "Hai esplorato {n} luoghi della Champagne gratis. Un account gratuito li apre tutti e {total}: ogni premier cru e villaggio di ogni zona, con la sua classe di cru, ettari, terreno, suoli e produttori.",
        "Sie haben {n} Champagne-Orte kostenlos erkundet. Ein kostenloses Konto öffnet alle {total}: jeden Premier Cru und jedes Dorf jeder Zone, mit Cru-Einstufung, Hektar, Gelände, Böden und Produzenten.",
        "Has explorado {n} lugares de Champagne gratis. Una cuenta gratuita abre los {total}: cada premier cru y pueblo de cada zona, con su categoría de cru, hectáreas, terreno, suelos y productores.",
        "Explorou {n} locais de Champagne gratuitamente. Uma conta gratuita abre os {total}: cada premier cru e aldeia de cada zona, com a sua classificação de cru, hectares, terreno, solos e produtores.",
        "Je hebt {n} Champagneplaatsen gratis verkend. Een gratis account opent ze alle {total}: elke premier cru en elk dorp van elke zone, met cru-klasse, hectares, terrein, bodems en producenten.",
        "シャンパーニュの{n}か所を無料で見ました。無料アカウントで{total}か所すべてが開きます：各地区のすべてのプルミエ・クリュと村、そのクリュ格付け、面積、地形、土壌、生産者。",
        "你已免费浏览{n}个香槟地点。免费账户可打开全部{total}个：每个园区的每个一级园和村庄，及其园级、公顷数、地形、土壤和生产商。",
        "샹파뉴 {n}곳을 무료로 둘러보았습니다. 무료 계정으로 {total}곳 모두 열립니다: 모든 지구의 프르미에 크뤼와 마을, 크뤼 등급, 면적, 지형, 토양, 생산자."],
    "You have explored {n} Bordeaux places for free. A free account opens all {total}: every communal appellation and classified estate, with hectares, classifications, terrain, soils and producers.": [
        "Vous avez exploré {n} lieux de Bordeaux gratuitement. Un compte gratuit ouvre les {total} : chaque appellation communale et chaque cru classé, avec hectares, classements, terrain, sols et producteurs.",
        "Hai esplorato {n} luoghi di Bordeaux gratis. Un account gratuito li apre tutti e {total}: ogni denominazione comunale e cru classificato, con ettari, classificazioni, terreno, suoli e produttori.",
        "Sie haben {n} Bordeaux-Orte kostenlos erkundet. Ein kostenloses Konto öffnet alle {total}: jede Gemeindeappellation und jedes klassifizierte Weingut, mit Hektar, Klassifizierungen, Gelände, Böden und Produzenten.",
        "Has explorado {n} lugares de Burdeos gratis. Una cuenta gratuita abre los {total}: cada denominación comunal y finca clasificada, con hectáreas, clasificaciones, terreno, suelos y productores.",
        "Explorou {n} locais de Bordéus gratuitamente. Uma conta gratuita abre os {total}: cada denominação comunal e propriedade classificada, com hectares, classificações, terreno, solos e produtores.",
        "Je hebt {n} Bordeauxplaatsen gratis verkend. Een gratis account opent ze alle {total}: elke gemeentelijke appellatie en elk geklasseerd wijngoed, met hectares, classificaties, terrein, bodems en producenten.",
        "ボルドーの{n}か所を無料で見ました。無料アカウントで{total}か所すべてが開きます：すべての村名アペラシオンと格付けシャトー、面積、格付け、地形、土壌、生産者。",
        "你已免费浏览{n}个波尔多地点。免费账户可打开全部{total}个：每个村庄级产区和列级酒庄，及其公顷数、分级、地形、土壤和生产商。",
        "보르도 {n}곳을 무료로 둘러보았습니다. 무료 계정으로 {total}곳 모두 열립니다: 모든 마을 아펠라시옹과 등급 샤토, 면적, 등급, 지형, 토양, 생산자."],
    "It is free, and it opens Burgundy, Champagne, Bordeaux and Switzerland in full depth.": [
        "C'est gratuit, et cela ouvre la Bourgogne, la Champagne, Bordeaux et la Suisse en profondeur.",
        "È gratuito e apre in profondità Borgogna, Champagne, Bordeaux e Svizzera.",
        "Es ist kostenlos und öffnet Burgund, die Champagne, Bordeaux und die Schweiz im ganzen Detail.",
        "Es gratis y abre en profundidad Borgoña, Champagne, Burdeos y Suiza.",
        "É gratuito e abre em profundidade a Borgonha, a Champagne, Bordéus e a Suíça.",
        "Het is gratis en opent Bourgondië, Champagne, Bordeaux en Zwitserland tot in detail.",
        "無料で、ブルゴーニュ、シャンパーニュ、ボルドー、スイスを隅々まで開きます。",
        "免费，并可深入浏览勃艮第、香槟、波尔多和瑞士。",
        "무료이며 부르고뉴, 샹파뉴, 보르도, 스위스를 깊이 열어 줍니다."],
    "Location of the château. The vines of an estate are often spread over several plots around it.": [
        "Emplacement du château. Les vignes d'un domaine sont souvent réparties en plusieurs parcelles autour de lui.",
        "Posizione dello château. Le vigne di una tenuta sono spesso divise in più appezzamenti intorno.",
        "Lage des Châteaus. Die Reben eines Weinguts liegen oft auf mehreren Parzellen ringsum.",
        "Ubicación del château. Las viñas de una finca suelen repartirse en varias parcelas a su alrededor.",
        "Localização do château. As vinhas de uma propriedade estão muitas vezes repartidas por várias parcelas à volta.",
        "Ligging van het château. De wijngaarden van een wijngoed liggen vaak verspreid over meerdere percelen eromheen.",
        "シャトーの所在地。畑は周辺の複数の区画に分かれていることが多い。",
        "酒庄所在地。酒庄的葡萄园常分散在周围多个地块。",
        "샤토의 위치. 포도밭은 주변 여러 구획에 흩어져 있는 경우가 많다."],
    "Union of the communes of the zone. The vines are only part of it: the vineyard layer of the map shows where they are.": [
        "Union des communes de la zone. Les vignes n'en couvrent qu'une partie : la couche des vignobles de la carte montre où elles sont.",
        "Unione dei comuni della zona. Le vigne ne coprono solo una parte: il livello dei vigneti della mappa mostra dove sono.",
        "Vereinigung der Gemeinden der Zone. Die Reben bedecken nur einen Teil davon: Die Rebflächen-Ebene der Karte zeigt, wo sie stehen.",
        "Unión de los municipios de la zona. Las viñas solo cubren una parte: la capa de viñedos del mapa muestra dónde están.",
        "União das comunas da zona. As vinhas cobrem apenas uma parte: a camada de vinhas do mapa mostra onde estão.",
        "Samenvoeging van de gemeenten van de zone. De wijnstokken beslaan maar een deel: de wijngaardlaag van de kaart toont waar ze staan.",
        "地区内のコミューンを合わせた範囲。ブドウ畑はその一部だけで、地図のブドウ畑レイヤーで場所がわかる。",
        "该区各市镇的合并范围。葡萄园只占其中一部分：地图的葡萄园图层显示其位置。",
        "지구 내 코뮌을 합친 범위. 포도밭은 그 일부일 뿐이며 지도의 포도밭 레이어에서 위치를 볼 수 있다."],
    "Estates without a link are listed but not on the map yet: their location is still to be checked.": [
        "Les domaines sans lien sont listés mais pas encore sur la carte : leur emplacement reste à vérifier.",
        "Le tenute senza link sono elencate ma non ancora sulla mappa: la loro posizione è da verificare.",
        "Weingüter ohne Link sind aufgeführt, aber noch nicht auf der Karte: Ihre Lage wird noch geprüft.",
        "Las fincas sin enlace aparecen en la lista pero aún no en el mapa: su ubicación está por comprobar.",
        "As propriedades sem ligação estão listadas mas ainda não no mapa: a sua localização ainda tem de ser verificada.",
        "Wijngoederen zonder link staan in de lijst maar nog niet op de kaart: hun ligging moet nog worden gecontroleerd.",
        "リンクのないシャトーは一覧にあるが、所在地の確認中のため地図にはまだない。",
        "无链接的酒庄已列出，但尚未标在地图上：其位置仍待核实。",
        "링크가 없는 샤토는 목록에는 있지만 위치 확인 중이라 아직 지도에 없다."],

}


def main():
    for i, lang in enumerate(LANGS):
        path = os.path.join(I18N, lang + ".json")
        d = json.load(open(path, encoding="utf-8"))
        n = 0
        for k, v in T.items():
            assert len(v) == len(LANGS), k
            if k not in d:
                d[k] = v[i]
                n += 1
        json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"  {lang}: +{n}")


if __name__ == "__main__":
    main()
