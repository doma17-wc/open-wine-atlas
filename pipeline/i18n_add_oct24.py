"""One-off: translations for the study walls of 24 October 2026 (a free account opens the full study).

Merges into web/i18n/<lang>.json without touching existing entries. Safe to rerun.
Order of each list: fr, it, de, es, pt, nl, ja, zh, ko.
"""
import json
import os

I18N = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "i18n")
LANGS = ["fr", "it", "de", "es", "pt", "nl", "ja", "zh", "ko"]

T = {
    "Create a free account to read the rest of this lesson.": [
        "Créez un compte gratuit pour lire la suite de cette leçon.",
        "Crea un account gratuito per leggere il resto di questa lezione.",
        "Erstellen Sie ein kostenloses Konto, um den Rest dieser Lektion zu lesen.",
        "Crea una cuenta gratuita para leer el resto de esta lección.",
        "Crie uma conta gratuita para ler o resto desta lição.",
        "Maak een gratis account aan om de rest van deze les te lezen.",
        "無料アカウントを作成すると、このレッスンの続きを読めます。",
        "创建免费账户即可阅读本课其余内容。",
        "무료 계정을 만들면 이 레슨의 나머지를 읽을 수 있습니다."],
    "The first lesson of every path is open to everyone. A free account opens every lesson and the full study, without a daily limit.": [
        "La première leçon de chaque parcours est ouverte à tous. Un compte gratuit ouvre toutes les leçons et l'étude complète, sans limite quotidienne.",
        "La prima lezione di ogni percorso è aperta a tutti. Un account gratuito apre tutte le lezioni e lo studio completo, senza limite giornaliero.",
        "Die erste Lektion jedes Pfads ist für alle offen. Ein kostenloses Konto öffnet alle Lektionen und das ganze Lernen, ohne Tageslimit.",
        "La primera lección de cada ruta está abierta a todos. Una cuenta gratuita abre todas las lecciones y el estudio completo, sin límite diario.",
        "A primeira lição de cada percurso está aberta a todos. Uma conta gratuita abre todas as lições e o estudo completo, sem limite diário.",
        "De eerste les van elk pad is voor iedereen open. Een gratis account opent alle lessen en de volledige studie, zonder daglimiet.",
        "各パスの最初のレッスンは誰でも読めます。無料アカウントですべてのレッスンと学習機能が1日の上限なしで使えます。",
        "每条路径的第一课对所有人开放。免费账户可解锁全部课程和完整学习，没有每日限制。",
        "모든 경로의 첫 레슨은 누구에게나 열려 있습니다. 무료 계정으로 모든 레슨과 전체 학습을 하루 제한 없이 이용할 수 있습니다."],
    "A free account opens the full study: every lesson, every quiz and the full review, without a daily limit.": [
        "Un compte gratuit ouvre l'étude complète : toutes les leçons, tous les quiz et la révision complète, sans limite quotidienne.",
        "Un account gratuito apre lo studio completo: tutte le lezioni, tutti i quiz e il ripasso completo, senza limite giornaliero.",
        "Ein kostenloses Konto öffnet das ganze Lernen: alle Lektionen, alle Quiz und die ganze Wiederholung, ohne Tageslimit.",
        "Una cuenta gratuita abre el estudio completo: todas las lecciones, todos los cuestionarios y el repaso completo, sin límite diario.",
        "Uma conta gratuita abre o estudo completo: todas as lições, todos os quizzes e a revisão completa, sem limite diário.",
        "Een gratis account opent de volledige studie: alle lessen, alle quizzen en de volledige herhaling, zonder daglimiet.",
        "無料アカウントですべてのレッスン、クイズ、復習が1日の上限なしで使えます。",
        "免费账户可解锁完整学习：全部课程、全部测验和完整复习，没有每日限制。",
        "무료 계정으로 모든 레슨, 모든 퀴즈, 전체 복습을 하루 제한 없이 이용할 수 있습니다."],
    "No card, no password: we email you a code.": [
        "Ni carte ni mot de passe : nous vous envoyons un code par e-mail.",
        "Nessuna carta, nessuna password: ti inviamo un codice via email.",
        "Keine Karte, kein Passwort: Wir senden Ihnen einen Code per E-Mail.",
        "Sin tarjeta ni contraseña: te enviamos un código por correo.",
        "Sem cartão nem palavra-passe: enviamos-lhe um código por e-mail.",
        "Geen kaart, geen wachtwoord: we mailen je een code.",
        "カードもパスワードも不要。コードをメールでお送りします。",
        "无需银行卡，无需密码：我们会通过电子邮件发送验证码。",
        "카드도 비밀번호도 필요 없습니다. 코드를 이메일로 보내 드립니다."],
    "questions today, no limit": [
        "questions aujourd'hui, sans limite", "domande oggi, senza limite", "Fragen heute, ohne Limit",
        "preguntas hoy, sin límite", "perguntas hoje, sem limite", "vragen vandaag, geen limiet",
        "今日の問題、上限なし", "今日题目，无限制", "오늘의 문제, 제한 없음"],
    "free account": [
        "compte gratuit", "account gratuito", "kostenloses Konto", "cuenta gratuita", "conta gratuita",
        "gratis account", "無料アカウント", "免费账户", "무료 계정"],
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
