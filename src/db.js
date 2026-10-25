// تخزين المعرض والشخصيات في IndexedDB على جهاز المستخدم
const DB_NAME = "aimation";
const DB_VERSION = 1;

let dbPromise;

function openDb() {
  if (!dbPromise) {
    dbPromise = new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onupgradeneeded = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains("gallery")) {
          db.createObjectStore("gallery", { keyPath: "id" }).createIndex("created", "created");
        }
        if (!db.objectStoreNames.contains("characters")) {
          db.createObjectStore("characters", { keyPath: "id" });
        }
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }
  return dbPromise;
}

async function tx(store, mode, fn) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const t = db.transaction(store, mode);
    const result = fn(t.objectStore(store));
    t.oncomplete = () => resolve(result?.result ?? result);
    t.onerror = () => reject(t.error);
    t.onabort = () => reject(t.error);
  });
}

export const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 8);

export const putItem = (store, item) => tx(store, "readwrite", (s) => s.put(item));
export const deleteItem = (store, id) => tx(store, "readwrite", (s) => s.delete(id));
export const clearStore = (store) => tx(store, "readwrite", (s) => s.clear());
export const getItem = (store, id) => tx(store, "readonly", (s) => s.get(id));
export const getAll = (store) => tx(store, "readonly", (s) => s.getAll());
