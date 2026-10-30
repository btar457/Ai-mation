import os, json, shutil, re, difflib, sys
import numpy as np, soundfile as sf, librosa
from gradio_client import Client, handle_file
from faster_whisper import WhisperModel
TOK = os.environ["HF_TOKEN"]
REF = {"hatim": "aud/refs/ru_m.flac", "hajib": "aud/refs/he_m1.flac", "caesar": "aud/refs/fi_m.flac",
       "narr": "aud/refs/pt_m1.flac", "mawiya": "aud/refs/ar_prompts2.flac"}
EXG = {"hatim": 0.45, "hajib": 0.55, "caesar": 0.7, "narr": 0.4, "mawiya": 0.45}
c = Client("ResembleAI/Chatterbox-Multilingual-TTS", token=TOK, verbose=False)
wm = WhisperModel("small", device="cpu", compute_type="int8")
norm = lambda s: re.sub(r"[ً-ْـ.,،!?؟…:\s]", "", s).replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه").replace("ى", "ي")
def transcribe(p):
    a, sr = librosa.load(p, sr=16000)
    segs, _ = wm.transcribe(a.astype(np.float32), language="ar", beam_size=5)
    return "".join(s.text for s in segs)
lines = json.load(open(sys.argv[1]))
for L in lines:
    out = f"aud/lines/{L['id']}.wav"
    if os.path.exists(out): print("skip", L["id"]); continue
    best = (-1, None, "")
    for seed in L.get("seeds", [1, 2, 3]):
        try:
            p = c.predict(text_input=L["text"], language_id="ar", audio_prompt_path_input=handle_file(REF[L["who"]]),
                          exaggeration_input=EXG[L["who"]], temperature_input=0.6, seed_num_input=seed, cfgw_input=0.5,
                          api_name="/generate_tts_audio")
        except Exception as e:
            print("ERR", L["id"], seed, str(e)[:150], flush=True); continue
        tr = transcribe(p)
        sc = difflib.SequenceMatcher(None, norm(tr), norm(L["text"])).ratio()
        print(L["id"], seed, round(sc, 2), tr, flush=True)
        if sc > best[0]: best = (sc, p, tr)
        if sc >= 0.9: break
    if best[1]:
        a, sr = librosa.load(best[1], sr=24000)
        a, _ = librosa.effects.trim(a, top_db=35)
        sf.write(out, a, 24000); print("BEST", L["id"], round(best[0], 2), round(len(a) / 24000, 2), "s", flush=True)
