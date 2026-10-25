import { InferenceClient } from "@huggingface/inference";
import { Client as GradioClient } from "@gradio/client";

export const STYLES = [
  { id: "none", label: "بدون", suffix: "" },
  { id: "realistic", label: "واقعي", suffix: "photorealistic, ultra detailed, natural lighting, 85mm photo, high detail skin texture" },
  { id: "cinematic", label: "سينمائي", suffix: "cinematic film still, dramatic lighting, shallow depth of field, color graded, anamorphic" },
  { id: "anime", label: "أنمي", suffix: "anime style, vibrant colors, detailed cel shading, studio quality key visual" },
  { id: "fantasy", label: "فانتازيا", suffix: "epic fantasy art, magical atmosphere, intricate details, concept art" },
  { id: "3d", label: "ثلاثي الأبعاد", suffix: "3d render, pixar style, soft global illumination, octane render" },
  { id: "oil", label: "رسم زيتي", suffix: "oil painting, visible brush strokes, classical masterpiece" },
  { id: "watercolor", label: "ألوان مائية", suffix: "watercolor painting, soft washes, paper texture" },
  { id: "comic", label: "كوميكس", suffix: "comic book art, bold ink lines, halftone shading" },
  { id: "cyberpunk", label: "سايبربانك", suffix: "cyberpunk, neon lights, futuristic city, rain reflections" },
  { id: "pixel", label: "بكسل آرت", suffix: "pixel art, 16-bit, retro game sprite" },
  { id: "arabic-heritage", label: "تراث عربي", suffix: "middle eastern heritage, arabic architecture, ornate details, warm golden light" },
];

export const IMAGE_ENGINES = {
  "hf-space": { label: "FLUX Space", needsToken: false, space: "black-forest-labs/FLUX.1-schnell" },
  pollinations: { label: "Pollinations", needsToken: false },
  "hf-flux-schnell": { label: "FLUX schnell", needsToken: true, model: "black-forest-labs/FLUX.1-schnell" },
  "hf-flux-dev": { label: "FLUX dev", needsToken: true, model: "black-forest-labs/FLUX.1-dev" },
  "hf-sdxl": { label: "SDXL", needsToken: true, model: "stabilityai/stable-diffusion-xl-base-1.0" },
};

export const VIDEO_MODELS = {
  t2v: "Wan-AI/Wan2.1-T2V-14B",
  i2v: "Wan-AI/Wan2.1-I2V-14B-720P",
};

const RATIOS = {
  "1:1": [1024, 1024],
  "9:16": [768, 1344],
  "16:9": [1344, 768],
  "3:4": [896, 1152],
  "4:3": [1152, 896],
};

const QUALITY = "masterpiece, best quality, sharp focus, highly detailed";
const DEFAULT_NEGATIVE = "nsfw, nudity, low quality, blurry, deformed, extra fingers, watermark, text";

export const randomSeed = () => Math.floor(Math.random() * 2_147_483_647);
const hasArabic = (s) => /[؀-ۿ]/.test(s);

function client(token) {
  if (!token) throw new Error("هذه الميزة تحتاج توكن Hugging Face. أضفه من تبويب الإعدادات.");
  return new InferenceClient(token);
}

function friendlyError(err) {
  const msg = String(err?.message || err);
  if (/401|unauthorized|invalid.*token/i.test(msg)) return "التوكن غير صحيح أو لا يملك صلاحية Inference Providers.";
  if (/gpu quota|zerogpu|exceeded your .*quota/i.test(msg)) return "انتهت حصة GPU المجانية لهذا اليوم على Hugging Face Spaces. أضف توكن Hugging Face في الإعدادات لحصة أكبر، أو انتظر تجددها.";
  if (/402|credit|payment|exceeded/i.test(msg)) return "انتهى الرصيد المجاني الشهري لـ Inference Providers على Hugging Face. استخدم محرك \"FLUX Space\" المجاني.";
  if (/429|rate/i.test(msg)) return "طلبات كثيرة خلال وقت قصير. انتظر قليلاً ثم أعد المحاولة.";
  if (/503|loading|unavailable/i.test(msg)) return "النموذج مشغول أو يتم تحميله حالياً. أعد المحاولة بعد دقيقة.";
  if (/metadata could not be loaded|app config|could not connect|space.*(sleeping|paused|error)/i.test(msg)) return "تعذر الاتصال بـ FLUX Space (قد يكون متوقفاً مؤقتاً). أعد المحاولة بعد قليل أو اختر محركاً آخر.";
  if (/failed to fetch|network/i.test(msg)) return "تعذر الاتصال. تأكد من الإنترنت.";
  return msg;
}

export async function withFriendlyErrors(fn) {
  try {
    return await fn();
  } catch (err) {
    const e = new Error(friendlyError(err));
    e.code = err?.code;
    throw e;
  }
}

