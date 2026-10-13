"""Original ambient score: slow piano over warm pads and a low organ, long reverb. usage: music.py preset out.wav [seconds]"""
import sys
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt
from scipy.io import wavfile

SR = 44100
preset, out = sys.argv[1], sys.argv[2]
DUR = float(sys.argv[3]) if len(sys.argv) > 3 else 24.0
rng = np.random.default_rng(7 if preset == "napa" else 11)
N = int(SR * DUR)
t = np.arange(N) / SR

def hz(n):  # midi -> Hz
    return 440.0 * 2 ** ((n - 69) / 12)

# chords as midi notes, one per 6 s; melody: (time, midi, velocity)
if preset == "napa":   # D major, warm and open
    chords = [[50, 57, 62, 66, 69, 73], [47, 54, 62, 66, 69, 74], [43, 50, 59, 62, 66, 71], [45, 52, 57, 62, 64, 69]]
    mel = [(0.8, 78, .55), (2.3, 76, .45), (3.6, 73, .5), (6.4, 74, .55), (7.9, 73, .4), (9.1, 71, .45), (10.4, 69, .5),
           (12.6, 71, .55), (14.0, 74, .5), (15.2, 78, .55), (16.6, 76, .45), (18.8, 73, .5), (20.2, 74, .45), (21.6, 69, .4)]
else:                  # E minor to G, a little more yearning
    chords = [[40, 52, 55, 59, 62, 66], [36, 48, 55, 59, 64, 67], [43, 50, 55, 59, 62, 67], [38, 50, 54, 57, 62, 66]]
    mel = [(0.8, 71, .5), (2.2, 74, .45), (3.7, 76, .55), (6.3, 79, .55), (7.7, 76, .45), (9.0, 74, .45), (10.5, 71, .5),
           (12.5, 74, .55), (13.9, 79, .5), (15.1, 78, .55), (16.6, 74, .45), (18.7, 76, .5), (20.1, 71, .45), (21.6, 69, .4)]

def env(start, length, a, r):
    e = np.zeros(N); i0 = int(start * SR); i1 = min(N, int((start + length) * SR))
    if i0 >= N: return e
    seg = np.arange(i1 - i0) / SR
    att = np.clip(seg / a, 0, 1); rel = np.clip((length - seg) / r, 0, 1)
    e[i0:i1] = np.sin(att * np.pi / 2) ** 2 * np.sin(rel * np.pi / 2) ** 2
    return e

pad = np.zeros((N, 2)); organ = np.zeros(N)
for k, ch in enumerate(chords):
    st = k * 6.0 - 0.8; ln = 7.6
    e = env(max(0, st), ln if st >= 0 else ln + st, 2.2, 2.4)
    for j, n in enumerate(ch[1:]):
        f = hz(n)
        for side, det in ((0, -0.13), (1, 0.13)):
            ph = rng.uniform(0, 2 * np.pi)
            v = np.sin(2 * np.pi * f * (1 + det / 100) * t + ph) + 0.28 * np.sin(2 * np.pi * 2 * f * t + ph) + 0.1 * np.sin(2 * np.pi * 3 * f * t)
            pad[:, side] += v * e * (0.06 if j < 2 else 0.045)
    fb = hz(ch[0])
    organ += (np.sin(2 * np.pi * fb * t) + 0.5 * np.sin(2 * np.pi * 2 * fb * t) + 0.25 * np.sin(2 * np.pi * 3 * fb * t)) * e * 0.11

# slow breathing filter on the pad
sos = butter(2, 1600, "low", fs=SR, output="sos")
pad = sosfilt(sos, pad, axis=0)
pad *= (0.85 + 0.15 * np.sin(2 * np.pi * t / 9.0))[:, None]

piano = np.zeros((N, 2))
for (st, n, vel) in mel:
    f = hz(n); i0 = int(st * SR); L = min(N - i0, int(5.5 * SR))
    if L <= 0: continue
    s = np.arange(L) / SR
    v = np.zeros(L)
    for h, (amp, dec) in enumerate([(1, 1.6), (.45, 1.1), (.22, .8), (.12, .6), (.06, .45)], start=1):
        fh = f * h * (1 + 0.0004 * h * h)
        v += amp * np.sin(2 * np.pi * fh * s) * np.exp(-s / dec)
    v *= np.minimum(1, s / 0.004) * vel * 0.16
    pan = 0.5 + 0.25 * np.sin(n)
    piano[i0:i0 + L, 0] += v * (1 - pan) * 2 * 0.7
    piano[i0:i0 + L, 1] += v * pan * 2 * 0.7
    # soft octave below on strong notes
    if vel >= .55:
        v2 = 0.35 * np.sin(2 * np.pi * f / 2 * s) * np.exp(-s / 2.0) * vel * 0.16
        piano[i0:i0 + L, :] += v2[:, None]

dry = pad + piano + organ[:, None]

# reverb: two decorrelated decaying-noise impulse responses
L = int(3.2 * SR); s = np.arange(L) / SR
ir = [rng.standard_normal(L) * np.exp(-s / 0.9) for _ in range(2)]
ir = [sosfilt(butter(1, 5000, "low", fs=SR, output="sos"), x) for x in ir]
wet = np.stack([fftconvolve(dry[:, c], ir[c])[:N] for c in range(2)], axis=1)
wet /= np.max(np.abs(wet)) + 1e-9
mix = 0.55 * dry / (np.max(np.abs(dry)) + 1e-9) + 0.6 * wet

# overall shape: fade in, a gentle lift in the middle, fade out at the end
shape = np.clip(t / 1.5, 0, 1) * np.clip((DUR - t) / 2.5, 0, 1) * (0.9 + 0.1 * np.sin(np.pi * t / DUR))
mix *= shape[:, None]
mix = mix / np.max(np.abs(mix)) * 0.84
wavfile.write(out, SR, (mix * 32767).astype(np.int16))
print("wrote", out, DUR, "s")
