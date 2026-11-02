"""Exercise action shots for the warm-up (Wan, from the group image s04). Mouths closed: the voice plays over the action.
python3 ex.py
"""
import os, sys, shutil, subprocess
SC = "/tmp/claude-0/-home-user-Ai-mation/2bd9efd6-c97a-5f39-86d7-33d600586032/scratchpad"
EP = "/home/user/Ai-mation/docs/oasis-team/ep01"
OUT = f"{SC}/lip/ex"; os.makedirs(OUT, exist_ok=True)
TALK_HEAD = 1.2   # seconds of the speaker's close-up before cutting to the action
def dur(p): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]))
BASE = ("the three cartoon friends, a baby camel with a red headband, a falcon with a teal satchel and an old tortoise with glasses, "
        "at the desert oasis, {a}, happy smiling faces with mouths closed, nobody talks, full bodies visible, steady camera, smooth Pixar-style 3D animation, stable characters")
EX = {
 "07": "all three stretch their arms and wings high up towards the sky, reaching higher and higher, swaying gently side to side",
 "08": "all three lower their arms and roll their shoulders in big circles, one, two, three, four",
 "09": "all three jump up and down in place again and again, landing softly on the sand, energetic and joyful",
 "10": "all three bend forward slowly and touch their toes, then come back up",
}
from gradio_client import Client, handle_file
c = Client('zerogpu-aoti/wan2-2-fp8da-aoti-faster', verbose=False)
for l, act in EX.items():
    out = f"{OUT}/{l}.mp4"
    if os.path.exists(out): continue
    d = round(min(5.0, max(2.0, dur(f"{SC}/tts/full/line_{l}.wav") - TALK_HEAD + 0.4)), 2)
    try:
        r = c.submit(input_image=handle_file(f"{EP}/s04.jpg"), prompt=BASE.format(a=act), steps=6, duration_seconds=d,
                     seed=42, randomize_seed=False, api_name='/generate_video').result(timeout=300)
        shutil.copy(r[0], out); print("ok", l, d, flush=True)
    except Exception as e:
        print("FAIL", l, str(e)[:200], flush=True)
        if "quota" in str(e).lower(): print("STOP", flush=True); sys.exit(0)
print("DONE", flush=True)
