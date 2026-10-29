import os, json, re, difflib, sys, time
import numpy as np, soundfile as sf, librosa, torch
torch.set_num_threads(4)
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
from faster_whisper import WhisperModel
REF = {"hatim": "aud/refs/ru_m.flac", "hajib": "aud/refs/he_m1.flac", "caesar": "aud/refs/fi_m.flac",
       "narr": os.environ.get("NARR_REF", "aud/refs/pt_m1.flac"), "mawiya": "aud/refs/ar_prompts2.flac"}
EXG = {"hatim": 0.45, "hajib": 0.55, "caesar": 0.65, "narr": 0.4, "mawiya": 0.45}
m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
wm = WhisperModel("small", device="cpu", compute_type="int8")
norm = lambda s: re.sub(r"[ً-ْـ.,،!?؟…:\s]", "", s).replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه").replace("ى", "ي")
def transcribe(a):
    segs, _ = wm.transcribe(librosa.resample(a, orig_sr=m.sr, target_sr=16000).astype(np.float32), language="ar", beam_size=5)
    return "".join(s.text for s in segs)
lines = json.load(open(sys.argv[1]))
only = set(sys.argv[2:])
for L in lines:
    if only and L["id"] not in only: continue
    out = f"aud/lines/{L['id']}.wav"
    if os.path.exists(out): print("skip", L["id"], flush=True); continue
    best = (-1, None, "")
    for seed in L.get("seeds", [1, 2, 3]):
        t = time.time(); torch.manual_seed(seed)
        w = m.generate(L["text"], language_id="ar", audio_prompt_path=REF[L["who"]], exaggeration=EXG[L["who"]], temperature=0.6, cfg_weight=0.5)
        a = w.squeeze().cpu().numpy()
        tr = transcribe(a); sc = difflib.SequenceMatcher(None, norm(tr), norm(L["text"])).ratio()
        print(L["id"], seed, round(sc, 2), round(time.time() - t), "s", tr, flush=True)
        if sc > best[0]: best = (sc, a, tr)
        if sc >= 0.88: break
    a, _ = librosa.effects.trim(best[1], top_db=35)
    sf.write(out, a, m.sr); print("BEST", L["id"], round(best[0], 2), round(len(a) / m.sr, 2), "s", flush=True)
