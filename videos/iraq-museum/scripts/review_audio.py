"""مراجعة صوتية بالاستماع عبر Gemini. الاستخدام: python review_audio.py FILE.mp3 "السؤال" """
import base64, json, sys, urllib.request
b = base64.b64encode(open(sys.argv[1], "rb").read()).decode()
body = {"contents": [{"parts": [{"inlineData": {"mimeType": "audio/mp3", "data": b}}, {"text": sys.argv[2]}]}]}
req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/"+__import__("os").environ.get("GM","gemini-3-flash-preview")+":generateContent",
                             data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
try:
    r = json.load(urllib.request.urlopen(req, timeout=300))
    print("".join(p.get("text", "") for p in r["candidates"][0]["content"]["parts"] if not p.get("thought")))
except urllib.error.HTTPError as e:
    print(e.read()[:400])
