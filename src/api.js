import { InferenceClient } from "@huggingface/inference";

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
  if (/402|credit|quota|payment|exceeded/i.test(msg)) return "انتهى الرصيد المجاني لهذا الشهر على Hugging Face. جرّب Pollinations للصور أو انتظر تجديد الرصيد.";
  if (/429|rate/i.test(msg)) return "طلبات كثيرة خلال وقت قصير. انتظر قليلاً ثم أعد المحاولة.";
  if (/503|loading|unavailable/i.test(msg)) return "النموذج مشغول أو يتم تحميله حالياً. أعد المحاولة بعد دقيقة.";
  if (/failed to fetch|network/i.test(msg)) return "تعذر الاتصال. تأكد من الإنترنت.";
  return msg;
}

export async function withFriendlyErrors(fn) {
  try {
    return await fn();
  } catch (err) {
    throw new Error(friendlyError(err));
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
  try {
    const q = `Translate the following text to English. Reply with the translation only, no quotes:\n${text}`;
    const res = await fetch(`https://text.pollinations.ai/${encodeURIComponent(q)}`);
    if (res.ok) {
      const t = (await res.text()).trim();
      if (t && !hasArabic(t)) return t;
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

async function pollinationsImage({ prompt, negative, width, height, seed, signal }) {
  const params = new URLSearchParams({
    width, height, seed,
    model: "flux",
    nologo: "true",
    safe: "true",
    negative_prompt: negative,
  });
  const url = `https://image.pollinations.ai/prompt/${encodeURIComponent(prompt)}?${params}`;
  const res = await fetch(url, { signal });
  if (!res.ok) throw new Error(`Pollinations: ${res.status}`);
  const blob = await res.blob();
  if (!blob.type.startsWith("image/")) throw new Error("Pollinations لم يرجع صورة. أعد المحاولة.");
  return blob;
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
  return withFriendlyErrors(() =>
    opts.engine === "pollinations" ? pollinationsImage(args) : hfImage(args),
  );
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
