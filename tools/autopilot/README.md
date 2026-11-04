# Autopilot (Open Wine Atlas Instagram)

`make.py` renders reels (`reel-cluster`, `reel-vs`), carousels (`carousel`) and stories (`story-teaser`, `story-member`) from a JSON spec in about a minute each: stills of the real atlas map, then ffmpeg. Run it with `OWA_CHROME` set. `music2.py` is the original score (presets japan, warm, dusk, alpine, south). `log.json` lists what the daily task made, so topics do not repeat. Quiz carousels and question stories come from `../study_posts/render.py`.

Spec fields: `name`, `eyebrow`, `title`, `sub`, `places` (atlas ids from web/data/search.json; 3 to 7 compact neighbours for a cluster, 2 for vs), `preset`, `seed`, `total` (false when outlines overlap), `no_area` (true for outlines drawn from whole communes), `no_labels` (true hides map labels such as estate names), `maxzoom` (cluster reel, default 13.5; raise to 15 for premier crus or anything under about 3 km across), `member` (replaces the member card text), `image` and `foot` (teaser story).
