"""الحوار كاملاً بطلب واحد (راوٍ عراقي + والٍ مصري) من Gemini TTS. الاستخدام: python tts_dialog.py MODEL OUT.wav [voiceR] [voiceW]"""
import base64, json, subprocess, sys, urllib.request
MODEL, OUT = sys.argv[1], sys.argv[2]
VR = sys.argv[3] if len(sys.argv) > 3 else "Charon"
VW = sys.argv[4] if len(sys.argv) > 4 else "Algenib"
LINES = [
 ("Narrator", "هذا الرجل… وجدَ كنزاً مدفوناً تحتَ بيتِه في بغداد."),
 ("Narrator", "لكنَّه لم يجدْه… إلّا بعدَ أن سافرَ إلى مصر، وضُرِب، وسُجِن!"),
 ("Narrator", "كان تاجراً غنيّاً، فخسرَ كلَّ شيء."),
 ("Narrator", "وفي ليلةٍ، جاءه هاتفٌ في المنام: رزقُك في مصر… فاذهبْ إليه."),
 ("Narrator", "مشى شهراً كاملاً، ووصلَ القاهرةَ ليلاً، فنامَ في المسجد."),
 ("Narrator", "وفي تلك الليلة، دخلَ لصوصٌ بيتاً بجوارِ المسجد… فجاء الحرسُ، وقبضوا عليه هو!"),
 ("Narrator", "ضربَه الوالي، وسألَه:"),
 ("Wali", "إنت منين؟ وإيه اللي جابك مصر؟"),
 ("Narrator", "قال: من بغداد… رأيتُ في المنامِ أنَّ رزقي بمصر."),
 ("Wali", "[laughs mockingly] يا قليل العقل! أنا شُفت في المنام تلات مرّات: بيت في بغداد، في حوشه جنينة، وتحت الفسقيّة كنز… وما صدّقتش!"),
 ("Narrator", "ولم يكن الوالي يعلم… أنَّه يصفُ بيتَه هو."),
 ("Narrator", "عادَ إلى بغداد، وحفرَ تحتَ الفسقيّة…"),
]
script = "\n".join(f"{s}: {t}" for s, t in LINES)
prompt = ("TTS the following conversation. Narrator is a gripping Arabian Nights storyteller speaking clear Modern "
          "Standard Arabic, fast-paced and full of suspense. Wali is a big, smug Egyptian governor speaking Cairene "
          "Egyptian Arabic, mocking the fool with a short natural chuckle.\n" + script)
body = {"contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"multiSpeakerVoiceConfig": {"speakerVoiceConfigs": [
            {"speaker": "Narrator", "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VR}}},
            {"speaker": "Wali", "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VW}}}]}}}}
req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
                             data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
try:
    r = json.load(urllib.request.urlopen(req, timeout=300))
except urllib.error.HTTPError as e:
    sys.exit(e.read()[:500])
part = r["candidates"][0]["content"]["parts"][0]["inlineData"]
raw = base64.b64decode(part["data"])
if "wav" in part["mimeType"]:
    open(OUT, "wb").write(raw)
else:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", "-", OUT], input=raw, check=True)
print(OUT, part["mimeType"])
