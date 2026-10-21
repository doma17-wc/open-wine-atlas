"""One-off: translations for the games in the study section (web/study.js) added in October 2026.

Merges into web/i18n/<lang>.json without touching existing entries. Safe to rerun.
Order of each list: fr, it, de, es, pt, nl, ja, zh, ko.
"""
import json
import os

I18N = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "i18n")
LANGS = ["fr", "it", "de", "es", "pt", "nl", "ja", "zh", "ko"]

T = {
    # Game names
    "Daily challenge": ["Défi du jour", "Sfida del giorno", "Tagesaufgabe", "Reto del día", "Desafio do dia", "Dagelijkse uitdaging", "今日のチャレンジ", "每日挑战", "오늘의 챌린지"],
    "Mystery place": ["Lieu mystère", "Luogo misterioso", "Geheimer Ort", "Lugar misterioso", "Lugar mistério", "Mysterieuze plek", "ミステリープレイス", "神秘地点", "미스터리 장소"],
    "Pin it": ["Placez-le", "Punta la mappa", "Markieren", "Márcalo", "Marque no mapa", "Prik het", "ピンを刺す", "标出位置", "핀 꽂기"],
    "In order": ["Dans l'ordre", "In ordine", "Der Reihe nach", "En orden", "Por ordem", "Op volgorde", "並べ替え", "排序", "순서대로"],
    "Where is it from?": ["D'où vient-il ?", "Da dove viene?", "Woher kommt er?", "¿De dónde es?", "De onde é?", "Waar komt hij vandaan?", "どこのワイン？", "来自哪里？", "어디 와인일까?"],
    "Odd one out": ["L'intrus", "L'intruso", "Was passt nicht?", "El intruso", "O intruso", "Wie hoort er niet bij?", "仲間はずれ", "找不同", "다른 하나 찾기"],
    "Match": ["Associer", "Abbina", "Zuordnen", "Emparejar", "Associar", "Koppelen", "組み合わせ", "配对", "짝 맞추기"],
    # Game descriptions
    "Five questions, the same for everyone today. Share your score.": ["Cinq questions, les mêmes pour tous aujourd'hui. Partagez votre score.", "Cinque domande, uguali per tutti oggi. Condividi il tuo punteggio.", "Fünf Fragen, heute für alle gleich. Teilen Sie Ihr Ergebnis.", "Cinco preguntas, las mismas para todos hoy. Comparte tu puntuación.", "Cinco perguntas, as mesmas para todos hoje. Partilhe a sua pontuação.", "Vijf vragen, vandaag voor iedereen dezelfde. Deel je score.", "5問、今日は全員共通。スコアをシェアしよう。", "五道题，今天人人相同。分享你的得分。", "5문제, 오늘은 모두 같은 문제. 점수를 공유하세요."],
    "Clue by clue: the slope, the rock, the grapes, the nearest town. Guess early for more points.": ["Indice après indice : la pente, la roche, les cépages, la ville la plus proche. Devinez tôt pour plus de points.", "Indizio dopo indizio: il pendio, la roccia, i vitigni, il centro più vicino. Indovina presto per più punti.", "Hinweis für Hinweis: Hang, Gestein, Rebsorten, nächster Ort. Wer früh rät, bekommt mehr Punkte.", "Pista a pista: la pendiente, la roca, las uvas, la localidad más cercana. Acierta pronto y suma más puntos.", "Pista a pista: o declive, a rocha, as castas, a localidade mais próxima. Acerte cedo para mais pontos.", "Hint na hint: de helling, het gesteente, de druiven, de dichtstbijzijnde plaats. Raad vroeg voor meer punten.", "ヒントを一つずつ：斜面、岩石、品種、最寄りの町。早く当てるほど高得点。", "线索逐条给出：坡度、岩石、葡萄、最近的城镇。越早猜中得分越高。", "단서가 하나씩: 경사, 암석, 품종, 가장 가까운 마을. 일찍 맞힐수록 점수가 높습니다."],
    "Drop a pin on the map. The closer, the more points.": ["Placez une épingle sur la carte. Plus c'est près, plus vous marquez.", "Metti un segnaposto sulla mappa. Più sei vicino, più punti fai.", "Setzen Sie eine Markierung auf die Karte. Je näher, desto mehr Punkte.", "Pon un marcador en el mapa. Cuanto más cerca, más puntos.", "Coloque um marcador no mapa. Quanto mais perto, mais pontos.", "Prik een speld op de kaart. Hoe dichterbij, hoe meer punten.", "地図にピンを刺そう。近いほど高得点。", "在地图上插上标记。越近得分越高。", "지도에 핀을 꽂으세요. 가까울수록 점수가 높습니다."],
    "North to south, lowest to highest, first to last: put them in line.": ["Du nord au sud, du plus bas au plus haut, du premier au dernier : mettez-les dans l'ordre.", "Da nord a sud, dal più basso al più alto, dal primo all'ultimo: mettili in fila.", "Von Nord nach Süd, von tief nach hoch, vom ersten bis zum letzten: bringen Sie sie in eine Reihe.", "De norte a sur, de más bajo a más alto, del primero al último: ponlos en fila.", "De norte a sul, do mais baixo ao mais alto, do primeiro ao último: ponha-os em fila.", "Van noord naar zuid, van laag naar hoog, van eerste tot laatste: zet ze op een rij.", "北から南、低い順、古い順：正しく並べよう。", "从北到南、从低到高、从先到后：把它们排好。", "북쪽에서 남쪽, 낮은 곳에서 높은 곳, 처음부터 끝까지: 순서대로 놓으세요."],
    "A real wine and its producer. Which appellation is it from?": ["Un vrai vin et son producteur. De quelle appellation vient-il ?", "Un vino vero e il suo produttore. Da quale denominazione viene?", "Ein echter Wein und sein Erzeuger. Aus welcher Appellation stammt er?", "Un vino real y su productor. ¿De qué denominación es?", "Um vinho real e o seu produtor. De que denominação é?", "Een echte wijn en zijn producent. Uit welke herkomstbenaming komt hij?", "実在のワインと生産者。どの原産地呼称のワイン？", "一款真实的葡萄酒及其生产商。它来自哪个法定产区？", "실제 와인과 생산자. 어느 원산지 명칭의 와인일까요?"],
    "Four answers, one does not belong. Which one, and why?": ["Quatre réponses, une n'a pas sa place. Laquelle, et pourquoi ?", "Quattro risposte, una non c'entra. Quale, e perché?", "Vier Antworten, eine passt nicht. Welche, und warum?", "Cuatro respuestas, una no encaja. ¿Cuál y por qué?", "Quatro respostas, uma não pertence. Qual, e porquê?", "Vier antwoorden, één hoort er niet bij. Welke, en waarom?", "4つの答えのうち1つだけ仲間はずれ。どれ？なぜ？", "四个答案，有一个不属于这一组。是哪个，为什么？", "네 개의 답 중 하나가 다릅니다. 어느 것이고, 왜일까요?"],
    "Pair them up: places and grapes, villages and regions, terms and meanings.": ["Associez-les : lieux et cépages, villages et régions, termes et définitions.", "Abbinali: luoghi e vitigni, villaggi e regioni, termini e significati.", "Ordnen Sie zu: Orte und Rebsorten, Dörfer und Regionen, Begriffe und Bedeutungen.", "Emparéjalos: lugares y uvas, pueblos y regiones, términos y significados.", "Associe-os: lugares e castas, aldeias e regiões, termos e significados.", "Koppel ze: plekken en druiven, dorpen en regio's, termen en betekenissen.", "組み合わせよう：産地と品種、村と地域、用語と意味。", "两两配对：产地与葡萄、村庄与产区、术语与含义。", "짝을 지으세요: 장소와 품종, 마을과 지역, 용어와 뜻."],
    # Play panel and themes
    "Play": ["Jouer", "Gioca", "Spielen", "Jugar", "Jogar", "Spelen", "プレイ", "游戏", "플레이"],
    "Play again": ["Rejouer", "Gioca ancora", "Nochmal spielen", "Jugar otra vez", "Jogar de novo", "Opnieuw spelen", "もう一度プレイ", "再玩一次", "다시 플레이"],
    "Play this path": ["Jouer ce parcours", "Gioca questo percorso", "Diesen Lernpfad spielen", "Jugar este itinerario", "Jogar este percurso", "Dit leerpad spelen", "このコースでプレイ", "用这条路线游戏", "이 과정으로 플레이"],
    "Theme": ["Thème", "Tema", "Thema", "Tema", "Tema", "Thema", "テーマ", "主题", "테마"],
    "Theme: {name}": ["Thème : {name}", "Tema: {name}", "Thema: {name}", "Tema: {name}", "Tema: {name}", "Thema: {name}", "テーマ：{name}", "主题：{name}", "테마: {name}"],
    "Everything": ["Tout", "Tutto", "Alles", "Todo", "Tudo", "Alles", "すべて", "全部", "전체"],
    "Everything, a new country each round": ["Tout, un nouveau pays à chaque partie", "Tutto, un paese nuovo a ogni partita", "Alles, jede Runde ein neues Land", "Todo, un país nuevo en cada ronda", "Tudo, um país novo em cada ronda", "Alles, elke ronde een nieuw land", "すべて（毎回別の国）", "全部，每轮换一个国家", "전체, 라운드마다 새로운 나라"],
    "Regions": ["Régions", "Regioni", "Regionen", "Regiones", "Regiões", "Regio's", "地域", "产区", "산지"],
    "Grapes": ["Cépages", "Vitigni", "Rebsorten", "Uvas", "Castas", "Druiven", "品種", "葡萄品种", "품종"],
    "Today: {country}. Five questions, the same for everyone. Share your score.": ["Aujourd'hui : {country}. Cinq questions, les mêmes pour tous. Partagez votre score.", "Oggi: {country}. Cinque domande, uguali per tutti. Condividi il tuo punteggio.", "Heute: {country}. Fünf Fragen, für alle gleich. Teilen Sie Ihr Ergebnis.", "Hoy: {country}. Cinco preguntas, las mismas para todos. Comparte tu puntuación.", "Hoje: {country}. Cinco perguntas, as mesmas para todos. Partilhe a sua pontuação.", "Vandaag: {country}. Vijf vragen, voor iedereen dezelfde. Deel je score.", "今日：{country}。全員共通の5問。スコアをシェアしよう。", "今天：{country}。五道题，人人相同。分享你的得分。", "오늘: {country}. 모두 같은 5문제. 점수를 공유하세요."],
    "Today: {marks} {r}/{n}. Tap to share.": ["Aujourd'hui : {marks} {r}/{n}. Touchez pour partager.", "Oggi: {marks} {r}/{n}. Tocca per condividere.", "Heute: {marks} {r}/{n}. Zum Teilen tippen.", "Hoy: {marks} {r}/{n}. Toca para compartir.", "Hoje: {marks} {r}/{n}. Toque para partilhar.", "Vandaag: {marks} {r}/{n}. Tik om te delen.", "今日：{marks} {r}/{n}。タップしてシェア。", "今天：{marks} {r}/{n}。点击分享。", "오늘: {marks} {r}/{n}. 눌러서 공유."],
    "The daily challenge takes 5 free questions, and fewer are left today. They come back tomorrow.": ["Le défi du jour utilise 5 questions gratuites, et il en reste moins aujourd'hui. Elles reviennent demain.", "La sfida del giorno richiede 5 domande gratuite, e oggi ne restano meno. Tornano domani.", "Die Tagesaufgabe braucht 5 kostenlose Fragen, heute sind weniger übrig. Morgen gibt es neue.", "El reto del día usa 5 preguntas gratuitas, y hoy quedan menos. Vuelven mañana.", "O desafio do dia usa 5 perguntas gratuitas, e hoje restam menos. Voltam amanhã.", "De dagelijkse uitdaging kost 5 gratis vragen, en vandaag zijn er minder over. Morgen zijn ze er weer.", "今日のチャレンジには無料の5問が必要ですが、今日は残りが足りません。明日また使えます。", "每日挑战需要5道免费题，今天剩余不足。明天会恢复。", "오늘의 챌린지에는 무료 문제 5개가 필요한데, 오늘은 남은 문제가 부족합니다. 내일 다시 채워집니다."],
    # Playing
    "Check": ["Vérifier", "Verifica", "Prüfen", "Comprobar", "Verificar", "Controleren", "答え合わせ", "检查", "확인"],
    "Another clue": ["Un autre indice", "Un altro indizio", "Noch ein Hinweis", "Otra pista", "Outra pista", "Nog een hint", "次のヒント", "再给一条线索", "다른 단서"],
    "Tap them in order.": ["Touchez-les dans l'ordre.", "Toccali in ordine.", "Tippen Sie sie der Reihe nach an.", "Tócalos en orden.", "Toque-os por ordem.", "Tik ze op volgorde aan.", "順番にタップしてください。", "按顺序点击。", "순서대로 누르세요."],
    "Tap one on the left, then its partner on the right.": ["Touchez un élément à gauche, puis son partenaire à droite.", "Tocca un elemento a sinistra, poi il suo abbinamento a destra.", "Tippen Sie links auf ein Feld, dann rechts auf sein Gegenstück.", "Toca uno a la izquierda y luego su pareja a la derecha.", "Toque num à esquerda e depois no seu par à direita.", "Tik er links een aan, dan zijn partner rechts.", "左の項目をタップしてから、右の対応する項目をタップしてください。", "先点击左侧一项，再点击右侧与之对应的一项。", "왼쪽에서 하나를 누른 뒤 오른쪽에서 짝을 누르세요."],
    "Tap the map where you think it is.": ["Touchez la carte là où vous pensez qu'il se trouve.", "Tocca la mappa dove pensi che si trovi.", "Tippen Sie auf die Karte, wo Sie es vermuten.", "Toca el mapa donde crees que está.", "Toque no mapa onde acha que fica.", "Tik op de kaart waar je denkt dat het ligt.", "あると思う場所を地図上でタップしてください。", "在地图上点击你认为它所在的位置。", "있다고 생각하는 곳을 지도에서 누르세요."],
    "Drop a pin on {name}.": ["Placez une épingle sur {name}.", "Metti un segnaposto su {name}.", "Markieren Sie {name}.", "Pon un marcador en {name}.", "Coloque um marcador em {name}.", "Prik een speld op {name}.", "{name}にピンを刺してください。", "在{name}上插上标记。", "{name}에 핀을 꽂으세요."],
    "Which place is it?": ["Quel est ce lieu ?", "Quale luogo è?", "Welcher Ort ist es?", "¿Qué lugar es?", "Que lugar é?", "Welke plek is het?", "どの場所でしょう？", "这是哪里？", "어느 곳일까요?"],
    "Where is this wine from?": ["D'où vient ce vin ?", "Da dove viene questo vino?", "Woher kommt dieser Wein?", "¿De dónde es este vino?", "De onde é este vinho?", "Waar komt deze wijn vandaan?", "このワインはどこのもの？", "这款酒来自哪里？", "이 와인은 어디 와인일까요?"],
    "Which one does not belong?": ["Lequel n'a pas sa place ?", "Quale non c'entra?", "Was passt nicht dazu?", "¿Cuál no encaja?", "Qual não pertence?", "Welke hoort er niet bij?", "仲間はずれはどれ？", "哪一个不属于这一组？", "다른 하나는 무엇일까요?"],
    "Which one is not a {rank}?": ["Lequel n'est pas un {rank} ?", "Quale non è un {rank}?", "Welcher ist kein {rank}?", "¿Cuál no es un {rank}?", "Qual não é um {rank}?", "Welke is geen {rank}?", "{rank}でないのはどれ？", "哪一个不是{rank}？", "{rank}이(가) 아닌 것은?"],
    "Which one is not in {region}?": ["Lequel n'est pas en {region} ?", "Quale non si trova in {region}?", "Welcher liegt nicht in {region}?", "¿Cuál no está en {region}?", "Qual não fica em {region}?", "Welke ligt niet in {region}?", "{region}にないのはどれ？", "哪一个不在{region}？", "{region}에 있지 않은 것은?"],
    "Which one is not made mainly from {grape}?": ["Lequel n'est pas élaboré surtout à partir de {grape} ?", "Quale non è fatto soprattutto con {grape}?", "Welcher wird nicht hauptsächlich aus {grape} gemacht?", "¿Cuál no se elabora principalmente con {grape}?", "Qual não é feito sobretudo de {grape}?", "Welke wordt niet hoofdzakelijk van {grape} gemaakt?", "主に{grape}から造られていないのはどれ？", "哪一个不是主要用{grape}酿造的？", "주로 {grape}(으)로 만들지 않는 것은?"],
    "Match each place to its main grape": ["Associez chaque lieu à son cépage principal", "Abbina ogni luogo al suo vitigno principale", "Ordnen Sie jedem Ort seine Hauptrebsorte zu", "Empareja cada lugar con su uva principal", "Associe cada lugar à sua casta principal", "Koppel elke plek aan zijn hoofddruif", "各産地を主要品種と組み合わせよう", "将每个产地与其主要葡萄配对", "각 장소를 주요 품종과 짝지으세요"],
    "Match each place to its region": ["Associez chaque lieu à sa région", "Abbina ogni luogo alla sua regione", "Ordnen Sie jedem Ort seine Region zu", "Empareja cada lugar con su región", "Associe cada lugar à sua região", "Koppel elke plek aan zijn regio", "各産地を地域と組み合わせよう", "将每个产地与其所属产区配对", "각 장소를 해당 지역과 짝지으세요"],
    "From north to south": ["Du nord au sud", "Da nord a sud", "Von Nord nach Süd", "De norte a sur", "De norte a sul", "Van noord naar zuid", "北から南へ", "从北到南", "북쪽에서 남쪽으로"],
    "From west to east": ["D'ouest en est", "Da ovest a est", "Von West nach Ost", "De oeste a este", "De oeste para leste", "Van west naar oost", "西から東へ", "从西到东", "서쪽에서 동쪽으로"],
    "From lowest to highest, on average": ["Du plus bas au plus haut, en moyenne", "Dal più basso al più alto, in media", "Von tief nach hoch, im Mittel", "De más bajo a más alto, de media", "Do mais baixo ao mais alto, em média", "Van laag naar hoog, gemiddeld", "標高の低い順に（平均）", "按平均海拔从低到高", "평균 고도가 낮은 순서로"],
    "From largest to smallest": ["Du plus grand au plus petit", "Dal più grande al più piccolo", "Vom größten zum kleinsten", "Del más grande al más pequeño", "Do maior ao mais pequeno", "Van groot naar klein", "面積の大きい順に", "按面积从大到小", "면적이 큰 순서로"],
    # Clues of a mystery place
    "The rock below is mostly {rock}.": ["La roche en dessous est surtout {rock}.", "La roccia sottostante è soprattutto {rock}.", "Das Gestein darunter ist überwiegend {rock}.", "La roca de debajo es sobre todo {rock}.", "A rocha por baixo é sobretudo {rock}.", "Het gesteente eronder is vooral {rock}.", "下の岩石は主に{rock}です。", "下方的岩石主要是{rock}。", "아래 암석은 주로 {rock}입니다."],
    "It covers about {ha} ha.": ["Il couvre environ {ha} ha.", "Si estende su circa {ha} ha.", "Es umfasst etwa {ha} ha.", "Ocupa unas {ha} ha.", "Ocupa cerca de {ha} ha.", "Het beslaat zo'n {ha} ha.", "面積は約{ha} haです。", "面积约{ha} ha。", "면적은 약 {ha} ha입니다."],
    "The sea is right there.": ["La mer est toute proche.", "Il mare è proprio lì.", "Das Meer ist direkt nebenan.", "El mar está justo al lado.", "O mar está mesmo ali.", "De zee ligt vlakbij.", "海がすぐそばにあります。", "大海就在旁边。", "바다가 바로 옆입니다."],
    "The sea is {km} km away.": ["La mer est à {km} km.", "Il mare è a {km} km.", "Das Meer ist {km} km entfernt.", "El mar está a {km} km.", "O mar fica a {km} km.", "De zee ligt op {km} km.", "海まで{km} kmです。", "距海{km} km。", "바다까지 {km} km입니다."],
    "A river nearby: the {river}.": ["Une rivière proche : {river}.", "Un fiume vicino: {river}.", "Ein Fluss in der Nähe: {river}.", "Un río cercano: el {river}.", "Um rio próximo: o {river}.", "Een rivier in de buurt: de {river}.", "近くを流れる川：{river}。", "附近的河流：{river}。", "근처의 강: {river}."],
    "Main grapes: {list}.": ["Cépages principaux : {list}.", "Vitigni principali: {list}.", "Hauptrebsorten: {list}.", "Uvas principales: {list}.", "Castas principais: {list}.", "Hoofddruiven: {list}.", "主要品種：{list}。", "主要葡萄：{list}。", "주요 품종: {list}."],
    "It lies in {parent}.": ["Il se trouve dans {parent}.", "Si trova in {parent}.", "Es liegt in {parent}.", "Está en {parent}.", "Fica em {parent}.", "Het ligt in {parent}.", "{parent}にあります。", "它位于{parent}。", "{parent}에 있습니다."],
    "The nearest town: {town}, {km} km away.": ["La ville la plus proche : {town}, à {km} km.", "Il centro più vicino: {town}, a {km} km.", "Der nächste Ort: {town}, {km} km entfernt.", "La localidad más cercana: {town}, a {km} km.", "A localidade mais próxima: {town}, a {km} km.", "De dichtstbijzijnde plaats: {town}, op {km} km.", "最寄りの町：{town}（{km} km）。", "最近的城镇：{town}，相距{km} km。", "가장 가까운 마을: {town}, {km} km 거리."],
    "Its outline is on the map.": ["Son contour est sur la carte.", "Il suo perimetro è sulla mappa.", "Sein Umriss ist auf der Karte.", "Su contorno está en el mapa.", "O seu contorno está no mapa.", "De omtrek staat op de kaart.", "輪郭を地図に表示しました。", "它的轮廓已显示在地图上。", "경계가 지도에 표시되어 있습니다."],
    # Answers and scores
    "Close enough.": ["Assez proche.", "Abbastanza vicino.", "Nah genug.", "Bastante cerca.", "Perto o suficiente.", "Dichtbij genoeg.", "ほぼ正解。", "足够接近。", "거의 정답."],
    "Inside it.": ["Dedans.", "Dentro.", "Mittendrin.", "Dentro.", "Dentro.", "Erbinnen.", "範囲内です。", "在范围内。", "범위 안입니다."],
    "{km} km away.": ["À {km} km.", "A {km} km.", "{km} km daneben.", "A {km} km.", "A {km} km.", "{km} km ernaast.", "{km} kmずれています。", "相差{km} km。", "{km} km 떨어졌습니다."],
    "No wrong tries.": ["Aucune erreur.", "Nessun errore.", "Kein Fehlversuch.", "Ningún fallo.", "Nenhum erro.", "Geen foute pogingen.", "ミスなし。", "没有失误。", "틀린 시도 없음."],
    "{n} wrong tries.": ["{n} erreurs.", "{n} errori.", "{n} Fehlversuche.", "{n} fallos.", "{n} erros.", "{n} foute pogingen.", "ミス{n}回。", "失误{n}次。", "틀린 시도 {n}번."],
    "{wine} by {producer} comes from {place}.": ["{wine} de {producer} vient de {place}.", "{wine} di {producer} viene da {place}.", "{wine} von {producer} stammt aus {place}.", "{wine} de {producer} procede de {place}.", "{wine} de {producer} vem de {place}.", "{wine} van {producer} komt uit {place}.", "{producer}の{wine}は{place}のワインです。", "{producer}的{wine}来自{place}。", "{producer}의 {wine}은(는) {place}에서 납니다."],
    "{n} points": ["{n} points", "{n} punti", "{n} Punkte", "{n} puntos", "{n} pontos", "{n} punten", "{n}点", "{n}分", "{n}점"],
    "{n} points if right": ["{n} points si c'est juste", "{n} punti se giusto", "{n} Punkte, wenn richtig", "{n} puntos si aciertas", "{n} pontos se acertar", "{n} punten als het goed is", "正解で{n}点", "答对得{n}分", "맞히면 {n}점"],
    "Best: {n}": ["Record : {n}", "Record: {n}", "Bestwert: {n}", "Récord: {n}", "Recorde: {n}", "Record: {n}", "ベスト：{n}", "最佳：{n}", "최고 기록: {n}"],
    "New personal best!": ["Nouveau record personnel !", "Nuovo record personale!", "Neuer persönlicher Bestwert!", "¡Nuevo récord personal!", "Novo recorde pessoal!", "Nieuw persoonlijk record!", "自己ベスト更新！", "个人新纪录！", "개인 최고 기록 경신!"],
    "Share my score": ["Partager mon score", "Condividi il mio punteggio", "Mein Ergebnis teilen", "Compartir mi puntuación", "Partilhar a minha pontuação", "Mijn score delen", "スコアをシェア", "分享我的得分", "내 점수 공유"],
    "Copied. Paste it anywhere.": ["Copié. Collez-le où vous voulez.", "Copiato. Incollalo dove vuoi.", "Kopiert. Fügen Sie es überall ein.", "Copiado. Pégalo donde quieras.", "Copiado. Cole onde quiser.", "Gekopieerd. Plak het waar je wilt.", "コピーしました。どこにでも貼り付けられます。", "已复制。可粘贴到任何地方。", "복사했습니다. 어디든 붙여 넣으세요."],
    # Terms used in questions and wine kinds
    "grand cru": ["grand cru", "grand cru", "Grand cru", "grand cru", "grand cru", "grand cru", "grand cru", "grand cru", "grand cru"],
    "premier cru": ["premier cru", "premier cru", "Premier cru", "premier cru", "premier cru", "premier cru", "premier cru", "premier cru", "premier cru"],
    "sparkling": ["effervescent", "spumante", "Schaumwein", "espumoso", "espumante", "mousserende", "スパークリング", "起泡", "스파클링"],
    "fortified": ["muté", "liquoroso", "Likörwein", "generoso", "fortificado", "versterkte", "酒精強化", "加强型", "주정강화"],
    "sweet": ["doux", "dolce", "Süßwein", "dulce", "doce", "zoete", "甘口", "甜", "스위트"],
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
