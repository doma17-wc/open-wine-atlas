# Study post tools

Instagram images for the Open Wine Atlas study posts (quiz carousels, question stories, feature carousels),
rendered in headless Chromium in the atlas style: night background, parchment text, gold, Cormorant Garamond,
IBM Plex Sans and IBM Plex Mono. Feed slides are 1080x1350, stories 1080x1920, all JPEG under 1.5 MB.
Every image carries "openwineatlas.com".

## Setup (fresh machine)

```sh
git clone --depth 1 https://github.com/doma17-wc/open-wine-atlas main            # the atlas (web/, api/)
git clone --depth 1 --branch social https://github.com/doma17-wc/open-wine-atlas social
pip install playwright pillow && python3 -m playwright install chromium          # skip if Chromium is already there
T=social/tools/study_posts
LIBS=$PWD/libs          # any writable folder; filled with npm on first use
OUT=$PWD/out            # where the images go
```

- Python 3 with `playwright` and `Pillow`. Chromium: set `OWA_CHROME=/path/to/chrome` to use a given binary;
  otherwise `/opt/pw-browsers/chromium-1194/chrome-linux/chrome` if present, else Playwright's own.
- Node and npm. On first use the tools install into `$LIBS`: `maplibre-gl@5.24.0`, `pmtiles@4.5.0` (the map),
  `@fontsource/cormorant-garamond`, `@fontsource/ibm-plex-sans`, `@fontsource/ibm-plex-mono` (fonts; without npm
  the TTFs in `main/api/fonts` are used) and, for the "Drawn at the same scale" picture, `@mapbox/vector-tile` and
  `pbf` to run `main/api/pair.mjs` locally. A folder with unpacked npm tarballs (`maplibre-gl-5.24.0/dist/...`,
  `pmtiles-4.5.0/dist/...`) also works.
- No outside network is needed while rendering: the atlas is served from `main/web` on a local port and every
  other request is blocked (the jsdelivr script URLs are answered from `$LIBS`).

All facts come from `main/web/data/study.json` (questions) and `search.json` (places). Question keys are
`<lesson id>#<question id>`, e.g. `bourgogne-overview#q1`. List them with:

```sh
python3 -c "import json;d=json.load(open('main/web/data/study.json'))
for p in d['paths']:
  for l in p['lessons']:
    for q in l['questions']: print(p['id'], l['id']+'#'+q['id'], q['q'])"
```

## (a) Quiz carousel for a study path

```sh
python3 $T/render.py quiz --repo main --libs $LIBS --out $OUT \
  --name study-2026-10-23-burgundy-quiz \
  --title "Burgundy quiz" --hook "3 questions WSET 3 students should get" \
  --hook-map fr-inao-a162 --map fr-inao-a165 \
  --q bourgogne-overview#q1 --q bourgogne-cote-de-beaune#q1 --q bourgogne-chablis#q4
```

Inputs: 2 to 4 `--q` keys (3 or 4 recommended), `--map` = place id shown on the answers slide (a place the
questions involve), `--hook-map` = place id behind the hook slide (pick one that does not give an answer away;
defaults to `--map`), `--title` (eyebrow) and `--hook` (big line). Place ids: `main/web/data/search.json`
(`[name, id, country, level, rank, parent, bbox, ...]`).

Output: `$OUT/<name>-1.jpg` hook (real atlas map, "Comment your answers before you swipe."), one slide per question
(question exactly as in study.json, options A to D in file order), last slide = answers with letters and the
study.json explanations under a map strip. The last line printed is JSON with the files and the answers
(letter, option, explanation) for checking and for the caption.

## (b) Single-question story

```sh
python3 $T/render.py story --repo main --libs $LIBS --out $OUT \
  --name study-2026-10-23-story-wehlen --q germany-austria-mosel#q3 --prev rhone-south-southern-rhone#q5
```

Inputs: one `--q`; optional `--prev` = yesterday's story question, whose answer is shown on top
("Yesterday: C. Tavel · ..."). Output: `$OUT/<name>.jpg`, 1080x1920, question, options A to D and
"Answer in our next post · openwineatlas.com". Content stays inside the Instagram story safe area
(250 px top and bottom). Long questions get a smaller size automatically.

## (c) Feature carousel from app screenshots

1. Screenshots of the app at phone size (390x844 CSS px, scale 2):

```sh
python3 $T/shots.py --list                                   # the scenes
python3 $T/shots.py --repo main --libs $LIBS --out shots --scene study-hub --scene compare --scene notebook
```

Scenes: study-hub, study-paths, study-path, study-lesson, lesson-fly, quiz-question, quiz-answered, map-quiz,
review-hub, review-quiz (study state is seeded in localStorage), place (Corton), compare (Romanée-Conti and
La Tâche at the same scale), notebook (two seeded notes pinned to places), saved (saves three places through the
UI), producer (searches a producer). Output: `shots/<scene>.png`. Add a scene by writing an `async def s_x(pg, a)`
in shots.py and listing it in `SCENES`.

2. Slides from a JSON spec (examples in `specs/`):

```sh
python3 $T/render.py feature --repo main --libs $LIBS --out $OUT \
  --name study-2026-10-28-study-group --spec $T/specs/study-group.json --shots shots
```

Spec: `{"slides": [...]}`, each slide one of
- `{"kind": "cover", "eyebrow", "title", "text", "shots": ["x.png"]}`
- `{"kind": "shots", "eyebrow", "title", "text", "shots": ["a.png", "b.png"], "caps": ["...", "..."], "crop": [0, 300], "top": 385, "phone_h": 740}`
  (one or two phones; `crop` hides the top N screen px of a shot and shows the rest larger; `top` moves the phones
  down when the title or text runs to two lines)
- `{"kind": "end", "eyebrow", "title", "list": ["...", "..."], "url": "openwineatlas.com"}`

Output: `$OUT/<name>-<n>.jpg`.

## Checks built in

Each render measures every text box and stops with `text runs out of its box on <file>` if anything would be cut;
shorten the text or change the layout values. Still look at every image before posting.

## Posting

Copy the JPEGs to `cards/` in the social branch, commit, `git push origin social` (fetch and rebase if refused,
never force). Public URL: `https://raw.githubusercontent.com/doma17-wc/open-wine-atlas/social/cards/<file>`
(check with `curl -sI`). Schedule in Metricool (brand 7132077, Europe/Zurich) and add the post to `posted.json`.
