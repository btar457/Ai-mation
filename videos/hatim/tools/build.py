import json, os, glob, subprocess, numpy as np, soundfile as sf, librosa, re
os.chdir('/root/hatim')
SR = 44100
import imageio_ffmpeg
FF = [imageio_ffmpeg.get_ffmpeg_exe()]
lines = {l['id']: l for l in json.load(open('lines.json'))}
# --- timeline ---
t = 0.0; scenes = []; placed = []
for n in range(1, 23):
    ids = sorted(k for k in lines if k.startswith(f'{n:02d}') and os.path.exists(f'aud/lines/{k}.wav'))
    start = t
    cur = t + (0.15 if n == 1 else 0.35)
    for k, i in zip(ids, range(99)):
        a, _ = librosa.load(f'aud/lines/{k}.wav', sr=SR)
        if i: cur += 0.3
        placed.append({'id': k, 'who': lines[k]['who'], 'text': lines[k]['text'], 'start': round(cur, 3), 'dur': round(len(a) / SR, 3)})
        cur += len(a) / SR
    end = cur + 0.35
    if not ids: end = start + 2.6          # silent beat (scene 20)
    if n == 21: end = cur + 1.5             # held silence after the reveal
    if n == 22: end = cur + 3.0             # "part two" card
    end = max(end, start + 2.4)
    scenes.append({'n': n, 'start': round(start, 3), 'dur': round(end - start, 3)})
    t = end
total = t
# --- clips: upscale, sharpen, retime to scene length ---
os.makedirs('/root/hstory/public/clips', exist_ok=True)
for s in scenes:
    src = f'vid/v{s["n"]:02d}.mp4'; dst = f'/root/hstory/public/clips/c{s["n"]:02d}.mp4'
    d = s['dur'] + 0.5
    if os.path.exists(src):
        src_d = 65 / 16
        k = max(1.0, min(d / src_d, 2.0))
        vf = (f"setpts={k:.4f}*PTS,minterpolate=fps=30:mi_mode=blend,scale=-2:1920:flags=lanczos,crop=1080:1920,"
              f"unsharp=5:5:0.9,tpad=stop_mode=clone:stop_duration={max(0, d - src_d * k) + 0.1:.2f}")
        cmd = FF + ['-y', '-loglevel', 'error', '-i', src, '-vf', vf, '-t', f'{d:.2f}', '-an', '-c:v', 'libx264', '-crf', '17', '-pix_fmt', 'yuv420p', dst]
    elif os.path.exists(f'vid/p{s["n"]:02d}.mp4'):
        k = max(1.0, d / 8.0)
        cmd = FF + ['-y', '-loglevel', 'error', '-i', f'vid/p{s["n"]:02d}.mp4', '-vf', f'setpts={k:.4f}*PTS,fps=30', '-t', f'{d:.2f}', '-an', '-c:v', 'libx264', '-crf', '17', '-pix_fmt', 'yuv420p', dst]
    else:
        img = f'img/scenes/s{s["n"]:02d}.png'
        cmd = FF + ['-y', '-loglevel', 'error', '-loop', '1', '-i', img, '-vf', 'scale=-2:1920:flags=lanczos,crop=1080:1920,fps=30', '-t', f'{d:.2f}', '-c:v', 'libx264', '-crf', '17', '-pix_fmt', 'yuv420p', dst]
    subprocess.run(cmd, check=True)
    s['clip'] = f'clips/c{s["n"]:02d}.mp4'
# --- audio mix ---
N = int((total + 0.5) * SR); mix = np.zeros(N); rng = np.random.default_rng(3)
def add(sig, at, g=1.0):
    i = int(at * SR); sig = sig[:N - i]; mix[i:i + len(sig)] += sig * g
for p in placed:
    a, _ = librosa.load(f'aud/lines/{p["id"]}.wav', sr=SR)
    a = a / (np.abs(a).max() + 1e-9) * 0.75
    add(a, p['start'])
tt = np.arange(N) / SR
def env(n, a, r):
    e = np.ones(n); a, r = int(a * SR), int(r * SR)
    e[:a] = np.linspace(0, 1, a); e[-r:] *= np.linspace(1, 0, r); return e
