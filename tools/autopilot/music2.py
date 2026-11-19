"""Original ambient score of any length for the deep dives: slow plucked melody over warm pads, long reverb.
usage: music2.py preset out.wav seconds [seed]
Presets pick the scale and chords: japan (in scale on D), warm (D major), dusk (E minor), alpine (G lydian), south (A dorian).
Since 20 Nov 2026 (asked by Stefano) there is a second style, an original harpsichord waltz with a warm vintage feel
(own chords and melody, not a copy of any song). It is now the main style: every seed that is not a multiple of 3 gives the
waltz, in a key chosen by the preset; seeds that are multiples of 3 give the older ambient score. Preset "harpsi" is always
the waltz. Set OWA_MUSIC=ambient or OWA_MUSIC=harpsi to force one style. Atlas videos only: runs started by wc.py stay ambient.
Everything is synthesised here (no samples), so the music is original and free to publish."""
import os, sys
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt
from scipy.io import wavfile

SR = 44100
preset, out, DUR = sys.argv[1], sys.argv[2], float(sys.argv[3])
seed = int(sys.argv[4]) if len(sys.argv) > 4 else 7
rng = np.random.default_rng(seed)
N = int(SR * DUR)
t = np.arange(N) / SR
hz = lambda n: 440.0 * 2 ** ((n - 69) / 12)

PRESETS = {
    # chords (midi), melody scale (midi), seconds per chord, pluck decay (s)
    "japan": ([[38, 45, 50, 55, 57, 62], [43, 50, 55, 58, 62, 67], [39, 46, 51, 55, 58, 62], [45, 50, 57, 62, 63, 69]],
              [62, 63, 67, 69, 70, 74, 75, 79, 81], 6.0, 1.1),
    "warm": ([[50, 57, 62, 66, 69, 73], [47, 54, 62, 66, 69, 74], [43, 50, 59, 62, 66, 71], [45, 52, 57, 62, 64, 69]],
             [66, 69, 71, 73, 74, 76, 78, 81], 6.0, 1.6),
    "dusk": ([[40, 52, 55, 59, 62, 66], [36, 48, 55, 59, 64, 67], [43, 50, 55, 59, 62, 67], [38, 50, 54, 57, 62, 66]],
             [64, 66, 67, 69, 71, 74, 76, 78, 79], 6.0, 1.6),
    "alpine": ([[43, 50, 55, 59, 62, 69], [45, 52, 57, 61, 64, 69], [40, 47, 55, 59, 64, 66], [48, 55, 60, 64, 67, 71]],
               [67, 69, 71, 73, 74, 76, 78, 79, 81], 6.0, 1.4),
    "south": ([[45, 52, 57, 60, 64, 66], [43, 50, 55, 59, 62, 67], [41, 48, 53, 57, 60, 64], [40, 47, 52, 56, 59, 64]],
              [64, 66, 67, 69, 71, 72, 74, 76], 6.0, 1.5),
}
def env(start, length, a, r):
    e = np.zeros(N); i0 = int(max(0, start) * SR); i1 = min(N, int((start + length) * SR))
    if i0 >= N or i1 <= i0: return e
    seg = np.arange(i1 - i0) / SR + max(0, -start)
    att = np.clip(seg / a, 0, 1); rel = np.clip((length - seg) / r, 0, 1)
    e[i0:i1] = np.sin(att * np.pi / 2) ** 2 * np.sin(rel * np.pi / 2) ** 2
    return e


