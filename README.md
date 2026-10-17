# Deep dives (Open Wine Atlas social videos)

One wine region, explored layer by layer on the real atlas map: place, terrain (3D), rain, sun, heat, grapes.
About 55 to 60 seconds, 1080x1920, original music, every number on screen with its source.
Two a day on Instagram (Reel), TikTok and YouTube (Short) via Metricool, at 10:20 and 17:50 Zurich time.
Separate from the short "Where exactly is…" reels.

## Files
- `eps/<slug>.json` one spec per episode (shots, overlay segments, music, cover). `eps/jp-yamanashi.json` is the reference episode.
- `plan.json` the queue of upcoming topics with the date they fit (events, harvests, series). `posted.json` what went out.
- `deep_map.mjs` pass 1: map footage per shot from `web/index.html` of the main branch (headless Chromium). Shots run at 10 fps (6 fps for 3D terrain shots) and are interpolated to 30 fps.
- `deep_ovl.mjs` pass 2: text and charts as transparent PNG frames at 30 fps. `--at 3,10,25` renders preview stills.
- `music2.py preset out.wav seconds seed` original score (presets: japan, warm, dusk, alpine, south).
- `deep_cover.mjs` cover image. `deep_make.py eps/<slug>.json` runs everything and writes `work/<slug>/<slug>.mp4` and `cover.jpg`.

## Setup
    git clone --depth 1 https://github.com/doma17-wc/open-wine-atlas /home/claude/open-wine-atlas      # main: the atlas page and fonts
    git clone --depth 1 --branch deep-dive https://github.com/doma17-wc/open-wine-atlas /home/claude/rend
    cd /home/claude/rend && npm i puppeteer-core maplibre-gl@5.24.0 pmtiles@4.5.0
Chromium at /opt/pw-browsers/chromium-1194. Terrain tiles come from tiles.mapterhorn.com through curl (cached in /home/claude/rend/tilecache).

## Spec
- `shots[]`: `dur` seconds, `cam` keyframes `[t, lng, lat, zoom, bearing, pitch]` (zoom in 540 px space), `globe`, `terrain` (3D exaggeration, e.g. 1.6), `fps`,
  `layers` {`alt` altitude tint, `altOpacity`, `slope`, `aspect`, `markers`, `wineries`}, `labels`, `pad` {top, bottom} in 540x960 px.
  Shots cross-fade by `xfade` (0.5 s), so shot k starts at sum(previous durations) minus k x 0.5.
- `markers[]`: {lng, lat, label, shots:[indexes]}.
- `segments[]`: `title`, `chips` (layer progress), `card` (kicker, n, u, count {v, d}, c, nt, chart, src), `note`, `outro`.
  Charts: `months` (a, optional b to compare, bands, hot, labels), `range` (min, max, hl), `compare` (rows), `shares` (rows in %).
- Text stays out of the app UI zones: top 250 px, bottom 470 px, right 150 px.

## Timing (2 CPUs)
Map pass about 25 to 35 min (a 3D shot is the slow part), overlay about 5 min, interpolation and encode about 15 min.
