const KEY = "aimation.settings";

const defaults = {
  hfToken: "",
  pollinationsKey: "",
  translate: true,
  autoSave: true,
  fallback: true,
  imgEngine: "hf-space",
  imgStyle: "realistic",
};

export function loadSettings() {
  try {
    return { ...defaults, ...JSON.parse(localStorage.getItem(KEY) || "{}") };
  } catch {
    return { ...defaults };
  }
}

export function saveSettings(patch) {
  const next = { ...loadSettings(), ...patch };
  try {
    localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    // التخزين غير متاح (وضع التصفح الخاص مثلاً)، نكمل بدون حفظ
  }
  return next;
}
