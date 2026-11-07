"""One-off: translations for the Piemonte and Toscana Deep Regions of 7 November 2026 (pipeline/it_deep.py).

Merges into web/i18n/<lang>.json without touching existing entries. Safe to rerun.
Order of each list: fr, it, de, es, pt, nl, ja, zh, ko.
"""
import json
import os

I18N = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "i18n")
LANGS = ["fr", "it", "de", "es", "pt", "nl", "ja", "zh", "ko"]

T = {
    "Piedmont in depth": ["Le Piémont en profondeur", "Piemonte in profondità", "Das Piemont im Detail", "Piamonte en profundidad",
                          "Piemonte em profundidade", "Piëmont in detail", "ピエモンテを深く", "深入皮埃蒙特", "피에몬테 깊이 보기"],
    "Tuscany in depth": ["La Toscane en profondeur", "Toscana in profondità", "Die Toskana im Detail", "Toscana en profundidad",
                         "Toscana em profundidade", "Toscane in detail", "トスカーナを深く", "深入托斯卡纳", "토스카나 깊이 보기"],
    "Piedmont in full depth": ["Le Piémont en profondeur", "Il Piemonte in profondità", "Das Piemont im ganzen Detail", "Piamonte en profundidad",
                               "O Piemonte em profundidade", "Piëmont tot in detail", "ピエモンテを隅々まで", "全面深入皮埃蒙特", "피에몬테를 깊이"],
    "Tuscany in full depth": ["La Toscane en profondeur", "La Toscana in profondità", "Die Toskana im ganzen Detail", "Toscana en profundidad",
                              "A Toscana em profundidade", "Toscane tot in detail", "トスカーナを隅々まで", "全面深入托斯卡纳", "토스카나를 깊이"],
    "Piemonte · 4 levels": ["Piemonte · 4 niveaux", "Piemonte · 4 livelli", "Piemonte · 4 Ebenen", "Piemonte · 4 niveles", "Piemonte · 4 níveis",
                            "Piemonte · 4 niveaus", "ピエモンテ · 4つの階層", "皮埃蒙特 · 4个层级", "피에몬테 · 4단계"],
    "Toscana · 4 levels": ["Toscana · 4 niveaux", "Toscana · 4 livelli", "Toscana · 4 Ebenen", "Toscana · 4 niveles", "Toscana · 4 níveis",
                           "Toscana · 4 niveaus", "トスカーナ · 4つの階層", "托斯卡纳 · 4个层级", "토스카나 · 4단계"],
    "Cru commune": ["Commune de cru", "Comune del cru", "Cru-Gemeinde", "Municipio de cru", "Comuna de cru", "Crugemeente",
                    "クリュの村", "名园村镇", "크뤼 마을"],
    "Regional DOC": ["DOC régionale", "DOC regionale", "Regionale DOC", "DOC regional", "DOC regional", "Regionale DOC",
                     "広域DOC", "大区级DOC", "광역 DOC"],
    "Sub-zone, UGA and Pieve": ["Sous-zone, UGA et Pieve", "Sottozona, UGA e Pieve", "Unterzone, UGA und Pieve", "Subzona, UGA y Pieve",
                                "Subzona, UGA e Pieve", "Subzone, UGA en Pieve", "サブゾーン、UGA、ピエーヴェ", "子产区、UGA与Pieve",
                                "하위 지구, UGA, 피에베"],
    "Commune": ["Commune", "Comune", "Gemeinde", "Municipio", "Comuna", "Gemeente", "村", "村镇", "마을"],
    "Sub-zone": ["Sous-zone", "Sottozona", "Unterzone", "Subzona", "Subzona", "Subzone", "サブゾーン", "子产区", "하위 지구"],
    "UGA": ["UGA"] * 9,
    "Pieve": ["Pieve"] * 6 + ["ピエーヴェ", "Pieve（教区）", "피에베"],
    "MGA · {n}": ["MGA · {n}"] * 9,
    "Pievi · {n}": ["Pievi · {n}"] * 6 + ["ピエーヴェ · {n}", "Pievi · {n}", "피에베 · {n}"],
    "Best known MGA": ["Les MGA les plus connues", "Le MGA più note", "Die bekanntesten MGA", "Las MGA más conocidas", "As MGA mais conhecidas",
                       "De bekendste MGA", "代表的なMGA", "最知名的MGA", "가장 잘 알려진 MGA"],
    "Commune name on the label": ["Nom de la commune sur l'étiquette", "Nome del comune in etichetta", "Gemeindename auf dem Etikett",
                                  "Nombre del municipio en la etiqueta", "Nome da comuna no rótulo", "Gemeentenaam op het etiket",
                                  "ラベルに記す村名", "酒标上的村镇名", "라벨의 마을 이름"],
    "MGA in this commune": ["MGA dans la commune", "MGA in questo comune", "MGA in dieser Gemeinde", "MGA en este municipio", "MGA nesta comuna",
                            "MGA in deze gemeente", "この村のMGA", "本村镇的MGA", "이 마을의 MGA"],
    "The twelve Pievi of the specification (2025), named on the label of Vino Nobile di Montepulciano Pieve. Those with a known village are markers on the map.": [
        "Les douze Pievi du cahier des charges (2025), nommées sur l'étiquette du Vino Nobile di Montepulciano Pieve. Celles dont le village est connu sont des repères sur la carte.",
        "Le dodici Pievi del disciplinare (2025), indicate in etichetta del Vino Nobile di Montepulciano Pieve. Quelle con un borgo noto sono segnate sulla mappa.",
        "Die zwölf Pievi der Produktionsvorschrift (2025), auf dem Etikett des Vino Nobile di Montepulciano Pieve genannt. Die mit bekanntem Ort sind Marker auf der Karte.",
        "Las doce Pievi del pliego (2025), nombradas en la etiqueta del Vino Nobile di Montepulciano Pieve. Las que tienen un pueblo conocido son marcadores en el mapa.",
        "As doze Pievi do caderno de especificações (2025), nomeadas no rótulo do Vino Nobile di Montepulciano Pieve. As que têm aldeia conhecida são marcadores no mapa.",
        "De twaalf Pievi van het lastenboek (2025), genoemd op het etiket van Vino Nobile di Montepulciano Pieve. Die met een bekend dorp zijn markeringen op de kaart.",
        "生産規定（2025年）の12のピエーヴェ。ヴィーノ・ノビレ・ディ・モンテプルチアーノ・ピエーヴェのラベルに記される。村が分かるものは地図上の目印。",
        "生产规范（2025年）中的十二个Pievi，标注于Vino Nobile di Montepulciano Pieve的酒标上。已知村落的在地图上以标记显示。",
        "생산 규정(2025)의 12개 피에베로, 비노 노빌레 디 몬테풀치아노 피에베 라벨에 표기된다. 마을이 알려진 곳은 지도에 표시했다."],
    "Menzioni geografiche aggiuntive: the named vineyard areas of the specification, which may appear on the label. Listed, not drawn on the map.": [
        "Menzioni geografiche aggiuntive : les lieux nommés du cahier des charges, qui peuvent figurer sur l'étiquette. Listés, non dessinés sur la carte.",
        "Menzioni geografiche aggiuntive: le zone vitate con nome del disciplinare, che possono comparire in etichetta. Elencate, non disegnate sulla mappa.",
        "Menzioni geografiche aggiuntive: die benannten Lagen der Produktionsvorschrift, die auf dem Etikett stehen dürfen. Aufgelistet, nicht auf der Karte gezeichnet.",
        "Menzioni geografiche aggiuntive: los parajes con nombre del pliego de condiciones, que pueden figurar en la etiqueta. Listados, no dibujados en el mapa.",
        "Menzioni geografiche aggiuntive: as parcelas com nome do caderno de especificações, que podem constar do rótulo. Listadas, não desenhadas no mapa.",
        "Menzioni geografiche aggiuntive: de benoemde wijngaardgebieden van het lastenboek, die op het etiket mogen staan. Opgesomd, niet op de kaart getekend.",
        "Menzioni geografiche aggiuntive：生産規定に名前のある畑の区域で、ラベルに表示できる。一覧のみで、地図には描かれていない。",
        "Menzioni geografiche aggiuntive：生产规范中列名的葡萄园区域，可标注在酒标上。仅列出，未在地图上绘制。",
        "Menzioni geografiche aggiuntive: 생산 규정에 이름이 오른 포도밭 구역으로 라벨에 표기할 수 있다. 목록만 있고 지도에는 그리지 않았다."],
    "Every Piedmont DOCG and DOC with its hectares, and the communes of Barolo, Barbaresco and Roero with their MGA": [
        "Chaque DOCG et DOC du Piémont avec ses hectares, et les communes de Barolo, Barbaresco et Roero avec leurs MGA",
        "Ogni DOCG e DOC del Piemonte con i suoi ettari, e i comuni di Barolo, Barbaresco e Roero con le loro MGA",
        "Jede DOCG und DOC des Piemonts mit ihren Hektar, und die Gemeinden von Barolo, Barbaresco und Roero mit ihren MGA",
        "Cada DOCG y DOC del Piamonte con sus hectáreas, y los municipios de Barolo, Barbaresco y Roero con sus MGA",
        "Cada DOCG e DOC do Piemonte com os seus hectares, e as comunas de Barolo, Barbaresco e Roero com as suas MGA",
        "Elke DOCG en DOC van Piëmont met haar hectares, en de gemeenten van Barolo, Barbaresco en Roero met hun MGA",
        "ピエモンテのすべてのDOCGとDOCを面積とともに、バローロ、バルバレスコ、ロエロの村をMGAとともに",
        "皮埃蒙特每个DOCG与DOC及其公顷数，以及巴罗洛、巴巴莱斯科和罗埃罗的村镇及其MGA",
        "피에몬테의 모든 DOCG와 DOC의 면적, 그리고 바롤로·바르바레스코·로에로의 마을과 MGA"],
    "Every Tuscan DOCG and DOC with its hectares, the sub-zones of Chianti and the UGA of Chianti Classico": [
        "Chaque DOCG et DOC de Toscane avec ses hectares, les sous-zones du Chianti et les UGA du Chianti Classico",
        "Ogni DOCG e DOC della Toscana con i suoi ettari, le sottozone del Chianti e le UGA del Chianti Classico",
        "Jede DOCG und DOC der Toskana mit ihren Hektar, die Unterzonen des Chianti und die UGA des Chianti Classico",
        "Cada DOCG y DOC de la Toscana con sus hectáreas, las subzonas del Chianti y las UGA del Chianti Classico",
        "Cada DOCG e DOC da Toscana com os seus hectares, as subzonas do Chianti e as UGA do Chianti Classico",
        "Elke DOCG en DOC van Toscane met haar hectares, de subzones van Chianti en de UGA van Chianti Classico",
        "トスカーナのすべてのDOCGとDOCを面積とともに、キアンティのサブゾーンとキアンティ・クラッシコのUGA",
        "托斯卡纳每个DOCG与DOC及其公顷数，基安蒂的子产区与经典基安蒂的UGA",
        "토스카나의 모든 DOCG와 DOC의 면적, 키안티의 하위 지구와 키안티 클라시코의 UGA"],
    "Every DOCG and DOC with its hectares, and the communes of Barolo, Barbaresco and Roero with their MGA.": [
        "Chaque DOCG et DOC avec ses hectares, et les communes de Barolo, Barbaresco et Roero avec leurs MGA.",
        "Ogni DOCG e DOC con i suoi ettari, e i comuni di Barolo, Barbaresco e Roero con le loro MGA.",
        "Jede DOCG und DOC mit ihren Hektar, und die Gemeinden von Barolo, Barbaresco und Roero mit ihren MGA.",
        "Cada DOCG y DOC con sus hectáreas, y los municipios de Barolo, Barbaresco y Roero con sus MGA.",
        "Cada DOCG e DOC com os seus hectares, e as comunas de Barolo, Barbaresco e Roero com as suas MGA.",
        "Elke DOCG en DOC met haar hectares, en de gemeenten van Barolo, Barbaresco en Roero met hun MGA.",
        "すべてのDOCGとDOCを面積とともに。バローロ、バルバレスコ、ロエロの村はMGAとともに。",
        "每个DOCG与DOC及其公顷数，以及巴罗洛、巴巴莱斯科和罗埃罗的村镇及其MGA。",
        "모든 DOCG와 DOC의 면적, 그리고 바롤로·바르바레스코·로에로의 마을과 MGA."],
    "Every DOCG and DOC with its hectares, the Chianti sub-zones, the Chianti Classico UGA and the Pievi of Montepulciano.": [
        "Chaque DOCG et DOC avec ses hectares, les sous-zones du Chianti, les UGA du Chianti Classico et les Pievi de Montepulciano.",
        "Ogni DOCG e DOC con i suoi ettari, le sottozone del Chianti, le UGA del Chianti Classico e le Pievi di Montepulciano.",
        "Jede DOCG und DOC mit ihren Hektar, die Unterzonen des Chianti, die UGA des Chianti Classico und die Pievi von Montepulciano.",
        "Cada DOCG y DOC con sus hectáreas, las subzonas del Chianti, las UGA del Chianti Classico y las Pievi de Montepulciano.",
        "Cada DOCG e DOC com os seus hectares, as subzonas do Chianti, as UGA do Chianti Classico e as Pievi de Montepulciano.",
        "Elke DOCG en DOC met haar hectares, de subzones van Chianti, de UGA van Chianti Classico en de Pievi van Montepulciano.",
        "すべてのDOCGとDOCを面積とともに。キアンティのサブゾーン、キアンティ・クラッシコのUGA、モンテプルチアーノのピエーヴェ。",
        "每个DOCG与DOC及其公顷数，基安蒂子产区、经典基安蒂UGA和蒙特普齐亚诺的Pievi。",
        "모든 DOCG와 DOC의 면적, 키안티의 하위 지구, 키안티 클라시코의 UGA, 몬테풀치아노의 피에베."],
    "Free preview: Piedmont place {n} of {free}. A free account opens all {total}.": [
        "Aperçu gratuit : lieu du Piémont {n} sur {free}. Un compte gratuit ouvre les {total}.",
        "Anteprima gratuita: luogo del Piemonte {n} di {free}. Un account gratuito li apre tutti e {total}.",
        "Kostenlose Vorschau: Ort im Piemont {n} von {free}. Ein kostenloses Konto öffnet alle {total}.",
        "Vista previa gratuita: lugar del Piamonte {n} de {free}. Una cuenta gratuita abre los {total}.",
        "Pré-visualização gratuita: lugar do Piemonte {n} de {free}. Uma conta gratuita abre todos os {total}.",
        "Gratis voorproef: plaats in Piëmont {n} van {free}. Een gratis account opent alle {total}.",
        "無料プレビュー：ピエモンテの場所 {n}/{free}。無料アカウントで全{total}件が開きます。",
        "免费预览：皮埃蒙特地点 {n}/{free}。免费账户可打开全部 {total} 个。",
        "무료 미리보기: 피에몬테 장소 {n}/{free}. 무료 계정으로 {total}곳 모두 열립니다."],
    "Free preview: Tuscany place {n} of {free}. A free account opens all {total}.": [
        "Aperçu gratuit : lieu de Toscane {n} sur {free}. Un compte gratuit ouvre les {total}.",
        "Anteprima gratuita: luogo della Toscana {n} di {free}. Un account gratuito li apre tutti e {total}.",
        "Kostenlose Vorschau: Ort in der Toskana {n} von {free}. Ein kostenloses Konto öffnet alle {total}.",
        "Vista previa gratuita: lugar de la Toscana {n} de {free}. Una cuenta gratuita abre los {total}.",
        "Pré-visualização gratuita: lugar da Toscana {n} de {free}. Uma conta gratuita abre todos os {total}.",
        "Gratis voorproef: plaats in Toscane {n} van {free}. Een gratis account opent alle {total}.",
        "無料プレビュー：トスカーナの場所 {n}/{free}。無料アカウントで全{total}件が開きます。",
        "免费预览：托斯卡纳地点 {n}/{free}。免费账户可打开全部 {total} 个。",
        "무료 미리보기: 토스카나 장소 {n}/{free}. 무료 계정으로 {total}곳 모두 열립니다."],
    "You have explored {n} Piedmont places for free. A free account opens all {total}: every DOC and every commune of Barolo, Barbaresco and Roero, with hectares, MGA, rules, terrain, soils and producers.": [
        "Vous avez exploré {n} lieux du Piémont gratuitement. Un compte gratuit ouvre les {total} : chaque DOC et chaque commune de Barolo, Barbaresco et Roero, avec hectares, MGA, règles, relief, sols et producteurs.",
        "Hai esplorato {n} luoghi del Piemonte gratis. Un account gratuito li apre tutti e {total}: ogni DOC e ogni comune di Barolo, Barbaresco e Roero, con ettari, MGA, regole, terreno, suoli e produttori.",
        "Sie haben {n} Orte im Piemont kostenlos erkundet. Ein kostenloses Konto öffnet alle {total}: jede DOC und jede Gemeinde von Barolo, Barbaresco und Roero, mit Hektar, MGA, Regeln, Gelände, Böden und Erzeugern.",
        "Has explorado {n} lugares del Piamonte gratis. Una cuenta gratuita abre los {total}: cada DOC y cada municipio de Barolo, Barbaresco y Roero, con hectáreas, MGA, normas, relieve, suelos y productores.",
        "Explorou {n} lugares do Piemonte gratuitamente. Uma conta gratuita abre todos os {total}: cada DOC e cada comuna de Barolo, Barbaresco e Roero, com hectares, MGA, regras, relevo, solos e produtores.",
        "Je hebt {n} plaatsen in Piëmont gratis verkend. Een gratis account opent alle {total}: elke DOC en elke gemeente van Barolo, Barbaresco en Roero, met hectares, MGA, regels, terrein, bodems en producenten.",
        "ピエモンテの{n}か所を無料で見ました。無料アカウントで全{total}件が開きます：すべてのDOC、バローロ、バルバレスコ、ロエロのすべての村を、面積、MGA、規定、地形、土壌、生産者とともに。",
        "您已免费浏览 {n} 个皮埃蒙特地点。免费账户可打开全部 {total} 个：每个DOC以及巴罗洛、巴巴莱斯科和罗埃罗的每个村镇，含公顷数、MGA、规定、地形、土壤和生产商。",
        "피에몬테 장소 {n}곳을 무료로 둘러봤습니다. 무료 계정으로 {total}곳 모두 열립니다: 모든 DOC와 바롤로·바르바레스코·로에로의 모든 마을을 면적, MGA, 규정, 지형, 토양, 생산자와 함께."],
    "You have explored {n} Tuscan places for free. A free account opens all {total}: every DOC, Chianti sub-zone, Chianti Classico UGA and Montepulciano Pieve, with hectares, rules, terrain, soils and producers.": [
        "Vous avez exploré {n} lieux de Toscane gratuitement. Un compte gratuit ouvre les {total} : chaque DOC, sous-zone du Chianti, UGA du Chianti Classico et Pieve de Montepulciano, avec hectares, règles, relief, sols et producteurs.",
        "Hai esplorato {n} luoghi della Toscana gratis. Un account gratuito li apre tutti e {total}: ogni DOC, sottozona del Chianti, UGA del Chianti Classico e Pieve di Montepulciano, con ettari, regole, terreno, suoli e produttori.",
        "Sie haben {n} Orte in der Toskana kostenlos erkundet. Ein kostenloses Konto öffnet alle {total}: jede DOC, Chianti-Unterzone, Chianti-Classico-UGA und Pieve von Montepulciano, mit Hektar, Regeln, Gelände, Böden und Erzeugern.",
        "Has explorado {n} lugares de la Toscana gratis. Una cuenta gratuita abre los {total}: cada DOC, subzona del Chianti, UGA del Chianti Classico y Pieve de Montepulciano, con hectáreas, normas, relieve, suelos y productores.",
        "Explorou {n} lugares da Toscana gratuitamente. Uma conta gratuita abre todos os {total}: cada DOC, subzona do Chianti, UGA do Chianti Classico e Pieve de Montepulciano, com hectares, regras, relevo, solos e produtores.",
        "Je hebt {n} plaatsen in Toscane gratis verkend. Een gratis account opent alle {total}: elke DOC, Chianti-subzone, Chianti Classico-UGA en Pieve van Montepulciano, met hectares, regels, terrein, bodems en producenten.",
        "トスカーナの{n}か所を無料で見ました。無料アカウントで全{total}件が開きます：すべてのDOC、キアンティのサブゾーン、キアンティ・クラッシコのUGA、モンテプルチアーノのピエーヴェを、面積、規定、地形、土壌、生産者とともに。",
        "您已免费浏览 {n} 个托斯卡纳地点。免费账户可打开全部 {total} 个：每个DOC、基安蒂子产区、经典基安蒂UGA和蒙特普齐亚诺Pieve，含公顷数、规定、地形、土壤和生产商。",
        "토스카나 장소 {n}곳을 무료로 둘러봤습니다. 무료 계정으로 {total}곳 모두 열립니다: 모든 DOC, 키안티 하위 지구, 키안티 클라시코 UGA, 몬테풀치아노 피에베를 면적, 규정, 지형, 토양, 생산자와 함께."],
    "Piemonte and Toscana in depth: cru communes, sub-zones, UGA and Pievi": [
        "Piémont et Toscane en profondeur : communes de cru, sous-zones, UGA et Pievi",
        "Piemonte e Toscana in profondità: comuni dei cru, sottozone, UGA e Pievi",
        "Piemont und Toskana im Detail: Cru-Gemeinden, Unterzonen, UGA und Pievi",
        "Piamonte y Toscana en profundidad: municipios de cru, subzonas, UGA y Pievi",
        "Piemonte e Toscana em profundidade: comunas de cru, subzonas, UGA e Pievi",
        "Piëmont en Toscane in detail: crugemeenten, subzones, UGA en Pievi",
        "ピエモンテとトスカーナを深く：クリュの村、サブゾーン、UGA、ピエーヴェ",
        "深入皮埃蒙特与托斯卡纳：名园村镇、子产区、UGA与Pievi",
        "피에몬테와 토스카나 깊이 보기: 크뤼 마을, 하위 지구, UGA, 피에베"],
    "Langhe and Roero": ["Langhe et Roero", "Langhe e Roero", "Langhe und Roero", "Langhe y Roero", "Langhe e Roero", "Langhe en Roero",
                         "ランゲとロエロ", "朗格与罗埃罗", "랑게와 로에로"],
    "Asti and Monferrato": ["Asti et Monferrato", "Astigiano e Monferrato", "Asti und Monferrato", "Asti y Monferrato", "Asti e Monferrato",
                            "Asti en Monferrato", "アスティとモンフェッラート", "阿斯蒂与蒙费拉托", "아스티와 몬페라토"],
    "Alto Piemonte": ["Alto Piemonte"] * 6 + ["アルト・ピエモンテ", "上皮埃蒙特", "알토 피에몬테"],
    "Turin, Canavese and Pinerolese": ["Turin, Canavese et Pinerolese", "Torino, Canavese e Pinerolese", "Turin, Canavese und Pinerolese",
                                       "Turín, Canavese y Pinerolese", "Turim, Canavese e Pinerolese", "Turijn, Canavese en Pinerolese",
                                       "トリノ、カナヴェーゼ、ピネロレーゼ", "都灵、卡纳韦塞与皮内罗莱塞", "토리노, 카나베세, 피네롤레세"],
    "Chianti and central Tuscany": ["Chianti et Toscane centrale", "Chianti e Toscana centrale", "Chianti und Zentraltoskana",
                                    "Chianti y Toscana central", "Chianti e Toscana central", "Chianti en Midden-Toscane",
                                    "キアンティとトスカーナ中部", "基安蒂与托斯卡纳中部", "키안티와 토스카나 중부"],
    "Montalcino, Montepulciano and southern Tuscany": ["Montalcino, Montepulciano et Toscane du Sud", "Montalcino, Montepulciano e Toscana meridionale",
                                                       "Montalcino, Montepulciano und Südtoskana", "Montalcino, Montepulciano y Toscana meridional",
                                                       "Montalcino, Montepulciano e sul da Toscana", "Montalcino, Montepulciano en Zuid-Toscane",
                                                       "モンタルチーノ、モンテプルチアーノとトスカーナ南部", "蒙塔奇诺、蒙特普齐亚诺与托斯卡纳南部",
                                                       "몬탈치노, 몬테풀치아노와 토스카나 남부"],
    "Maremma and the coast": ["Maremme et littoral", "Maremma e costa", "Maremma und Küste", "Maremma y la costa", "Maremma e a costa",
                              "Maremma en de kust", "マレンマと海岸", "马雷马与沿海", "마렘마와 해안"],
    "Northern Tuscany": ["Toscane du Nord", "Toscana settentrionale", "Nordtoskana", "Toscana septentrional", "Norte da Toscana",
                         "Noord-Toscane", "トスカーナ北部", "托斯卡纳北部", "토스카나 북부"],
}


def main():
    for i, lang in enumerate(LANGS):
        p = os.path.join(I18N, lang + ".json")
        d = json.load(open(p, encoding="utf-8"))
        n = 0
        for k, v in T.items():
            assert len(v) == len(LANGS), k
            if k not in d:
                d[k] = v[i]
                n += 1
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(lang, "+", n)


if __name__ == "__main__":
    main()
