#!/usr/bin/env python3
"""Fast autopilot renders for the Open Wine Atlas Instagram: reels, carousels and stories from one JSON spec.
Stills of the real atlas map are rendered once, then animated with ffmpeg, so a reel takes minutes, not hours.

  python3 make.py reel-cluster --spec s.json   places added one by one, then the total
  python3 make.py reel-vs      --spec s.json   two places at the same zoom
  python3 make.py carousel     --spec s.json   cover, one slide per place, member slide
  python3 make.py story-teaser --spec s.json   a story pointing to a reel or post
  python3 make.py story-member --spec s.json   a story asking people to become members
Common: --repo MAIN --libs LIBS --out DIR. Spec: {"name", "eyebrow", "title", "sub", "places": [ids], "preset", "seed"}.
Areas always come from web/data/details-<cc>.json, never from the spec. The last printed line is JSON.
"""
import argparse
import asyncio
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "study_posts"))
import owa  # noqa: E402
from owa import esc, GOLD, MUTED, PARCH, NIGHT  # noqa: E402

RW, RH, FW, FH, FPS = 1080, 1920, 1080, 1350, 30
MEMBER = {"kick": "Join the atlas", "title": "Become a Founding Member", "line": "Free for the first 1,000. A numbered badge and first access to every new tool.",
          "url": "openwineatlas.com/founding"}
CSS = f"""
.full{{position:absolute;inset:0}}.full img{{width:100%;height:100%;object-fit:cover;display:block}}
.shade{{position:absolute;left:0;right:0;bottom:0;background:linear-gradient(rgba(11,11,13,0),rgba(11,11,13,.96) 42%)}}
.brand{{position:absolute;left:0;right:0;top:175px;text-align:center;font:500 26px 'IBM Plex Mono';letter-spacing:.24em;color:{GOLD};text-transform:uppercase}}
.block{{position:absolute;left:90px;right:150px;text-align:center}}
.kick{{font:500 30px 'IBM Plex Mono';letter-spacing:.14em;text-transform:uppercase;color:{MUTED}}}
.h{{font:500 112px/1.05 'Cormorant Garamond';color:#f6eedd;margin:20px 0 0;text-wrap:balance}}
.h2{{font:500 88px/1.08 'Cormorant Garamond';color:#f6eedd;margin:12px 0 0;text-wrap:balance}}
.ha{{font:500 66px 'Cormorant Garamond';color:{GOLD};margin-top:8px}}
.sub{{font:italic 500 54px/1.15 'Cormorant Garamond';color:{GOLD};margin-top:22px;text-wrap:balance}}
.note{{font:400 32px/1.3 'IBM Plex Sans';color:#cfc6b6;margin-top:18px;text-wrap:balance}}
.big{{font:500 170px/1 'Cormorant Garamond';color:{GOLD}}}
.rule{{width:120px;height:3px;background:{GOLD};margin:26px auto}}
.url{{display:inline-block;margin-top:34px;padding:16px 30px;border-radius:999px;background:{GOLD};color:#17130b;font:500 36px 'IBM Plex Mono'}}
.tag{{font:500 28px 'IBM Plex Mono';letter-spacing:.1em;color:{MUTED};margin-top:30px}}
.fb{{position:absolute;left:80px;right:80px}}
"""


NOAREA = False  # spec "no_area": true, for outlines drawn from whole communes, whose area is not the appellation's


def area(atlas, pid):
    if NOAREA:
        return None
    d = details(atlas, pid)
    return d.get("area_ha") or d.get("outline_area_ha")


def details(atlas, pid):
    cc = atlas.index[pid][2].lower()
    cache = atlas.__dict__.setdefault("_det", {})
    if cc not in cache:
        cache[cc] = json.load(open(os.path.join(atlas.web, "data", f"details-{cc}.json"), encoding="utf-8"))
    return cache[cc].get(pid, {})


def fmt_ha(v):
    if v is None:
        return ""
    return (f"{v:,.0f}" if v >= 100 else f"{v:.1f}") + " ha"


