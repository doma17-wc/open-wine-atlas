"""One-off: translations for the texts of 21 October 2026 (one path for Founding Members, payment soon).

Merges into web/i18n/<lang>.json without touching existing entries. Safe to rerun.
"""
import json
import os

I18N = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "i18n")
LANGS = ["fr", "it", "de", "es", "pt", "nl", "ja", "zh", "ko"]

T = {
    "Membership opens soon: reserve a Founding spot now, nothing to pay until then.": [
        "L'adhésion ouvre bientôt : réservez une place Founding maintenant, rien à payer d'ici là.",
        "L'abbonamento apre a breve: prenota ora un posto Founding, nulla da pagare fino ad allora.",
        "Die Mitgliedschaft startet bald: Reservieren Sie jetzt einen Founding-Platz, bis dahin zahlen Sie nichts.",
        "La membresía abre pronto: reserva ya una plaza Founding, nada que pagar hasta entonces.",
        "A adesão abre em breve: reserve já um lugar Founding, nada a pagar até lá.",
        "Het lidmaatschap opent binnenkort: reserveer nu een Founding-plek, tot dan niets te betalen.",
        "メンバーシップはまもなく開始します。今すぐFoundingの枠を予約できます。それまでお支払いはありません。",
        "会员即将开放：现在预留创始席位，届时之前无需付款。",
        "멤버십이 곧 열립니다. 지금 Founding 자리를 예약하세요. 그때까지 결제는 없습니다."],
    "Reserve my Founding spot": ["Réserver ma place Founding", "Prenota il mio posto Founding", "Meinen Founding-Platz reservieren",
                                 "Reservar mi plaza Founding", "Reservar o meu lugar Founding", "Mijn Founding-plek reserveren",
                                 "Foundingの枠を予約", "预留我的创始席位", "내 Founding 자리 예약"],
    "Membership opens soon. The first 1,000 members get a full year for CHF 19, nothing to pay now.": [
        "L'adhésion ouvre bientôt. Les 1 000 premiers membres ont une année complète pour CHF 19, rien à payer maintenant.",
        "L'abbonamento apre a breve. I primi 1.000 membri hanno un anno intero a CHF 19, nulla da pagare ora.",
        "Die Mitgliedschaft startet bald. Die ersten 1'000 Mitglieder erhalten ein ganzes Jahr für CHF 19, jetzt nichts zu zahlen.",
        "La membresía abre pronto. Los primeros 1.000 miembros tienen un año completo por CHF 19, nada que pagar ahora.",
        "A adesão abre em breve. Os primeiros 1000 membros têm um ano inteiro por CHF 19, nada a pagar agora.",
        "Het lidmaatschap opent binnenkort. De eerste 1.000 leden krijgen een volledig jaar voor CHF 19, nu niets te betalen.",
        "メンバーシップはまもなく開始。先着1,000名は1年間CHF 19。今はお支払い不要です。",
        "会员即将开放。前1000名会员首年仅需CHF 19，现在无需付款。",
        "멤버십이 곧 열립니다. 선착순 1,000명은 1년에 CHF 19, 지금은 결제가 없습니다."],
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
