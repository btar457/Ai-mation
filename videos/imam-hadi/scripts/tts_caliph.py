"""سطرا المتوكل فقط بصوت أفخم. الاستخدام: python tts_caliph.py VOICE OUT.wav"""
import base64, json, subprocess, sys, urllib.request
VOICE, OUT = sys.argv[1], sys.argv[2]
script = "Caliph: أنشِدني شعراً أستحسنُه.\n\nCaliph: لا بدّ أن تُنشدَني!"
import os
desc = os.environ.get("DESC", "Caliph is the most powerful emperor on earth, seated on his throne in a vast stone hall: a booming, "
        "thunderous, very deep chest voice, loud and projected, slow and heavy, every word an order that cannot be refused, "
        "full of pride and menace.")
body = {"contents": [{"parts": [{"text": f"TTS the following conversation. {desc}\n{script}"}]}],
        "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"multiSpeakerVoiceConfig": {"speakerVoiceConfigs": [
            {"speaker": "Caliph", "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}},
            {"speaker": "Narrator", "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Charon"}}}]}}}}
req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent",
                             data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
try: r = json.load(urllib.request.urlopen(req, timeout=300))
except urllib.error.HTTPError as e: sys.exit(e.read()[:300])
p = r["candidates"][0]["content"]["parts"][0]["inlineData"]
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", "-", OUT], input=base64.b64decode(p["data"]), check=True)
print("ok", OUT)
