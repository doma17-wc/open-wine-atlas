import sys, json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
from kokoro_onnx.tokenizer import Tokenizer
# usage: tts.py lines.json outdir  ; lines.json: {"voice":..,"lang":..,"speed":1.0,"lines":[{"text":..,"ph":optional, "fix":{"word":"ipa"}}]}
cfg = json.load(open(sys.argv[1])); out = sys.argv[2]
tok = Tokenizer(); k = Kokoro("/home/claude/tts/kokoro-v1.0.onnx", "/home/claude/tts/voices-v1.0.bin")
res = []
for i, L in enumerate(cfg["lines"]):
    ph = L.get("ph")
    if not ph:
        ph = tok.phonemize(L["text"], cfg["lang"])
        for a, b in (L.get("fix") or {}).items():
            ph = ph.replace(a, b)
    a, sr = k.create(ph, voice=cfg["voice"], speed=L.get("speed", cfg.get("speed", 1.0)), lang=cfg["lang"], is_phonemes=True)
    a = np.asarray(a, dtype=np.float32)
    # trim silence
    nz = np.where(np.abs(a) > 0.01)[0]
    if len(nz): a = a[max(0, nz[0] - 200): nz[-1] + 1200]
    sf.write(f"{out}/l{i}.wav", a, sr)
    res.append({"i": i, "dur": round(len(a) / sr, 2), "ph": ph, "text": L["text"]})
print(json.dumps(res, ensure_ascii=False, indent=0))
