"""صور HiDream-O1 (مساحة Hugging Face خارج حصة ZeroGPU) → images/ID.png. الاستخدام: python gen_hidream.py L10,L11 [seed]"""
import os, sys, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shots import SHOTS, STYLE
from gradio_client import Client
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ids = sys.argv[1].split(","); seed = int(sys.argv[2]) if len(sys.argv) > 2 else 21
c = Client("HiDream-ai/HiDream-O1-Image", verbose=False)
for sid in ids:
    try:
        r = c.predict(SHOTS[sid] + ", " + STYLE, "9:16", "text, letters, watermark, cartoon, deformed", False, seed, 5.0, api_name="/_generate_wrapped")
        shutil.copy(r[0]["path"] if isinstance(r[0], dict) else r[0], f"images/{sid}.png"); print("ok", sid, flush=True)
    except Exception as e: print("ERR", sid, str(e)[:200], flush=True)