def union(atlas, ids):
    b = [atlas.index[i][6] for i in ids]
    return [min(x[0] for x in b), min(x[1] for x in b), max(x[2] for x in b), max(x[3] for x in b)]


MARK = """(ids) => { const map = window.__map; window.OWA.clearSelected && window.OWA.clearSelected();
  (window.__sel || []).forEach((f) => { try { map.setFeatureState(f, {selected:false}); } catch (e) {} });
  const srcs = Object.entries(map.getStyle().sources).filter(([k, v]) => v.type === 'vector' && !['base','poi','ovlo','geo','osm'].includes(k)).map(([k]) => k);
  window.__sel = [];
  ids.forEach((id) => srcs.forEach((s) => ['appellations','crus','grosslagen'].forEach((sl) => { const f = {source:s, sourceLayer:sl, id};
    try { map.setFeatureState(f, {selected:true}); window.__sel.push(f); } catch (e) {} }))); }"""


GOLD_PAINT = """() => { const m = window.__map, SEL = ['boolean', ['feature-state', 'selected'], false];
  m.getStyle().layers.filter((l) => ['appellations','crus','grosslagen'].includes(l['source-layer'])).forEach((l) => { try {
    if (l.type === 'fill') { m.setPaintProperty(l.id, 'fill-color', ['case', SEL, '#e7c06a', '#2a2a2e']); m.setPaintProperty(l.id, 'fill-opacity', ['case', SEL, 0.72, 0.16]); }
    if (l.type === 'line') { m.setPaintProperty(l.id, 'line-color', ['case', SEL, '#f4d98e', '#6d6a63']); m.setPaintProperty(l.id, 'line-opacity', ['case', SEL, 1, 0.55]); }
  } catch (e) {} }); }"""


class Mapper:
    def __init__(self, br, base, libs, atlas, first, w, h):
        self.a = (br, base, libs, atlas, first, w, h)

    async def __aenter__(self):
        br, base, libs, atlas, first, w, h = self.a
        self.atlas = atlas
        self.pg = await owa.atlas_page(br, base, libs, w, h)
        await self.pg.goto(f"{base}/index.html#{first}")
        await owa.wait_atlas(self.pg, 2500)
        await self.pg.add_style_tag(content=owa.HIDE_UI)
        await self.pg.evaluate("() => { const m = window.__map; m.setPadding({top:0,bottom:0,left:0,right:0}); ['wineries','winery-labels'].forEach((l) => m.getLayer(l) && m.setLayoutProperty(l,'visibility','none')); }")
        await self.pg.evaluate(GOLD_PAINT)
        return self

    async def __aexit__(self, *e):
        await self.pg.close()

    async def fit(self, bbox, pad, maxzoom=13.5):
        await self.pg.evaluate("([b,p,z]) => window.__map.fitBounds([[b[0],b[1]],[b[2],b[3]]], {padding:p, maxZoom:z, duration:0})", [bbox, pad, maxzoom])

    async def shot(self, ids, out):
        await self.pg.evaluate(MARK, ids)
        await self.pg.evaluate(owa.IDLE)
        await self.pg.wait_for_timeout(1200)
        await self.pg.screenshot(path=out, type="jpeg", quality=92)


def doc(atlas, libs, w, h, body):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{owa.page_css(atlas, w, h, libs)}{CSS}</style></head><body>{body}</body></html>"


async def card(br, atlas, libs, w, h, body, out):
    over = await owa.html_jpg(br, doc(atlas, libs, w, h, body), out, w, h)
    if over:
        raise SystemExit(f"text runs out of its box on {out}: {over}")
    return out


def bg(p):
    return f'<div class="full"><img src="{owa.data_uri(p)}"></div>'


