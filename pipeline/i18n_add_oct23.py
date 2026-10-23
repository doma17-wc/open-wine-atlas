"""One-off: translations for the Burgundy Deep Region (wall, map key) and the free Founding texts added on 23 October 2026.

Merges into web/i18n/<lang>.json without touching existing entries. Safe to rerun.
Order of each list: fr, it, de, es, pt, nl, ja, zh, ko.
"""
import json
import os

I18N = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "i18n")
LANGS = ["fr", "it", "de", "es", "pt", "nl", "ja", "zh", "ko"]

T = {
    "Deep Region": ["Région en profondeur", "Regione in profondità", "Region im Detail", "Región en profundidad", "Região em profundidade",
                    "Regio in detail", "ディープ・リージョン", "深度产区", "딥 리전"],
    "Burgundy in full depth": ["La Bourgogne en profondeur", "La Borgogna in profondità", "Burgund bis ins Detail", "Borgoña en profundidad",
                               "A Borgonha em profundidade", "Bourgogne tot in detail", "ブルゴーニュを隅々まで", "深入勃艮第", "부르고뉴를 깊이 있게"],
    "Free preview: Burgundy place {n} of {free}. A free account opens all {total}.": [
        "Aperçu gratuit : lieu de Bourgogne {n} sur {free}. Un compte gratuit ouvre les {total}.",
        "Anteprima gratuita: luogo della Borgogna {n} di {free}. Un account gratuito li apre tutti e {total}.",
        "Kostenlose Vorschau: Burgund-Ort {n} von {free}. Ein kostenloses Konto öffnet alle {total}.",
        "Vista previa gratuita: lugar de Borgoña {n} de {free}. Una cuenta gratuita abre los {total}.",
        "Pré-visualização gratuita: lugar da Borgonha {n} de {free}. Uma conta gratuita abre os {total}.",
        "Gratis voorproefje: Bourgogne-plek {n} van {free}. Een gratis account opent ze alle {total}.",
        "無料プレビュー：ブルゴーニュの {free} か所中 {n} か所目。無料アカウントで {total} か所すべてが開きます。",
        "免费预览：勃艮第地点 {n}/{free}。免费账户可打开全部 {total} 个。",
        "무료 미리보기: 부르고뉴 장소 {free}곳 중 {n}번째. 무료 계정으로 {total}곳 모두 열립니다."],
    "You have explored {n} Burgundy places for free. A free account opens all {total}: every village, premier cru and climat, with terrain, soils, rules and producers.": [
        "Vous avez exploré {n} lieux de Bourgogne gratuitement. Un compte gratuit ouvre les {total} : chaque village, premier cru et climat, avec relief, sols, règles et producteurs.",
        "Hai esplorato {n} luoghi della Borgogna gratis. Un account gratuito li apre tutti e {total}: ogni villaggio, premier cru e climat, con rilievo, suoli, disciplinari e produttori.",
        "Du hast {n} Burgund-Orte kostenlos entdeckt. Ein kostenloses Konto öffnet alle {total}: jedes Dorf, jeden Premier cru und jeden Climat, mit Gelände, Böden, Regeln und Erzeugern.",
        "Has explorado {n} lugares de Borgoña gratis. Una cuenta gratuita abre los {total}: cada pueblo, premier cru y climat, con relieve, suelos, normas y productores.",
        "Explorou {n} lugares da Borgonha gratuitamente. Uma conta gratuita abre os {total}: cada aldeia, premier cru e climat, com relevo, solos, regras e produtores.",
        "Je hebt {n} Bourgogne-plekken gratis verkend. Een gratis account opent ze alle {total}: elk dorp, elke premier cru en climat, met reliëf, bodems, regels en producenten.",
        "ブルゴーニュの {n} か所を無料で見ました。無料アカウントで {total} か所すべてが開きます。すべての村、プルミエ・クリュ、クリマを地形、土壌、規定、生産者とともに。",
        "你已免费浏览了 {n} 个勃艮第地点。免费账户可打开全部 {total} 个：每个村庄、一级园和 climat，附带地形、土壤、法规和生产者。",
        "부르고뉴 {n}곳을 무료로 둘러보셨습니다. 무료 계정으로 {total}곳 모두 열립니다. 모든 마을, 프르미에 크뤼, 클리마를 지형, 토양, 규정, 생산자와 함께."],
    "Create my free account": ["Créer mon compte gratuit", "Crea il mio account gratuito", "Mein kostenloses Konto erstellen", "Crear mi cuenta gratuita",
                               "Criar a minha conta gratuita", "Mijn gratis account maken", "無料アカウントを作成", "创建我的免费账户", "무료 계정 만들기"],
    "I already have an account": ["J'ai déjà un compte", "Ho già un account", "Ich habe schon ein Konto", "Ya tengo una cuenta", "Já tenho uma conta",
                                  "Ik heb al een account", "アカウントをお持ちの方", "我已有账户", "이미 계정이 있어요"],
    "No card, no password: we email you a code. Grand crus stay open for everyone.": [
        "Sans carte, sans mot de passe : nous vous envoyons un code par e-mail. Les grands crus restent ouverts à tous.",
        "Niente carta, niente password: ti mandiamo un codice via email. I grand cru restano aperti a tutti.",
        "Keine Karte, kein Passwort: Wir schicken dir einen Code per E-Mail. Die Grands crus bleiben für alle offen.",
        "Sin tarjeta ni contraseña: te enviamos un código por email. Los grand crus siguen abiertos para todos.",
        "Sem cartão nem palavra-passe: enviamos-lhe um código por email. Os grand crus continuam abertos a todos.",
        "Geen kaart, geen wachtwoord: we mailen je een code. De grands crus blijven voor iedereen open.",
        "カードもパスワードも不要。コードをメールでお送りします。グラン・クリュは誰でも見られます。",
        "无需银行卡，无需密码：我们会通过邮件发送验证码。特级园对所有人开放。",
        "카드도 비밀번호도 필요 없습니다. 이메일로 코드를 보내드립니다. 그랑 크뤼는 누구에게나 열려 있습니다."],
    "It is free, and it opens Burgundy in full depth.": [
        "C'est gratuit, et cela ouvre la Bourgogne en profondeur.",
        "È gratuito e apre la Borgogna in profondità.",
        "Es ist kostenlos und öffnet Burgund bis ins Detail.",
        "Es gratis y abre Borgoña en profundidad.",
        "É gratuito e abre a Borgonha em profundidade.",
        "Het is gratis en opent Bourgogne tot in detail.",
        "無料で、ブルゴーニュを隅々まで開きます。",
        "完全免费，并可深入浏览勃艮第。",
        "무료이며 부르고뉴를 깊이 있게 열어 줍니다."],
    "Free for the first 1,000: a numbered Founding badge and first access to every new tool.": [
        "Gratuit pour les 1 000 premiers : un badge Founding numéroté et un accès en avant-première à chaque nouvel outil.",
        "Gratis per i primi 1.000: un badge Founding numerato e accesso in anteprima a ogni nuovo strumento.",
        "Kostenlos für die ersten 1'000: ein nummeriertes Founding-Abzeichen und als Erste Zugang zu jedem neuen Werkzeug.",
        "Gratis para los 1.000 primeros: una insignia Founding numerada y acceso anticipado a cada nueva herramienta.",
        "Gratuito para os primeiros 1000: um distintivo Founding numerado e acesso antecipado a cada nova ferramenta.",
        "Gratis voor de eerste 1.000: een genummerde Founding-badge en als eerste toegang tot elke nieuwe tool.",
        "先着1,000名は無料：番号入りの Founding バッジと、新しいツールすべてへの先行アクセス。",
        "前 1000 名免费：带编号的 Founding 徽章，并抢先使用每一项新工具。",
        "선착순 1,000명 무료: 번호가 새겨진 Founding 배지와 모든 새 도구의 우선 이용."],
    "Free for the first 1,000. Reserve your spot with this account: a numbered Founding badge and first access to every new tool. We email you about them, and you can leave the list at any time.": [
        "Gratuit pour les 1 000 premiers. Réservez votre place avec ce compte : un badge Founding numéroté et un accès en avant-première à chaque nouvel outil. Nous vous écrivons à leur sujet, et vous pouvez quitter la liste à tout moment.",
        "Gratis per i primi 1.000. Prenota il tuo posto con questo account: un badge Founding numerato e accesso in anteprima a ogni nuovo strumento. Ti scriviamo quando arrivano, e puoi lasciare la lista quando vuoi.",
        "Kostenlos für die ersten 1'000. Reserviere deinen Platz mit diesem Konto: ein nummeriertes Founding-Abzeichen und als Erste Zugang zu jedem neuen Werkzeug. Wir schreiben dir dazu, und du kannst die Liste jederzeit verlassen.",
        "Gratis para los 1.000 primeros. Reserva tu plaza con esta cuenta: una insignia Founding numerada y acceso anticipado a cada nueva herramienta. Te escribimos sobre ellas, y puedes dejar la lista cuando quieras.",
        "Gratuito para os primeiros 1000. Reserve o seu lugar com esta conta: um distintivo Founding numerado e acesso antecipado a cada nova ferramenta. Escrevemos-lhe sobre elas, e pode sair da lista a qualquer momento.",
        "Gratis voor de eerste 1.000. Reserveer je plek met dit account: een genummerde Founding-badge en als eerste toegang tot elke nieuwe tool. We mailen je erover, en je kunt de lijst altijd verlaten.",
        "先着1,000名は無料。このアカウントで枠を予約：番号入りの Founding バッジと、新しいツールすべてへの先行アクセス。新機能のお知らせをメールでお送りします。リストはいつでも解除できます。",
        "前 1000 名免费。用此账户预留名额：带编号的 Founding 徽章，并抢先使用每一项新工具。我们会就此给你发邮件，你可以随时退出名单。",
        "선착순 1,000명 무료. 이 계정으로 자리를 예약하세요. 번호가 새겨진 Founding 배지와 모든 새 도구의 우선 이용. 새 소식은 이메일로 알려 드리며, 언제든 목록에서 나갈 수 있습니다."],
    "Village": ["Village", "Villaggio", "Village", "Village", "Village", "Village", "村名", "村庄级", "빌라주"],
    "Regional": ["Régional", "Regionale", "Regional", "Regional", "Regional", "Regionaal", "地方名", "大区级", "지역"],
    "Bourgogne · 4 levels": ["Bourgogne · 4 niveaux", "Bourgogne · 4 livelli", "Bourgogne · 4 Stufen", "Bourgogne · 4 niveles", "Bourgogne · 4 níveis",
                             "Bourgogne · 4 niveaus", "Bourgogne · 4つの格付け", "Bourgogne · 4 个等级", "Bourgogne · 4단계"],
    "Burgundy levels": ["Niveaux de la Bourgogne", "Livelli della Borgogna", "Stufen des Burgund", "Niveles de Borgoña", "Níveis da Borgonha",
                        "Niveaus van Bourgogne", "ブルゴーニュの格付け", "勃艮第等级", "부르고뉴 등급"],
    "Founding Members hear first when the full study opens. Reserve your free spot.": [
        "Les Founding Members sont les premiers informés quand l'étude complète ouvre. Réservez votre place gratuite.",
        "I Founding Member sono i primi a sapere quando apre lo studio completo. Prenota il tuo posto gratuito.",
        "Founding Members erfahren als Erste, wenn das ganze Lernen öffnet. Reserviere deinen kostenlosen Platz.",
        "Los Founding Members se enteran primero cuando abre el estudio completo. Reserva tu plaza gratuita.",
        "Os Founding Members são os primeiros a saber quando o estudo completo abre. Reserve o seu lugar gratuito.",
        "Founding Members horen het als eerste wanneer de volledige studie opent. Reserveer je gratis plek.",
        "学習機能のすべてが開くとき、Founding Members に最初にお知らせします。無料で枠を予約しましょう。",
        "完整学习功能开放时，Founding Members 将最先获知。预留你的免费名额。",
        "전체 학습이 열리면 Founding Members가 가장 먼저 알게 됩니다. 무료 자리를 예약하세요."],
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
