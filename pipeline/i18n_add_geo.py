"""One-off: translations for the geography layer added on 14 October 2026 (rivers, lakes, mountains, towns).

Merges into web/i18n/<lang>.json without touching existing entries. Safe to rerun.
"""
import json
import os

I18N = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "i18n")
LANGS = ["fr", "it", "de", "es", "pt", "nl", "ja", "zh", "ko"]

T = {
    "River": ["Rivière", "Fiume", "Fluss", "Río", "Rio", "Rivier", "川", "河流", "강"],
    "Lake": ["Lac", "Lago", "See", "Lago", "Lago", "Meer", "湖", "湖泊", "호수"],
    "Peak": ["Sommet", "Vetta", "Gipfel", "Cumbre", "Pico", "Top", "山頂", "山峰", "봉우리"],
    "Mountain range": ["Massif", "Catena montuosa", "Gebirge", "Cordillera", "Cordilheira", "Gebergte", "山脈", "山脉", "산맥"],
    "Plateau": ["Plateau", "Altopiano", "Hochebene", "Meseta", "Planalto", "Plateau", "高原", "高原", "고원"],
    "Valley": ["Vallée", "Valle", "Tal", "Valle", "Vale", "Dal", "谷", "山谷", "계곡"],
    "Rivers and lakes": ["Rivières et lacs", "Fiumi e laghi", "Flüsse und Seen", "Ríos y lagos", "Rios e lagos", "Rivieren en meren",
                         "川と湖", "河流和湖泊", "강과 호수"],
    "Mountains and peaks": ["Massifs et sommets", "Montagne e vette", "Gebirge und Gipfel", "Montañas y cumbres", "Montanhas e picos",
                            "Gebergten en toppen", "山脈と山頂", "山脉和山峰", "산맥과 봉우리"],
    "Towns and villages": ["Villes et villages", "Città e paesi", "Städte und Dörfer", "Ciudades y pueblos", "Cidades e aldeias",
                           "Steden en dorpen", "町と村", "城镇和村庄", "도시와 마을"],
    "Towns and cities": ["Villes", "Città", "Städte", "Ciudades", "Cidades", "Steden", "都市と町", "城镇", "도시"],
    "Remove the highlight": ["Retirer la mise en évidence", "Togli l'evidenziazione", "Hervorhebung entfernen", "Quitar el resaltado",
                             "Retirar o destaque", "Markering verwijderen", "ハイライトを解除", "取消高亮", "강조 해제"],
    "Show all of it": ["Tout afficher", "Mostra tutto", "Ganz zeigen", "Verlo entero", "Ver tudo", "Helemaal tonen", "全体を表示", "显示全部", "전체 보기"],
    "Show it on the map": ["Afficher sur la carte", "Mostra sulla mappa", "Auf der Karte zeigen", "Verlo en el mapa", "Ver no mapa",
                           "Op de kaart tonen", "地図で表示", "在地图上显示", "지도에서 보기"],
    "Rivers, lakes, mountain ranges and peaks": ["Rivières, lacs, massifs et sommets", "Fiumi, laghi, catene montuose e vette",
                                                 "Flüsse, Seen, Gebirge und Gipfel", "Ríos, lagos, cordilleras y cumbres",
                                                 "Rios, lagos, cordilheiras e picos", "Rivieren, meren, gebergten en toppen",
                                                 "川、湖、山脈、山頂", "河流、湖泊、山脉和山峰", "강, 호수, 산맥, 봉우리"],
    "Close up: small rivers, streams, villages and peaks": ["De près : petites rivières, ruisseaux, villages et sommets",
                                                           "Da vicino: piccoli fiumi, torrenti, paesi e vette",
                                                           "Aus der Nähe: kleine Flüsse, Bäche, Dörfer und Gipfel",
                                                           "De cerca: ríos pequeños, arroyos, pueblos y cumbres",
                                                           "De perto: pequenos rios, ribeiros, aldeias e picos",
                                                           "Van dichtbij: kleine rivieren, beken, dorpen en toppen",
                                                           "拡大時：小さな川、小川、村、山頂", "放大后：小河、溪流、村庄和山峰",
                                                           "확대 시: 작은 강, 개울, 마을, 봉우리"],
}


def main():
    for i, lang in enumerate(LANGS):
        path = os.path.join(I18N, lang + ".json")
        d = json.load(open(path, encoding="utf-8"))
        added = 0
        for k, v in T.items():
            if k not in d:
                d[k] = v[i]
                added += 1
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        print(lang, "added", added)


if __name__ == "__main__":
    main()
