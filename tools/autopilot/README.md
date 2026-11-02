# Autopilot (Open Wine Atlas Instagram)

`make.py` renders reels (`reel-cluster`, `reel-vs`), carousels (`carousel`) and stories (`story-teaser`, `story-member`) from a JSON spec in about a minute each: stills of the real atlas map, then ffmpeg. Run it with `OWA_CHROME` set. `music2.py` is the original score (presets japan, warm, dusk, alpine, south). `log.json` lists what the daily task made, so topics do not repeat. Quiz carousels and question stories come from `../study_posts/render.py`.

Spec fields: `name`, `eyebrow`, `title`, `sub`, `places` (atlas ids from web/data/search.json; 3 to 7 compact neighbours for a cluster, 2 for vs), `preset`, `seed`, `total` (false when outlines overlap), `no_area` (true for outlines drawn from whole communes), `member` (replaces the member card text), `image` and `foot` (teaser story).
