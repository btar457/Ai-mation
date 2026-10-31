import sys, json, base64, urllib.request, wave
model, voice, style, text, out, mode = sys.argv[1:7]
if mode=="sys":
    body={"systemInstruction":{"parts":[{"text":style}]},"contents":[{"parts":[{"text":text}]}]}
elif mode=="tags":
    body={"contents":[{"parts":[{"text":text}]}]}
else:
    body={"contents":[{"parts":[{"text":f"{style}:\n{text}"}]}]}
body["generationConfig"]={"responseModalities":["AUDIO"],"speechConfig":{"voiceConfig":{"prebuiltVoiceConfig":{"voiceName":voice}}}}
req=urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"})
try: d=json.load(urllib.request.urlopen(req,timeout=180))
except urllib.error.HTTPError as e: print("ERR",out,e.code,e.read()[:300].decode()); sys.exit(1)
pcm=base64.b64decode(d["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
w=wave.open(out,"wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm); w.close(); print("ok",out,round(len(pcm)/48000,2))
