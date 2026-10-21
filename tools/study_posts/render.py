"""Instagram images for the atlas study posts, rendered in headless Chromium in the atlas style.

    python3 render.py quiz    --repo MAIN --libs LIBS --out DIR --name NAME --title "Burgundy quiz" --hook "3 questions WSET 3 students should get"
                              --map PLACE_ID --q LESSON#QID --q LESSON#QID [--q ...]
    python3 render.py story   --repo MAIN --libs LIBS --out DIR --name NAME --q LESSON#QID [--prev LESSON#QID]
    python3 render.py feature --repo MAIN --libs LIBS --out DIR --name NAME --spec SLIDES.json

Feed slides are 1080x1350, stories 1080x1920, JPEG under 1.5 MB, written as DIR/NAME-<n>.jpg (a story: DIR/NAME.jpg).
Questions are quoted exactly from web/data/study.json (key: <lesson id>#<question id>, e.g. bourgogne-overview#q1);
options keep the order of the file and are lettered A to D. Every run prints the files written and a JSON line
with the answers, and stops with an error if any text runs out of its box.
"""
import argparse
import asyncio
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import owa  # noqa: E402
from owa import esc, GOLD, MUTED, LINE, PARCH, NIGHT  # noqa: E402

FW, FH = 1080, 1350
SW, SH = 1080, 1920
L = "ABCD"


LIBS = None


def doc(atlas, w, h, css, body):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{owa.page_css(atlas, w, h, LIBS)}{css}</style></head><body>{body}</body></html>"


# ---------- quiz carousel
QUIZ_CSS = f"""
.pad{{position:absolute;left:80px;right:80px}}
.hook .bg{{position:absolute;inset:0;background-size:cover;background-position:center}}
.hook .shade{{position:absolute;inset:0;background:linear-gradient({NIGHT} 0%,rgba(11,11,13,.86) 36%,rgba(11,11,13,.1) 60%,rgba(11,11,13,.35) 82%,{NIGHT} 100%)}}
.hook h1{{font:500 112px/1.1 'Cormorant Garamond';margin:22px 0 0;text-wrap:balance}}
.hook p{{font:400 40px/1.35 'IBM Plex Sans';margin:30px 0 0;color:{PARCH};max-width:880px}}
.pill{{display:inline-block;padding:10px 24px;border:2px solid {GOLD};color:{GOLD};border-radius:999px;font:500 28px 'IBM Plex Mono'}}
.qtext{{font:500 72px/1.1 'Cormorant Garamond';margin:24px 0 0;text-wrap:balance}}
.opts{{display:grid;gap:22px}}
.opt{{display:flex;align-items:center;gap:30px;padding:26px 30px;border:2px solid {LINE};border-radius:22px;background:#151519;font:400 40px/1.2 'IBM Plex Sans'}}
.opt b{{flex:none;width:68px;height:68px;border-radius:50%;border:2px solid {GOLD};color:{GOLD};display:grid;place-items:center;font:500 34px 'IBM Plex Mono'}}
.band{{position:absolute;left:0;right:0;top:0;background-size:cover;background-position:center}}
.band:after{{content:"";position:absolute;inset:0;background:linear-gradient(rgba(11,11,13,.55),rgba(11,11,13,0) 30%,rgba(11,11,13,0) 70%,{NIGHT})}}
.band .lbl{{position:absolute;left:80px;top:64px;z-index:2}}
.ans{{display:grid;gap:30px}}
.tag{{display:inline-block;background:rgba(11,11,13,.86);padding:8px 16px;margin-left:-16px;border-radius:10px}}
.a{{display:grid;grid-template-columns:84px 1fr;gap:6px 26px;align-items:start}}
.a .n{{grid-row:span 2;width:84px;height:84px;border-radius:50%;background:{GOLD};color:#17130b;display:grid;place-items:center;font:500 40px 'IBM Plex Mono'}}
.a h3{{margin:0;font:500 46px/1.1 'Cormorant Garamond'}}
.a p{{margin:0;font:400 28px/1.38 'IBM Plex Sans';color:#cfc6b6}}
.a.sm h3{{font-size:40px}}.a.sm p{{font-size:25px;line-height:1.34}}.a.sm{{grid-template-columns:72px 1fr}}.a.sm .n{{width:72px;height:72px;font-size:34px}}
"""


