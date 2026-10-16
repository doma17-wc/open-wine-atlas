"""Apply pipeline/notes/corrections.json to the merged place facts.

The open data is right almost everywhere, but a few appellations overlap or are cut short in the source
(Chambertin includes Clos de Bèze, Charmes and Mazoyères share one area, part of Hengst is missing).
Each correction sets the official figure and keeps an `area_note` that says what the source shows.

Run on its own to patch the published files in web/data:  python pipeline/corrections.py
"""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WEB = os.path.join(ROOT, "web", "data")


def load():
    return json.load(open(os.path.join(HERE, "notes", "corrections.json"), encoding="utf-8"))["corrections"]


def apply(merged):
    """merged: {place id: facts}. Changes it in place and returns the ids it touched."""
    done = []
    for c in load():
        d = merged.get(c["id"])
        if d is None:
            continue
        d.update(c.get("set", {}))
        if c.get("area_note"):
            d["area_note"] = c["area_note"]
        done.append(c["id"])
    return done


def main():
    for path in sorted(glob.glob(os.path.join(WEB, "details-*.json"))):
        d = json.load(open(path, encoding="utf-8"))
        done = apply(d)
        if done:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
            print(os.path.basename(path), done)


if __name__ == "__main__":
    main()
