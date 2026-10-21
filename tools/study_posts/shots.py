"""Phone-size screenshots of the atlas app for feature carousels.

    python3 shots.py --repo MAIN_CHECKOUT --libs LIBS_DIR --out SHOTS_DIR [--scene NAME ...] [--stub SUPABASE_STUB_JS]

Each scene is written to SHOTS_DIR/<scene>.png at 390x844 CSS pixels, device scale 2 (780x1688).
Scenes: see SCENES below (`--list` prints them). Without --scene all scenes are taken.
The app runs from MAIN_CHECKOUT/web on a local server; no outside network is used.
"""
import argparse
import asyncio
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import owa  # noqa: E402

W, H, SCALE = 390, 844, 2
NOW = int(time.time() * 1000)


def study_state(atlas, path_id="north-france", n_due=6):
    """A study record as the app keeps it after a few days of use: lesson questions answered, some due again today."""
    p = atlas.path(path_id)
    keys = ["l:" + l["id"] + ":" + q["id"] for l in p["lessons"][:2] for q in l["questions"]]
    cards = {}
    for i, k in enumerate(keys):
        due = NOW - 3600_000 if i < n_due else NOW + (i % 5 + 1) * 864e5
        cards[k] = {"b": 1 if i < n_due else 2, "n": 1, "ok": 0 if i < n_due else 1, "due": int(due), "last": NOW - 864e5}
    days = [time.strftime("%Y-%m-%d", time.localtime(time.time() - d * 86400)) for d in (3, 2, 1)]
    return {"cards": cards, "done": {p["lessons"][0]["id"]: NOW - 2 * 864e5},
            "stats": {"answered": len(keys), "right": len(keys) - n_due, "days": days}, "today": {"d": "", "n": 0}}


async def open_dash(pg, tab):
    await pg.evaluate("(t) => window.OWA.openDash(t)", tab)
    await pg.wait_for_timeout(1800)


async def click(pg, sel, wait=1500):
    await pg.locator(sel).first.click()
    await pg.wait_for_timeout(wait)


async def answer_right(pg, atlas):
    """Click the right option of the lesson question on screen (looked up in study.json)."""
    qtext = (await pg.inner_text("#quiz .qz-q")).strip()
    for _, _, q in atlas.questions.values():
        if q["q"] == qtext:
            await pg.locator(f'#quiz [data-opt="{q["answer"]}"]').click()
            await pg.wait_for_timeout(2500)
            return
    raise RuntimeError("question not found in study.json: " + qtext)


async def first_mc_with_place(pg, atlas, title_sel="#quiz .qz-q"):
    """Skip ahead (by answering) until a lesson question tied to a place is on screen."""
    for _ in range(8):
        qtext = (await pg.inner_text(title_sel)).strip()
        hit = next((q for _, _, q in atlas.questions.values() if q["q"] == qtext), None)
        if hit and hit.get("place"):
            return hit
        await answer_right(pg, atlas)
        await pg.locator('#quiz [data-qz="next"]').click()
        await pg.wait_for_timeout(2500)
    return None


# each scene: (description, storage, async function(pg, atlas))
async def s_study_hub(pg, a):
    await open_dash(pg, "study")


async def s_study_path(pg, a):
    await open_dash(pg, "study")
    await click(pg, '[data-st-path="bourgogne"]')


async def s_study_lesson(pg, a):
    await open_dash(pg, "study")
    await click(pg, '[data-st-path="bourgogne"]')
    await click(pg, '[data-st-lesson="bourgogne-overview"]')
    await pg.evaluate("document.querySelector('.st-lesson .st-places')?.scrollIntoView({block:'end'})")
    await pg.wait_for_timeout(500)


async def s_lesson_fly(pg, a):
    await open_dash(pg, "study")
    await click(pg, '[data-st-path="bourgogne"]')
    await click(pg, '[data-st-lesson="bourgogne-overview"]')
    await click(pg, '.st-lesson [data-go="fr-inao-a182"]', 6000)
    await pg.evaluate(owa.IDLE)
    await pg.wait_for_timeout(1500)


