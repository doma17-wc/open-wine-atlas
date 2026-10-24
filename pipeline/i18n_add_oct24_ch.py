"""One-off: translations for the Swiss wine areas of 24 October 2026 (pipeline/ch_regions.py).

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
