"""The artifact host serves text, not arbitrary binary: store each binary file as base64 text next to it."""
import base64, os, sys
here = os.path.dirname(os.path.abspath(__file__))
n = 0
for d in ("data", "fonts"):
    for root, _, files in os.walk(os.path.join(here, d)):
        for f in files:
            if f.endswith((".pmtiles", ".pbf")):
                p = os.path.join(root, f)
                with open(p, "rb") as src, open(p + ".txt", "w") as out:
                    out.write(base64.b64encode(src.read()).decode())
                n += 1
print("encoded", n)
