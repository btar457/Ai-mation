"""يجمع مقاطع الصوت بالترتيب ويحسب توقيت كل كلمة (للترجمة) وكل شطر (لأبيات القصيدة) → voice/voice.wav و timeline.json"""
import json, os, re, subprocess, sys, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lines import PART_RG, PART_IB
from faster_whisper import WhisperModel
import numpy as np
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SR = 48000
RTEMPO = 1.05  # تسريع خفيف للراوي والمتوكل فقط

def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).copy()

def tempo(x, t):
    if t == 1: return x
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", f"atempo={t}",
                        "-f", "f32le", "-"], input=x.tobytes(), capture_output=True).stdout
    return np.frombuffer(p, np.float32).copy()

def norm(w):
    w = re.sub(r"[ً-ْٰـ]", "", w)
    w = re.sub(r"[^ء-ي]", "", w)
    return w.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه").replace("ى", "ي")

model = WhisperModel("small", device="cpu", compute_type="int8")
def words_of(x):
    segs, _ = model.transcribe(x[::3].astype(np.float32), language="ar", word_timestamps=True)  # 16 kHz
    return [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]

def align(script_text, wtimes, offset):
    """يطابق كلمات النص (بالتشكيل) مع كلمات Whisper ويعيد [(كلمة, بداية, نهاية)] بزمن مطلق."""
    sw = script_text.replace("…", " ").split()
    a = [norm(w) for w in sw]; b = [norm(w[0]) for w in wtimes]
    out = [None] * len(sw)
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag in ("equal", "replace"):
            for k in range(i2 - i1):
                j = j1 + min(k * max(j2 - j1, 1) // max(i2 - i1, 1), j2 - j1 - 1) if j2 > j1 else None
                if j is not None: out[i1 + k] = (wtimes[j][1], wtimes[j][2])
    # استيفاء ما لم يُطابق
    known = [i for i, v in enumerate(out) if v]
    for i, v in enumerate(out):
        if v: continue
        prev = max([k for k in known if k < i], default=None); nxt = min([k for k in known if k > i], default=None)
        s = out[prev][1] if prev is not None else (wtimes[0][1] if wtimes else 0)
        e = out[nxt][0] if nxt is not None else (wtimes[-1][2] if wtimes else s + 0.4)
        out[i] = (s, max(s + 0.15, e))
    return [(w, round(s + offset, 3), round(e + offset, 3)) for w, (s, e) in zip(sw, out)]

rg, ib = load("voice/rg.wav"), load("voice/ib.wav")
S = lambda x, a, b: x[int(a * SR):int(b * SR)]
R = [t for _, t in PART_RG]; I = [t for _, t in PART_IB]
PLAN = [
 ("rg", 0.00, 9.55, R[0], "R", 0.55, "hook"),
 ("rg", 9.55, 18.55, R[1], "R", 0.25, "intro"),
 ("rg", 18.55, 25.35, R[2], "R", 0.3, "pass"),
 ("ib", 0.00, 8.40, I[0], "I", 0.2, "ask"),
 ("rg", 25.40, 26.36, R[3], "G", 0.35, "girl"),
 ("ib", 8.45, 15.20, I[1], "I", 0.4, "answer"),
 ("rg", 26.36, 34.80, R[4], "R", 0.15, "inside"),
 ("rg", 34.80, 43.50, R[5], "R", 0.2, "run"),
 ("ib", 15.35, 19.53, I[2], "B", 0.4, "bishr"),
 ("rg", 43.50, 53.20, R[6], "R", 0.4, "repent"),
 ("rg", 53.20, 60.37, R[7], "R", 1.5, "end"),
]
out, t, segs, words = [], 0.0, [], []
for src, a, b, text, who, gap, tag in PLAN:
    x = S({"rg": rg, "ib": ib}[src], a, b)
    if src == "rg" and who != "G": x = tempo(x, RTEMPO)
    fade = int(0.015 * SR); x[:fade] *= np.linspace(0, 1, fade); x[-fade:] *= np.linspace(1, 0, fade)
    w = align(text, words_of(x), t)
    segs.append({"tag": tag, "who": who, "start": round(t, 3), "end": round(t + len(x) / SR, 3), "text": text})
    words.append({"tag": tag, "who": who, "words": w})
    out += [x, np.zeros(int(gap * SR), np.float32)]
    t += len(x) / SR + gap
    print(f"{tag:7s} {segs[-1]['start']:7.2f} → {segs[-1]['end']:7.2f}", flush=True)
y = np.concatenate(out)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af",
                "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", str(SR), "voice/voice.wav"], input=y.tobytes(), check=True)
json.dump({"duration": round(t, 3), "segments": segs, "words": words}, open("timeline.json", "w"), ensure_ascii=False, indent=1)
print("TOTAL", round(t, 2))
