"""الحوار بطلبين متعددي المتكلمين. الاستخدام: python tts.py RG|IB OUT.wav"""
import base64, json, subprocess, sys, urllib.request, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lines import PART_RG, PART_IB
part, OUT = sys.argv[1], sys.argv[2]
MODEL = os.environ.get("MODEL", "gemini-2.5-flash-preview-tts")
V = {"R": ("Narrator", "Charon"), "G": ("Girl", "Leda"), "I": ("Imam", "Enceladus"), "B": ("Bishr", "Fenrir")}
if part == "RG":
    lines, spk = PART_RG, ["R", "G"]
    desc = ("Narrator is a deep, gripping Arabic storyteller in classical Modern Standard Arabic with dramatic pauses, "
            "warm and moving. Girl is a young servant girl answering quickly and a little proudly.")
else:
    lines, spk = PART_IB, ["I", "B"]
    desc = ("Imam is a saintly, sorrowful elder with a warm, deep, slightly husky voice, speaking classical Arabic very "
            "slowly and gently, each word heavy with meaning. Bishr is a rich man who has just run barefoot through the "
            "streets, out of breath, his voice breaking, weeping with repentance.")
script = "\n".join(f"{V[s][0]}: {t}" for s, t in lines)
body = {"contents": [{"parts": [{"text": f"TTS the following conversation. {desc}\n{script}"}]}],
        "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"multiSpeakerVoiceConfig": {"speakerVoiceConfigs": [
            {"speaker": V[s][0], "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": V[s][1]}}} for s in spk]}}}}
req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
                             data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
try: r = json.load(urllib.request.urlopen(req, timeout=400))
except urllib.error.HTTPError as e: sys.exit(e.read()[:300])
p = r["candidates"][0]["content"]["parts"][0]["inlineData"]
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", "-", OUT], input=base64.b64decode(p["data"]), check=True)
print("ok", OUT)
