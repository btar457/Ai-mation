import { Capacitor } from "@capacitor/core";
import { Filesystem, Directory } from "@capacitor/filesystem";
import { Share } from "@capacitor/share";

const isNative = () => Capacitor.isNativePlatform();

const extFor = (blob) => (blob.type.split("/")[1] || "bin").replace("jpeg", "jpg").split(";")[0];

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result).split(",")[1]);
    r.onerror = () => reject(r.error);
    r.readAsDataURL(blob);
  });
}

async function writeNative(blob, name, directory) {
  const res = await Filesystem.writeFile({
    path: `Ai-mation/${name}`,
    data: await blobToBase64(blob),
    directory,
    recursive: true,
  });
  return res.uri;
}

// حفظ الملف على الجهاز
export async function downloadBlob(blob, baseName) {
  const name = `${baseName}.${extFor(blob)}`;
  if (isNative()) {
    await writeNative(blob, name, Directory.Documents);
    return `تم الحفظ في Documents/Ai-mation/${name}`;
  }
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement("a"), { href: url, download: name });
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
  return "تم التنزيل";
}

// مشاركة الملف إلى واتساب، تيك توك، إنستغرام...
export async function shareBlob(blob, baseName, text) {
  const name = `${baseName}.${extFor(blob)}`;
  if (isNative()) {
    const uri = await writeNative(blob, name, Directory.Cache);
    await Share.share({ files: [uri], text });
    return;
  }
  const file = new File([blob], name, { type: blob.type });
  if (navigator.canShare?.({ files: [file] })) {
    await navigator.share({ files: [file], text });
    return;
  }
  await downloadBlob(blob, baseName);
}
