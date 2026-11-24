"""الصوت الكامل: Gemini TTS، الرجل=Orus (النموذج 4). الاستخدام: python tts.py OUT.wav"""
import base64, json, subprocess, sys, urllib.request, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lines import LINES
OUT = sys.argv[1]
MODEL = os.environ.get("MODEL", "gemini-2.5-flash-preview-tts")
desc = ("Man is a young man from Baghdad speaking pure Baghdadi Iraqi Arabic dialect (not Gulf, not Levantine, not Fusha), "
        "with a deep, full, resonant chest voice. He is NOT whispering: he speaks in a normal voice, at first sleepy and "
        "confused, then calling out louder for his mother and father, then growing uneasy and afraid as he walks the empty "
        "streets, then he SHOUTS loudly in panic: 'أكو أحد؟!'. After the shout there is a long silence, and the last four "
        "lines are slow, quiet and stunned, his voice trembling with shock and deep sadness, the final line almost broken. "
        "He pauses clearly between lines.")
script = "\n".join(f"Man: {t}" for t in LINES)
body = {"contents": [{"parts": [{"text": f"TTS the following conversation. {desc}\n{script}"}]}],
        "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"multiSpeakerVoiceConfig": {"speakerVoiceConfigs": [
            {"speaker": "Man", "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Orus"}}},
            {"speaker": "Other", "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Charon"}}}]}}}}
req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
                             data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
try: r = json.load(urllib.request.urlopen(req, timeout=400))
except urllib.error.HTTPError as e: sys.exit(e.read()[:300])
p = r["candidates"][0]["content"]["parts"][0]["inlineData"]
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", "-", OUT], input=base64.b64decode(p["data"]), check=True)
print("ok", OUT)
