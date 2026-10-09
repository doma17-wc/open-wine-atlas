# Translations of the Open Wine Atlas interface

The atlas is written in English. `_keys.json` lists every English text shown in the interface (key) with the
kind of text it is (value). Each language has one file, `<code>.json`, that maps every English text to its
translation. A text missing from a language file is shown in English. `pipeline/i18n_extract.py` refreshes
`_keys.json` from the code and the data and reports what each language is missing.

Languages: `fr` Français, `it` Italiano, `de` Deutsch, `es` Español, `pt` Português, `nl` Nederlands,
`ja` 日本語, `zh` 中文（简体）, `ko` 한국어. To add one, add a file and one line to `LANGS` and `LOCALES` in
`web/index.src.html`.

## Rules for translators

* Keep every placeholder in curly brackets exactly as it is, for example `{name}`, `{n}`, `{gst}`. Move it
  where the grammar of your language needs it.
* Plain text only: no HTML. Keep symbols such as `·`, `›`, `°C`, `%`, `–`, `…`, `★`, units (`m`, `ha`, `mm`, `hl/ha`)
  and keyboard keys (`Esc`, `F`, `G`, `M`, `[`, `/`).
* Keep proper names as written: places, appellations, regions with a local name (Bourgogne, Côte de Nuits,
  Vallée de la Loire, Piemonte, Rheinhessen), producers, grapes, datasets and organisations (INAO, ERA5-Land,
  SoilGrids, Mapterhorn, OpenStreetMap, Wine Australia, UC Davis), laws and registers.
* Keep the legal and classification terms of each country as the trade uses them: Grand cru, Premier cru,
  climat, lieu-dit, AOC, DOC, DOCG, DO, DOCa, Vino de Pago, AVA, GI, PDO, Einzellage, Großlage, Bereich,
  Anbaugebiet, Gemarkung, Gemeinde. Translate the words around them.
* Translate descriptive names: "Regional appellations", "Northern Rhône", "Chablis and Grand Auxerrois",
  "Upper Loire and Auvergne", continent names, the English names of US states where your language has its own.
* Write like a good wine guide in your language: short, plain, precise. Use the terms sommeliers use.
* Some texts are pieces of one sentence. They are joined like this, so make the pieces fit together:
  * `{name} is {what}{of} in {country}{area}{towns}.` where `{what}` is one of the texts starting with
    "a"/"an" ("a grand cru appellation", "an appellation", "a climat"…), `{of}` is ` of {parent}`, `{area}` is
    `, covering {ha} ha`, `{towns}` is ` in {list}` or ` across {n} communes`. Keep the leading space or comma of
    a piece when your language needs it there. If articles do not fit your grammar, drop them in the `{what}`
    texts and shape the sentence around them.
  * Terrain: `The ground lies at about {m} m` or `Most of the ground lies between {a} and {b} m`, then
    `, almost flat` or `, on a mean slope of {d}°`, then `, facing {dir}` (`{dir}` is "north", "south-east"…)
    or `, facing several directions`, then `.` (translate `.` with the full stop of your language).
  * Climate: `{climate}: the growing season averages {gst} °C ({winkler}, Huglin {hi}, {huglin}).` where
    `{climate}` is one of "A cool climate for wine", "A warm climate for wine"… and `{huglin}` one of "cool",
    "warm temperate"…
* Atlas notes are short editorial descriptions of a place. Translate them fully and naturally.
