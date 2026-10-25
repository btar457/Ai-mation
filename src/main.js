import { Capacitor } from "@capacitor/core";
import { Browser } from "@capacitor/browser";
import {
  STYLES, IMAGE_ENGINES, VIDEO_MODELS,
  buildPrompt, sizeFor, randomSeed, translateToEnglish,
  generateImage, generateVideo, testToken,
} from "./api.js";
import { checkPrompt } from "./safety.js";
import { loadSettings, saveSettings } from "./settings.js";
import { putItem, deleteItem, clearStore, getAll, uid } from "./db.js";
import { downloadBlob, shareBlob } from "./save.js";

const $ = (id) => document.getElementById(id);
const COLAB_URL = "https://colab.research.google.com/github/btar457/Ai-mation/blob/ccr-64095e7e-ed952s/colab/Ai-mation-Video.ipynb";

async function openColab() {
  if (Capacitor.isNativePlatform()) await Browser.open({ url: COLAB_URL });
  else window.open(COLAB_URL, "_blank", "noopener");
}
let settings = loadSettings();
// المستخدمون القدامى: Pollinations لم يعد مجانياً بلا حدود، ننقلهم إلى FLUX Space
if (!settings.engineMigrated) {
  settings = saveSettings({ engineMigrated: true, imgEngine: settings.imgEngine === "pollinations" ? "hf-space" : settings.imgEngine });
}

// ---------- أدوات عامة ----------

