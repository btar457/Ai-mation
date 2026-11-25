"""تجربة: مطلع دعاء كميل بأسلوب القرّاء العراقيين (صوت أصلي، لا نسخ لصوت شخص). الاستخدام: python tts.py VOICE OUT.wav"""
import base64, json, subprocess, sys, urllib.request, os
VOICE, OUT = sys.argv[1], sys.argv[2]
MODEL = os.environ.get("MODEL", "gemini-2.5-flash-preview-tts")
TEXT = ("اللّهُمَّ إِنّي أَسْأَلُكَ بِرَحْمَتِكَ الَّتي وَسِعَتْ كُلَّ شَيْءٍ… "
        "وَبِقُوَّتِكَ الَّتي قَهَرْتَ بِها كُلَّ شَيْءٍ… وَخَضَعَ لَها كُلُّ شَيْءٍ… وَذَلَّ لَها كُلُّ شَيْءٍ…")
desc = ("Reciter is an Iraqi Shia supplication reciter (like the famous reciters of Dua Kumayl in Karbala) reciting in classical Arabic "
        "with a deep, warm, heartbroken voice. He does not speak normally: he CHANTS melodically in the sorrowful Saba maqam, "
        "very slowly, stretching the long vowels for a long time (اللّهُمَّـــ ... شَيْءٍـــ), his voice rising and falling with "
        "emotion and trembling as if holding back tears, like a man begging God at night in a shrine. Long pauses between phrases.")
body = {"contents": [{"parts": [{"text": f"TTS the following conversation. {desc}\nReciter: {TEXT}"}]}],
        "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"multiSpeakerVoiceConfig": {"speakerVoiceConfigs": [
            {"speaker": "Reciter", "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}},
            {"speaker": "Other", "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Puck"}}}]}}}}
req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
                             data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
try: r = json.load(urllib.request.urlopen(req, timeout=400))
except urllib.error.HTTPError as e: sys.exit(e.read()[:300])
p = r["candidates"][0]["content"]["parts"][0]["inlineData"]
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", "-", OUT], input=base64.b64decode(p["data"]), check=True)
print("ok", OUT)