async def quiz(a, atlas, br, base):
    qs = [atlas.q(k) for k in a.q]
    tmp = tempfile.mkdtemp()
    path_title = qs[0][0]["title"]
    n = len(qs)
    files, report = [], []
    # the map: one full-page render for the hook, a wide one for the answers
    hook_png, band_png = os.path.join(tmp, "hook.png"), os.path.join(tmp, "band.png")
    await owa.map_png(br, base, a.libs, atlas, a.hook_map or a.map, hook_png, FW, FH, pad={"top": 520, "bottom": 300, "left": 120, "right": 120})
    band_h = 470 if n <= 3 else 330
    await owa.map_png(br, base, a.libs, atlas, a.map, band_png, FW, band_h, pad={"top": 70, "bottom": 70, "left": 140, "right": 140})
    place = atlas.index[a.map][0]
    slides = []
    slides.append(f"""<div class="hook"><div class="bg" style="background-image:url({owa.data_uri(hook_png)})"></div><div class="shade"></div>
      <div class="pad" style="top:96px"><div class="eb">{esc(a.title)} · {n} questions</div><h1 data-fit="hook" style="max-height:340px;overflow:hidden">{esc(a.hook)}</h1>
      <p>Comment your answers before you swipe.</p></div>
      <div class="pad" style="bottom:150px"><span class="pill">Map: {esc(atlas.index[a.hook_map or a.map][0])}</span></div>{owa.foot()}</div>""")
    for i, (p, l, q) in enumerate(qs):
        opts = "".join(f'<div class="opt"><b>{L[j]}</b><span>{esc(o)}</span></div>' for j, o in enumerate(q["options"]))
        slides.append(f"""<div class="pad" style="top:96px;bottom:170px;display:flex;flex-direction:column">
          <div class="eb">Question {i + 1} of {n} · {esc(p['title'])}</div>
          <div class="qtext" data-fit="q{i + 1}" style="max-height:330px;overflow:hidden">{esc(q['q'])}</div>
          <div style="flex:1"></div><div class="opts">{opts}</div></div>{owa.foot(right='Answers on the last slide')}""")
        report.append({"key": l["id"] + "#" + q["id"], "q": q["q"], "answer": L[q["answer"]], "option": q["options"][q["answer"]], "explain": q["explain"]})
    ans = "".join(f"""<div class="a{' sm' if n > 3 else ''}"><div class="n">{L[q['answer']]}</div><h3>{i + 1}. {esc(q['options'][q['answer']])}</h3>
        <p>{esc(q['explain'])}</p></div>""" for i, (_, _, q) in enumerate(qs))
    slides.append(f"""<div class="band" style="height:{band_h}px;background-image:url({owa.data_uri(band_png)})"><div class="lbl"><div class="eb tag" style="color:{PARCH}">Answers</div></div>
        <div style="position:absolute;left:80px;bottom:18px;z-index:2" class="eb tag">{esc(place)} on the atlas</div></div>
      <div class="pad ans" data-fit="answers" data-strict="1" style="top:{band_h + 36}px;bottom:150px;overflow:hidden;{'gap:22px' if n > 3 else ''}">{ans}</div>
      {owa.foot(left='Open Wine Atlas', right=f"{path_title.split(' and ')[0].split(',')[0]} path · openwineatlas.com")}""")
    for i, body in enumerate(slides):
        out = os.path.join(a.out, f"{a.name}-{i + 1}.jpg")
        over = await owa.html_jpg(br, doc(atlas, FW, FH, QUIZ_CSS, body), out, FW, FH)
        if over:
            raise SystemExit(f"text runs out of its box on {out}: {over}")
        files.append(out)
    return files, report


# ---------- story
STORY_CSS = f"""
.pad{{position:absolute;left:80px;right:80px}}
.glow{{position:absolute;inset:0;background:radial-gradient(1200px 800px at 85% 8%,rgba(231,192,106,.13),rgba(11,11,13,0) 60%),radial-gradient(900px 700px at 0% 100%,rgba(231,192,106,.08),rgba(11,11,13,0) 60%)}}
.prev{{padding:22px 28px;border:2px solid #3b3426;border-radius:20px;background:#17140e;font:400 30px/1.35 'IBM Plex Sans';color:#d8cfbf}}
.prev b{{color:{GOLD};font-weight:400}}
.qtext{{font:500 84px/1.1 'Cormorant Garamond';margin:26px 0 0;text-wrap:balance;flex:none}}
.opts{{display:grid;gap:24px}}
.opt{{display:flex;align-items:center;gap:30px;padding:30px 32px;border:2px solid {LINE};border-radius:24px;background:#151519;font:400 42px/1.2 'IBM Plex Sans'}}
.opt b{{flex:none;width:74px;height:74px;border-radius:50%;border:2px solid {GOLD};color:{GOLD};display:grid;place-items:center;font:500 36px 'IBM Plex Mono'}}
.sfoot{{position:absolute;left:80px;right:80px;bottom:270px;text-align:center;font:400 32px 'IBM Plex Mono';color:{MUTED};letter-spacing:.04em}}
.sfoot b{{color:{GOLD};font-weight:400}}
"""


