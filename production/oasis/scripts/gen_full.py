import sys, json, base64, urllib.request, wave
from lines import LINES
ch = sys.argv[1]; voice, lines = LINES[ch]
text = "\n\n[long pause]\n\n".join(f"[{tag}] {t}" for _, tag, t in lines)
body={"contents":[{"parts":[{"text":text}]}],"generationConfig":{"responseModalities":["AUDIO"],"speechConfig":{"voiceConfig":{"prebuiltVoiceConfig":{"voiceName":voice}}}}}
req=urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-tts-preview:generateContent",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"})
try: d=json.load(urllib.request.urlopen(req,timeout=300))
except urllib.error.HTTPError as e: print("ERR",ch,e.code,e.read()[:300].decode()); sys.exit(1)
pcm=base64.b64decode(d["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
w=wave.open(f"{ch}.wav","wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm); w.close(); print("ok",ch,round(len(pcm)/48000,1),"s")