async def s_quiz_question(pg, a):
    await open_dash(pg, "study")
    await click(pg, '[data-st-path="bourgogne"]')
    await click(pg, '[data-st-lesson="bourgogne-overview"]')
    await click(pg, '[data-st-quiz="bourgogne-overview"]', 4000)
    await first_mc_with_place(pg, a)
    await pg.evaluate(owa.IDLE)
    await pg.wait_for_timeout(1500)


async def s_quiz_answered(pg, a):
    await s_quiz_question(pg, a)
    await answer_right(pg, a)
    await pg.evaluate(owa.IDLE)
    await pg.wait_for_timeout(1500)


async def s_map_quiz(pg, a):
    await open_dash(pg, "study")
    await click(pg, '[data-st-path="bourgogne"]')
    await click(pg, '[data-st-map="bourgogne"]', 6000)
    for _ in range(10):  # a "find it on the map" question shows the hint line
        if await pg.locator("#quiz .qz-hint").count():
            break
        await pg.locator("#quiz [data-opt], #quiz [data-qz=giveup]").first.click()
        await pg.wait_for_timeout(1500)
        await pg.locator('#quiz [data-qz="next"]').click()
        await pg.wait_for_timeout(3500)
    await pg.evaluate(owa.IDLE)
    await pg.wait_for_timeout(1500)


async def s_study_paths(pg, a):
    await open_dash(pg, "study")
    await pg.evaluate("document.querySelector('.st-paths')?.scrollIntoView({block:'start'})")
    await pg.wait_for_timeout(400)


async def s_review_hub(pg, a):
    await open_dash(pg, "study")
    await pg.evaluate("document.querySelector('.st-review')?.scrollIntoView({block:'start'})")
    await pg.wait_for_timeout(400)


async def s_review_quiz(pg, a):
    await open_dash(pg, "study")
    await click(pg, '[data-st="review"]', 4500)
    await pg.evaluate(owa.IDLE)
    await pg.wait_for_timeout(1500)


async def s_place(pg, a):
    await pg.evaluate("location.hash = 'fr-inao-a165'")
    await pg.wait_for_timeout(7000)
    await pg.evaluate(owa.IDLE)
    await pg.wait_for_timeout(1000)


async def s_compare(pg, a):
    await pg.evaluate("location.hash = 'vs:fr-inao-a222,fr-inao-a191'")
    await pg.wait_for_timeout(9000)
    await pg.evaluate(owa.IDLE)
    await pg.wait_for_timeout(3000)
    # the drawing needs the outlines loaded; open the pair again now that the tiles are in
    await pg.evaluate("location.hash = 'vs:fr-inao-a222,fr-inao-a191,'")
    await pg.wait_for_timeout(6000)
    await pg.evaluate(owa.IDLE)
    await pg.wait_for_timeout(2000)
    print("set-shapes:", await pg.evaluate("(() => { const e = document.getElementById('set-shapes'); return e ? [e.hidden, e.innerHTML.length] : null })()"))
    await pg.evaluate("document.getElementById('set-shapes')?.scrollIntoView({block:'end'})")
    await pg.evaluate(owa.IDLE)
    await pg.wait_for_timeout(1500)


async def s_notebook(pg, a):
    await open_dash(pg, "notebook")


async def s_saved(pg, a):
    for pid in ["fr-inao-a207", "fr-inao-a211", "fr-inao-d443"]:
        await pg.evaluate("(h) => location.hash = h", pid)
        await pg.wait_for_timeout(10000)
        await pg.evaluate(owa.IDLE)
        await pg.wait_for_timeout(2500)
        b = pg.locator('.sheet [data-act="save"]').first
        if await b.get_attribute("aria-pressed") != "true":
            await b.click()
            await pg.wait_for_timeout(2500)
    await open_dash(pg, "saved")


async def s_producer(pg, a):
    await pg.locator("#q").click()
    await pg.locator("#q").type("Comtes Lafon", delay=40)
    await pg.wait_for_timeout(3500)
    await pg.locator("#results [data-producer], #results li").first.click()
    await pg.wait_for_timeout(8000)
    await pg.evaluate(owa.IDLE)
    await pg.wait_for_timeout(1500)


