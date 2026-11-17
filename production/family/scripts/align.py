import sys, re, subprocess, difflib, numpy as np, json
from lines import LINES
from faster_whisper import WhisperModel
m = WhisperModel("medium", device="cpu", compute_type="int8")
def norm(s): return re.sub(r'[ً-ْـ…!?؟،.,:\-"]','',s).replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ة','ه').replace('ى','ي').replace(' ','')
def pcm(path, ss=None, to=None):
    cmd=["ffmpeg","-nostdin","-v","error"]+(["-ss",str(ss)] if ss is not None else [])+(["-to",str(to)] if to is not None else [])+["-i",path,"-ac","1","-ar","16000","-f","s16le","-"]
    return np.frombuffer(subprocess.run(cmd,capture_output=True).stdout,dtype=np.int16).astype(np.float32)/32768
EXTRA = {'gp_extra': ('grandpa', ['24','31']), 'sami17': ('sami', ['17'])}
WT = json.load(open('word_times.json')) if len(sys.argv) > 1 and sys.argv[1] in EXTRA else {}
for ch in sys.argv[1:]:
    if ch in EXTRA:
        base, ids = EXTRA[ch]; voice, ls = LINES[base]; ls = [x for x in ls if x[0] in ids]
    else:
        voice, ls = LINES[ch]
    words = [w for s in m.transcribe(pcm(f"{ch}.wav"), language="ar", beam_size=5, word_timestamps=True)[0] for w in s.words]
    i = 0; res = []
    for k, (lid, tag, txt) in enumerate(ls):
        if i >= len(words): print('MISSING', lid); continue
        target = norm(txt); best = (-1, i+1)
        for j in range(i+1, min(len(words), i+40)+1):
            r = difflib.SequenceMatcher(None, norm("".join(w.word for w in words[i:j])), target).ratio()
            if r > best[0]: best = (r, j)
        r, j = best; a = words[i].start; b = words[j-1].end
        # extend into the gap but not into the next word
        a = max(0.0, a - 0.12); nxt = words[j].start if j < len(words) else b + 0.5; b = min(b + 0.15, (b + nxt) / 2)
        subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-ss",f"{a:.3f}","-to",f"{b:.3f}","-i",f"{ch}.wav","-af","apad=pad_dur=0.08","-ar","44100",f"line_{lid}.wav"], check=True)
        heard = "".join(w.word for w in words[i:j]).strip()
        print(f"{lid:4s} {ch:8s} {b-a:4.1f}s match {r:.2f} {'OK ' if r>0.75 else 'CHK'} | {heard}", flush=True)
        WT[lid] = [(w.start - a, w.end - a) for w in words[i:j]]
        i = j
json.dump(WT, open("word_times.json","w"))
