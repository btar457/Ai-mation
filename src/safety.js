// فلتر محتوى بسيط قبل إرسال الوصف: يمنع المحتوى الجنسي الصريح
// ويمنع أي وصف يجمع بين القاصرين وإيحاءات جنسية أو رومانسية.

const EXPLICIT = [
  "nude", "naked", "nsfw", "porn", "sex", "sexual", "erotic", "hentai", "topless",
  "nipple", "genital", "penis", "vagina", "orgasm", "fetish", "bdsm",
  "undress", "stripping", "explicit",
  "عاري", "عارية", "عراة", "جنس", "جنسي", "جنسية", "إباحي", "اباحي", "إباحية", "اباحية",
  "بورن", "سكس", "نيك", "مثير جنسيا", "بدون ملابس", "بلا ملابس", "صدر عاري", "شهوة", "شهواني",
];

const MINOR = [
  "child", "kid", "minor", "underage", "teen", "teenager", "loli", "shota", "schoolgirl",
  "schoolboy", "young girl", "young boy", "baby", "toddler",
  "طفل", "طفلة", "أطفال", "اطفال", "قاصر", "قاصرة", "مراهق", "مراهقة", "صغيرة", "بنت صغيرة", "ولد صغير", "تلميذة",
];

const SUGGESTIVE = [
  "sexy", "seductive", "sensual", "romantic", "kiss", "bikini", "swimsuit", "lingerie", "bed", "flirt",
  "مثير", "مثيرة", "مغري", "مغرية", "رومانسي", "رومانسية", "قبلة", "بكيني", "ملابس سباحة", "سرير", "ملابس داخلية",
];

const norm = (s) => ` ${s.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ")} `;
const has = (text, words) => words.some((w) => text.includes(` ${w.toLowerCase()} `) || text.includes(` ${w.toLowerCase()}s `));

export function checkPrompt(...parts) {
  const text = norm(parts.filter(Boolean).join(" "));
  if (has(text, EXPLICIT)) {
    return "الوصف يحتوي على محتوى جنسي صريح، وهذا غير مدعوم في التطبيق. عدّل الوصف وحاول مرة أخرى.";
  }
  if (has(text, MINOR) && has(text, SUGGESTIVE)) {
    return "لا يمكن الجمع بين شخصيات صغيرة السن وأي إيحاءات رومانسية أو مثيرة.";
  }
  return null;
}