def note_seed():
    return [{"id": "n1", "at": "2026-10-20T18:10:00.000Z", "up": "2026-10-20T18:10:00.000Z",
             "title": "Chablis grand crus: soils and exposures",
             "body": "Seven climats on one hillside, right bank of the Serein.\nLes Clos is the largest.\nKimmeridgian marl: Upper Jurassic, small fossil oysters.",
             "tags": ["wset3", "burgundy"], "placeId": "fr-inao-a147", "place": "Chablis Grand Cru", "country": "FR", "lat": 47.822, "lon": 3.803},
            {"id": "n2", "at": "2026-10-19T17:00:00.000Z", "up": "2026-10-19T17:00:00.000Z",
             "title": "Corton: the only red grand cru of the Côte de Beaune", "body": "The other grands crus of the Côte de Beaune are white.",
             "tags": ["wset3", "burgundy"], "placeId": "fr-inao-a165", "place": "Corton", "country": "FR", "lat": 47.073, "lon": 4.863}]


SCENES = {
    "study-hub": ("Study tab: stats, review, the ten paths", "study", s_study_hub),
    "study-paths": ("The list of study paths", "study", s_study_paths),
    "study-path": ("Burgundy path: drills and lessons", "study", s_study_path),
    "study-lesson": ("A lesson with its place buttons", "study", s_study_lesson),
    "lesson-fly": ("The map after a place button in a lesson", "study", s_lesson_fly),
    "quiz-question": ("A lesson quiz question over the map", "study", s_quiz_question),
    "quiz-answered": ("The same question answered, place outlined", "study", s_quiz_answered),
    "map-quiz": ("Map quiz: find the place on the map", "study", s_map_quiz),
    "review-hub": ("Review box with cards due", "study", s_review_hub),
    "review-quiz": ("A review session", "study", s_review_quiz),
    "place": ("A place sheet (Chablis Grand Cru Les Clos)", None, s_place),
    "compare": ("Romanée-Conti and La Tâche at the same scale", None, s_compare),
    "notebook": ("Notebook with notes pinned to places", "notes", s_notebook),
    "saved": ("Saved places", None, s_saved),
    "producer": ("A producer and where its wines are made", None, s_producer),
}


async def run(a):
    from playwright.async_api import async_playwright
    atlas = owa.Atlas(a.repo)
    try:
        pair = owa.pair_runner(atlas.repo, a.libs)
    except Exception as e:  # no node or npm: the compare scene then lacks the same-scale picture
        print("api/pair not available:", e, file=sys.stderr)
        pair = None
    srv, base = owa.serve(atlas.web, pair)
    os.makedirs(a.out, exist_ok=True)
    names = a.scene or list(SCENES)
    try:
        async with async_playwright() as p:
            br = await owa.launch(p)
            for name in names:
                desc, seed, fn = SCENES[name]
                storage = {}
                if seed == "study":
                    storage["study"] = study_state(atlas)
                if seed == "notes":
                    storage["notes"] = note_seed()
                pg = await owa.atlas_page(br, base, a.libs, W, H, SCALE, mobile=True, storage=storage, supabase_stub=a.stub)
                errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                await pg.goto(f"{base}/index.html", wait_until="domcontentloaded")
                await owa.wait_atlas(pg, 2500)
                await fn(pg, atlas)
                out = os.path.join(a.out, name + ".png")
                await pg.screenshot(path=out)
                print(out, ("errors: " + "; ".join(errs)) if errs else "")
                await pg.close()
            await br.close()
    finally:
        srv.shutdown()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, help="checkout of main (has web/ and api/fonts)")
    ap.add_argument("--libs", required=True, help="folder with maplibre-gl and pmtiles (installed with npm if missing)")
    ap.add_argument("--out", default="shots")
    ap.add_argument("--scene", action="append", choices=list(SCENES))
    ap.add_argument("--stub", default=None, help="optional fake supabase-js for signed-in screens")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        for k, v in SCENES.items():
            print(f"{k:15} {v[0]}")
        return
    asyncio.run(run(a))


if __name__ == "__main__":
    main()
