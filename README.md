# Reel renderer v2 (Open Wine Atlas social videos)

Renders 1080x1920 reels from the real atlas page (`web/index.html`) in headless Chromium, with readable labels and terrain.

- `page.mjs` opens the atlas at 540x960 with deviceScaleFactor 2, lets Mapterhorn terrain through (via curl, cached), and scales map labels 1.55x, lighter colour, thicker halo.
- `render.mjs spec.json outdir [from to]` renders frames. Spec: `id`, `camera` keyframes `[t, lng, lat, zoom, bearing, pitch]` (zoom in 540px space), `segments` (title, fact, note, src, outro). Text is kept out of the TikTok/Instagram UI zones (top 250px, bottom 470px, right 150px).
- `music.py preset out.wav seconds` writes the original ambient score.
- Encode: `ffmpeg -framerate 30 -i f/%05d.jpg -i music.wav -c:v libx264 -preset slow -crf 16 -x264-params aq-mode=3 -pix_fmt yuv420p -movflags +faststart -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:a aac -b:a 192k -shortest out.mp4`
- Covers: `covers.py items.json list.json` resolves place names to atlas ids and bbox, then `node covers.mjs list.json outdir` makes one cover per reel (title big in the middle third, readable in the 3:4 profile grid). Send it to Metricool as `videoThumbnailUrl`.

Needs: `npm i puppeteer-core maplibre-gl@5.24.0 pmtiles@4.5.0`, Chromium at /opt/pw-browsers, the repo checked out at /home/claude/open-wine-atlas. About 8 s per frame on 2 CPUs.
