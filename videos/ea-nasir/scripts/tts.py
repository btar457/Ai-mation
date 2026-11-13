"""توليد الأصوات من Gemini TTS. الاستخدام: python tts.py [ids] [voiceR] [voiceN]"""
import base64, json, subprocess, sys, time, urllib.request
from lines import LINES
MODEL = "gemini-3.8-flash-tts"
VOICE = {"R": sys.argv[2] if len(sys.argv) > 2 else "Charon", "N": sys.argv[3] if len(sys.argv) > 3 else "Fenrir"}
STYLE = {
 "R": "Say like a calm, intriguing documentary narrator: ",
 "N": "Say furiously, like a cheated customer: ",
}
ids = sys.argv[1].split(",") if len(sys.argv) > 1 and sys.argv[1] != "all" else [l[0] for l in LINES]
for i, sp, text in LINES:
    if i not in ids:
        continue
    time.sleep(25)  # حد الطلبات في الدقيقة
    body = {"contents": [{"parts": [{"text": STYLE[sp] + text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE[sp]}}}}}
    req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
                                 data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=180))
        part = r["candidates"][0]["content"]["parts"][0]["inlineData"]
        raw = base64.b64decode(part["data"])
        mime = part["mimeType"]
        if "wav" in mime:
            open(f"voice/{i}.wav", "wb").write(raw)
        else:  # PCM 24 kHz s16le
            open("voice/tmp.pcm", "wb").write(raw)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", "24000", "-ac", "1",
                            "-i", "voice/tmp.pcm", f"voice/{i}.wav"], check=True)
        print("OK", i, mime, flush=True)
    except Exception as e:
        print("ERR", i, getattr(e, "read", lambda: b"")()[:300] or e, flush=True)