# music: low drone in D with slow swells + soft hijaz-flavoured plucks
drone = sum(np.sin(2 * np.pi * f * tt + 0.3 * np.sin(2 * np.pi * 0.07 * tt)) / (i + 1) for i, f in enumerate([73.42, 110.0, 146.83]))
drone *= 0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * tt) ** 2
mix += 0.05 * drone / np.abs(drone).max() * env(N, 2, 3)
scale = [293.66, 311.13, 369.99, 392.0, 440.0, 466.16, 523.25]
for i, at in enumerate(np.arange(1.0, total - 4, 1.6)):
    f = scale[int(rng.integers(0, len(scale)))]; L = int(1.4 * SR); x = np.arange(L) / SR
    pl = (np.sin(2 * np.pi * f * x) + 0.4 * np.sin(4 * np.pi * f * x) + 0.2 * np.sin(6 * np.pi * f * x)) * np.exp(-x * 3.2)
    add(pl, at, 0.022)
def noise_lp(n, a):
    x = rng.standard_normal(n); y = np.zeros(n); v = 0.0
    for i in range(n): v += a * (x[i] - v); y[i] = v
    return y / (np.abs(y).max() + 1e-9)
S = {s['n']: s for s in scenes}
def span(a, b): return S[a]['start'], S[b]['start'] + S[b]['dur']
# wind (desert scenes)
for a, b in [(4, 4), (7, 7), (12, 12), (16, 17)]:
    s0, s1 = span(a, b); n = int((s1 - s0) * SR)
    w = noise_lp(n, 0.02) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * np.arange(n) / SR)) * env(n, 0.8, 0.8)
    add(w, s0, 0.10)
# fire crackle (night camp scenes)
s0, s1 = span(5, 15); n = int((s1 - s0) * SR); fire = noise_lp(n, 0.05) * 0.25
for c in rng.uniform(0, s1 - s0, int((s1 - s0) * 6)):
    L = int(0.02 * SR); i = int(c * SR)
    if i + L < n: fire[i:i + L] += rng.standard_normal(L) * np.exp(-np.arange(L) / (0.004 * SR)) * rng.uniform(0.3, 1)
add(fire * env(n, 1, 1), s0, 0.05)
# dawn birds
s0, _ = span(16, 16)
for c in rng.uniform(0, 3.5, 7):
    L = int(0.12 * SR); x = np.arange(L) / SR; f = rng.uniform(2800, 4200)
    add(np.sin(2 * np.pi * (f + 900 * np.sin(2 * np.pi * 18 * x)) * x) * np.sin(np.pi * x / x[-1]), s0 + c, 0.05)
# reveal hit on "فرسك" + heartbeat in the held silence
hit = [p for p in placed if p['id'] == '21a']
if hit:
    x = np.arange(int(1.8 * SR)) / SR; f = 70 * np.exp(-x * 3) + 35
    add(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 2.2), hit[0]['start'], 0.6)
    s0 = S[21]['start'] + S[21]['dur'] - 1.5
    for k in range(4):
        for dt, g in [(0, 1), (0.22, 0.6)]:
            x = np.arange(int(0.25 * SR)) / SR
            add(np.sin(2 * np.pi * 55 * x) * np.exp(-x * 18), s0 + k * 0.85 + dt, 0.35 * g)
mix /= max(1.0, np.abs(mix).max() / 0.95)
sf.write('/root/hstory/public/mix.wav', mix.astype(np.float32), SR)
# --- captions: 2-3 word chunks timed by character share ---
caps = []
for p in placed:
    words = p['text'].split(); chunks = []; i = 0
    while i < len(words):
        k = 3 if len(words) - i > 4 else (len(words) - i if len(words) - i <= 3 else 2)
        chunks.append(' '.join(words[i:i + k])); i += k
    tot = sum(len(c) for c in chunks); cur = p['start']
    for c in chunks:
        d = p['dur'] * len(c) / tot; caps.append({'t': re.sub(r'\.\.\.|…', '…', c), 's': round(cur, 3), 'e': round(cur + d, 3), 'who': p['who']}); cur += d
json.dump({'total': round(total + 0.3, 2), 'scenes': scenes, 'lines': placed, 'caps': caps}, open('/root/hstory/src/timeline.json', 'w'), ensure_ascii=False, indent=0)
print('total', round(total, 2), 's;', len(placed), 'lines')
