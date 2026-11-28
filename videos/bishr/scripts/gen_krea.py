"""صور FLUX.1-Krea (Hugging Face، بدون تمرير توكن: الوكيل يحقنه) → images/ID.png. الاستخدام: python gen_krea.py [IDs] [seed]"""
import os, sys, shutil, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shots import SHOTS, STYLE
from gradio_client import Client
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ids = sys.argv[1].split(",") if len(sys.argv) > 1 and sys.argv[1] != "all" else list(SHOTS)
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 11
c = Client("mcp-tools/FLUX.1-Krea-dev", verbose=False)
for k, sid in enumerate(ids):
    out = f"images/{sid}.png"
    if os.path.exists(out) and len(sys.argv) < 3: continue
    try:
        res, _ = c.predict(SHOTS[sid] + ", " + STYLE, seed + k, False, 576, 1024, 4.5, 22, api_name="/infer")
        shutil.copy(res["path"] if isinstance(res, dict) else res, out); print("ok", sid, flush=True)
    except Exception as e:
        msg = str(e); print("ERR", sid, msg[:160], flush=True)
        if "limit" in msg.lower() or "quota" in msg.lower(): break