def harpsi():
    """Original harpsichord waltz: plucked arpeggios in 3/4, a slow tune on top, soft bass and organ underneath."""
    beat = float(rng.choice([0.33, 0.345, 0.36])); bar = 3 * beat
    # (bass, chord tones) in D minor; two bars per chord
    prog = [(38, [62, 65, 69]), (34, [62, 65, 70]), (31, [62, 67, 70]), (33, [61, 64, 69]),
            (38, [62, 65, 69]), (41, [60, 65, 69]), (36, [60, 64, 67]), (33, [61, 64, 67])]
    rot = int(rng.integers(0, 2)) * 4
    prog = prog[rot:] + prog[:rot]
    shapes = [[0, 1, 2, 1, 2, 1], [0, 2, 1, 2, 0, 1], [0, 1, 2, 2, 1, 0]]
    L = np.zeros(N); R = np.zeros(N); low = np.zeros(N)
    def pluck(st, n, vel, pan, dec=0.55):
        i0 = int(st * SR); ln = min(N - i0, int(2.2 * SR))
        if i0 < 0 or ln <= 0: return
        s = np.arange(ln) / SR; f = hz(n + TR); v = np.zeros(ln)
        for h in range(1, 15):
            if f * h > 9000: break
            v += (1.0 / h ** 0.8) * np.sin(2 * np.pi * f * h * s + 0.3 * h) * np.exp(-s * (1 / dec + 0.55 * h))
        v += 0.22 * np.sin(2 * np.pi * 2 * f * s) * np.exp(-s / (dec * 0.6))  # quiet octave stop
        click = rng.standard_normal(min(ln, 220)) * np.exp(-np.arange(min(ln, 220)) / 40.0) * 0.25
        v[:len(click)] += click
        v *= np.minimum(1, s / 0.0015) * vel
        L[i0:i0 + ln] += v * (1 - pan); R[i0:i0 + ln] += v * pan
    nb = int(DUR / bar) + 1
    mel_scale = [62, 64, 65, 67, 69, 70, 72, 74, 76, 77, 79, 81]
    idx = 6
    for b in range(nb):
        bass, tones = prog[(b // 2) % len(prog)]
        t0 = 0.12 + b * bar
        sh = shapes[int(rng.integers(0, len(shapes)))] if b % 2 else shapes[0]
        for e in range(6):
            st = t0 + e * beat / 2 + float(rng.normal(0, 0.004))
            if e == 0:
                pluck(st, bass + 12, 0.34, 0.42, 0.7)
                i0 = int(st * SR); ln = min(N - i0, int(bar * SR))
                if ln > 0:
                    s = np.arange(ln) / SR
                    low[i0:i0 + ln] += np.sin(2 * np.pi * hz(bass + TR) * s) * np.minimum(1, s / 0.02) * np.exp(-s / 0.9) * 0.3
            else:
                pluck(st, tones[sh[e]], 0.2 if e % 2 else 0.24, 0.5 + 0.18 * (sh[e] - 1), 0.45)
        # tune: one to three notes a bar, landing on a chord tone on the downbeat
        if t0 < DUR - 2.5 and b >= 1:
            on = [x for x in range(len(mel_scale)) if (mel_scale[x] - tones[0]) % 12 in {(q - tones[0]) % 12 for q in tones}]
            near = min(on, key=lambda x: abs(x - idx) + 0.3 * abs(x - 7))
            idx = near; adj = 1 if any((q % 12) == 1 for q in tones) and mel_scale[idx] % 12 == 0 else 0
            pluck(t0, mel_scale[idx] + 12 + adj, 0.3, 0.6, 0.9)
            kind = int(rng.integers(0, 4))
            if kind >= 1:
                idx = int(np.clip(idx + rng.choice([-1, 1, 2, -2]), 2, len(mel_scale) - 2))
                n2 = mel_scale[idx] + 12
                if n2 % 12 == 0 and any((q % 12) == 1 for q in tones): n2 += 1
                pluck(t0 + (2 if kind == 1 else 1) * beat, n2, 0.24, 0.62, 0.8)
            if kind == 3:
                idx = int(np.clip(idx + rng.choice([-1, 1]), 2, len(mel_scale) - 2))
                n3 = mel_scale[idx] + 12
                if n3 % 12 == 0 and any((q % 12) == 1 for q in tones): n3 += 1
                pluck(t0 + 2 * beat, n3, 0.22, 0.64, 0.8)
    # soft organ bed, two bars per chord
    bed = np.zeros(N)
    for c in range(nb // 2 + 1):
        bass, tones = prog[c % len(prog)]
        e = env(0.12 + c * 2 * bar - 0.1, 2 * bar + 0.2, 0.25, 0.35)
        for n in tones:
            f = hz(n - 12 + TR)
            bed += (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)) * e * 0.035
    bed = sosfilt(butter(2, 1200, "low", fs=SR, output="sos"), bed)
    dry = np.stack([L, R], axis=1)
    dry = sosfilt(butter(2, 7000, "low", fs=SR, output="sos"), dry, axis=0)  # take the edge off, vintage tape feel
    dry += (bed + low)[:, None]
    Lr = int(1.4 * SR); s = np.arange(Lr) / SR
    ir = [sosfilt(butter(1, 4200, "low", fs=SR, output="sos"), rng.standard_normal(Lr) * np.exp(-s / 0.35)) for _ in range(2)]
    wet = np.stack([fftconvolve(dry[:, c], ir[c])[:N] for c in range(2)], axis=1)
    wet /= np.max(np.abs(wet)) + 1e-9
    mix = 0.8 * dry / (np.max(np.abs(dry)) + 1e-9) + 0.22 * wet
    mix = np.tanh(mix * 1.6) / np.tanh(1.6)
    mix *= (np.clip(t / 0.25, 0, 1) * np.clip((DUR - t) / 2.5, 0, 1))[:, None]
    mix = mix / np.max(np.abs(mix)) * 0.84
    wavfile.write(out, SR, (mix * 32767).astype(np.int16))
    print("wrote", out, DUR, "s, harpsi waltz, beat", beat)

TR = {"harpsi": 0, "japan": 0, "warm": 2, "dusk": -3, "alpine": 5, "south": -2}.get(preset, 0)
FORCE = os.environ.get("OWA_MUSIC", "")
if not FORCE:
    # the waltz is for the atlas' own videos; renders started by Winecore's wc.py keep the ambient score
    try:
        if "wc.py" in open(f"/proc/{os.getppid()}/cmdline", "rb").read().decode("utf-8", "ignore"): FORCE = "ambient"
    except OSError: pass
if FORCE != "ambient" and (preset == "harpsi" or FORCE == "harpsi" or seed % 3 != 0):
    harpsi(); sys.exit(0)
if preset == "harpsi": preset = "warm"
chords, scale, CH, DEC = PRESETS[preset]

pad = np.zeros((N, 2)); organ = np.zeros(N)
k = 0
while k * CH - 0.8 < DUR:
    ch = chords[k % len(chords)]
    e = env(k * CH - 0.8, CH + 1.6, 2.2, 2.4)
    for j, n in enumerate(ch[1:]):
        f = hz(n)
        for side, det in ((0, -0.13), (1, 0.13)):
            ph = rng.uniform(0, 2 * np.pi)
            v = np.sin(2 * np.pi * f * (1 + det / 100) * t + ph) + 0.28 * np.sin(2 * np.pi * 2 * f * t + ph) + 0.1 * np.sin(2 * np.pi * 3 * f * t)
            pad[:, side] += v * e * (0.06 if j < 2 else 0.045)
    fb = hz(ch[0])
    organ += (np.sin(2 * np.pi * fb * t) + 0.5 * np.sin(2 * np.pi * 2 * fb * t) + 0.25 * np.sin(2 * np.pi * 3 * fb * t)) * e * 0.11
    k += 1
pad = sosfilt(butter(2, 1600, "low", fs=SR, output="sos"), pad, axis=0)
pad *= (0.85 + 0.15 * np.sin(2 * np.pi * t / 9.0))[:, None]

# melody: a slow walk through the scale, phrases of 4 to 6 notes with breaths in between
mel, tt, idx = [], 0.9, len(scale) // 2
while tt < DUR - 3.0:
    for _ in range(int(rng.integers(4, 7))):
        idx = int(np.clip(idx + rng.choice([-2, -1, -1, 1, 1, 2, 0]), 0, len(scale) - 1))
        mel.append((tt, scale[idx], float(rng.uniform(0.38, 0.58))))
        tt += float(rng.choice([0.9, 1.2, 1.4, 1.7]))
        if tt >= DUR - 3.0: break
    tt += float(rng.uniform(1.6, 2.8))

piano = np.zeros((N, 2))
for (st, n, vel) in mel:
    f = hz(n); i0 = int(st * SR); L = min(N - i0, int(5.0 * SR))
    if L <= 0: continue
    s = np.arange(L) / SR
    v = np.zeros(L)
    for h, (amp, dec) in enumerate([(1, DEC), (.5, DEC * .7), (.28, DEC * .5), (.15, DEC * .35), (.08, DEC * .25)], start=1):
        v += amp * np.sin(2 * np.pi * f * h * (1 + 0.0004 * h * h) * s) * np.exp(-s / dec)
    v *= np.minimum(1, s / 0.003) * vel * 0.16
    pan = 0.5 + 0.25 * np.sin(n)
    piano[i0:i0 + L, 0] += v * (1 - pan) * 1.4
    piano[i0:i0 + L, 1] += v * pan * 1.4
    if vel >= .5:
        piano[i0:i0 + L, :] += (0.3 * np.sin(np.pi * f * s) * np.exp(-s / 2.0) * vel * 0.16)[:, None]

dry = pad + piano + organ[:, None]
L = int(3.2 * SR); s = np.arange(L) / SR
ir = [sosfilt(butter(1, 5000, "low", fs=SR, output="sos"), rng.standard_normal(L) * np.exp(-s / 0.9)) for _ in range(2)]
wet = np.stack([fftconvolve(dry[:, c], ir[c])[:N] for c in range(2)], axis=1)
wet /= np.max(np.abs(wet)) + 1e-9
mix = 0.55 * dry / (np.max(np.abs(dry)) + 1e-9) + 0.6 * wet
shape = np.clip(t / 1.5, 0, 1) * np.clip((DUR - t) / 3.0, 0, 1) * (0.9 + 0.1 * np.sin(np.pi * t / DUR))
mix *= shape[:, None]
mix = mix / np.max(np.abs(mix)) * 0.84
wavfile.write(out, SR, (mix * 32767).astype(np.int16))
print("wrote", out, DUR, "s,", len(mel), "notes")