async def story(a, atlas, br, base):
    p, l, q = atlas.q(a.q[0])
    prev = ""
    if a.prev:
        pp, pl, pq = atlas.q(a.prev)
        prev = (f'<div class="prev" data-fit="prev" style="max-height:170px;overflow:hidden">Yesterday: <b>{L[pq["answer"]]}. {esc(pq["options"][pq["answer"]])}</b>'
                f' · {esc(pq["q"])}</div>')
    opts = "".join(f'<div class="opt"><b>{L[j]}</b><span>{esc(o)}</span></div>' for j, o in enumerate(q["options"]))
    body = f"""<div class="glow"></div>
      <div class="pad" style="top:250px">{prev}</div>
      <div class="pad" data-fit="story" data-strict="1" style="top:{470 if prev else 330}px;bottom:350px;display:flex;flex-direction:column;overflow:hidden">
        <div class="eb">Question of the day · {esc(p['title'])}</div>
        <div class="qtext" data-fit="q" style="font-size:{88 if len(q['q']) <= 50 else 78 if len(q['q']) <= 75 else 70}px;max-height:{430 if prev else 520}px;overflow:hidden">{esc(q['q'])}</div>
        <div style="flex:1;min-height:30px"></div><div class="opts" style="flex:none">{opts}</div></div>
      <div class="sfoot">Answer in our next post · <b>openwineatlas.com</b></div>"""
    out = os.path.join(a.out, f"{a.name}.jpg")
    over = await owa.html_jpg(br, doc(atlas, SW, SH, STORY_CSS, body), out, SW, SH)
    if over:
        raise SystemExit(f"text runs out of its box on {out}: {over}")
    return [out], [{"key": l["id"] + "#" + q["id"], "q": q["q"], "answer": L[q["answer"]], "option": q["options"][q["answer"]], "explain": q["explain"]}]


# ---------- feature carousel from app screenshots
FEAT_CSS = f"""
.pad{{position:absolute;left:80px;right:80px}}
h1{{font:500 92px/1.1 'Cormorant Garamond';margin:18px 0 0;text-wrap:balance}}
h2{{font:500 70px/1.1 'Cormorant Garamond';margin:16px 0 0;text-wrap:balance}}
.lead{{font:400 34px/1.38 'IBM Plex Sans';color:#d6cdbd;margin:20px 0 0}}
.phones{{position:absolute;left:0;right:0;display:flex;justify-content:center;align-items:flex-start;gap:44px}}
.phone{{padding:10px;border-radius:46px;background:#18181d;border:2px solid #34343c;box-shadow:0 30px 80px rgba(0,0,0,.6),0 0 0 1px rgba(231,192,106,.10)}}
.phone img{{display:block;border-radius:36px}}
.cap{{text-align:center;font:400 24px 'IBM Plex Mono';color:{MUTED};margin-top:16px;letter-spacing:.04em}}
.big{{font:500 120px/1.1 'Cormorant Garamond';text-wrap:balance}}
.list{{margin:34px 0 0;padding:0;list-style:none;display:grid;gap:18px;font:400 36px/1.3 'IBM Plex Sans'}}
.list li{{display:flex;gap:22px}}.list li:before{{content:"";flex:none;width:14px;height:14px;margin-top:16px;border-radius:50%;background:{GOLD}}}
.glow{{position:absolute;inset:0;background:radial-gradient(900px 700px at 90% 0%,rgba(231,192,106,.12),rgba(11,11,13,0) 60%)}}
.url{{display:inline-block;margin-top:34px;padding:16px 30px;border-radius:999px;background:{GOLD};color:#17130b;font:500 34px 'IBM Plex Mono'}}
"""


def phone_html(path, h, cap="", crop_top=0):
    """A screenshot (390x844 CSS px at scale 2) in a phone frame of height h. crop_top (screenshot CSS px) hides the
    top of the screen and shows the rest larger, for a detail lower down."""
    from PIL import Image
    im = Image.open(path)
    css_w, css_h = 390, round(390 * im.height / im.width)
    scale = h / (css_h - crop_top)
    w = round(css_w * scale)
    img = (f'<div style="width:{w}px;height:{h}px;overflow:hidden;border-radius:36px"><img src="{owa.data_uri(path)}" '
           f'style="display:block;width:{w}px;margin-top:-{round(crop_top * scale)}px"></div>')
    return f'<div><div class="phone" style="width:fit-content;margin:0 auto">{img}</div>' + (f'<div class="cap">{esc(cap)}</div>' if cap else "") + "</div>"


def to_jpg_shot(path, tmp):
    """Screenshots are PNG; embed them as high quality JPEG to keep the slides small."""
    from PIL import Image
    out = os.path.join(tmp, os.path.basename(path).rsplit(".", 1)[0] + ".jpg")
    Image.open(path).convert("RGB").save(out, quality=90)
    return out


