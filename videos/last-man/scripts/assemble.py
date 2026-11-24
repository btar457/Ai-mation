"""يقطع voice/voice_a.wav إلى 12 جملة (بتوقيت Whisper في asr.json)، يضيف وقفات، ويحسب توقيت الكلمات → voice/voice.wav و timeline.json"""
import json, os, re, subprocess, sys, difflib
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lines import LINES
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SR = 48000
SRC = "voice/voice_a.wav"
# وقفة بعد كل جملة (ث): صمت طويل بعد الصرخة قبل المفاجأة
GAPS = [0.35, 0.25, 0.25, 0.2, 0.2, 0.25, 0.3, 1.5, 0.35, 0.35, 0.45, 1.8]

def norm(w):
    w = re.sub(r"[ً-ْٰـ]", "", w); w = re.sub(r"[^ء-ي]", "", w)
    for a, b in (("أ","ا"),("إ","ا"),("آ","ا"),("ة","ه"),("ى","ي"),("گ","ك"),("چ","ج")): w = w.replace(a, b)
    return w

raw = subprocess.run(["ffmpeg","-v","error","-i",SRC,"-f","f32le","-ac","1","-ar",str(SR),"-"], capture_output=True).stdout
x = np.frombuffer(raw, np.float32).copy()
asr = json.load(open("asr.json"))[SRC]
sw, owner = [], []
for li, t in enumerate(LINES):
    for w in t.replace("…", " ").split(): sw.append(w); owner.append(li)
a = [norm(w) for w in sw]; b = [norm(w[0]) for w in asr]
tm = [None] * len(sw)
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
    if tag in ("equal", "replace") and j2 > j1:
        for k in range(i2 - i1):
            j = j1 + min(k * (j2 - j1) // (i2 - i1), j2 - j1 - 1); tm[i1 + k] = (asr[j][1], asr[j][2])
for i in range(len(tm)):
    if tm[i] is None:
        p = tm[i-1] if i else (0, 0); tm[i] = (p[1], p[1] + .2)
ls = [min(tm[i][0] for i in range(len(sw)) if owner[i] == li) for li in range(12)]
le = [max(tm[i][1] for i in range(len(sw)) if owner[i] == li) for li in range(12)]
cuts = [0.0] + [(le[i] + ls[i+1]) / 2 for i in range(11)] + [len(x) / SR]
out, t, segs, words = [], 0.0, [], []
for li in range(12):
    c0, c1 = cuts[li], cuts[li+1]
    seg = x[int(c0*SR):int(c1*SR)].copy(); f = int(.012*SR)
    seg[:f] *= np.linspace(0,1,f); seg[-f:] *= np.linspace(1,0,f)
    off = t - c0
    ws = [(sw[i], round(tm[i][0] + off, 3), round(tm[i][1] + off, 3)) for i in range(len(sw)) if owner[i] == li]
    segs.append({"tag": f"l{li+1}", "who": "M", "start": round(t, 3), "end": round(t + len(seg)/SR, 3), "text": LINES[li]})
    words.append({"tag": f"l{li+1}", "who": "M", "words": ws})
    out += [seg, np.zeros(int(GAPS[li]*SR), np.float32)]; t += len(seg)/SR + GAPS[li]
    print(f"l{li+1:<3d}{segs[-1]['start']:7.2f} → {segs[-1]['end']:7.2f}")
y = np.concatenate(out)
subprocess.run(["ffmpeg","-y","-v","error","-f","f32le","-ar",str(SR),"-ac","1","-i","-","-af","loudnorm=I=-16:TP=-1.5:LRA=11","-ar",str(SR),"voice/voice.wav"], input=y.tobytes(), check=True)
json.dump({"duration": round(t,3), "segments": segs, "words": words}, open("timeline.json","w"), ensure_ascii=False, indent=1)
print("TOTAL", round(t,2))
