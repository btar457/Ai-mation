"""يجمع مقاطع الصوت بالترتيب ويحسب توقيت كل كلمة (للترجمة) وكل شطر (لأبيات القصيدة) → voice/voice.wav و timeline.json"""
import json, os, re, subprocess, sys, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lines import PART_RM, PART_I, POEM
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

rm, im, cf, en = load("voice/rm.wav"), load("voice/imam.wav"), load("voice/caliph_fx.wav"), load("voice/imam_Enceladus.wav")  # الإمام: Enceladus، أداء رثائي  # المتوكل: صوت Alnilam أفخم مع صدى قاعة
S = lambda x, a, b: x[int(a * SR):int(b * SR)]
R_TEXT = [t for _, t in PART_RM]
I_TEXT = [t for _, t in PART_I]
V = [v.replace(" ... ", "… ") for v in POEM]
# (المصدر، من، إلى، النص، المتكلم، فجوة بعده)
PLAN = [
 ("en", 41.30, 45.60, "أين الأسِرّةُ والتيجانُ والحُلَلُ؟", "I", 0.55, "hook"),
 ("rm", 0.30, 7.83, R_TEXT[0], "R", 0.7, "intro"),
 ("rm", 7.83, 57.78, " ".join(R_TEXT[1:8]), "R", 0.3, "story"),
 ("en", 0.00, 6.60, I_TEXT[0], "I", 0.3, "refuse"),
 ("rm", 57.78, 59.95, R_TEXT[8], "R", 0.1, "ask_r"),
 ("cf", 0.28, 4.85, R_TEXT[9], "M", 0.3, "ask"),
 ("en", 7.65, 11.90, I_TEXT[1], "I", 0.25, "little"),
 ("cf", 4.97, 8.44, R_TEXT[10], "M", 0.2, "insist"),
 ("rm", 63.43, 64.60, R_TEXT[11], "R", 0.45, "insist_r"),
] + [("en", a, b, V[k], "I", 0.5 if k < 5 else 0.9, f"v{k+1}") for k, (a, b) in enumerate(
    [(12.90, 23.10), (24.60, 34.30), (35.80, 45.80), (47.40, 56.80), (58.20, 67.90), (69.40, 78.60)])] + [
 ("rm", 64.64, 97.33, " ".join(R_TEXT[12:]), "R", 1.6, "end"),
]
out, t, segs, words = [], 0.0, [], []
for src, a, b, text, who, gap, tag in PLAN:
    x = S({"rm": rm, "im": im, "cf": cf, "en": en}[src], a, b)
    if src == "rm": x = tempo(x, RTEMPO)
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
