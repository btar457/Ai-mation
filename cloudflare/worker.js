// Ai-mation — Cloudflare Worker لتوليد الصور عبر Workers AI
// الحصة المجانية: 10,000 Neuron يومياً، تتجدد 00:00 UTC (الساعة 3 فجراً بتوقيت بغداد).
//
// الإعداد (مرة واحدة، من المتصفح):
//   1) Workers & Pages → Create → Worker → Deploy، ثم Edit code والصق هذا الملف.
//   2) Settings → Bindings → Add → Workers AI، واسم المتغير: AI
//   3) Settings → Variables and Secrets → Add → Secret، الاسم: APP_KEY، والقيمة كلمة سرية من اختيارك.
//   4) انسخ رابط الـ Worker والكلمة السرية إلى إعدادات Ai-mation.

const MODELS = {
  // مربع 1024×1024 فقط، الأرخص والأسرع
  schnell: "@cf/black-forest-labs/flux-1-schnell",
  // يدعم الأبعاد الحرة (256–1920)، مناسب لـ 9:16 و16:9
  klein: "@cf/black-forest-labs/flux-2-klein-4b",
};

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, X-App-Key",
  "Access-Control-Expose-Headers": "X-Model",
};

const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), {
    status,
    headers: { ...CORS, "Content-Type": "application/json; charset=utf-8" },
  });

const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, Math.round(Number(n) || 0)));
const snap16 = (n) => Math.max(256, Math.round(n / 16) * 16);

function b64ToBytes(b64) {
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function sniffType(bytes) {
  if (bytes[0] === 0x89 && bytes[1] === 0x50) return "image/png";
  if (bytes[0] === 0x52 && bytes[1] === 0x49 && bytes[8] === 0x57) return "image/webp";
  return "image/jpeg";
}

function imageFrom(result) {
  if (!result) return null;
  if (typeof result === "string") return result;
  if (typeof result.image === "string") return result.image;
  if (typeof result.result?.image === "string") return result.result.image;
  return null;
}

async function runSchnell(env, { prompt, seed }) {
  const input = { prompt, steps: 4 };
  if (seed !== undefined) input.seed = seed;
  return imageFrom(await env.AI.run(MODELS.schnell, input));
}

async function runKlein(env, { prompt, width, height, seed }) {
  // هذا النموذج يستقبل multipart/form-data حتى للوصف النصي فقط
  const form = new FormData();
  form.append("prompt", prompt);
  form.append("width", String(width));
  form.append("height", String(height));
  if (seed !== undefined) form.append("seed", String(seed));
  const packed = new Response(form);
  const result = await env.AI.run(MODELS.klein, {
    multipart: { body: packed.body, contentType: packed.headers.get("content-type") },
  });
  return imageFrom(result);
}

const isQuotaError = (msg) => /4006|daily free allocation|neurons/i.test(msg);

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return new Response(null, { headers: CORS });

    if (env.APP_KEY && request.headers.get("X-App-Key") !== env.APP_KEY) {
      return json({ error: "unauthorized" }, 401);
    }
    if (!env.AI) return json({ error: "no_ai_binding", detail: "أضف Workers AI binding باسم AI" }, 500);
    if (request.method === "GET") return json({ ok: true, models: Object.keys(MODELS) });
    if (request.method !== "POST") return json({ error: "method_not_allowed" }, 405);

    let body;
    try {
      body = await request.json();
    } catch {
      return json({ error: "bad_json" }, 400);
    }

    const prompt = String(body.prompt || "").trim().slice(0, 2048);
    if (!prompt) return json({ error: "empty_prompt" }, 400);

    const width = snap16(clamp(body.width || 1024, 256, 1920));
    const height = snap16(clamp(body.height || 1024, 256, 1920));
    const seed = Number.isFinite(Number(body.seed))
      ? Math.abs(Math.floor(Number(body.seed))) % 2147483647
      : undefined;

    const preferred = body.model === "schnell" || body.model === "klein"
      ? body.model
      : width === height ? "schnell" : "klein";
    const order = preferred === "klein" ? ["klein", "schnell"] : ["schnell", "klein"];

    const errors = [];
    for (const model of order) {
      try {
        const b64 = model === "klein"
          ? await runKlein(env, { prompt, width, height, seed })
          : await runSchnell(env, { prompt, seed });
        if (!b64) throw new Error("empty image");
        const bytes = b64ToBytes(b64);
        return new Response(bytes, {
          headers: { ...CORS, "Content-Type": sniffType(bytes), "X-Model": model, "Cache-Control": "no-store" },
        });
      } catch (e) {
        const msg = String(e?.message || e);
        if (isQuotaError(msg)) return json({ error: "daily_limit", detail: msg }, 429);
        errors.push(`${model}: ${msg}`);
      }
    }
    return json({ error: "generation_failed", detail: errors.join(" | ") }, 502);
  },
};