def member_block(top):
    return f"""<div class="block" data-fit="m" style="top:{top}px;overflow:hidden"><div class="kick">{esc(MEMBER['kick'])}</div>
      <div class="h" style="font-size:104px">{esc(MEMBER['title'])}</div><div class="rule"></div>
      <div class="note" style="font-size:38px">{esc(MEMBER['line'])}</div><div class="url" style="font-size:32px">{esc(MEMBER['url'])}</div><div class="tag">Link in bio</div></div>"""


def video(frames, out, preset, seed):
    """frames: [(jpg, seconds)]. Slow push-in on each still, cross-fades, original score, loudness normalised."""
    xf = 0.35
    args, chain = ["ffmpeg", "-v", "error", "-y"], []
    for i, (f, sec) in enumerate(frames):
        n = int((sec + xf) * FPS)
        args += ["-loop", "1", "-t", f"{sec + xf:.2f}", "-i", f]
        chain.append(f"[{i}:v]scale={RW * 2}:-2,zoompan=z='min(1+0.00035*on,1.04)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={n}:s={RW}x{RH}:fps={FPS},format=yuv420p,setsar=1[v{i}]")
    last, t = "v0", frames[0][1]
    for i in range(1, len(frames)):
        chain.append(f"[{last}][v{i}]xfade=transition=fade:duration={xf}:offset={t:.2f}[x{i}]")
        last, t = f"x{i}", t + frames[i][1]
    total = t + xf
    wav = out + ".wav"
    subprocess.run([sys.executable, os.path.join(HERE, "music2.py"), preset, wav, f"{total:.1f}", str(seed)], check=True, capture_output=True)
    args += ["-i", wav, "-filter_complex", ";".join(chain), "-map", f"[{last}]", "-map", f"{len(frames)}:a", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "160k", "-shortest", out]
    subprocess.run(args, check=True)
    os.remove(wav)
    return total


async def reel_cluster(s, a, atlas, br, base):
    ids, tmp, frames = s["places"], tempfile.mkdtemp(), []
    async with Mapper(br, base, a.libs, atlas, ids[0], RW, RH) as m:
        await m.fit(union(atlas, ids), {"top": 300, "bottom": 900, "left": 110, "right": 170})
        for i in range(len(ids) + 1):
            p = os.path.join(tmp, f"m{i}.jpg")
            await m.shot(ids[:i], p)
            hd = '<div class="brand">Open Wine Atlas</div><div class="shade" style="height:1000px"></div>'
            if i == 0:
                t = f"""<div class="block" data-fit="t" style="top:1010px;height:480px;overflow:hidden"><div class="kick">{esc(s['eyebrow'])}</div><div class="h">{esc(s['title'])}</div>
                  <div class="sub">{esc(s.get('sub', ''))}</div></div>"""
                sec = 2.4
            else:
                t = f"""<div class="block" data-fit="t" style="top:1060px;height:400px;overflow:hidden"><div class="kick">{i} / {len(ids)}</div><div class="h2">{esc(atlas.index[ids[i - 1]][0])}</div>
                  <div class="ha">{esc(fmt_ha(area(atlas, ids[i - 1])))}</div></div>"""
                sec = 1.7
            frames.append((await card(br, atlas, a.libs, RW, RH, bg(p) + hd + t, os.path.join(tmp, f"c{i}.jpg")), sec))
    tot = [area(atlas, i) for i in ids]
    if all(tot) and s.get("total", True):
        t = f"""<div class="block" data-fit="t" style="top:1060px;height:400px;overflow:hidden"><div class="big">{esc(fmt_ha(sum(tot)))}</div><div class="sub">all {len(ids)} together</div>
          <div class="note">Delimited area, not vineyard planted</div></div>"""
        frames.append((await card(br, atlas, a.libs, RW, RH, bg(p) + '<div class="brand">Open Wine Atlas</div><div class="shade" style="height:1000px"></div>' + t, os.path.join(tmp, "t.jpg")), 2.2))
    frames.append((await card(br, atlas, a.libs, RW, RH, member_block(620), os.path.join(tmp, "e.jpg")), 2.8))
    out = os.path.join(a.out, s["name"] + ".mp4")
    dur = video(frames, out, s.get("preset", "warm"), s.get("seed", 7))
    cover = os.path.join(a.out, s["name"] + "-cover.jpg")
    subprocess.run(["cp", frames[0][0], cover], check=True)
    return {"files": [out, cover], "seconds": round(dur, 1), "areas": {atlas.index[i][0]: area(atlas, i) for i in ids}, "total": sum(tot) if all(tot) else None}


