"""One-off: translations for the Swiss wine areas and the Swiss Deep Region of 24 October 2026 (pipeline/ch_regions.py).

Merges into web/i18n/<lang>.json without touching existing entries. Safe to rerun.
Order of each list: fr, it, de, es, pt, nl, ja, zh, ko.
"""
import json
import os

I18N = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "i18n")
LANGS = ["fr", "it", "de", "es", "pt", "nl", "ja", "zh", "ko"]

T = {
    "Grapes planted": ["Cépages plantés", "Vitigni piantati", "Angebaute Rebsorten", "Variedades plantadas", "Castas plantadas",
                       "Aangeplante druiven", "植えられているブドウ品種", "种植的葡萄品种", "재배 품종"],
    "Growers": ["Viticulteurs", "Viticoltori", "Winzer", "Viticultores", "Viticultores", "Wijnboeren", "栽培者", "种植者", "재배자"],
    "On the label": ["Sur l'étiquette", "In etichetta", "Auf dem Etikett", "En la etiqueta", "No rótulo", "Op het etiket", "ラベル表示", "酒标标注", "라벨 표기"],
    "Known producers": ["Producteurs connus", "Produttori noti", "Bekannte Produzenten", "Productores conocidos", "Produtores conhecidos",
                        "Bekende producenten", "主な生産者", "知名生产商", "주요 생산자"],
    "Premier grand cru": ["Premier grand cru"] * 9,
    "Premiers crus · {n}": ["Premiers crus · {n}", "Premiers crus · {n}", "Premiers crus · {n}", "Premiers crus · {n}", "Premiers crus · {n}",
                            "Premiers crus · {n}", "プルミエ・クリュ · {n}", "一级园 · {n}", "프르미에 크뤼 · {n}"],
    "Wine area": ["Région viticole", "Zona vinicola", "Weinbaugebiet", "Zona vitícola", "Zona vitícola", "Wijngebied", "ワイン産地", "葡萄酒产区", "와인 산지"],
    "Traditional wine district": ["District viticole traditionnel", "Distretto vinicolo tradizionale", "Traditionelles Weinbaugebiet",
                                  "Distrito vitícola tradicional", "Distrito vitícola tradicional", "Traditioneel wijndistrict",
                                  "伝統的なワイン地区", "传统葡萄酒区", "전통 와인 지구"],
    "Commune designation": ["Mention communale", "Menzione comunale", "Gemeindebezeichnung", "Mención municipal", "Menção comunal",
                            "Gemeentevermelding", "村名表示", "村庄名称", "마을 명칭"],
    "Commune": ["Commune", "Comune", "Gemeinde", "Municipio", "Comuna", "Gemeente", "村", "市镇", "코뮌"],
    "Regional AOC": ["AOC régionale", "AOC regionale", "Regionale AOC", "AOC regional", "AOC regional", "Regionale AOC", "地域AOC", "区域AOC", "지역 AOC"],
    "Grand cru appellation": ["Appellation grand cru", "Denominazione grand cru", "Grand-Cru-Appellation", "Denominación grand cru",
                              "Denominação grand cru", "Grand-cru-appellation", "グラン・クリュのアペラシオン", "特级园产区", "그랑 크뤼 아펠라시옹"],
    "Lieu de production": ["Lieu de production", "Luogo di produzione", "Produktionsort", "Lugar de producción", "Local de produção",
                           "Productieplaats", "生産地区（リュー・ド・プロデュクシオン）", "产地（lieu de production）", "생산지(리외 드 프로뒥시옹)"],
    "Switzerland in depth": ["La Suisse en profondeur", "Svizzera in profondità", "Die Schweiz im Detail", "Suiza en profundidad", "Suíça em profundidade",
                             "Zwitserland in detail", "スイスを深く", "深入瑞士", "스위스 깊이 보기"],
    "Switzerland in full depth": ["La Suisse en profondeur", "La Svizzera in profondità", "Die Schweiz im ganzen Detail", "Suiza en profundidad",
                                  "A Suíça em profundidade", "Zwitserland tot in detail", "スイスを隅々まで", "全面深入瑞士", "스위스를 깊이"],
    "Switzerland · 4 levels": ["Suisse · 4 niveaux", "Svizzera · 4 livelli", "Schweiz · 4 Ebenen", "Suiza · 4 niveles", "Suíça · 4 níveis",
                               "Zwitserland · 4 niveaus", "スイス · 4つの階層", "瑞士 · 4个层级", "스위스 · 4단계"],
    "Regional AOC and wine area": ["AOC régionale et région viticole", "AOC regionale e zona vinicola", "Regionale AOC und Weinbaugebiet",
                                   "AOC regional y zona vitícola", "AOC regional e zona vitícola", "Regionale AOC en wijngebied",
                                   "地域AOCとワイン産地", "区域AOC与产区", "지역 AOC와 와인 산지"],
    "Cantonal AOC": ["AOC cantonale", "AOC cantonale", "Kantonale AOC", "AOC cantonal", "AOC cantonal", "Kantonale AOC", "州のAOC", "州级AOC", "칸톤 AOC"],
    "Every Swiss wine area, commune and grand cru, with its planted hectares": [
        "Chaque région viticole, commune et grand cru de Suisse, avec ses hectares de vigne",
        "Ogni zona vinicola, comune e grand cru della Svizzera, con i suoi ettari vitati",
        "Jedes Weinbaugebiet, jede Gemeinde und jeder Grand Cru der Schweiz, mit der Rebfläche",
        "Cada zona vitícola, municipio y grand cru de Suiza, con sus hectáreas de viñedo",
        "Cada zona vitícola, comuna e grand cru da Suíça, com os seus hectares de vinha",
        "Elk wijngebied, elke gemeente en grand cru van Zwitserland, met de hectares wijngaard",
        "スイスのすべてのワイン産地、村、グラン・クリュとその栽培面積", "瑞士每个产区、市镇和特级园及其种植面积", "스위스의 모든 와인 산지, 마을, 그랑 크뤼와 재배 면적"],
    "Every canton, regional AOC, wine area, commune and grand cru, with its planted hectares.": [
        "Chaque canton, AOC régionale, région viticole, commune et grand cru, avec ses hectares de vigne.",
        "Ogni cantone, AOC regionale, zona vinicola, comune e grand cru, con i suoi ettari vitati.",
        "Jeder Kanton, jede regionale AOC, jedes Weinbaugebiet, jede Gemeinde und jeder Grand Cru, mit der Rebfläche.",
        "Cada cantón, AOC regional, zona vitícola, municipio y grand cru, con sus hectáreas de viñedo.",
        "Cada cantão, AOC regional, zona vitícola, comuna e grand cru, com os seus hectares de vinha.",
        "Elk kanton, elke regionale AOC, elk wijngebied, elke gemeente en grand cru, met de hectares wijngaard.",
        "すべての州、地域AOC、ワイン産地、村、グラン・クリュとその栽培面積。", "每个州、区域AOC、产区、市镇和特级园及其种植面积。",
        "모든 칸톤, 지역 AOC, 와인 산지, 마을, 그랑 크뤼와 재배 면적."],
    "Free preview: Swiss place {n} of {free}. A free account opens all {total}.": [
        "Aperçu gratuit : lieu suisse {n} sur {free}. Un compte gratuit les ouvre tous les {total}.",
        "Anteprima gratuita: luogo svizzero {n} di {free}. Un account gratuito li apre tutti e {total}.",
        "Kostenlose Vorschau: Schweizer Ort {n} von {free}. Ein kostenloses Konto öffnet alle {total}.",
        "Vista previa gratuita: lugar suizo {n} de {free}. Una cuenta gratuita abre los {total}.",
        "Pré-visualização gratuita: local suíço {n} de {free}. Uma conta gratuita abre todos os {total}.",
        "Gratis voorproef: Zwitserse plaats {n} van {free}. Een gratis account opent alle {total}.",
        "無料プレビュー：スイスの場所 {n} / {free}。無料アカウントで全{total}か所が開きます。",
        "免费预览：瑞士地点 {n} / {free}。免费账户可打开全部 {total} 个。",
        "무료 미리보기: 스위스 장소 {n} / {free}. 무료 계정으로 {total}곳 모두 열립니다."],
    "You have explored {n} Swiss places for free. A free account opens all {total}: every regional AOC, wine area, commune and lieu de production, with planted hectares, grapes, label rules and producers.": [
        "Vous avez exploré {n} lieux suisses gratuitement. Un compte gratuit les ouvre tous les {total} : chaque AOC régionale, région viticole, commune et lieu de production, avec les hectares de vigne, les cépages, les règles d'étiquetage et les producteurs.",
        "Hai esplorato {n} luoghi svizzeri gratis. Un account gratuito li apre tutti e {total}: ogni AOC regionale, zona vinicola, comune e lieu de production, con ettari vitati, vitigni, regole di etichetta e produttori.",
        "Sie haben {n} Schweizer Orte kostenlos erkundet. Ein kostenloses Konto öffnet alle {total}: jede regionale AOC, jedes Weinbaugebiet, jede Gemeinde und jeden Lieu de production, mit Rebfläche, Sorten, Etikettenregeln und Produzenten.",
        "Has explorado {n} lugares suizos gratis. Una cuenta gratuita abre los {total}: cada AOC regional, zona vitícola, municipio y lieu de production, con hectáreas, variedades, reglas de etiqueta y productores.",
        "Explorou {n} locais suíços gratuitamente. Uma conta gratuita abre todos os {total}: cada AOC regional, zona vitícola, comuna e lieu de production, com hectares, castas, regras de rotulagem e produtores.",
        "Je hebt {n} Zwitserse plaatsen gratis verkend. Een gratis account opent alle {total}: elke regionale AOC, elk wijngebied, elke gemeente en lieu de production, met hectares, druiven, etiketregels en producenten.",
        "スイスの場所を{n}か所無料で見ました。無料アカウントで全{total}か所が開きます：すべての地域AOC、ワイン産地、村、生産地区を、栽培面積、品種、ラベル規則、生産者とともに。",
        "您已免费浏览 {n} 个瑞士地点。免费账户可打开全部 {total} 个：每个区域AOC、产区、市镇和产地，附种植面积、葡萄品种、酒标规则和生产商。",
        "스위스 장소 {n}곳을 무료로 둘러보았습니다. 무료 계정으로 {total}곳 모두 열립니다: 모든 지역 AOC, 와인 산지, 마을, 생산지를 재배 면적, 품종, 라벨 규정, 생산자와 함께."],
    "It is free, and it opens Burgundy and Switzerland in full depth.": [
        "C'est gratuit, et cela ouvre la Bourgogne et la Suisse en profondeur.",
        "È gratuito e apre la Borgogna e la Svizzera in profondità.",
        "Es ist kostenlos und öffnet Burgund und die Schweiz im ganzen Detail.",
        "Es gratis y abre Borgoña y Suiza en profundidad.",
        "É gratuito e abre a Borgonha e a Suíça em profundidade.",
        "Het is gratis en opent Bourgondië en Zwitserland tot in detail.",
        "無料で、ブルゴーニュとスイスを隅々まで開きます。", "免费，并可深入浏览勃艮第和瑞士。", "무료이며 부르고뉴와 스위스를 깊이 열어 줍니다."],
}


def main():
    for i, lang in enumerate(LANGS):
        path = os.path.join(I18N, lang + ".json")
        d = json.load(open(path, encoding="utf-8"))
        n = 0
        for k, v in T.items():
            if k not in d:
                d[k] = v[i]
                n += 1
        json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"  {lang}: +{n}")


if __name__ == "__main__":
    main()
