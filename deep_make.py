"""Builds one deep dive video from its spec: map pass, overlay pass, music, interpolation, cross-fades, final mp4 and cover.
usage: python3 deep_make.py eps/<spec>.json [--interp mci|blend]
Output: work/<slug>/<slug>.mp4 and work/<slug>/cover.jpg. Re-running skips finished steps (delete a folder to redo it)."""
import json, os, subprocess, sys, glob, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
spec_path = os.path.abspath(sys.argv[1])
interp = sys.argv[sys.argv.index("--interp") + 1] if "--interp" in sys.argv else "mci"
spec = json.load(open(spec_path))
slug = spec["slug"]
W = os.path.join(HERE, "work", slug)
os.makedirs(W, exist_ok=True)
FPS = 30
X = spec.get("xfade", 0.5)
DUR = spec["duration"]

def run(cmd, **kw):
    print("+", " ".join(cmd) if isinstance(cmd, list) else cmd, flush=True)
    subprocess.run(cmd, check=True, cwd=HERE, **kw)

# 1. map frames
map_dir = os.path.join(W, "map")
run(["node", "deep_map.mjs", spec_path, map_dir])

# 2. overlay frames
ovl_dir = os.path.join(W, "ovl")
if not os.path.exists(os.path.join(ovl_dir, "%05d.png" % (round(DUR * FPS) - 1))):
    run(["node", "deep_ovl.mjs", spec_path, ovl_dir])

# 3. music
wav = os.path.join(W, "music.wav")
if not os.path.exists(wav):
    preset, seed = spec.get("music", ["warm", 7])
    run(["python3", "music2.py", preset, wav, str(DUR), str(seed)])

# 4. each shot to 30 fps, cut to its exact length
vf_interp = {"mci": "minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
             "blend": "framerate=fps=30:interp_start=0:interp_end=255:scene=100"}[interp]
clips = []
for i, shot in enumerate(spec["shots"]):
    sf = shot.get("fps", spec.get("fpsMap", 10))
    clip = os.path.join(W, "shot%02d.mp4" % i)
    clips.append((clip, shot["dur"]))
    if os.path.exists(clip):
        continue
    src = os.path.join(map_dir, "shot%02d" % i, "%05d.jpg")
    run(["ffmpeg", "-v", "error", "-y", "-framerate", str(sf), "-i", src, "-vf",
         f"{vf_interp},trim=duration={shot['dur']},setpts=PTS-STARTPTS,format=yuv420p",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", clip])

# 5. cross-fade the shots, lay the overlay on top, add the music
inputs, fc, last, acc = [], [], "0:v", clips[0][1]
for c, _ in clips:
    inputs += ["-i", c]
for k in range(1, len(clips)):
    off = acc - X
    fc.append(f"[{last}][{k}:v]xfade=transition=fade:duration={X}:offset={off:.3f}[x{k}]")
    last = f"x{k}"; acc = acc - X + clips[k][1]
pad = max(0.0, DUR - acc)
fc.append(f"[{last}]tpad=stop_mode=add:stop_duration={pad:.3f}:color=0x0b0b0d,trim=duration={DUR}[base]")
n = len(clips)
inputs += ["-framerate", "30", "-i", os.path.join(ovl_dir, "%05d.png"), "-i", wav]
fc.append(f"[{n}:v]format=rgba[ov];[base][ov]overlay=0:0:format=auto,format=yuv420p[v]")
final = os.path.join(W, slug + ".mp4")
run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[v]", "-map", f"{n + 1}:a",
     "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "7M", "-bufsize", "14M", "-x264-params", "aq-mode=3", "-pix_fmt", "yuv420p", "-r", "30",
     "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-t", str(DUR), "-movflags", "+faststart", final])

# 6. cover: a frame of the chosen shot behind the series title
cov = spec.get("cover")
if cov:
    shot_dir = os.path.join(map_dir, "shot%02d" % cov["shot"])
    frames = sorted(glob.glob(os.path.join(shot_dir, "*.jpg")))
    bg = frames[min(len(frames) - 1, int(len(frames) * cov.get("at", 0.6)))]
    run(["node", "deep_cover.mjs", bg, os.path.join(W, "cover.jpg"), json.dumps(cov)])
print("done", final)