async def reel_vs(s, a, atlas, br, base):
    x, y = s["places"]
    tmp = tempfile.mkdtemp()
    ax, ay = area(atlas, x), area(atlas, y)
    big = x if ax >= ay else y
    W, H = RW, 620
    async with Mapper(br, base, a.libs, atlas, big, W, H) as m:
        await m.fit(atlas.index[big][6], 70)
        z = await m.pg.evaluate("() => window.__map.getZoom()")
        shots = {}
        for pid in (x, y):
            b = atlas.index[pid][6]
            await m.pg.evaluate("([c,z]) => window.__map.jumpTo({center:c, zoom:z})", [[(b[0] + b[2]) / 2, (b[1] + b[3]) / 2], z])
            shots[pid] = os.path.join(tmp, pid + ".jpg")
            await m.shot([pid], shots[pid])
    def panel(pid, top):
        return f"""<div class="block" style="top:{top}px;left:60px;right:60px;font:500 60px 'Cormorant Garamond';color:#f6eedd">{esc(atlas.index[pid][0])} <span style="color:{GOLD};font-size:50px">{esc(fmt_ha(area(atlas, pid)))}</span></div>
          <div style="position:absolute;left:0;right:0;top:{top + 86}px;height:{H}px"><img style="width:100%;height:100%;object-fit:cover" src="{owa.data_uri(shots[pid])}"></div>"""
    hook = f"""<div class="full" style="opacity:.28">{bg(shots[big])}</div><div class="block" data-fit="t" style="top:600px;height:640px;overflow:hidden"><div class="kick">{esc(s['eyebrow'])}</div>
      <div class="h">{esc(atlas.index[x][0])}</div><div class="sub" style="margin:0">vs</div><div class="h">{esc(atlas.index[y][0])}</div><div class="sub">{esc(s.get('sub', 'drawn at the same zoom'))}</div></div>"""
    r = max(ax, ay) / min(ax, ay)
    head = '<div class="brand" style="top:150px">Open Wine Atlas</div>'
    frames = [(await card(br, atlas, a.libs, RW, RH, hook, os.path.join(tmp, "h.jpg")), 2.4),
              (await card(br, atlas, a.libs, RW, RH, head + panel(x, 230), os.path.join(tmp, "a.jpg")), 1.7),
              (await card(br, atlas, a.libs, RW, RH, head + panel(x, 230) + panel(y, 950), os.path.join(tmp, "b.jpg")), 3.0),
              (await card(br, atlas, a.libs, RW, RH, f"""<div class="block" data-fit="t" style="top:680px;height:560px;overflow:hidden"><div class="big">{r:.1f}×</div>
                <div class="h2" style="font-size:66px">{esc(atlas.index[big][0])} is {r:.1f}× bigger</div><div class="note">Delimited areas, not vineyard planted</div></div>""", os.path.join(tmp, "r.jpg")), 2.4),
              (await card(br, atlas, a.libs, RW, RH, member_block(620), os.path.join(tmp, "e.jpg")), 2.8)]
    out = os.path.join(a.out, s["name"] + ".mp4")
    dur = video(frames, out, s.get("preset", "dusk"), s.get("seed", 5))
    cover = os.path.join(a.out, s["name"] + "-cover.jpg")
    subprocess.run(["cp", frames[0][0], cover], check=True)
    return {"files": [out, cover], "seconds": round(dur, 1), "areas": {atlas.index[x][0]: ax, atlas.index[y][0]: ay}, "ratio": round(r, 1)}


