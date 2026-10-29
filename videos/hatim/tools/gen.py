import os, sys, json, shutil, time
from gradio_client import Client, handle_file
TOK = os.environ["HF_TOKEN"]
STYLE_OLD = "High-quality modern Japanese anime feature-film style, clean sharp line art, cel shading, expressive anime eyes, highly detailed painted backgrounds, dramatic cinematic lighting, vivid colors, anime key visual, no text, no letters"
STYLE = "Masterpiece anime film still, high-budget Japanese anime movie quality, ultra detailed, sharp clean line art, detailed intense anime eyes, cel shading with soft gradients, dramatic cinematic lighting with rim light, majestic dignified characters with commanding presence, no text, no letters"
_c = {}
def cl(name):
    if name not in _c: _c[name] = Client(name, token=TOK, verbose=False)
    return _c[name]
def _retry(fn, n=3):
    for i in range(n):
        try: return fn()
        except Exception as e:
            print("retry", i, str(e)[:200], flush=True); time.sleep(5)
    raise
def img(prompt, out, seed=1, w=768, h=1344):
    r = _retry(lambda: cl("mcp-tools/FLUX.1-Krea-dev").predict(prompt=STYLE + ". " + prompt + ". Anime illustration, not a photo.", seed=seed, randomize_seed=False, width=w, height=h, guidance_scale=4.5, num_inference_steps=24, api_name="/infer"))
    p = r[0] if isinstance(r, (list, tuple)) else r
    if isinstance(p, dict): p = p.get("path") or p.get("url")
    shutil.copy(p, out); return out
def edit(ref, prompt, out, seed=1, steps=24, g=2.5):
    r = _retry(lambda: cl("mcp-tools/FLUX.1-Kontext-Dev").predict(input_image=handle_file(ref), prompt=prompt + ". Keep the same character design, same face and clothes, and the same high-quality anime film style.", seed=seed, randomize_seed=False, guidance_scale=g, steps=steps, api_name="/infer"))
    p = r[0] if isinstance(r, (list, tuple)) else r
    if isinstance(p, dict): p = p.get("path") or p.get("url")
    shutil.copy(p, out); return out
def vid(image, prompt, out, seed=42, dur=4.0, steps=6):
    import base64, io
    from PIL import Image
    im = Image.open(image).convert("RGB"); b = io.BytesIO(); im.save(b, "JPEG", quality=93)
    b64 = "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()
    neg = "static, blurry, deformed face, melting, extra fingers, distorted hands, text, watermark"
    r = _retry(lambda: cl("prithivMLmods/Wan2.2-Fast").predict(image_b64=b64, prompt=prompt, steps=steps, negative_prompt=neg, duration_seconds=dur, guidance_scale=1.0, guidance_scale_2=1.0, seed=seed, randomize_seed=False, api_name="/generate_video"), n=2)
    v = r["video"]; open(out, "wb").write(base64.b64decode(v.split(",", 1)[1])); return out
if __name__ == "__main__":
    jobs = json.load(open(sys.argv[1]))
    for j in jobs:
        if os.path.exists(j["out"]) and not j.get("force"): print("skip", j["out"]); continue
        t = time.time()
        try:
            f = {"img": img, "edit": edit, "vid": vid}[j.pop("kind")]
            j.pop("force", None)
            f(**j); print("ok", j["out"], round(time.time() - t), "s", flush=True)
        except Exception as e:
            print("FAIL", j.get("out"), str(e)[:300], flush=True)
