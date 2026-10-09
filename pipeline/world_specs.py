"""Wine places outside the EU and the US, defined through administrative units.

Most countries outside the EU publish no open boundary files for their wine geographical
indications (GIs). Many GIs are, however, legally defined by administrative units: Chilean
DOs by comunas (Decreto 464/1994), Argentine IGs by departments (INV resolutions), Japanese GIs
by prefecture, Moldovan IGPs by raion. For those, the outline is the union of the named units
("legal"). Where the law draws the line differently (roads, rivers, farm boundaries, altitude),
the units only approximate the area ("approx"), and the map draws the outline dashed.

A GI much smaller than any unit (a ward, a paraje, a village PDO) is shown as a point at the
place it is named after ("point"), never as a misleadingly large polygon.

Each spec: cc, type (default register type), basis (legal basis), adm (default admin layer),
outline ("legal" | "approx"), places: list of dicts
    name, level, parent, units (names in the admin layer; [name, lon, lat] picks the copy
    nearest that point when a name repeats), adm (override), outline (override), type (override),
    point ((lat, lon) of the namesake town: shown as a marker), note, registered
Chile and Argentina come from the JSON tables in pipeline/world/ (compiled from the law texts).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def P(name, level, units=None, parent="", **kw):
    d = {"name": name, "level": level, "parent": parent, "units": units or []}
    d.update(kw)
    return d


def pt(name, level, lat, lon, parent="", **kw):
    return P(name, level, [], parent, point=(lat, lon), **kw)


SPECS = []

# ---------------------------------------------------------------- New Zealand
_AKL = ["Albert-Eden Local Board Area", "Aotea/Great Barrier Local Board Area", "Devonport-Takapuna Local Board Area",
        "Franklin Local Board Area", "Henderson-Massey Local Board Area", "Hibiscus and Bays Local Board Area",
        "Howick Local Board Area", "Kaipātiki Local Board Area", "Manurewa Local Board Area",
        "Maungakiekie-Tāmaki Local Board Area", "Māngere-Ōtāhuhu Local Board Area", "Papakura Local Board Area",
        "Puketāpapa Local Board Area", "Rodney Local Board Area", "Upper Harbour Local Board Area",
        "Waiheke Local Board Area", "Waitematā Local Board Area", "Waitākere Ranges Local Board Area",
        "Whau Local Board Area", "Ōrākei Local Board Area", "Ōtara-Papatoetoe Local Board Area"]
SPECS.append(dict(
    cc="NZ", type="GI (Geographical Indications (Wine and Spirits) Registration Act 2006)", adm="NZL-ADM2", outline="approx",
    basis="Registered with IPONZ. The registered boundaries are drawn on maps; the units here are the districts that contain them.",
    places=[
        P("Northland", "appellation", ["Far North District", "Whangarei District", "Kaipara District"]),
        P("Auckland", "appellation", _AKL),
        pt("Matakana", "subzone", -36.353, 174.716, "Auckland"),
        pt("Kumeu", "subzone", -36.776, 174.557, "Auckland"),
        P("Waiheke Island", "subzone", ["Waiheke Local Board Area"], "Auckland", outline="legal"),
        P("Gisborne", "appellation", ["Gisborne District"]),
        P("Hawke's Bay", "appellation", ["Napier City", "Hastings District", "Central Hawke's Bay District", "Wairoa District"]),
        P("Central Hawke's Bay", "subzone", ["Central Hawke's Bay District"], "Hawke's Bay"),
        P("Wairarapa", "appellation", ["Masterton District", "Carterton District", "South Wairarapa District"]),
        pt("Martinborough", "subzone", -41.218, 175.459, "Wairarapa"),
        pt("Gladstone", "subzone", -41.084, 175.648, "Wairarapa"),
        P("Nelson", "appellation", ["Nelson City", "Tasman District"]),
        P("Marlborough", "appellation", ["Marlborough District"]),
        P("Canterbury", "appellation", ["Kaikoura District", "Hurunui District", "Waimakariri District", "Christchurch City",
                                        "Selwyn District", "Ashburton District", "Timaru District", "Mackenzie District", "Waimate District"]),
        P("North Canterbury", "subzone", ["Hurunui District", "Waimakariri District"], "Canterbury"),
        pt("Waipara Valley", "subzone", -43.060, 172.755, "North Canterbury"),
        P("Waitaki Valley North Otago", "appellation", ["Waitaki District"]),
        P("Central Otago", "appellation", ["Central Otago District", "Queenstown-Lakes District"]),
        pt("Bannockburn", "subzone", -45.083, 169.163, "Central Otago"),
    ]))

# ---------------------------------------------------------------- South Africa
_ZA_GU = dict(adm="ZAF-ADM1", outline="legal", type="Wine of Origin geographical unit")
SPECS.append(dict(
    cc="ZA", type="Wine of Origin", adm="ZAF-ADM3", outline="approx",
    basis="Wine of Origin Scheme (Liquor Products Act 60 of 1989); areas published in the Government Gazette and administered by SAWIS.",
    places=[
        P("Western Cape", "region", ["Western Cape"], **_ZA_GU),
        P("Northern Cape", "region", ["Nothern Cape"], **_ZA_GU),
        P("Eastern Cape", "region", ["Eastern Cape"], **_ZA_GU),
        P("KwaZulu-Natal", "region", ["KwaZulu-Natal"], **_ZA_GU),
        P("Limpopo", "region", ["Limpopo"], **_ZA_GU),
        P("Free State", "region", ["Free State"], **_ZA_GU),
        P("Coastal Region", "region", ["City of Cape Town", "Stellenbosch", "Drakenstein", "Swartland", "Witzenberg"], "Western Cape", type="Wine of Origin region"),
        P("Breede River Valley", "region", ["Breede Valley", "Langeberg"], "Western Cape", type="Wine of Origin region"),
        P("Cape South Coast", "region", ["Theewaterskloof", "Overstrand", "Cape Agulhas", "Swellendam", "Hessequa", "Mossel Bay",
                                         "George", "Knysna", "Bitou"], "Western Cape", type="Wine of Origin region"),
        P("Klein Karoo", "region", ["Kannaland", "Oudtshoorn", "Langeberg", "Dr Beyers Naude"], "Western Cape", type="Wine of Origin region"),
        P("Olifants River", "region", ["Matzikama", "Cederberg"], "Western Cape", type="Wine of Origin region"),
        P("Boberg", "region", ["Drakenstein", "Witzenberg"], "Western Cape", type="Wine of Origin region (fortified wines)"),
        P("Cape Town", "appellation", ["City of Cape Town"], "Coastal Region", type="Wine of Origin district"),
        P("Stellenbosch", "appellation", ["Stellenbosch"], "Coastal Region", type="Wine of Origin district"),
        pt("Franschhoek", "appellation", -33.913, 19.121, "Coastal Region", type="Wine of Origin district"),
        pt("Paarl", "appellation", -33.734, 18.962, "Coastal Region", type="Wine of Origin district"),
        pt("Wellington", "appellation", -33.640, 19.011, "Coastal Region", type="Wine of Origin district"),
        P("Swartland", "appellation", ["Swartland"], "Coastal Region", type="Wine of Origin district"),
        pt("Darling", "appellation", -33.380, 18.383, "Coastal Region", type="Wine of Origin district"),
        pt("Tulbagh", "appellation", -33.289, 19.138, "Coastal Region", type="Wine of Origin district"),
        pt("Breedekloof", "appellation", -33.690, 19.310, "Breede River Valley", type="Wine of Origin district"),
        pt("Worcester", "appellation", -33.646, 19.448, "Breede River Valley", type="Wine of Origin district"),
        P("Robertson", "appellation", ["Langeberg"], "Breede River Valley", type="Wine of Origin district"),
        P("Overberg", "appellation", ["Theewaterskloof"], "Cape South Coast", type="Wine of Origin district"),
        pt("Elgin", "appellation", -34.152, 19.043, "Cape South Coast", type="Wine of Origin district"),
        P("Walker Bay", "appellation", ["Overstrand"], "Cape South Coast", type="Wine of Origin district"),
        P("Cape Agulhas", "appellation", ["Cape Agulhas"], "Cape South Coast", type="Wine of Origin district"),
        P("Swellendam", "appellation", ["Swellendam"], "Cape South Coast", type="Wine of Origin district"),
        P("Plettenberg Bay", "appellation", ["Bitou"], "Cape South Coast", type="Wine of Origin district"),
        P("Calitzdorp", "appellation", ["Kannaland"], "Klein Karoo", type="Wine of Origin district"),
        P("Langeberg-Garcia", "appellation", ["Hessequa"], "Klein Karoo", type="Wine of Origin district"),
        P("Lutzville Valley", "appellation", ["Matzikama"], "Olifants River", type="Wine of Origin district"),
        P("Citrusdal Valley", "appellation", ["Cederberg", "Bergrivier"], "Olifants River", type="Wine of Origin district"),
        P("Douglas", "appellation", ["Siyancuma"], "Northern Cape", type="Wine of Origin district"),
        P("Sutherland-Karoo", "appellation", ["Karoo Hoogland"], "Northern Cape", type="Wine of Origin district"),
        P("Central Orange River", "appellation", ["Kai Garib", "Dawid Kruiper", "Kheis", "Tsantsabane"], "Northern Cape", type="Wine of Origin ward"),
        P("Hartswater", "appellation", ["Phokwane"], "Northern Cape", type="Wine of Origin ward"),
        P("Prince Albert Valley", "appellation", ["Prince Albert"], "Western Cape", type="Wine of Origin ward"),
        pt("Constantia", "subzone", -34.025, 18.430, "Cape Town", type="Wine of Origin ward"),
        pt("Durbanville", "subzone", -33.832, 18.647, "Cape Town", type="Wine of Origin ward"),
        pt("Ceres Plateau", "subzone", -33.017, 19.283, "Western Cape", type="Wine of Origin ward"),
        pt("Cederberg", "subzone", -32.497, 19.263, "Western Cape", type="Wine of Origin ward"),
        pt("Simonsberg-Stellenbosch", "subzone", -33.873, 18.900, "Stellenbosch", type="Wine of Origin ward"),
        pt("Jonkershoek Valley", "subzone", -33.965, 18.950, "Stellenbosch", type="Wine of Origin ward"),
        pt("Banghoek", "subzone", -33.905, 18.965, "Stellenbosch", type="Wine of Origin ward"),
        pt("Polkadraai Hills", "subzone", -33.965, 18.760, "Stellenbosch", type="Wine of Origin ward"),
        pt("Bottelary", "subzone", -33.885, 18.770, "Stellenbosch", type="Wine of Origin ward"),
        pt("Devon Valley", "subzone", -33.903, 18.810, "Stellenbosch", type="Wine of Origin ward"),
        pt("Papegaaiberg", "subzone", -33.938, 18.838, "Stellenbosch", type="Wine of Origin ward"),
        pt("Vlottenburg", "subzone", -33.957, 18.800, "Stellenbosch", type="Wine of Origin ward"),
        pt("Simonsberg-Paarl", "subzone", -33.800, 18.935, "Paarl", type="Wine of Origin ward"),
        pt("Hemel-en-Aarde Valley", "subzone", -34.390, 19.250, "Walker Bay", type="Wine of Origin ward"),
        pt("Upper Hemel-en-Aarde Valley", "subzone", -34.360, 19.300, "Walker Bay", type="Wine of Origin ward"),
        pt("Hemel-en-Aarde Ridge", "subzone", -34.330, 19.370, "Walker Bay", type="Wine of Origin ward"),
        pt("Malmesbury", "subzone", -33.462, 18.727, "Swartland", type="Wine of Origin ward"),
        pt("Riebeekberg", "subzone", -33.370, 18.880, "Swartland", type="Wine of Origin ward"),
    ]))

# ---------------------------------------------------------------- Brazil
SPECS.append(dict(
    cc="BR", type="IG (Indicação Geográfica)", adm="BRA-ADM2", outline="approx",
    basis="Recognised by INPI (Lei 9.279/1996). The specifications delimit the area by maps; the outline is the municipalities it touches.",
    places=[
        pt("Vale dos Vinhedos", "appellation", -29.170, -51.580, type="DO (2012), first IP (2002)"),
        pt("Pinto Bandeira", "appellation", -29.097, -51.450, type="IP (2010)"),
        pt("Altos de Pinto Bandeira", "subzone", -29.090, -51.470, "Pinto Bandeira", type="DO (sparkling wine)"),
        pt("Altos Montes", "appellation", -29.030, -51.180, type="IP (2012)"),
        pt("Monte Belo", "appellation", -29.163, -51.633, type="IP (2013)"),
        P("Farroupilha", "appellation", ["Farroupilha"], type="IP (2015)"),
        P("Campanha Gaúcha", "appellation", ["Aceguá", "Barra do Quaraí", "Candiota", "Hulha Negra", "Itaqui", "Quaraí", "Rosário do Sul",
                                             "Sant'Ana do Livramento", "Uruguaiana", "Alegrete", "Bagé", "Dom Pedrito", "Lavras do Sul", "Maçambará"],
          type="IP (2020)"),
        P("Vales da Uva Goethe", "appellation", ["Urussanga", "Pedras Grandes", "Morro da Fumaça", "Cocal do Sul", "Treze de Maio",
                                                 "Orleans", ["Nova Veneza", -49.50, -28.64], "Içara"], type="IP (2012)", outline="legal"),
        P("Vinhos de Altitude de Santa Catarina", "appellation",
          ["Água Doce", "Anitápolis", "Arroio Trinta", "Bom Jardim da Serra", "Bom Retiro", "Brunópolis", "Caçador", "Campo Belo do Sul",
           "Capão Alto", "Cerro Negro", "Curitibanos", "Fraiburgo", "Frei Rogério", "Iomerê", "Lages", "Macieira", "Painel", "Pinheiro Preto",
           "Rancho Queimado", "Rio das Antas", "Salto Veloso", "São Joaquim", "São José do Cerrito", ["Tangará", -51.25, -27.10],
           "Treze Tílias", "Urubici", "Urupema", ["Vargem Bonita", -51.74, -27.01], "Videira"], type="IP (2021)", outline="legal"),
        P("Vale do São Francisco", "appellation", [["Lagoa Grande", -40.27, -8.99], "Petrolina", "Santa Maria da Boa Vista", "Casa Nova", "Curaçá"],
          type="IP (2022)"),
        P("Bituruna", "appellation", ["Bituruna"], type="IP (2022)"),
    ]))

# ---------------------------------------------------------------- Uruguay
SPECS.append(dict(
    cc="UY", type="Wine region (INAVI)", adm="URY-ADM1", outline="approx",
    basis="Uruguay has no legally delimited wine GIs (Decreto 283/993 sets up a register only). These are INAVI's descriptive regions, by department.",
    places=[P(n, "region", u) for n, u in {
        "Litoral Norte": ["Artigas", "Paysandú", "Salto"], "Litoral Sur": ["Colonia", "Río Negro", "Soriano"],
        "Metropolitana": ["Canelones", "Montevideo", "San José"], "Central": ["Durazno", "Florida", "Lavalleja"],
        "Oceánica": ["Maldonado", "Rocha"], "Norte": ["Rivera", "Tacuarembó"], "Centro-Este": ["Lavalleja", "Treinta y Tres"]}.items()]))

# ---------------------------------------------------------------- Canada
_CA_ON = dict(adm="CAN-ADM3", type="VQA Ontario designated viticultural area (O. Reg. 359/24)")
_CA_BC = dict(type="BC VQA geographical indication (Wines of Marque Regulation)")
SPECS.append(dict(
    cc="CA", type="Viticultural area", adm="CAN-ADM3", outline="approx",
    basis="Ontario: O. Reg. 359/24 under the VQA Act, areas defined by roads and natural features. British Columbia: GIs under the Wines of Marque Regulation, defined by watersheds and schedule maps.",
    places=[
        P("Niagara Peninsula", "appellation", ["Niagara-on-the-Lake", "St. Catharines", ["Lincoln", -79.41, 43.15], "Grimsby", "Pelham",
                                               "Niagara Falls", "Thorold", "Welland", "West Lincoln", "Fort Erie", "Port Colborne", "Wainfleet",
                                               ["Hamilton", -79.9, 43.26]], **_CA_ON),
        P("Niagara-on-the-Lake", "subzone", ["Niagara-on-the-Lake"], "Niagara Peninsula", **_CA_ON),
        pt("Niagara River", "subzone", 43.200, -79.060, "Niagara-on-the-Lake", type=_CA_ON["type"]),
        pt("Niagara Lakeshore", "subzone", 43.245, -79.115, "Niagara-on-the-Lake", type=_CA_ON["type"]),
        pt("Four Mile Creek", "subzone", 43.215, -79.150, "Niagara-on-the-Lake", type=_CA_ON["type"]),
        pt("St. David's Bench", "subzone", 43.157, -79.125, "Niagara-on-the-Lake", type=_CA_ON["type"]),
        pt("Niagara Escarpment", "subzone", 43.150, -79.420, "Niagara Peninsula", type=_CA_ON["type"]),
        pt("Beamsville Bench", "subzone", 43.157, -79.490, "Niagara Escarpment", type=_CA_ON["type"]),
        pt("Twenty Mile Bench", "subzone", 43.152, -79.370, "Niagara Escarpment", type=_CA_ON["type"]),
        pt("Short Hills Bench", "subzone", 43.100, -79.300, "Niagara Escarpment", type=_CA_ON["type"]),
        pt("Vinemount Ridge", "subzone", 43.130, -79.430, "Niagara Peninsula", type=_CA_ON["type"]),
        pt("Lincoln Lakeshore", "subzone", 43.185, -79.430, "Niagara Peninsula", type=_CA_ON["type"]),
        pt("Creek Shores", "subzone", 43.172, -79.300, "Niagara Peninsula", type=_CA_ON["type"]),
        P("Lake Erie North Shore", "appellation", ["Essex", "Kingsville", "Leamington", ["Lakeshore", -82.65, 42.24], "Amherstburg", "LaSalle",
                                                   "Tecumseh", "Chatham-Kent", "West Elgin", "Dutton/Dunwich", "Southwold", "Central Elgin",
                                                   "Malahide", "Bayham", "Aylmer", "Pelee"], **_CA_ON),
        P("South Islands", "subzone", ["Pelee"], "Lake Erie North Shore", **_CA_ON),
        P("Prince Edward County", "appellation", ["Prince Edward County"], **_CA_ON),
        pt("Okanagan Valley", "appellation", 49.700, -119.580, **_CA_BC),
        pt("Golden Mile Bench", "subzone", 49.150, -119.585, "Okanagan Valley", **_CA_BC),
        pt("Okanagan Falls", "subzone", 49.345, -119.570, "Okanagan Valley", **_CA_BC),
        pt("Skaha Bench", "subzone", 49.440, -119.555, "Okanagan Valley", **_CA_BC),
        pt("Naramata Bench", "subzone", 49.560, -119.585, "Okanagan Valley", **_CA_BC),
        pt("Summerland Bench", "subzone", 49.600, -119.670, "Okanagan Valley", **_CA_BC),
        pt("Similkameen Valley", "appellation", 49.200, -119.830, **_CA_BC),
        pt("Fraser Valley", "appellation", 49.100, -122.300, **_CA_BC),
        pt("Vancouver Island", "appellation", 48.780, -123.700, **_CA_BC),
        pt("Gulf Islands", "appellation", 48.800, -123.400, **_CA_BC),
        pt("Lillooet", "appellation", 50.690, -121.940, **_CA_BC),
        pt("Shuswap", "appellation", 50.800, -119.300, **_CA_BC),
        pt("Thompson Valley", "appellation", 50.680, -120.340, **_CA_BC),
        pt("Kootenays", "appellation", 49.500, -117.300, **_CA_BC),
        P("Vin du Québec", "appellation", ["Montérégie", "Estrie", "Centre-du-Québec", "Chaudière-Appalaches", "Capitale-Nationale",
                                           "Laurentides", "Lanaudière", "Outaouais", "Mauricie", "Laval", "Montréal"], adm="CAN-ADM2",
          type="IGP Vin du Québec (CARTV)", note="The IGP covers the parts of Québec with at least 900 growing degree days; the outline shows the regions that contain them."),
        P("Nova Scotia (Annapolis Valley)", "appellation", ["Annapolis Valley"], adm="CAN-ADM2", type="Wine region (no legal sub-regions)"),
    ]))

# ---------------------------------------------------------------- Mexico
SPECS.append(dict(
    cc="MX", type="Wine region", adm="MEX-ADM2", outline="approx",
    basis="Mexico has no legally delimited wine denomination of origin. The outlines are the municipalities of the main wine valleys.",
    places=[
        P("Valle de Guadalupe (Ensenada)", "appellation", ["Ensenada"], note="The 2012 municipality still includes San Quintín, separated in 2020."),
        P("Valle de Tecate", "appellation", ["Tecate"]),
        P("Parras", "appellation", ["Parras"]),
        P("Querétaro", "appellation", ["Ezequiel Montes", "Tequisquiapan", ["Colón", -100.05, 20.78], ["San Juan del Río", -99.99, 20.39]]),
        P("Guanajuato (San Miguel de Allende, Dolores Hidalgo)", "appellation", ["San Miguel de Allende", "Dolores Hidalgo Cuna de la Independencia Nacional"]),
        P("Aguascalientes", "appellation", ["Rincón de Romos", "Pabellón de Arteaga"]),
    ]))

# ---------------------------------------------------------------- Georgia
_GE_K = "Kakheti"
SPECS.append(dict(
    cc="GE", type="PDO (Appellation of Origin, Sakpatenti)", adm="GEO-ADM2", outline="approx",
    basis="Appellations of origin registered with Sakpatenti under the Law of Georgia on Appellations of Origin and Geographical Indications. Most are village micro-zones, shown here as points at the namesake village.",
    places=[
        P("Kakheti", "region", ["Akhmeta", "Telavi", "Qvareli", "Gurjaani", "Sighnaghi", "Dedoplis Tskaro", "Lagodekhi", "Sagarejo"]),
        pt("Tsinandali", "appellation", 41.894, 45.570, _GE_K),
        pt("Napareuli", "appellation", 42.010, 45.493, _GE_K),
        pt("Teliani", "appellation", 41.900, 45.583, _GE_K),
        pt("Mukuzani", "appellation", 41.808, 45.732, _GE_K),
        pt("Kardenakhi", "appellation", 41.673, 45.888, _GE_K),
        pt("Tsarapi", "appellation", 41.665, 45.900, _GE_K),
        pt("Akhoebi", "appellation", 41.683, 45.873, _GE_K),
        pt("Akhasheni", "appellation", 41.793, 45.747, _GE_K),
        P("Gurjaani", "appellation", ["Gurjaani"], _GE_K),
        pt("Vazisubani", "appellation", 41.790, 45.710, _GE_K),
        pt("Kotekhi", "appellation", 41.753, 45.779, _GE_K),
        pt("Zegaani", "appellation", 41.798, 45.733, _GE_K),
        pt("Tibaani", "appellation", 41.574, 46.002, _GE_K),
        pt("Kindzmarauli", "appellation", 41.960, 45.780, _GE_K),
        P("Kvareli", "appellation", ["Qvareli"], _GE_K),
        pt("Manavi", "appellation", 41.720, 45.466, _GE_K),
        pt("Khashmis Saperavi", "appellation", 41.730, 45.180, _GE_K),
        P("Akhmeta", "appellation", ["Akhmeta"], _GE_K),
        pt("Magraanis Kisi", "appellation", 42.110, 45.352, _GE_K),
        pt("Atenuri", "appellation", 41.925, 44.085),
        pt("Okami", "appellation", 41.984, 44.479),
        P("Bolnisi", "appellation", ["Bolnisi"]),
        pt("Asuretuli Shala", "appellation", 41.593, 44.667),
        P("Racha", "appellation", ["Ambrolauri", "Oni"]),
        pt("Khvanchkara", "subzone", 42.560, 43.040, "Racha"),
        P("Lechkhumi", "appellation", ["Tsageri"]),
        pt("Tvishi", "subzone", 42.530, 42.800, "Lechkhumi"),
        pt("Okureshis Usakhelouri", "subzone", 42.541, 42.676, "Lechkhumi"),
        pt("Sviri", "appellation", 42.130, 42.980),
        P("Salkhino Ojaleshi", "appellation", ["Martvili"]),
        P("Obcha", "appellation", ["Baghdati"]),
        P("Sazanos Otskhanuri", "appellation", ["Terjola", "Zestaponi"]),
    ]))

# ---------------------------------------------------------------- Moldova
SPECS.append(dict(
    cc="MD", type="IGP (Indicație Geografică Protejată)", adm="MDA-ADM1", outline="legal",
    basis="Registered with AGEPI; each IGP is defined by the raions listed in its product specification.",
    places=[
        P("Codru", "appellation", ["Hincesti", "Ialoveni", "Anenii Noi", "Criuleni", "Straseni", "Orhei", "Calarasi", "Nisporeni",
                                   "Telenesti", "Ungheni", "Dubasari"]),
        P("Ștefan Vodă", "appellation", ["Stefan Voda", "Causeni", "Cimislia", "Basarabeasca"]),
        P("Valul lui Traian", "appellation", ["Leova", "Cantemir", "Cahul", "Taraclia", "Gagauzia"]),
    ]))

# ---------------------------------------------------------------- Ukraine (Crimea is left out)
SPECS.append(dict(
    cc="UA", type="GI (Ukrainepatent register)", adm="UKR-ADM2", outline="approx",
    basis="Geographical indications registered by Ukrainepatent. Raion outlines are the 2006 units, before the 2020 reform.",
    places=[
        P("Zakarpattia", "appellation", ["Berehove", "Vynohradiv", "Uzhhorod", "Perechyn", "Velykyy Bereznyi", "Khust", "Irshava",
                                         "Mukachevo\t", "Svaliava"]),
        P("Prydunaiska Bessarabia", "appellation", ["Izmali", "Reni", "Kiliia", "Bolhrad"]),
        P("Yalpuh", "subzone", ["Bolhrad"], "Prydunaiska Bessarabia"),
        P("Shabo (Chabag)", "appellation", ["Bilhorod Dnistrovskyi"]),
        P("Odesa region", "region", ["Odessa Oblast"], adm="UKR-ADM1", type="Wine region"),
        P("Tavria (Kherson)", "region", ["Kherson Oblast"], adm="UKR-ADM1", type="Wine region"),
    ]))

# ---------------------------------------------------------------- Armenia
SPECS.append(dict(
    cc="AM", type="Wine region", adm="ARM-ADM1", outline="approx",
    basis="Armenia has no registered wine GIs yet (Vayots Dzor is the candidate). Regions follow the marzer.",
    places=[P(n, "region", [n]) for n in ["Vayots Dzor", "Ararat", "Armavir", "Aragatsotn", "Tavush", "Syunik"]]))

# ---------------------------------------------------------------- Turkey
SPECS.append(dict(
    cc="TR", type="Wine region", adm="TUR-ADM1", outline="approx",
    basis="Turkish wine regions are informal and described by province.",
    places=[P(n, "region", u) for n, u in {
        "Thrace-Marmara": ["Kırklareli", "Tekirdağ", "Edirne", "Çanakkale", "Balıkesir", "İstanbul"],
        "Aegean": ["İzmir", "Manisa", "Denizli", "Aydın", "Muğla", "Uşak"],
        "Central Anatolia (Cappadocia)": ["Nevşehir", "Kayseri", "Kırşehir", "Aksaray", "Niğde"],
        "Ankara (Kalecik)": ["Ankara"], "Eastern Anatolia": ["Elazığ", "Malatya", "Tokat"],
        "Southeast Anatolia": ["Diyarbakır", "Şanlıurfa"]}.items()]))

# ---------------------------------------------------------------- Israel (no Golan Heights, no West Bank)
SPECS.append(dict(
    cc="IL", type="Wine region", adm="ISR-ADM2", outline="approx",
    basis="Israel's five wine regions have no published admin-unit definition. Outlines follow Israeli districts inside the pre-1967 lines; the Golan Heights and the West Bank are not drawn.",
    places=[
        P("Galilee", "region", ["Akko", "Zefat", "Kinneret", "Yizre'el"]),
        P("Upper Galilee", "appellation", ["Zefat", "Akko"], "Galilee"),
        P("Shomron (Carmel, Sharon)", "region", ["Haifa", "Hadera"]),
        P("Samson", "region", ["Ramla", "Rehovot", "Petah Tiqwa"]),
        P("Judean Hills", "region", ["Jerusalem"]),
        P("Negev", "region", ["Be'er Sheva", "Ashqelon"]),
    ]))

# ---------------------------------------------------------------- Lebanon
SPECS.append(dict(
    cc="LB", type="Wine region", adm="LBN-ADM2", outline="approx",
    basis="Lebanon has no delimited appellations yet (Law 216/2000; none delimited by the INVV). Regions follow the cazas.",
    places=[P(n, "region", u) for n, u in {
        "Bekaa Valley": ["Zahle", "West Bekaa", "Baalbek", "Rachaya"], "Batroun": ["Batroun"], "Jezzine": ["Jezzine"],
        "Mount Lebanon": ["Baabda", "Aley", "Chouf", "El Metn", "Kesrouan", "Jbail"],
        "North Lebanon highlands": ["Koura", "Zgharta", "Bcharre"]}.items()]))

# ---------------------------------------------------------------- Serbia
SPECS.append(dict(
    cc="RS", type="Wine region (2013 zoning)", adm="SRB-ADM2", outline="approx",
    basis="Serbia's 2013 rulebook defines 22 wine regions by municipality lists. These outlines approximate them by district and municipality.",
    places=[P(n, "region", u, adm="SRB-ADM1") for n, u in {
        "Srem": ["Syrmia District"], "Šumadija": ["Sumadija District"], "Belgrade": ["Belgrade"], "Toplica": ["Toplica District"],
        "Niš": ["Nisava District"], "Leskovac": ["Jablanica District"], "Vranje": ["Pcinja District"], "Mlava": ["Branicevo District"],
        "Čačak-Kraljevo": ["Moravica District", "Raska District"], "Pocerina-Valjevo": ["Macva District", "Kolubara District"],
        "Tri Morave": ["Rasina District", "Pomoravlje District"], "South Banat": ["South Banat District"],
        "Banat": ["Central Banat District", "North Banat District"], "Bačka": ["South Backa District", "West Backa District"]}.items()] + [
        P("Fruška Gora", "appellation", ["Sremski Karlovci Municipality", "Irig Municipality", "Beocin Municipality", "Sremska Mitrovica City",
                                         "Indjija Municipality", "Ruma Municipality", "Sid Municipality", "Novi Sad City"], "Srem"),
        P("Negotin", "appellation", ["Negotin Municipality", "Kladovo Municipality"]),
        P("Knjaževac", "appellation", ["Knjazevac Municipality"]),
        P("Subotica", "appellation", ["Subotica City"]),
        P("Vršac", "appellation", ["Vrsac Municipality", "Bela Crkva Municipality"], "South Banat"),
        P("Župa", "appellation", ["Aleksandrovac Municipality"], "Tri Morave"),
        P("Oplenac", "appellation", ["Topola Municipality"], "Šumadija"),
        P("Smederevo", "appellation", ["Smederevo City"]),
    ]))

# ---------------------------------------------------------------- North Macedonia
SPECS.append(dict(
    cc="MK", type="Wine region", adm="MKD-ADM2", outline="approx",
    basis="Three wine regions under the Law on Wine; vinogorje lists by municipality were not available, so outlines are approximate.",
    places=[
        P("Povardarie", "region", ["Kavadartsi", "Negotino", "Rosoman", "Demir Kapija", "Gradsko", "Veles", "Sveti Nikole", "Shtip", "Strumitsa",
                                   "Radovish", "Gevgelija", "Valandovo", "Bogdantsi", "Dojran", "Lozovo", "Chashka"]),
        P("Tikveš", "appellation", ["Kavadartsi", "Negotino", "Rosoman", "Demir Kapija"], "Povardarie"),
        P("Pčinja-Osogovo", "region", ["Kumanovo", "Kratovo", "Kochani", "Vinitsa", "Probishtip", "Kriva Palanka", "Zrnovtsi", "Cheshinovo - Obleshevo"]),
        P("Pelagonija-Polog", "region", ["Bitola", "Prilep", "Ohrid", "Resen", "Tetovo", "Kichevo", "Struga", "Demir Hisar", "Krivogashtani",
                                         "Mogila", "Novatsi", "Dolneni"]),
    ]))

# ---------------------------------------------------------------- Montenegro
SPECS.append(dict(
    cc="ME", type="Wine region (2017 decision)", adm="MNE-ADM1", outline="approx",
    basis="Decision on wine-growing regions, Official Gazette 65/2017. Sub-regions are not listed by municipality.",
    places=[
        P("Skadar Lake basin", "region", ["Podgorica Municipality", "Danilovgrad Municipality", "Cetinje Municipality", "Bar Municipality"]),
        P("Montenegrin Coast", "region", ["Herceg Novi Municipality", "Kotor Municipality", "Tivat Municipality", "Budva Municipality",
                                          "Bar Municipality", "Ulcinj Municipality"]),
        P("Nudo", "region", ["Nikšić Municipality"]),
    ]))

# ---------------------------------------------------------------- Bosnia and Herzegovina
SPECS.append(dict(
    cc="BA", type="Wine region", adm="BIH-ADM3", outline="approx",
    basis="No registered wine GIs. Herzegovina is the main wine region (Žilavka, Blatina).",
    places=[P("Herzegovina", "region", ["Mostar", "Istočni Mostar", "Čitluk", "Ljubuški", "Čapljina", "Stolac", "Trebinje", "Široki Brijeg",
                                        "Grude", "Posušje", "Neum", "Ravno", "Ljubinje"])]))

# ---------------------------------------------------------------- Japan
SPECS.append(dict(
    cc="JP", type="GI (National Tax Agency)", adm="JPN-ADM1", outline="legal",
    basis="Geographical indications for wine designated by the National Tax Agency; each covers the whole prefecture.",
    places=[
        P("Yamanashi", "appellation", ["Yamanashi"], registered="2013-07-16"),
        P("Hokkaido", "appellation", ["Hokkaido"], registered="2018-06-28"),
        P("Yamagata", "appellation", ["Yamagata"], registered="2021-06-30"),
        P("Nagano", "appellation", ["Nagano"], registered="2021-06-30"),
        P("Osaka", "appellation", ["Osaka Prefecture"], registered="2021-06-30"),
    ]))

# ---------------------------------------------------------------- China
SPECS.append(dict(
    cc="CN", type="Geographical indication", adm="CHN-ADM2", outline="approx",
    basis="Wine GIs protected in China and listed in the EU-China agreement (2021). Counties as in the 2017 boundaries.",
    places=[
        P("Helan Mountain East (Ningxia)", "appellation", ["Shizhuishanshi", "Pingluoxian", "Helanxian", "Yinchuanshi", ["Yongningxian", 106.2, 38.3],
                                                           "Qingtongxiashi", "Wuzhongshi"]),
        P("Yantai", "appellation", ["Yantaishi", "Penglaixian", "Longkoushi", "Laiyangshi", "Laizhoushi", "Zhaoyuanshi", "Qixiashi",
                                    "Haiyangxian", "Mupingxian"], outline="legal"),
        P("Shacheng (Huailai)", "appellation", ["Huailaixian"]),
        P("Huanren icewine", "appellation", ["Huanrenmanzuzizhixian"]),
        P("Xinjiang (Turpan, Manas, Yanqi)", "region", ["Tulufanshi", "Manashixian", "Changjishi", "Yanqihuizuzizhixian", "Hejingxian", "Heshuoxian"],
          type="Wine region (not a registered GI)"),
        P("Yunnan (Mile, Deqin)", "region", ["Milexian", "Deqinxian"], type="Wine region (not a registered GI)"),
    ]))

# ---------------------------------------------------------------- India
SPECS.append(dict(
    cc="IN", type="Wine region", adm="IND-ADM2", outline="approx",
    basis="Nashik Valley wine is a registered GI (2010); the outline is Nashik district.",
    places=[P("Nashik Valley", "appellation", ["Nashik"], type="GI (Geographical Indications Registry, India)")]))

# ---------------------------------------------------------------- Australia: Tasmania (the GI is the state)
SPECS.append(dict(
    cc="AU", type="GI (Wine Australia)", adm="AUS-ADM1", outline="legal",
    basis="Wine Australia Act 2013; Register of Protected GIs and Other Terms.",
    places=[P("Tasmania", "appellation", ["Tasmania"], type="GI zone and region (Wine Australia)")]))


# ---------------------------------------------------------------- Chile (Decreto 464/1994, consolidated 2026)
def chile():
    t = json.load(open(os.path.join(HERE, "world", "cl_do.json"), encoding="utf-8"))
    lv = {"region": "region", "subregion": "appellation", "zone": "subzone", "area": "subzone"}
    label = {"region": "DO wine region (región vitícola)", "subregion": "DO subregion (subregión)", "zone": "DO zone (zona)", "area": "DO area (área)"}
    # rural localities: much smaller than their comuna, shown as a point
    points = {"Apalta": (-34.610, -71.290), "Lo Abarca": (-33.530, -71.580), "Los Lingues": (-34.620, -70.970)}
    skip = {"San Juan"}  # a locality in San Antonio with no reliable point yet
    places = []
    for name, v in t.items():
        if name in skip:
            continue
        p = P(name, lv[v["level"]], v.get("comunas") or [], v.get("parent") or "", type=label[v["level"]])
        if name in points:
            p.update(point=points[name], units=[])
        places.append(p)
    return dict(cc="CL", type="DO (Denominación de Origen)", adm="CHL-ADM3", outline="legal",
                basis="Decreto 464/1994 of the Ministry of Agriculture (zonificación vitícola), consolidated text 2026, with the 2025 amendment (Chiloé, Rapa Nui).",
                places=places)


# ---------------------------------------------------------------- Argentina (INV)
def argentina():
    t = json.load(open(os.path.join(HERE, "world", "ar_ig.json"), encoding="utf-8"))
    points = {"Agrelo": (-33.120, -68.900), "Alto Agrelo": (-33.180, -68.990), "Las Compuertas": (-33.030, -68.980),
              "Vistalba": (-33.030, -68.910), "Barrancas": (-33.090, -68.730), "Lunlunta": (-33.035, -68.815),
              "Russel": (-32.995, -68.800), "La Consulta": (-33.735, -69.120), "Paraje Altamira": (-33.770, -69.150),
              "Pampa El Cepillo": (-33.850, -69.160), "Los Chacayes": (-33.600, -69.280), "Vista Flores": (-33.650, -69.160),
              "San Pablo": (-33.450, -69.320), "El Peral": (-33.360, -69.210)}
    dept_ig = {}
    for name, v in t.items():
        if v["type"].startswith("IG (department)") and len(v["admin2"]) == 1:
            dept_ig[v["admin2"][0][2]] = name
    places, extra = [], {}
    for name, v in t.items():
        ty, prec = v["type"], v["precision"]
        ids = [["@id", a[2]] for a in v["admin2"]]
        prov = v["admin2"][0][0].replace("La Roja", "La Rioja") if v["admin2"] else ""
        if ty == "IG (provincial)":
            p = P(name, "region", ids, type="IG (provincial)")
        elif ty.startswith("IG (regional") or (ty == "IG" and prec.startswith("approx")):
            p = P(name, "region", ids, type=ty)
        elif ty == "DOC":
            p = P(name, "appellation", ids, prov, type="DOC (Denominación de Origen Controlada)")
        elif ty == "IG (department)":
            p = P(name, "appellation", ids, prov, type="IG (department)")
        else:  # sub-department IGs
            parent = dept_ig.get(v["admin2"][0][2], "")
            if name in points:
                p = pt(name, "subzone", *points[name], parent, type="IG (district or paraje)")
            else:
                extra.setdefault(parent, []).append(name)
                continue
        if not prec.startswith("exact"):
            p["outline"] = "approx"
        if v.get("note"):
            p["note"] = v["note"]
        if v.get("resolution"):
            p["registered"] = v["resolution"]
        places.append(p)
    for p in places:
        if p["name"] in extra:
            p["also_registered"] = sorted(extra[p["name"]])
    return dict(cc="AR", type="IG (Indicación Geográfica)", adm="ARG-ADM2", outline="legal",
                basis="Ley 25.163 (1999) and INV resolutions (C.32/2002, C.37/2002 and later); official INV list of 18 April 2024 plus the 2025 IGs.",
                places=places)


SPECS += [chile(), argentina()]
