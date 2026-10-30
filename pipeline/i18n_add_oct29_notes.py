"""One-off: translations of the Champagne zone notes and fixed sheet texts of 29 October 2026 (pipeline/champagne.py).

Merges into web/i18n/<lang>.json without touching existing entries. Safe to rerun.
Order of each list: fr, it, de, es, pt, nl, ja, zh, ko.
"""
import json
import os

I18N = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "i18n")
LANGS = ["fr", "it", "de", "es", "pt", "nl", "ja", "zh", "ko"]

T = {
    "The wooded plateau between Reims and Épernay, with vines on its north, east and south slopes. Pinot Noir leads, above all in the nine grand cru villages of the Grande Montagne. The zone also takes in the Massif de Saint-Thierry, the Monts de Berru and the Vesle and Ardre valleys.": [
        "Le plateau boisé entre Reims et Épernay, avec des vignes sur ses versants nord, est et sud. Le pinot noir domine, surtout dans les neuf villages grands crus de la Grande Montagne. La zone comprend aussi le massif de Saint-Thierry, les monts de Berru et les vallées de la Vesle et de l'Ardre.",
        "L'altopiano boscoso tra Reims ed Épernay, con vigne sui versanti nord, est e sud. Domina il Pinot Noir, soprattutto nei nove villaggi grand cru della Grande Montagne. La zona comprende anche il massiccio di Saint-Thierry, i monti di Berru e le valli della Vesle e dell'Ardre.",
        "Das bewaldete Plateau zwischen Reims und Épernay, mit Reben an den Nord-, Ost- und Südhängen. Pinot Noir führt, vor allem in den neun Grand-Cru-Dörfern der Grande Montagne. Zur Zone gehören auch das Massif de Saint-Thierry, die Monts de Berru und die Täler von Vesle und Ardre.",
        "La meseta boscosa entre Reims y Épernay, con viñas en sus laderas norte, este y sur. Domina la Pinot Noir, sobre todo en los nueve pueblos grand cru de la Grande Montagne. La zona incluye también el macizo de Saint-Thierry, los montes de Berru y los valles del Vesle y el Ardre.",
        "O planalto arborizado entre Reims e Épernay, com vinhas nas encostas norte, este e sul. Domina a Pinot Noir, sobretudo nas nove aldeias grand cru da Grande Montagne. A zona inclui também o maciço de Saint-Thierry, os montes de Berru e os vales do Vesle e do Ardre.",
        "Het beboste plateau tussen Reims en Épernay, met wijnstokken op de noord-, oost- en zuidhellingen. Pinot noir overheerst, vooral in de negen grand-crudorpen van de Grande Montagne. De zone omvat ook het Massif de Saint-Thierry, de Monts de Berru en de dalen van de Vesle en de Ardre.",
        "ランスとエペルネの間に広がる森の台地で、北・東・南の斜面にブドウ畑がある。ピノ・ノワールが中心で、とくにグランド・モンターニュの9つのグラン・クリュの村で多い。サン・ティエリ山塊、ベリュの丘、ヴェール川とアルドル川の谷もこの地区に含まれる。",
        "兰斯与埃佩尔奈之间的林木高原，北、东、南坡种有葡萄。黑皮诺占主导，尤其是大山区的九个特级园村庄。该区还包括圣蒂埃里山地、贝吕丘陵以及韦勒河和阿尔德尔河谷。",
        "랭스와 에페르네 사이의 숲이 우거진 고원으로, 북·동·남쪽 비탈에 포도밭이 있다. 피노 누아가 중심이며, 특히 그랑드 몽타뉴의 그랑 크뤼 마을 9곳에서 그렇다. 생티에리 산괴, 베뤼 언덕, 벨 강과 아르드르 강 계곡도 이 지구에 속한다."],
    "The largest zone. It follows the Marne from east of Épernay west into the Aisne and the Seine-et-Marne. Meunier leads on the clay slopes of the valley. The Grande Vallée around Aÿ is Pinot Noir country, with the grands crus of Aÿ and Tours-sur-Marne.": [
        "La plus grande zone. Elle suit la Marne de l'est d'Épernay jusqu'à l'Aisne et la Seine-et-Marne à l'ouest. Le meunier domine sur les coteaux argileux de la vallée. La Grande Vallée autour d'Aÿ est un pays de pinot noir, avec les grands crus d'Aÿ et de Tours-sur-Marne.",
        "La zona più grande. Segue la Marna da est di Épernay verso ovest fino all'Aisne e alla Seine-et-Marne. Sui pendii argillosi della valle domina il Meunier. La Grande Vallée intorno ad Aÿ è terra di Pinot Noir, con i grand cru di Aÿ e Tours-sur-Marne.",
        "Die größte Zone. Sie folgt der Marne von östlich von Épernay nach Westen bis ins Aisne und ins Seine-et-Marne. An den Tonhängen des Tals führt Meunier. Die Grande Vallée um Aÿ ist Pinot-Noir-Land, mit den Grands Crus Aÿ und Tours-sur-Marne.",
        "La zona más grande. Sigue el Marne desde el este de Épernay hacia el oeste hasta el Aisne y el Sena y Marne. En las laderas arcillosas del valle domina la Meunier. La Grande Vallée en torno a Aÿ es tierra de Pinot Noir, con los grands crus de Aÿ y Tours-sur-Marne.",
        "A maior zona. Segue o Marne desde leste de Épernay para oeste até ao Aisne e ao Sena e Marne. Nas encostas argilosas do vale domina a Meunier. A Grande Vallée em torno de Aÿ é terra de Pinot Noir, com os grands crus de Aÿ e Tours-sur-Marne.",
        "De grootste zone. Ze volgt de Marne van ten oosten van Épernay westwaarts tot in de Aisne en de Seine-et-Marne. Op de kleihellingen van het dal overheerst meunier. De Grande Vallée rond Aÿ is pinot-noirland, met de grands crus Aÿ en Tours-sur-Marne.",
        "最大の地区。エペルネの東からマルヌ川に沿って西へ、エーヌ県とセーヌ＝エ＝マルヌ県まで続く。谷の粘土質の斜面ではムニエが中心。アイ周辺のグランド・ヴァレはピノ・ノワールの地で、アイとトゥール・シュル・マルヌのグラン・クリュがある。",
        "最大的产区。沿马恩河从埃佩尔奈以东向西延伸至埃纳省和塞纳-马恩省。河谷的黏土坡上以莫尼耶为主。阿伊周围的大河谷是黑皮诺之乡，有阿伊和马恩河畔图尔两个特级园。",
        "가장 큰 지구. 에페르네 동쪽에서 마른 강을 따라 서쪽으로 엔 주와 센에마른 주까지 이어진다. 계곡의 점토 비탈에서는 뫼니에가 중심이다. 아이 주변의 그랑드 발레는 피노 누아의 땅으로, 아이와 투르쉬르마른의 그랑 크뤼가 있다."],
    "An east-facing chalk slope running south from Épernay to Vertus. It is almost all Chardonnay. Six of the 17 grand cru villages are here.": [
        "Un coteau de craie exposé à l'est, d'Épernay jusqu'à Vertus au sud. Presque tout en chardonnay. Six des 17 villages grands crus s'y trouvent.",
        "Un pendio di gesso esposto a est che va da Épernay a sud fino a Vertus. È quasi tutto Chardonnay. Qui si trovano sei dei 17 villaggi grand cru.",
        "Ein nach Osten gerichteter Kreidehang von Épernay südwärts bis Vertus. Fast nur Chardonnay. Sechs der 17 Grand-Cru-Dörfer liegen hier.",
        "Una ladera de creta orientada al este que va de Épernay hacia el sur hasta Vertus. Casi todo es Chardonnay. Aquí están seis de los 17 pueblos grand cru.",
        "Uma encosta de cré virada a leste que vai de Épernay para sul até Vertus. É quase toda Chardonnay. Aqui ficam seis das 17 aldeias grand cru.",
        "Een naar het oosten gerichte krijthelling van Épernay zuidwaarts tot Vertus. Bijna alleen chardonnay. Zes van de 17 grand-crudorpen liggen hier.",
        "エペルネから南のヴェルテュまで続く東向きの白亜質の斜面。ほぼすべてがシャルドネ。17のグラン・クリュの村のうち6つがここにある。",
        "一道朝东的白垩坡，从埃佩尔奈向南延伸至韦尔蒂。几乎全是霞多丽。17个特级园村庄中有6个在这里。",
        "에페르네에서 남쪽 베르튀까지 이어지는 동향 백악질 비탈. 거의 모두 샤르도네다. 그랑 크뤼 마을 17곳 중 6곳이 여기에 있다."],
    "Twenty communes around the marshes of Saint-Gond, between the Côte des Blancs and the Côte de Sézanne. Chardonnay leads, with much Meunier. The houses' union counts it in a wider Côte des Blancs.": [
        "Vingt communes autour des marais de Saint-Gond, entre la Côte des Blancs et la Côte de Sézanne. Le chardonnay domine, avec beaucoup de meunier. L'union des maisons le compte dans une Côte des Blancs élargie.",
        "Venti comuni intorno alle paludi di Saint-Gond, tra la Côte des Blancs e la Côte de Sézanne. Domina lo Chardonnay, con molto Meunier. L'unione delle maison lo conta in una Côte des Blancs più ampia.",
        "Zwanzig Gemeinden um die Sümpfe von Saint-Gond, zwischen der Côte des Blancs und der Côte de Sézanne. Chardonnay führt, mit viel Meunier. Der Verband der Häuser zählt sie zu einer erweiterten Côte des Blancs.",
        "Veinte municipios en torno a las marismas de Saint-Gond, entre la Côte des Blancs y la Côte de Sézanne. Domina la Chardonnay, con mucha Meunier. La unión de las casas lo cuenta en una Côte des Blancs ampliada.",
        "Vinte comunas em torno dos pântanos de Saint-Gond, entre a Côte des Blancs e a Côte de Sézanne. Domina a Chardonnay, com muita Meunier. A união das casas conta-o numa Côte des Blancs alargada.",
        "Twintig gemeenten rond de moerassen van Saint-Gond, tussen de Côte des Blancs en de Côte de Sézanne. Chardonnay overheerst, met veel meunier. De unie van de huizen rekent het tot een ruimere Côte des Blancs.",
        "サン・ゴンの湿地を囲む20のコミューンで、コート・デ・ブランとコート・ド・セザンヌの間にある。シャルドネが中心で、ムニエも多い。メゾン組合はこれを広義のコート・デ・ブランに含める。",
        "圣贡沼泽周围的二十个市镇，位于白丘与塞扎讷丘之间。以霞多丽为主，莫尼耶也很多。酒商联合会将其计入广义的白丘。",
        "생공 습지 주변의 20개 코뮌으로, 코트 데 블랑과 코트 드 세잔 사이에 있다. 샤르도네가 중심이고 뫼니에도 많다. 메종 연합은 이를 넓은 의미의 코트 데 블랑에 포함한다."],
    "Slopes around Sézanne in the south of the Marne. Chardonnay leads. The houses' union counts it in a wider Côte des Blancs.": [
        "Des coteaux autour de Sézanne, au sud de la Marne. Le chardonnay domine. L'union des maisons le compte dans une Côte des Blancs élargie.",
        "Pendii intorno a Sézanne, nel sud della Marna. Domina lo Chardonnay. L'unione delle maison lo conta in una Côte des Blancs più ampia.",
        "Hänge um Sézanne im Süden des Départements Marne. Chardonnay führt. Der Verband der Häuser zählt sie zu einer erweiterten Côte des Blancs.",
        "Laderas en torno a Sézanne, en el sur del Marne. Domina la Chardonnay. La unión de las casas lo cuenta en una Côte des Blancs ampliada.",
        "Encostas em torno de Sézanne, no sul do Marne. Domina a Chardonnay. A união das casas conta-o numa Côte des Blancs alargada.",
        "Hellingen rond Sézanne in het zuiden van de Marne. Chardonnay overheerst. De unie van de huizen rekent het tot een ruimere Côte des Blancs.",
        "マルヌ県南部、セザンヌ周辺の斜面。シャルドネが中心。メゾン組合はこれを広義のコート・デ・ブランに含める。",
        "马恩省南部塞扎讷周围的坡地。以霞多丽为主。酒商联合会将其计入广义的白丘。",
        "마른 주 남부 세잔 주변의 비탈. 샤르도네가 중심이다. 메종 연합은 이를 넓은 의미의 코트 데 블랑에 포함한다."],
    "A small outlying area around Vitry-le-François in the east of the Marne. It is almost all Chardonnay. The houses' union counts it in a wider Côte des Blancs.": [
        "Une petite zone isolée autour de Vitry-le-François, à l'est de la Marne. Presque tout en chardonnay. L'union des maisons la compte dans une Côte des Blancs élargie.",
        "Una piccola area isolata intorno a Vitry-le-François, nell'est della Marna. È quasi tutto Chardonnay. L'unione delle maison la conta in una Côte des Blancs più ampia.",
        "Ein kleines, abgelegenes Gebiet um Vitry-le-François im Osten des Départements Marne. Fast nur Chardonnay. Der Verband der Häuser zählt es zu einer erweiterten Côte des Blancs.",
        "Una pequeña zona apartada en torno a Vitry-le-François, en el este del Marne. Casi todo es Chardonnay. La unión de las casas la cuenta en una Côte des Blancs ampliada.",
        "Uma pequena área isolada em torno de Vitry-le-François, no leste do Marne. É quase toda Chardonnay. A união das casas conta-a numa Côte des Blancs alargada.",
        "Een klein afgelegen gebied rond Vitry-le-François in het oosten van de Marne. Bijna alleen chardonnay. De unie van de huizen rekent het tot een ruimere Côte des Blancs.",
        "マルヌ県東部、ヴィトリ・ル・フランソワ周辺の小さな飛び地。ほぼすべてがシャルドネ。メゾン組合はこれを広義のコート・デ・ブランに含める。",
        "马恩省东部维特里勒弗朗索瓦周围的一小块外围产区。几乎全是霞多丽。酒商联合会将其计入广义的白丘。",
        "마른 주 동부 비트리르프랑수아 주변의 작은 외곽 지역. 거의 모두 샤르도네다. 메종 연합은 이를 넓은 의미의 코트 데 블랑에 포함한다."],
    "A single chalk hill just west of Troyes in the Aube, mostly Chardonnay. The houses' union counts it in a wider Côte des Blancs, far to the north.": [
        "Une seule colline de craie juste à l'ouest de Troyes, dans l'Aube, surtout en chardonnay. L'union des maisons la compte dans une Côte des Blancs élargie, loin au nord.",
        "Un'unica collina di gesso appena a ovest di Troyes, nell'Aube, soprattutto Chardonnay. L'unione delle maison la conta in una Côte des Blancs più ampia, molto più a nord.",
        "Ein einzelner Kreidehügel gleich westlich von Troyes im Département Aube, meist Chardonnay. Der Verband der Häuser zählt ihn zu einer erweiterten Côte des Blancs, weit im Norden.",
        "Una sola colina de creta justo al oeste de Troyes, en el Aube, sobre todo Chardonnay. La unión de las casas la cuenta en una Côte des Blancs ampliada, muy al norte.",
        "Uma única colina de cré logo a oeste de Troyes, no Aube, sobretudo Chardonnay. A união das casas conta-a numa Côte des Blancs alargada, bem mais a norte.",
        "Eén enkele krijtheuvel net ten westen van Troyes in de Aube, vooral chardonnay. De unie van de huizen rekent hem tot een ruimere Côte des Blancs, ver naar het noorden.",
        "オーブ県トロワのすぐ西にある白亜の丘ひとつで、主にシャルドネ。メゾン組合は遠く北の広義のコート・デ・ブランに含める。",
        "奥布省特鲁瓦以西的一座白垩小山，以霞多丽为主。酒商联合会将其计入远在北方的广义白丘。",
        "오브 주 트루아 바로 서쪽의 백악 언덕 하나로, 주로 샤르도네다. 메종 연합은 멀리 북쪽의 넓은 의미의 코트 데 블랑에 포함한다."],
    "The south of the appellation, in the Aube, with two communes in the Haute-Marne. Pinot Noir covers more than four fifths of the vines, on Kimmeridgian marl. It splits into the Bar-sur-Aubois and the Barséquanais, which includes Les Riceys.": [
        "Le sud de l'appellation, dans l'Aube, avec deux communes en Haute-Marne. Le pinot noir couvre plus des quatre cinquièmes des vignes, sur des marnes kimméridgiennes. Elle se divise en Bar-sur-Aubois et Barséquanais, qui comprend Les Riceys.",
        "Il sud della denominazione, nell'Aube, con due comuni nell'Alta Marna. Il Pinot Noir copre più dei quattro quinti delle vigne, su marne kimmeridgiane. Si divide in Bar-sur-Aubois e Barséquanais, che comprende Les Riceys.",
        "Der Süden der Appellation, im Département Aube, mit zwei Gemeinden in der Haute-Marne. Pinot Noir bedeckt mehr als vier Fünftel der Reben, auf Kimmeridge-Mergel. Sie teilt sich in Bar-sur-Aubois und Barséquanais, zu dem Les Riceys gehört.",
        "El sur de la denominación, en el Aube, con dos municipios en el Alto Marne. La Pinot Noir cubre más de cuatro quintas partes de las viñas, sobre margas kimmeridgienses. Se divide en Bar-sur-Aubois y Barséquanais, que incluye Les Riceys.",
        "O sul da denominação, no Aube, com duas comunas no Alto Marne. A Pinot Noir cobre mais de quatro quintos das vinhas, sobre margas kimeridgianas. Divide-se em Bar-sur-Aubois e Barséquanais, que inclui Les Riceys.",
        "Het zuiden van de appellatie, in de Aube, met twee gemeenten in de Haute-Marne. Pinot noir beslaat meer dan vier vijfde van de wijnstokken, op kimmeridge-mergel. Ze valt uiteen in Bar-sur-Aubois en Barséquanais, waartoe Les Riceys behoort.",
        "アペラシオンの南部で、オーブ県にあり、オート＝マルヌ県の2つのコミューンを含む。キンメリッジ泥灰土の上で、ピノ・ノワールが畑の5分の4以上を占める。バール・シュル・オーボワと、レ・リセを含むバルセカネに分かれる。",
        "产区南部，位于奥布省，另有两个市镇在上马恩省。黑皮诺占葡萄园的五分之四以上，种植在启莫里阶泥灰岩上。分为奥布河畔巴尔区和包括里赛的塞纳河畔巴尔区。",
        "아펠라시옹의 남부로 오브 주에 있으며, 오트마른 주의 코뮌 2곳을 포함한다. 키메리지 이회토 위에서 피노 누아가 포도밭의 5분의 4 이상을 차지한다. 바르쉬르오부아와 레 리세를 포함하는 바르세카네로 나뉜다."],
    "The commune boundary: the Champagne appellation is delimited commune by commune. The vines are only part of it: the vineyard layer of the map shows where they are.": [
        "Les limites de la commune : l'appellation champagne est délimitée commune par commune. Les vignes n'en couvrent qu'une partie : la couche des vignobles de la carte montre où elles sont.",
        "Il confine del comune: la denominazione Champagne è delimitata comune per comune. Le vigne ne coprono solo una parte: il livello dei vigneti della mappa mostra dove sono.",
        "Die Gemeindegrenze: Die Appellation Champagne ist Gemeinde für Gemeinde abgegrenzt. Die Reben bedecken nur einen Teil davon: Die Rebflächen-Ebene der Karte zeigt, wo sie stehen.",
        "El límite del municipio: la denominación Champagne se delimita municipio por municipio. Las viñas solo cubren una parte: la capa de viñedos del mapa muestra dónde están.",
        "O limite da comuna: a denominação Champagne é delimitada comuna a comuna. As vinhas cobrem apenas uma parte: a camada de vinhas do mapa mostra onde estão.",
        "De gemeentegrens: de appellatie Champagne is gemeente per gemeente afgebakend. De wijnstokken beslaan maar een deel: de wijngaardlaag van de kaart toont waar ze staan.",
        "コミューンの境界。シャンパーニュのアペラシオンはコミューン単位で定められている。ブドウ畑はその一部だけで、地図のブドウ畑レイヤーで場所がわかる。",
        "市镇边界：香槟产区按市镇划定。葡萄园只占其中一部分：地图的葡萄园图层显示其位置。",
        "코뮌 경계. 샹파뉴 아펠라시옹은 코뮌 단위로 정해진다. 포도밭은 그 일부일 뿐이며 지도의 포도밭 레이어에서 위치를 볼 수 있다."],
    "The Côte des Blancs proper, 10 communes. With the Val du Petit Morin, Côte de Sézanne, Vitryat and Montgueux, the wider zone of the Union des Maisons de Champagne covers 6,304 ha.": [
        "La Côte des Blancs proprement dite, 10 communes. Avec le Val du Petit Morin, la Côte de Sézanne, le Vitryat et Montgueux, la zone élargie de l'Union des Maisons de Champagne couvre 6 304 ha.",
        "La Côte des Blancs vera e propria, 10 comuni. Con Val du Petit Morin, Côte de Sézanne, Vitryat e Montgueux, la zona più ampia dell'Union des Maisons de Champagne copre 6.304 ha.",
        "Die eigentliche Côte des Blancs, 10 Gemeinden. Mit Val du Petit Morin, Côte de Sézanne, Vitryat und Montgueux umfasst die erweiterte Zone der Union des Maisons de Champagne 6.304 ha.",
        "La Côte des Blancs propiamente dicha, 10 municipios. Con el Val du Petit Morin, la Côte de Sézanne, el Vitryat y Montgueux, la zona ampliada de la Union des Maisons de Champagne cubre 6304 ha.",
        "A Côte des Blancs propriamente dita, 10 comunas. Com o Val du Petit Morin, a Côte de Sézanne, o Vitryat e Montgueux, a zona alargada da Union des Maisons de Champagne cobre 6304 ha.",
        "De eigenlijke Côte des Blancs, 10 gemeenten. Met Val du Petit Morin, Côte de Sézanne, Vitryat en Montgueux beslaat de ruimere zone van de Union des Maisons de Champagne 6.304 ha.",
        "本来のコート・デ・ブランで、10のコミューン。ヴァル・デュ・プティ・モラン、コート・ド・セザンヌ、ヴィトリア、モングーを合わせたメゾン組合の広い地区は6,304 ha。",
        "狭义的白丘，共10个市镇。加上小莫兰河谷、塞扎讷丘、维特里亚和蒙格，香槟酒商联合会的广义产区共6,304公顷。",
        "본래의 코트 데 블랑으로 코뮌 10곳. 발 뒤 프티 모랭, 코트 드 세잔, 비트리아, 몽구를 합친 메종 연합의 넓은 지구는 6,304 ha다."],
    "Share of the planted area of the zone. Union des Maisons de Champagne (UMC), aire géographique tables; the year is not given.": [
        "Part de la surface plantée de la zone. Union des Maisons de Champagne (UMC), tableaux de l'aire géographique ; l'année n'est pas indiquée.",
        "Quota della superficie vitata della zona. Union des Maisons de Champagne (UMC), tabelle dell'area geografica; l'anno non è indicato.",
        "Anteil an der bestockten Fläche der Zone. Union des Maisons de Champagne (UMC), Tabellen des geografischen Gebiets; das Jahr ist nicht angegeben.",
        "Parte de la superficie plantada de la zona. Union des Maisons de Champagne (UMC), tablas del área geográfica; no se indica el año.",
        "Parte da área plantada da zona. Union des Maisons de Champagne (UMC), tabelas da área geográfica; o ano não é indicado.",
        "Aandeel in de beplante oppervlakte van de zone. Union des Maisons de Champagne (UMC), tabellen van het geografische gebied; het jaar wordt niet vermeld.",
        "地区の植栽面積に占める割合。シャンパーニュ・メゾン組合（UMC）の地理的区域の表による。年は記載なし。",
        "占该区种植面积的比例。香槟酒商联合会（UMC）地理区域表；未注明年份。",
        "지구 재배 면적에서 차지하는 비율. 샹파뉴 메종 연합(UMC) 지리적 구역 표 기준이며 연도는 표시되지 않음."],
    "a classified estate": ["un cru classé", "un cru classificato", "ein klassifiziertes Weingut", "una finca clasificada", "uma propriedade classificada",
                            "een geklasseerd wijngoed", "格付けシャトー", "一座列级酒庄", "등급 샤토"],
    "a grand cru village": ["un village grand cru", "un villaggio grand cru", "eine Grand-Cru-Gemeinde", "un pueblo grand cru", "uma aldeia grand cru",
                            "een grand-crudorp", "グラン・クリュの村", "一个特级园村庄", "그랑 크뤼 마을"],
    "a premier cru village": ["un village premier cru", "un villaggio premier cru", "eine Premier-Cru-Gemeinde", "un pueblo premier cru", "uma aldeia premier cru",
                              "een premier-crudorp", "プルミエ・クリュの村", "一个一级园村庄", "프르미에 크뤼 마을"],
    "a vineyard zone": ["une zone viticole", "una zona viticola", "eine Weinbauzone", "una zona vitícola", "uma zona vitícola", "een wijnbouwzone",
                        "ブドウ栽培地区", "一个葡萄园区", "포도밭 지구"],
    "a village": ["un village", "un villaggio", "ein Dorf", "un pueblo", "uma aldeia", "een dorp", "村", "一个村庄", "마을"],
    "{rank} in the {list}": ["{rank} dans le {list}", "{rank} nella {list}", "{rank} in der {list}", "{rank} en la {list}", "{rank} na {list}",
                             "{rank} in de {list}", "{list}の{rank}", "{list}中的{rank}", "{list}의 {rank}"],
    "{name} is a classified estate of {parent}: {ranks}.": ["{name} est un cru classé de {parent} : {ranks}.", "{name} è un cru classificato di {parent}: {ranks}.",
        "{name} ist ein klassifiziertes Weingut der Appellation {parent}: {ranks}.", "{name} es una finca clasificada de {parent}: {ranks}.",
        "{name} é uma propriedade classificada de {parent}: {ranks}.", "{name} is een geklasseerd wijngoed van {parent}: {ranks}.",
        "{name}は{parent}の格付けシャトー：{ranks}。", "{name}是{parent}的列级酒庄：{ranks}。", "{name}은(는) {parent}의 등급 샤토: {ranks}."],
    "classified estates": ["crus classés", "cru classificati", "klassifizierte Weingüter", "fincas clasificadas", "propriedades classificadas",
                           "geklasseerde wijngoederen", "格付けシャトー", "列级酒庄", "등급 샤토"],

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
