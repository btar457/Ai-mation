"""تفريغ الصوت بتوقيت الكلمات (faster-whisper) للتحقق والترجمة."""
import sys, json, subprocess
import numpy as np

def load(f):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32)

from faster_whisper import WhisperModel
m = WhisperModel(sys.argv[2] if len(sys.argv) > 2 else "small", device="cpu", compute_type="int8")
out = {}
for f in sys.argv[1].split(","):
    segs, _ = m.transcribe(load(f), language="ar", word_timestamps=True, vad_filter=False)
    words = [(w.word.strip(), round(w.start, 2), round(w.end, 2)) for s in segs for w in s.words]
    out[f] = words
    print(f, " ".join(f"{w}[{a}-{b}]" for w, a, b in words), flush=True)
json.dump(out, open("asr.json", "w"), ensure_ascii=False)