// ترجمة الوصف العربي إلى الإنجليزية (النماذج تفهم الإنجليزية أفضل بكثير)
export async function translateToEnglish(text, token) {
  if (!text || !hasArabic(text)) return text;
  if (token) {
    try {
      const out = await new InferenceClient(token).translation({
        model: "Helsinki-NLP/opus-mt-ar-en",
        provider: "hf-inference",
        inputs: text,
      });
      const t = Array.isArray(out) ? out[0]?.translation_text : out?.translation_text;
      if (t) return t;
    } catch {
      // ننتقل إلى البديل المجاني
    }
  }
  // بديل مجاني بدون مفتاح: MyMemory
  try {
    const res = await fetch(
      `https://api.mymemory.translated.net/get?langpair=ar|en&q=${encodeURIComponent(text.slice(0, 500))}`,
    );
    if (res.ok) {
      const t = (await res.json())?.responseData?.translatedText?.trim();
      if (t && !hasArabic(t) && !/MYMEMORY WARNING/i.test(t)) return t;
    }
  } catch {
    // إذا فشلت الترجمة نرسل النص كما هو
  }
  return text;
}

export function buildPrompt({ prompt, styleId, character, enhance }) {
  const style = STYLES.find((s) => s.id === styleId);
  return [character?.desc, prompt, style?.suffix, enhance ? QUALITY : ""]
    .filter((p) => p && p.trim())
    .join(", ");
}

export function sizeFor(ratio) {
  return RATIOS[ratio] || RATIOS["1:1"];
}

async function pollinationsImage({ prompt, width, height, seed, pollinationsKey, signal }) {
  const params = new URLSearchParams({ width, height, seed, nologo: "true", safe: "true" });
  let url;
  if (pollinationsKey) {
    params.set("key", pollinationsKey);
    url = `https://gen.pollinations.ai/image/${encodeURIComponent(prompt)}?${params}`;
  } else {
    params.set("model", "flux");
    url = `https://image.pollinations.ai/prompt/${encodeURIComponent(prompt)}?${params}`;
  }
  const res = await fetch(url, { signal });
  if (res.status === 402 || res.status === 429) {
    const body = await res.json().catch(() => ({}));
    const code = body?.error?.code;
    const e = new Error(
      pollinationsKey
        ? "رصيد مفتاح Pollinations انتهى. استخدم محرك \"FLUX Space\" المجاني."
        : "Pollinations المجاني يسمح بصورة واحدة كل 45 ثانية فقط.",
    );
    e.code = pollinationsKey ? code : "FREE_LIMIT";
    throw e;
  }
  if (res.status === 401) throw new Error("مفتاح Pollinations غير صحيح.");
  if (!res.ok) throw new Error(`Pollinations: خطأ ${res.status}`);
  const blob = await res.blob();
  if (!blob.type.startsWith("image/")) throw new Error("Pollinations لم يرجع صورة. أعد المحاولة.");
  return blob;
}

// Hugging Face Spaces (ZeroGPU): حصة مجانية يومية، وتعمل بدون توكن بحصة أقل
const spaceClients = new Map();
async function spaceImage({ engine, prompt, width, height, seed, token }) {
  const { space } = IMAGE_ENGINES[engine];
  const key = `${space}|${token || ""}`;
  if (!spaceClients.has(key)) {
    spaceClients.set(key, GradioClient.connect(space, token ? { hf_token: token } : {}));
  }
  let app;
  try {
    app = await spaceClients.get(key);
  } catch (e) {
    spaceClients.delete(key);
    throw e;
  }
  const res = await app.predict("/infer", {
    prompt,
    seed,
    randomize_seed: false,
    width,
    height,
    num_inference_steps: 4,
  });
  const out = res?.data?.[0];
  const url = typeof out === "string" ? out : out?.url;
  if (!url) throw new Error("الـ Space لم يرجع صورة. أعد المحاولة.");
  const img = await fetch(url, token ? { headers: { Authorization: `Bearer ${token}` } } : {});
  if (!img.ok) throw new Error(`تعذر تحميل الصورة: ${img.status}`);
  return img.blob();
}

async function hfImage({ engine, prompt, negative, width, height, seed, token, signal }) {
  const { model } = IMAGE_ENGINES[engine];
  const parameters = { width, height, seed };
  if (!engine.includes("schnell")) parameters.negative_prompt = negative;
  return client(token).textToImage(
    { model, provider: "auto", inputs: prompt, parameters },
    { outputType: "blob", signal },
  );
}

export async function generateImage(opts) {
  const negative = [DEFAULT_NEGATIVE, opts.negative].filter(Boolean).join(", ");
  const args = { ...opts, negative };
  const run = { pollinations: pollinationsImage, "hf-space": spaceImage }[opts.engine] || hfImage;
  return withFriendlyErrors(() => run(args));
}

export async function generateVideo({ mode, model, prompt, image, token, signal }) {
  return withFriendlyErrors(async () => {
    const c = client(token);
    if (mode === "i2v") {
      if (!image) throw new Error("اختر صورة مصدر أولاً.");
      return c.imageToVideo(
        { model, provider: "auto", inputs: image, parameters: { prompt, negative_prompt: DEFAULT_NEGATIVE } },
        { signal },
      );
    }
    return c.textToVideo(
      { model, provider: "auto", inputs: prompt, parameters: { negative_prompt: DEFAULT_NEGATIVE } },
      { signal },
    );
  });
}

export async function testToken(token) {
  const res = await fetch("https://huggingface.co/api/whoami-v2", {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("التوكن غير صالح.");
  return res.json();
}
