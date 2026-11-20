import sys, json, subprocess, numpy as np, soundfile as sf
from scipy.signal import resample_poly, butter, sosfilt
# usage: mix.py video.mp4 linesdir starts.json out.mp4   ; starts: [t0, t1, ...] seconds per line
vid, ld, starts, outp = sys.argv[1], sys.argv[2], json.load(open(sys.argv[3])), sys.argv[4]
SR = 48000
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-vn", "-ac", "2", "-ar", str(SR), f"{ld}/music.wav"], check=True)
mus, _ = sf.read(f"{ld}/music.wav"); n = len(mus)
voice = np.zeros(n); mask = np.zeros(n)
for i, t in enumerate(starts):
    a, sr = sf.read(f"{ld}/l{i}.wav")
    if a.ndim > 1: a = a.mean(1)
    a = resample_poly(a, SR, sr) if sr != SR else a
    s = int(t * SR); e = min(n, s + len(a))
    voice[s:e] += a[:e - s]; mask[s:e] = 1
sos = butter(2, 80, "highpass", fs=SR, output="sos"); voice = sosfilt(sos, voice)
# smooth envelope 0.25 s
w = int(0.25 * SR); ker = np.ones(w) / w
env = np.convolve(mask, ker, mode="same"); env = np.clip(env * 1.0, 0, 1)
gain = 10 ** (-6 * env / 20)  # duck about 6 dB
m = mus * gain[:, None] * 0.55
v = voice / (np.abs(voice).max() + 1e-9) * 0.9
mix = m + v[:, None]
mix = mix / (np.abs(mix).max() + 1e-9) * 0.95
sf.write(f"{ld}/mix.wav", mix, SR)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", f"{ld}/mix.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", outp], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", outp, "-filter_complex", "showwavespic=s=1600x300:split_channels=0", "-frames:v", "1", f"{ld}/wave.png"], check=True)
print("ok")
