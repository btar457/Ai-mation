"""الحوار كاملاً بطلب واحد متعدد المتكلمين من Gemini TTS. الاستخدام: python tts_dialog.py MODEL OUT.wav"""
import base64, json, subprocess, sys, urllib.request
from lines import LINES
MODEL, OUT = sys.argv[1], sys.argv[2]
NAME = {"R": "Narrator", "N": "Nanni"}
script = "\n".join(f"{NAME[s]}: {t}" for _, s, t in LINES)
prompt = ("TTS the following conversation in Modern Standard Arabic. Nanni is a furious ancient customer shouting "
          "indignantly. Narrator is a calm, intriguing documentary narrator.\n" + script)
body = {"contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"multiSpeakerVoiceConfig": {"speakerVoiceConfigs": [
            {"speaker": "Narrator", "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Charon"}}},
            {"speaker": "Nanni", "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Fenrir"}}}]}}}}
req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
                             data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
try:
    r = json.load(urllib.request.urlopen(req, timeout=300))
except urllib.error.HTTPError as e:
    sys.exit(e.read()[:500])
part = r["candidates"][0]["content"]["parts"][0]["inlineData"]
raw = base64.b64decode(part["data"])
print(part["mimeType"])
if "wav" in part["mimeType"]:
    open(OUT, "wb").write(raw)
else:
    open("voice/tmp.pcm", "wb").write(raw)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", "voice/tmp.pcm", OUT], check=True)
