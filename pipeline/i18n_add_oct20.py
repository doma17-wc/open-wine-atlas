"""One-off: translations for the texts added on 20 October 2026 (vineyard area measured from OpenStreetMap,
vineyards on the map for every country).

Merges into web/i18n/<lang>.json without touching existing entries. Safe to rerun.
"""
import json
import os

I18N = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "i18n")
LANGS = ["fr", "it", "de", "es", "pt", "nl", "ja", "zh", "ko"]

T = {
    "Vineyards worldwide and their area; close up: small rivers, streams, villages and peaks": [
        "Vignes du monde entier et leur surface ; de près : petites rivières, ruisseaux, villages et sommets",
        "Vigneti di tutto il mondo e la loro area; da vicino: piccoli fiumi, torrenti, paesi e vette",
        "Rebflächen weltweit und ihre Fläche; aus der Nähe: kleine Flüsse, Bäche, Dörfer und Gipfel",
        "Viñedos de todo el mundo y su superficie; de cerca: ríos pequeños, arroyos, pueblos y cumbres",
        "Vinhas de todo o mundo e a sua área; de perto: pequenos rios, ribeiros, aldeias e picos",
        "Wijngaarden wereldwijd en hun oppervlakte; van dichtbij: kleine rivieren, beken, dorpen en toppen",
        "世界のブドウ畑とその面積、拡大時：小さな川、小川、村、山頂",
        "全球葡萄园及其面积；放大后：小河、溪流、村庄和山峰",
        "전 세계 포도밭과 면적, 확대 시: 작은 강, 개울, 마을, 봉우리"],
    "Vineyards (OSM)": ["Vignes (OSM)", "Vigneti (OSM)", "Rebflächen (OSM)", "Viñedos (OSM)", "Vinhas (OSM)", "Wijngaarden (OSM)",
                        "ブドウ畑（OSM）", "葡萄园（OSM）", "포도밭(OSM)"],
    "Measuring the vineyards…": ["Mesure des vignes…", "Misurazione dei vigneti…", "Rebflächen werden gemessen…", "Midiendo los viñedos…",
                                 "A medir as vinhas…", "Wijngaarden worden gemeten…", "ブドウ畑を計測中…", "正在测量葡萄园…", "포도밭 측정 중…"],
    "Zoom in on the place to measure its vineyards.": [
        "Zoomez sur le lieu pour mesurer ses vignes.", "Ingrandisci il luogo per misurarne i vigneti.",
        "Zoomen Sie an den Ort heran, um seine Rebflächen zu messen.", "Acerca el mapa al lugar para medir sus viñedos.",
        "Aproxime o mapa do lugar para medir as suas vinhas.", "Zoom in op de plek om de wijngaarden te meten.",
        "ブドウ畑を計測するには、その場所にズームインしてください。", "放大到该地点以测量其葡萄园。", "포도밭을 측정하려면 장소를 확대하세요."],
    "This place is too large to measure its vineyards live. Open one of its appellations.": [
        "Ce lieu est trop vaste pour mesurer ses vignes en direct. Ouvrez l'une de ses appellations.",
        "Questo luogo è troppo esteso per misurarne i vigneti in tempo reale. Apri una delle sue denominazioni.",
        "Dieser Ort ist zu groß, um seine Rebflächen live zu messen. Öffnen Sie eine seiner Appellationen.",
        "Este lugar es demasiado grande para medir sus viñedos en directo. Abre una de sus denominaciones.",
        "Este lugar é demasiado grande para medir as suas vinhas em direto. Abra uma das suas denominações.",
        "Deze plek is te groot om de wijngaarden live te meten. Open een van de herkomstbenamingen erin.",
        "この場所は広すぎるため、ブドウ畑をその場で計測できません。含まれるアペラシオンを開いてください。",
        "该地点范围过大，无法实时测量葡萄园。请打开其中的某个产区。",
        "이곳은 너무 넓어 포도밭을 실시간으로 측정할 수 없습니다. 포함된 아펠라시옹 중 하나를 여세요."],
    "{pct}% of the {ha} ha outline.": ["{pct} % du périmètre de {ha} ha.", "Il {pct}% del perimetro di {ha} ha.", "{pct} % des Umrisses von {ha} ha.",
                                       "El {pct} % del contorno de {ha} ha.", "{pct} % do contorno de {ha} ha.", "{pct}% van de omtrek van {ha} ha.",
                                       "{ha} haの輪郭の{pct}%。", "占{ha}公顷轮廓的{pct}%。", "{ha} ha 경계의 {pct}%."],
    "Large place, measured at a coarse scale: plots under about {ha} ha are left out, so this is a minimum.": [
        "Lieu étendu, mesuré à une échelle grossière : les parcelles de moins d'environ {ha} ha sont omises, c'est donc un minimum.",
        "Luogo esteso, misurato a scala grossolana: gli appezzamenti sotto circa {ha} ha restano fuori, quindi è un valore minimo.",
        "Großer Ort, in grobem Maßstab gemessen: Parzellen unter etwa {ha} ha fehlen, daher ist dies ein Mindestwert.",
        "Lugar extenso, medido a escala gruesa: se omiten las parcelas de menos de unas {ha} ha, así que es un mínimo.",
        "Lugar extenso, medido a uma escala grosseira: as parcelas com menos de cerca de {ha} ha ficam de fora, por isso é um mínimo.",
        "Groot gebied, op grove schaal gemeten: percelen kleiner dan ongeveer {ha} ha vallen weg, dus dit is een minimum.",
        "広い場所のため粗い縮尺で計測しました。約{ha} ha未満の区画は含まれないため、これは最小値です。",
        "范围较大，按粗略比例测量：约{ha}公顷以下的地块未计入，因此这是最小值。",
        "넓은 곳이라 개략적인 축척으로 측정했습니다. 약 {ha} ha 미만의 구획은 빠지므로 최솟값입니다."],
    "no vineyards mapped in OpenStreetMap here yet": [
        "aucune vigne encore cartographiée ici dans OpenStreetMap", "nessun vigneto ancora mappato qui in OpenStreetMap",
        "hier noch keine Rebflächen in OpenStreetMap kartiert", "aún no hay viñedos cartografiados aquí en OpenStreetMap",
        "ainda não há vinhas cartografadas aqui no OpenStreetMap", "hier nog geen wijngaarden in OpenStreetMap gekarteerd",
        "OpenStreetMapにはまだここのブドウ畑が描かれていません", "OpenStreetMap中此处尚未标绘葡萄园", "OpenStreetMap에 아직 이곳 포도밭이 표시되지 않음"],
    "Vineyards cover about {ha} ha of it.": ["Les vignes en couvrent environ {ha} ha.", "I vigneti ne coprono circa {ha} ha.",
                                             "Reben bedecken davon etwa {ha} ha.", "Los viñedos ocupan unas {ha} ha.", "As vinhas ocupam cerca de {ha} ha.",
                                             "Wijngaarden beslaan er ongeveer {ha} ha van.", "そのうちブドウ畑は約{ha} haです。", "其中葡萄园约占{ha}公顷。",
                                             "그중 포도밭은 약 {ha} ha입니다."],
    "The vineyard map could not be loaded right now.": [
        "La carte des vignes n'a pas pu être chargée pour le moment.", "Al momento non è stato possibile caricare la mappa dei vigneti.",
        "Die Rebflächenkarte konnte gerade nicht geladen werden.", "No se ha podido cargar el mapa de viñedos en este momento.",
        "Não foi possível carregar o mapa das vinhas neste momento.", "De wijngaardkaart kon nu niet worden geladen.",
        "現在、ブドウ畑の地図を読み込めませんでした。", "暂时无法加载葡萄园地图。", "지금은 포도밭 지도를 불러올 수 없습니다."],
    "The land inside the outline that OpenStreetMap maps as vineyard, measured in your browser. The outline is the legal or administrative area and also takes in woods, villages and fields, so the vineyard area is the better measure of how much is planted. OpenStreetMap is mapped by volunteers: very complete in most of Europe, patchier in places elsewhere, so a low figure can mean vineyards not yet mapped.": [
        "La surface à l'intérieur du périmètre qu'OpenStreetMap cartographie comme vigne, mesurée dans votre navigateur. Le périmètre est l'aire légale ou administrative et englobe aussi bois, villages et champs : la surface en vigne dit donc mieux ce qui est planté. OpenStreetMap est tenu par des bénévoles : très complet dans la plupart de l'Europe, plus inégal ailleurs, si bien qu'un chiffre bas peut signifier des vignes pas encore cartographiées.",
        "Il terreno all'interno del perimetro che OpenStreetMap mappa come vigneto, misurato nel tuo browser. Il perimetro è l'area legale o amministrativa e comprende anche boschi, paesi e campi, quindi l'area vitata indica meglio quanto è piantato. OpenStreetMap è curato da volontari: molto completo in gran parte d'Europa, più irregolare altrove, quindi un valore basso può voler dire vigneti non ancora mappati.",
        "Die Fläche innerhalb des Umrisses, die OpenStreetMap als Weinberg kartiert, gemessen in Ihrem Browser. Der Umriss ist das rechtliche oder administrative Gebiet und umfasst auch Wälder, Dörfer und Felder, deshalb zeigt die Rebfläche besser, wie viel bestockt ist. OpenStreetMap wird von Freiwilligen gepflegt: in den meisten Teilen Europas sehr vollständig, anderswo lückenhafter. Ein niedriger Wert kann also noch nicht kartierte Weinberge bedeuten.",
        "El terreno dentro del contorno que OpenStreetMap cartografía como viñedo, medido en tu navegador. El contorno es la zona legal o administrativa e incluye también bosques, pueblos y campos, así que la superficie de viñedo indica mejor cuánto está plantado. OpenStreetMap lo mantienen voluntarios: muy completo en casi toda Europa, más irregular en otros lugares, de modo que una cifra baja puede deberse a viñedos aún no cartografiados.",
        "O terreno dentro do contorno que o OpenStreetMap cartografa como vinha, medido no seu navegador. O contorno é a área legal ou administrativa e inclui também matas, aldeias e campos, por isso a área de vinha mostra melhor quanto está plantado. O OpenStreetMap é mantido por voluntários: muito completo na maior parte da Europa, mais irregular noutros sítios, pelo que um valor baixo pode significar vinhas ainda não cartografadas.",
        "Het land binnen de omtrek dat OpenStreetMap als wijngaard karteert, gemeten in je browser. De omtrek is het wettelijke of bestuurlijke gebied en omvat ook bossen, dorpen en akkers, dus de wijngaardoppervlakte zegt beter hoeveel er beplant is. OpenStreetMap wordt bijgehouden door vrijwilligers: zeer volledig in het grootste deel van Europa, elders onvollediger, dus een laag cijfer kan betekenen dat wijngaarden nog niet gekarteerd zijn.",
        "輪郭の内側で、OpenStreetMapがブドウ畑として描いている土地を、お使いのブラウザで計測したものです。輪郭は法定または行政上の範囲で、森や集落、畑も含むため、実際に植えられている広さはブドウ畑の面積の方がよく表します。OpenStreetMapはボランティアが作成しており、ヨーロッパの大部分ではとても詳しい一方、他の地域では欠けている所もあるため、小さな数値はまだ描かれていないブドウ畑を意味することがあります。",
        "轮廓内被OpenStreetMap标为葡萄园的土地，在您的浏览器中测量。轮廓是法定或行政范围，也包括森林、村庄和农田，因此葡萄园面积更能反映实际种植了多少。OpenStreetMap由志愿者绘制：欧洲大部分地区非常完整，其他地方则有缺漏，所以数值偏低可能意味着葡萄园尚未标绘。",
        "경계 안에서 OpenStreetMap이 포도밭으로 표시한 땅을 브라우저에서 측정한 값입니다. 경계는 법적 또는 행정 구역이라 숲, 마을, 밭도 포함하므로 실제로 얼마나 심어져 있는지는 포도밭 면적이 더 잘 보여 줍니다. OpenStreetMap은 자원봉사자가 만들며 유럽 대부분에서는 매우 상세하지만 다른 곳에서는 빈 곳이 있어, 값이 낮으면 아직 표시되지 않은 포도밭일 수 있습니다."],
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