async def feature(a, atlas, br, base):
    spec = json.load(open(a.spec, encoding="utf-8"))
    sdir = os.path.dirname(os.path.abspath(a.spec))
    tmp = tempfile.mkdtemp()
    files = []
    for i, s in enumerate(spec["slides"]):
        shots = [to_jpg_shot(x if os.path.isabs(x) else os.path.join(a.shots or sdir, x), tmp) for x in s.get("shots", [])]
        caps = s.get("caps", [""] * len(shots))
        crops = s.get("crop", [0] * len(shots))
        top = f'<div class="eb">{esc(s.get("eyebrow", ""))}</div>' if s.get("eyebrow") else ""
        if s["kind"] == "cover":
            ph = phone_html(shots[0], 730, "", crops[0]) if shots else ""
            body = f"""<div class="glow"></div><div class="pad" style="top:90px">{top}<h1 data-fit="t" style="max-height:200px;overflow:hidden">{esc(s['title'])}</h1>
              <p class="lead" data-fit="l" style="max-height:100px;overflow:hidden">{esc(s.get('text', ''))}</p></div>
              <div class="phones" style="top:430px">{ph}</div>{owa.foot()}"""
        elif s["kind"] == "shots":
            hph = s.get("phone_h", 740 if len(shots) > 1 else 760 if any(caps) else 790)
            ph = "".join(phone_html(x, hph, c, cr) for x, c, cr in zip(shots, caps, crops))
            body = f"""<div class="pad" style="top:80px">{top}<h2 data-fit="t" style="max-height:150px;overflow:hidden">{esc(s['title'])}</h2>
              <p class="lead" data-fit="l" style="max-height:96px;overflow:hidden">{esc(s.get('text', ''))}</p></div>
              <div class="phones" style="top:{s.get('top', 385)}px">{ph}</div>{owa.foot()}"""
        else:  # end
            items = "".join(f"<li>{esc(x)}</li>" for x in s.get("list", []))
            body = f"""<div class="glow"></div><div class="pad" style="top:150px">{top}<div class="big" data-fit="t" style="margin-top:22px;max-height:400px;overflow:hidden">{esc(s['title'])}</div>
              <ul class="list" data-fit="list" style="max-height:470px;overflow:hidden">{items}</ul>
              <div class="url">{esc(s.get('url', 'openwineatlas.com'))}</div></div>{owa.foot()}"""
        out = os.path.join(a.out, f"{a.name}-{i + 1}.jpg")
        over = await owa.html_jpg(br, doc(atlas, FW, FH, FEAT_CSS, body), out, FW, FH)
        if over:
            raise SystemExit(f"text runs out of its box on {out}: {over}")
        files.append(out)
    return files, []


async def run(a):
    global LIBS
    from playwright.async_api import async_playwright
    LIBS = a.libs
    atlas = owa.Atlas(a.repo)
    srv, base = owa.serve(atlas.web)
    os.makedirs(a.out, exist_ok=True)
    try:
        async with async_playwright() as p:
            br = await owa.launch(p)
            files, report = await {"quiz": quiz, "story": story, "feature": feature}[a.cmd](a, atlas, br, base)
            await br.close()
    finally:
        srv.shutdown()
    for f in files:
        print(f, os.path.getsize(f))
    print(json.dumps({"files": files, "answers": report}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["quiz", "story", "feature"])
    ap.add_argument("--repo", required=True, help="checkout of main (web/data/study.json, api/fonts)")
    ap.add_argument("--libs", required=True, help="folder with maplibre-gl and pmtiles (npm installs them there if missing)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", required=True, help="file name stem, e.g. study-2026-10-23-burgundy-quiz")
    ap.add_argument("--q", action="append", default=[], help="question key <lesson id>#<question id>; repeat for a quiz")
    ap.add_argument("--prev", default="", help="story: yesterday's question key, its answer is shown on top")
    ap.add_argument("--title", default="", help="quiz: eyebrow, e.g. 'Burgundy quiz'")
    ap.add_argument("--hook", default="", help="quiz: big line on slide 1")
    ap.add_argument("--map", default="", help="quiz: place id for the map on the answers slide (and the hook, unless --hook-map)")
    ap.add_argument("--hook-map", default="", help="quiz: place id for the hook slide map; pick one that does not give answers away")
    ap.add_argument("--spec", default="", help="feature: JSON with the slides")
    ap.add_argument("--shots", default="", help="feature: folder of the screenshots named in the spec (default: the spec's folder)")
    a = ap.parse_args()
    if a.cmd == "quiz" and not (a.q and a.map and a.hook and a.title):
        ap.error("quiz needs --q (2 to 4), --map, --hook and --title")
    if a.cmd == "story" and len(a.q) != 1:
        ap.error("story needs exactly one --q")
    if a.cmd == "feature" and not a.spec:
        ap.error("feature needs --spec")
    asyncio.run(run(a))


if __name__ == "__main__":
    main()
