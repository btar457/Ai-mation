"""أماكن وأشياء من Pollinations → images/ID.jpg"""
import os, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pol_prompts import POL
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for k, (sid, p) in enumerate(POL.items()):
    if os.path.exists(f"images/{sid}.jpg") or os.path.exists(f"images/{sid}.png"): continue
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p)}?width=1080&height=1920&model=flux&nologo=true&seed={70+k}"
    for a in range(12):
        try:
            d = urllib.request.urlopen(url, timeout=180).read()
            if len(d) > 20000: open(f"images/{sid}.jpg", "wb").write(d); print("ok", sid, flush=True); break
        except Exception as e: print("retry", sid, a, str(e)[:50], flush=True)
        time.sleep(15)