async def carousel(s, a, atlas, br, base):
    ids, tmp, files = s["places"], tempfile.mkdtemp(), []
    async with Mapper(br, base, a.libs, atlas, ids[0], FW, FH) as m:
        await m.fit(union(atlas, ids), {"top": 90, "bottom": 500, "left": 110, "right": 110})
        p = os.path.join(tmp, "all.jpg")
        await m.shot(ids, p)
        o = os.path.join(a.out, s["name"] + "-1.jpg")
        files.append(await card(br, atlas, a.libs, FW, FH, bg(p) + f"""<div class="shade" style="height:760px"></div><div class="fb" data-fit="t" style="bottom:70px;height:470px;overflow:hidden">
          <div class="kick">{esc(s['eyebrow'])}</div><div class="h" style="font-size:96px">{esc(s['title'])}</div><div class="sub" style="font-size:46px">{esc(s.get('sub', ''))}</div></div>""", o))
        for i, pid in enumerate(ids):
            await m.fit(atlas.index[pid][6], {"top": 90, "bottom": 430, "left": 130, "right": 130}, 15)
            p = os.path.join(tmp, f"p{i}.jpg")
            await m.shot([pid], p)
            o = os.path.join(a.out, f"{s['name']}-{i + 2}.jpg")
            files.append(await card(br, atlas, a.libs, FW, FH, bg(p) + f"""<div class="shade" style="height:620px"></div><div class="fb" data-fit="t" style="bottom:70px;height:320px;overflow:hidden">
              <div class="kick">{i + 1} / {len(ids)}</div><div class="h2">{esc(atlas.index[pid][0])}</div><div class="ha">{esc(fmt_ha(area(atlas, pid)))}</div></div>""", o))
    o = os.path.join(a.out, f"{s['name']}-{len(ids) + 2}.jpg")
    files.append(await card(br, atlas, a.libs, FW, FH, member_block(330), o))
    return {"files": files, "areas": {atlas.index[i][0]: area(atlas, i) for i in ids}}


async def story_teaser(s, a, atlas, br, base):
    o = os.path.join(a.out, s["name"] + ".jpg")
    img = f'<div class="full" style="opacity:.3">{bg(s["image"])}</div>' if s.get("image") else ""
    await card(br, atlas, a.libs, RW, RH, img + f"""<div class="shade" style="height:1200px"></div><div class="block" data-fit="t" style="top:800px;height:760px;overflow:hidden">
      <div class="kick">{esc(s['eyebrow'])}</div><div class="h">{esc(s['title'])}</div><div class="sub">{esc(s.get('sub', ''))}</div><div class="tag">{esc(s.get('foot', 'New on our feed'))}</div></div>""", o)
    return {"files": [o]}


async def story_member(s, a, atlas, br, base):
    o = os.path.join(a.out, s["name"] + ".jpg")
    await card(br, atlas, a.libs, RW, RH, member_block(520), o)
    return {"files": [o]}


async def run(a):
    from playwright.async_api import async_playwright
    atlas = owa.Atlas(a.repo)
    srv, base = owa.serve(atlas.web)
    os.makedirs(a.out, exist_ok=True)
    s = json.load(open(a.spec, encoding="utf-8"))
    if s.get("member"):
        MEMBER.update(s["member"])
    global NOAREA
    NOAREA = bool(s.get("no_area"))
    try:
        async with async_playwright() as p:
            br = await owa.launch(p)
            r = await {"reel-cluster": reel_cluster, "reel-vs": reel_vs, "carousel": carousel, "story-teaser": story_teaser, "story-member": story_member}[a.cmd](s, a, atlas, br, base)
            await br.close()
    finally:
        srv.shutdown()
    print(json.dumps(r, ensure_ascii=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["reel-cluster", "reel-vs", "carousel", "story-teaser", "story-member"])
    ap.add_argument("--spec", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--libs", required=True)
    ap.add_argument("--out", required=True)
    asyncio.run(run(ap.parse_args()))
