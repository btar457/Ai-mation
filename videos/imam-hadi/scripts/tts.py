"""طلب حوار متعدد المتكلمين من Gemini TTS. الاستخدام: python tts.py RM|I MODEL OUT.wav"""
import base64, json, subprocess, sys, urllib.request, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lines import PART_RM, PART_I
part, MODEL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
VOICE = {"R": "Charon", "M": "Algenib", "I": sys.argv[4] if len(sys.argv) > 4 else "Algieba"}
NAME = {"R": "Narrator", "M": "Caliph", "I": "Imam"}
if part == "RM":
    lines, spk = PART_RM, ["R", "M"]
    desc = ("Narrator is a deep, solemn and gripping Arabic storyteller in classical Modern Standard Arabic, with "
            "dramatic pauses. Caliph is a proud, half-drunk Abbasid caliph, commanding and arrogant.")
else:
    lines, spk = PART_I, ["I", "R"]
    desc = os.environ.get("IMAM_DESC", "Imam is a saintly, sorrowful elder with a warm, deep, slightly husky voice. He speaks classical Arabic "
            "very slowly and gently, heavy with grief. When he recites the poem it is a mournful elegy (ritha'): slow, "
            "trembling with emotion, his voice almost breaking with sorrow, drawing out the long vowels, a soft pause "
            "between the two halves of each verse and a long sad pause after each verse, as if reminding kings of death.")
script = "\n".join(f"{NAME[s]}: {t}" for s, t in lines)
body = {"contents": [{"parts": [{"text": f"TTS the following conversation. {desc}\n{script}"}]}],
        "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"multiSpeakerVoiceConfig": {"speakerVoiceConfigs": [
            {"speaker": NAME[s], "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE[s]}}} for s in spk]}}}}
req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
                             data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
try:
    r = json.load(urllib.request.urlopen(req, timeout=400))
except urllib.error.HTTPError as e:
    sys.exit(e.read()[:400])
p = r["candidates"][0]["content"]["parts"][0]["inlineData"]
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", "-", OUT],
               input=base64.b64decode(p["data"]), check=True)
print(OUT, p["mimeType"])