let toastTimer;
function toast(msg) {
  const t = $("toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("show"), 3000);
}

function setStatus(el, msg, isError = false) {
  el.textContent = msg || "";
  el.classList.toggle("error", isError);
}

// روابط الـ Blob لكل حاوية حتى نحررها من الذاكرة عند إعادة الرسم
const urlBuckets = new Map();
function blobUrl(bucket, blob) {
  const url = URL.createObjectURL(blob);
  if (!urlBuckets.has(bucket)) urlBuckets.set(bucket, []);
  urlBuckets.get(bucket).push(url);
  return url;
}
function releaseUrls(bucket) {
  (urlBuckets.get(bucket) || []).forEach((u) => URL.revokeObjectURL(u));
  urlBuckets.set(bucket, []);
}

function mediaEl(blob, bucket, { controls = false } = {}) {
  const url = blobUrl(bucket, blob);
  if (blob.type.startsWith("video/")) {
    const v = document.createElement("video");
    Object.assign(v, { src: url, muted: !controls, loop: true, playsInline: true, controls, autoplay: !controls });
    return v;
  }
  const img = document.createElement("img");
  img.src = url;
  img.alt = "";
  return img;
}

function loadingTile(label) {
  const tile = document.createElement("div");
  tile.className = "tile loading";
  tile.innerHTML = `<div class="spinner"></div><span class="badge">${label}</span>`;
  return tile;
}

function fileBase(item) {
  return `aimation-${item.type}-${new Date(item.created).toISOString().slice(0, 19).replace(/[:T]/g, "-")}`;
}

function updateBadge() {
  $("engineBadge").textContent = settings.hfToken ? "✅ Hugging Face متصل" : "مجاني بدون توكن";
}

// ---------- التبويبات ----------

function showView(name) {
  document.querySelectorAll(".view").forEach((v) => v.classList.toggle("active", v.id === `view-${name}`));
  document.querySelectorAll(".tabbar button").forEach((b) => b.classList.toggle("on", b.dataset.view === name));
  if (name === "gallery") renderGallery();
  window.scrollTo({ top: 0 });
}
document.querySelectorAll(".tabbar button").forEach((b) => b.addEventListener("click", () => showView(b.dataset.view)));

// ---------- عارض الصور/الفيديو ----------

function openViewer(item, { inGallery }) {
  releaseUrls("viewer");
  const body = $("viewerBody");
  body.replaceChildren(mediaEl(item.blob, "viewer", { controls: true }));
  $("viewerPrompt").textContent = item.prompt || "";

  const actions = [
    ["⬇️ حفظ", async () => toast(await downloadBlob(item.blob, fileBase(item)))],
    ["📤 مشاركة", () => shareBlob(item.blob, fileBase(item), item.prompt).catch(() => {})],
  ];
  if (item.type === "image") {
    actions.push(["🎬 تحريك", () => { $("viewer").close(); useAsVideoSource(item.blob); }]);
    actions.push(["🚀 حرّكها في Colab", async () => {
      toast(await downloadBlob(item.blob, fileBase(item)) + " — ارفعها من زر 🖼️ في Colab");
      setTimeout(openColab, 1500);
    }]);
    actions.push(["🔁 نفس الوصف", () => {
      $("viewer").close();
      $("imgPrompt").value = item.originalPrompt || item.prompt;
      showView("image");
    }]);
  }
  if (!inGallery && !settings.autoSave) {
    actions.push(["💾 للمعرض", async () => { await putItem("gallery", item); toast("أضيف إلى المعرض"); }]);
  }
  if (inGallery) {
    actions.push(["🗑️ حذف", async () => {
      await deleteItem("gallery", item.id);
      $("viewer").close();
      renderGallery();
    }]);
  }
  actions.push(["✖️ إغلاق", () => $("viewer").close()]);

  $("viewerActions").replaceChildren(...actions.map(([label, fn]) => {
    const b = document.createElement("button");
    b.textContent = label;
    b.addEventListener("click", async () => {
      try { await fn(); } catch (e) { toast(e.message); }
    });
    return b;
  }));
  $("viewer").showModal();
}
$("viewer").addEventListener("close", () => {
  $("viewerBody").replaceChildren();
  releaseUrls("viewer");
});

function resultTile(item, bucket, { inGallery = false } = {}) {
  const tile = document.createElement("div");
  tile.className = "tile";
  tile.appendChild(mediaEl(item.blob, bucket));
  if (item.type === "video") tile.insertAdjacentHTML("beforeend", `<span class="badge">🎬 فيديو</span>`);
  tile.addEventListener("click", () => openViewer(item, { inGallery }));
  return tile;
}

// ---------- الشخصيات ----------

let characters = [];

async function refreshCharacters() {
  characters = (await getAll("characters")).sort((a, b) => a.name.localeCompare(b.name, "ar"));
  for (const id of ["imgCharacter", "vidCharacter"]) {
    const sel = $(id);
    const current = sel.value;
    sel.replaceChildren(new Option("— بدون شخصية —", ""), ...characters.map((c) => new Option(c.name, c.id)));
    sel.value = characters.some((c) => c.id === current) ? current : "";
  }

  const list = $("charList");
  list.replaceChildren(...characters.map((c) => {
    const row = document.createElement("div");
    row.className = "item";
    row.innerHTML = `<div class="info"><b></b><small></small></div>`;
    row.querySelector("b").textContent = `${c.name} · seed ${c.seed}`;
    row.querySelector("small").textContent = c.desc;
    const edit = Object.assign(document.createElement("button"), { textContent: "✏️" });
    edit.addEventListener("click", () => {
      $("charId").value = c.id;
      $("charName").value = c.name;
      $("charDesc").value = c.desc;
      $("charSeed").value = c.seed;
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
    const del = Object.assign(document.createElement("button"), { textContent: "🗑️" });
    del.addEventListener("click", async () => {
      if (!confirm(`حذف الشخصية "${c.name}"؟`)) return;
      await deleteItem("characters", c.id);
      refreshCharacters();
    });
    row.append(edit, del);
    return row;
  }));
  if (!characters.length) list.innerHTML = `<p class="empty">لا توجد شخصيات بعد.</p>`;
}

function resetCharForm() {
  $("charForm").reset();
  $("charId").value = "";
  $("charSeed").value = randomSeed();
}

$("charReset").addEventListener("click", resetCharForm);
$("charForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = $("charName").value.trim();
  const descRaw = $("charDesc").value.trim();
  const blocked = checkPrompt(name, descRaw);
  if (blocked) return toast(blocked);

  const desc = settings.translate ? await translateToEnglish(descRaw, settings.hfToken) : descRaw;
  await putItem("characters", {
    id: $("charId").value || uid(),
    name,
    desc,
    seed: Number($("charSeed").value) || randomSeed(),
  });
  toast("تم حفظ الشخصية");
  resetCharForm();
  refreshCharacters();
});

const selectedCharacter = (selId) => characters.find((c) => c.id === $(selId).value);

// ---------- توليد الصور ----------

$("styleChips").replaceChildren(...STYLES.map((s) => {
  const chip = document.createElement("button");
  chip.type = "button";
  chip.className = "chip" + (s.id === settings.imgStyle ? " on" : "");
  chip.textContent = s.label;
  chip.addEventListener("click", () => {
    settings = saveSettings({ imgStyle: s.id });
    document.querySelectorAll("#styleChips .chip").forEach((c) => c.classList.toggle("on", c === chip));
  });
  return chip;
}));

$("imgEngine").value = settings.imgEngine;
$("imgEngine").addEventListener("change", () => { settings = saveSettings({ imgEngine: $("imgEngine").value }); });

$("imgGenerate").addEventListener("click", async () => {
  const btn = $("imgGenerate");
  const status = $("imgStatus");
  const raw = $("imgPrompt").value.trim();
  const character = selectedCharacter("imgCharacter");
  if (!raw && !character) return setStatus(status, "اكتب وصفاً أولاً.", true);

  const negativeRaw = $("imgNegative").value.trim();
  const blocked = checkPrompt(raw, character?.desc, character?.name);
  if (blocked) return setStatus(status, blocked, true);

  let engine = $("imgEngine").value;
  if (IMAGE_ENGINES[engine].needsToken && !settings.hfToken) {
    toast("لا يوجد توكن، سيتم استخدام المحركات المجانية");
    engine = "hf-space";
  }

  btn.disabled = true;
  releaseUrls("imgResults");
  const results = $("imgResults");
  results.replaceChildren();

  try {
    let prompt = raw;
    let negative = negativeRaw;
    if (settings.translate) {
      setStatus(status, "🌐 جارٍ ترجمة الوصف...");
      [prompt, negative] = await Promise.all([
        translateToEnglish(raw, settings.hfToken),
        translateToEnglish(negativeRaw, settings.hfToken),
      ]);
    }
    const fullPrompt = buildPrompt({
      prompt,
      styleId: settings.imgStyle,
      character,
      enhance: $("imgEnhance").checked,
    });
    const blockedEn = checkPrompt(fullPrompt);
    if (blockedEn) throw new Error(blockedEn);

    const count = Number($("imgCount").value);
    const [width, height] = sizeFor($("imgRatio").value);
    const baseSeed = Number($("imgSeed").value) || character?.seed || randomSeed();

    setStatus(status, `🎨 جارٍ توليد ${count} ${count > 1 ? "صور" : "صورة"}...`);
    const tiles = Array.from({ length: count }, (_, i) => loadingTile(`${i + 1}/${count}`));
    results.replaceChildren(...tiles);

    let ok = 0;
    const errors = [];
    // نولد بالتتابع لتجنب حدود الطلبات في الخدمات المجانية
    for (let i = 0; i < count; i++) {
      const genArgs = {
        engine, prompt: fullPrompt, negative, width, height,
        seed: baseSeed + i, token: settings.hfToken, pollinationsKey: settings.pollinationsKey,
        fallback: settings.fallback,
        onStatus: (msg) => setStatus(status, `[${i + 1}/${count}] ${msg}`),
      };
      try {
        let blob, used;
        try {
          ({ blob, engine: used } = await generateImage(genArgs));
        } catch (e) {
          if (e.code !== "FREE_LIMIT") throw e;
          // حد Pollinations المجاني: ننتظر ثم نعيد المحاولة مرة واحدة
          for (let s = 46; s > 0; s--) {
            setStatus(status, `⏳ Pollinations المجاني يسمح بصورة كل 45 ثانية... الصورة ${i + 1} بعد ${s} ثانية`);
            await new Promise((r) => setTimeout(r, 1000));
          }
          setStatus(status, `🎨 جارٍ توليد الصورة ${i + 1} من ${count}...`);
          ({ blob, engine: used } = await generateImage({ ...genArgs, fallback: false }));
        }
        const item = {
          id: uid(), type: "image", blob, created: Date.now(),
          prompt: fullPrompt, originalPrompt: raw, engine: used, seed: baseSeed + i,
        };
        if (used !== engine) toast(`تم التوليد عبر ${IMAGE_ENGINES[used].label}`);
        if (settings.autoSave) await putItem("gallery", item);
        tiles[i].replaceWith(resultTile(item, "imgResults"));
        ok++;
      } catch (e) {
        errors.push(e.message);
        tiles[i].remove();
      }
    }
    if (!ok) throw new Error(errors[0] || "فشل التوليد");
    setStatus(status, `✅ تم توليد ${ok} من ${count}` + (errors.length ? `\n⚠️ ${errors[0]}` : "") +
      (settings.autoSave ? " — محفوظة في المعرض" : ""));
  } catch (e) {
    setStatus(status, "❌ " + e.message, true);
  } finally {
    btn.disabled = false;
  }
});

// ---------- توليد الفيديو ----------

let vidMode = "t2v";
let vidSource = null;

function setVidMode(mode) {
  vidMode = mode;
  document.querySelectorAll("#vidMode button").forEach((b) => b.classList.toggle("on", b.dataset.mode === mode));
  $("i2vSource").hidden = mode !== "i2v";
  $("vidModel").value = VIDEO_MODELS[mode];
  $("vidModelHint").textContent = "يمكنك تغيير النموذج بأي نموذج " +
    (mode === "t2v" ? "text-to-video" : "image-to-video") + " من huggingface.co/models يدعم Inference Providers.";
}
document.querySelectorAll("#vidMode button").forEach((b) => b.addEventListener("click", () => setVidMode(b.dataset.mode)));

function setVidSource(blob) {
  vidSource = blob;
  releaseUrls("vidSource");
  const img = $("vidSourcePreview");
  img.src = blobUrl("vidSource", blob);
  img.hidden = false;
}

function useAsVideoSource(blob) {
  setVidMode("i2v");
  setVidSource(blob);
  showView("video");
}

$("vidUpload").addEventListener("change", (e) => {
  const f = e.target.files?.[0];
  if (f) setVidSource(f);
  e.target.value = "";
});

$("vidPickGallery").addEventListener("click", async () => {
  releaseUrls("picker");
  const images = (await getAll("gallery")).filter((i) => i.type === "image").sort((a, b) => b.created - a.created);
  const grid = $("pickerGrid");
  grid.replaceChildren(...images.map((item) => {
    const tile = document.createElement("div");
    tile.className = "tile";
    tile.appendChild(mediaEl(item.blob, "picker"));
    tile.addEventListener("click", () => { setVidSource(item.blob); $("picker").close(); });
    return tile;
  }));
  if (!images.length) grid.innerHTML = `<p class="empty">لا توجد صور في المعرض.</p>`;
  $("picker").showModal();
});
$("pickerClose").addEventListener("click", () => $("picker").close());
$("picker").addEventListener("close", () => releaseUrls("picker"));

$("vidGenerate").addEventListener("click", async () => {
  const btn = $("vidGenerate");
  const status = $("vidStatus");
  const raw = $("vidPrompt").value.trim();
  const character = selectedCharacter("vidCharacter");

  if (!settings.hfToken) return setStatus(status, "الفيديو يحتاج توكن Hugging Face. أضفه من الإعدادات.", true);
  if (vidMode === "t2v" && !raw && !character) return setStatus(status, "اكتب وصف الفيديو أولاً.", true);
  if (vidMode === "i2v" && !vidSource) return setStatus(status, "اختر صورة مصدر أولاً.", true);
  const blocked = checkPrompt(raw, character?.desc);
  if (blocked) return setStatus(status, blocked, true);

  btn.disabled = true;
  const started = Date.now();
  const timer = setInterval(() => {
    setStatus(status, `🎬 جارٍ توليد الفيديو... ${Math.round((Date.now() - started) / 1000)} ثانية (قد يستغرق عدة دقائق، لا تغلق التطبيق)`);
  }, 1000);

  try {
    const prompt = settings.translate ? await translateToEnglish(raw, settings.hfToken) : raw;
    const fullPrompt = buildPrompt({ prompt, styleId: "none", character, enhance: false }) || "subtle natural motion";
    const blockedEn = checkPrompt(fullPrompt);
    if (blockedEn) throw new Error(blockedEn);

    const blob = await generateVideo({
      mode: vidMode,
      model: $("vidModel").value.trim() || VIDEO_MODELS[vidMode],
      prompt: fullPrompt,
      image: vidSource,
      token: settings.hfToken,
    });
    const item = { id: uid(), type: "video", blob, created: Date.now(), prompt: fullPrompt, originalPrompt: raw };
    if (settings.autoSave) await putItem("gallery", item);
    releaseUrls("vidResults");
    $("vidResults").replaceChildren(resultTile(item, "vidResults"));
    clearInterval(timer);
    setStatus(status, "✅ تم توليد الفيديو" + (settings.autoSave ? " — محفوظ في المعرض" : ""));
  } catch (e) {
    clearInterval(timer);
    setStatus(status, "❌ " + e.message, true);
  } finally {
    btn.disabled = false;
  }
});

// ---------- المعرض ----------

let galFilter = "all";
document.querySelectorAll("#galFilter button").forEach((b) => b.addEventListener("click", () => {
  galFilter = b.dataset.f;
  document.querySelectorAll("#galFilter button").forEach((x) => x.classList.toggle("on", x === b));
  renderGallery();
}));

async function renderGallery() {
  releaseUrls("gallery");
  const items = (await getAll("gallery"))
    .filter((i) => galFilter === "all" || i.type === galFilter)
    .sort((a, b) => b.created - a.created);
  $("galleryGrid").replaceChildren(...items.map((i) => resultTile(i, "gallery", { inGallery: true })));
  $("galleryEmpty").hidden = items.length > 0;
}

// ---------- الإعدادات ----------

$("setToken").value = settings.hfToken;
$("setPollKey").value = settings.pollinationsKey;
$("setTranslate").checked = settings.translate;
$("setAutoSave").checked = settings.autoSave;

$("setSave").addEventListener("click", () => {
  settings = saveSettings({ hfToken: $("setToken").value.trim(), pollinationsKey: $("setPollKey").value.trim() });
  updateBadge();
  toast("تم الحفظ");
});
$("setTest").addEventListener("click", async () => {
  const token = $("setToken").value.trim();
  if (!token) return setStatus($("setStatus"), "أدخل التوكن أولاً.", true);
  setStatus($("setStatus"), "جارٍ الاختبار...");
  try {
    const me = await testToken(token);
    setStatus($("setStatus"), `✅ التوكن يعمل — الحساب: ${me.name}`);
  } catch (e) {
    setStatus($("setStatus"), "❌ " + e.message, true);
  }
});
$("setTranslate").addEventListener("change", (e) => { settings = saveSettings({ translate: e.target.checked }); });
$("setAutoSave").addEventListener("change", (e) => { settings = saveSettings({ autoSave: e.target.checked }); });
$("setFallback").checked = settings.fallback;
$("setFallback").addEventListener("change", (e) => { settings = saveSettings({ fallback: e.target.checked }); });
$("openColab").addEventListener("click", () => openColab().catch((e) => toast(e.message)));
$("setClearGallery").addEventListener("click", async () => {
  if (!confirm("حذف كل الصور والفيديوهات من المعرض؟ لا يمكن التراجع.")) return;
  await clearStore("gallery");
  toast("تم حذف المعرض");
});

// ---------- التشغيل ----------

setVidMode("t2v");
resetCharForm();
refreshCharacters();
updateBadge();

// في نسخة الويب نسجل Service Worker ليعمل كتطبيق قابل للتثبيت على الهاتف
if (!Capacitor.isNativePlatform() && "serviceWorker" in navigator && location.protocol === "https:") {
  navigator.serviceWorker.register("./sw.js").catch(() => {});
}
