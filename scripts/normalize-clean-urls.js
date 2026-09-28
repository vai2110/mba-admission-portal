const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const EXCLUDED = new Set(["404.html"]);

function normalize(value) {
  if (!value || EXCLUDED.has(value)) return value;
  value = value.replace(/(https?:\/\/collegedecoded\.in\/[^"'\s?#<>]+)\.html(?=([?#]|$))/gi, "$1");
  value = value.replace(/(^|["'\s=(])\/?([A-Za-z0-9][A-Za-z0-9-]*)\.html(?=([?#]|["'\s)<>]))/g, "$1$2");
  return value;
}

let changed = 0;
for (const name of fs.readdirSync(ROOT)) {
  if (!name.endsWith(".html") || EXCLUDED.has(name)) continue;
  const file = path.join(ROOT, name);
  const html = fs.readFileSync(file, "utf8");
  const normalized = normalize(html);
  if (normalized !== html) {
    fs.writeFileSync(file, normalized, "utf8");
    changed++;
  }
}
console.log("Clean URL normalization complete. Pages updated:", changed);
