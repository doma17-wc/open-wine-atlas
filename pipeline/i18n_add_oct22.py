"""One-off: translations for the study levels and the independence note added on 22 October 2026.

Merges into web/i18n/<lang>.json without touching existing entries. Safe to rerun.
Order of each list: fr, it, de, es, pt, nl, ja, zh, ko.
"""
import json
import os

I18N = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "i18n")
LANGS = ["fr", "it", "de", "es", "pt", "nl", "ja", "zh", "ko"]

T = {
    "Intermediate": ["Intermédiaire", "Intermedio", "Mittelstufe", "Intermedio", "Intermédio", "Gevorderd", "中級", "中级", "중급"],
    "Advanced": ["Avancé", "Avanzato", "Fortgeschritten", "Avanzado", "Avançado", "Expert", "上級", "高级", "고급"],
    "The levels are our own. As a guide, Intermediate suits students between WSET Level 2 and 3, Advanced suits Level 3 to Diploma. Open Wine Atlas is independent and is not affiliated with or endorsed by WSET, the Court of Master Sommeliers or the Institute of Masters of Wine.": [
        "Ces niveaux sont les nôtres. À titre indicatif, Intermédiaire convient entre le WSET Level 2 et 3, Avancé du Level 3 au Diploma. Open Wine Atlas est indépendant, sans lien avec le WSET, la Court of Master Sommeliers ou l'Institute of Masters of Wine, ni approuvé par eux.",
        "I livelli sono nostri. Come riferimento, Intermedio va bene tra WSET Level 2 e 3, Avanzato dal Level 3 al Diploma. Open Wine Atlas è indipendente e non è affiliato né approvato da WSET, Court of Master Sommeliers o Institute of Masters of Wine.",
        "Die Stufen sind unsere eigenen. Als Orientierung: Mittelstufe passt zwischen WSET Level 2 und 3, Fortgeschritten zu Level 3 bis Diploma. Open Wine Atlas ist unabhängig und weder mit WSET, dem Court of Master Sommeliers noch dem Institute of Masters of Wine verbunden oder von ihnen anerkannt.",
        "Los niveles son nuestros. Como guía, Intermedio encaja entre WSET Level 2 y 3, Avanzado del Level 3 al Diploma. Open Wine Atlas es independiente y no está afiliado ni avalado por WSET, la Court of Master Sommeliers ni el Institute of Masters of Wine.",
        "Os níveis são nossos. Como referência, Intermédio serve entre o WSET Level 2 e 3, Avançado do Level 3 ao Diploma. O Open Wine Atlas é independente e não é afiliado nem aprovado pelo WSET, pela Court of Master Sommeliers ou pelo Institute of Masters of Wine.",
        "De niveaus zijn van ons. Als richtlijn: Gevorderd past tussen WSET Level 2 en 3, Expert bij Level 3 tot Diploma. Open Wine Atlas is onafhankelijk en niet verbonden aan of goedgekeurd door WSET, de Court of Master Sommeliers of het Institute of Masters of Wine.",
        "レベルは当アトラス独自のものです。目安として、中級は WSET Level 2〜3、上級は Level 3〜Diploma の学習者向けです。Open Wine Atlas は独立しており、WSET、Court of Master Sommeliers、Institute of Masters of Wine とは提携しておらず、承認も受けていません。",
        "这些级别是我们自己设定的。作为参考，中级适合 WSET Level 2 到 3 的学员，高级适合 Level 3 到 Diploma。Open Wine Atlas 是独立的，与 WSET、Court of Master Sommeliers 或 Institute of Masters of Wine 没有关联，也未获其认可。",
        "레벨은 자체 기준입니다. 참고로 중급은 WSET Level 2~3, 고급은 Level 3~Diploma 학습자에게 맞습니다. Open Wine Atlas는 독립적이며 WSET, Court of Master Sommeliers, Institute of Masters of Wine과 제휴하거나 승인받지 않았습니다."],
}

def main():
    for i, lang in enumerate(LANGS):
        path = os.path.join(I18N, lang + ".json")
        d = json.load(open(path, encoding="utf-8"))
        for en, tr in T.items():
            assert len(tr) == len(LANGS), en
            d.setdefault(en, tr[i])
        json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("added", len(T), "texts to", len(LANGS), "languages")


if __name__ == "__main__":
    main()
