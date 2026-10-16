const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const CSS_TAG = '<link rel="stylesheet" href="/assets/ai-advisor.css?v=1" data-collegedecoded-advisor="css">';
const JS_TAG = '<script defer src="/assets/ai-advisor.js?v=1" data-collegedecoded-advisor="js"></script>';
const EXCLUDED = new Set([
  "404.html",
  "admin.html",
  "cms-admin.html",
  "login.html",
  "preview.html"
]);

// Never publish the advisor on Production while it is still being tested.
// Preview can enable it explicitly with ENABLE_AI_ADVISOR=true.
const ENABLED =
  process.env.ENABLE_AI_ADVISOR === "true" &&
  process.env.VERCEL_ENV !== "production";

let changed = 0;
let scanned = 0;

for (const name of fs.readdirSync(ROOT)) {
  if (!name.toLowerCase().endsWith(".html")) continue;
  const file = path.join(ROOT, name);
  if (!fs.statSync(file).isFile()) continue;
  scanned++;

  const original = fs.readFileSync(file, "utf8");
  let html = original;

  // Always remove previously injected advisor tags first. This matters when
  // Production is disabled after a previous build already wrote them to HTML.
  html = html.replace(/<link\b(?=[^>]*(?:data-collegedecoded-advisor=["']css["']|href=["'][^"']*ai-advisor\.css(?:\?[^"']*)?["']))[^>]*>\s*/gi, "");
  html = html.replace(/<script\b(?=[^>]*(?:data-collegedecoded-advisor=["']js["']|src=["'][^"']*ai-advisor\.js(?:\?[^"']*)?["']))[^>]*>\s*<\/script>\s*/gi, "");

  if (ENABLED && !EXCLUDED.has(name.toLowerCase())) {
    if (/<\/head\s*>/i.test(html)) {
      html = html.replace(/<\/head\s*>/i, CSS_TAG + "\n</head>");
    } else {
      html = CSS_TAG + "\n" + html;
    }

    if (/<\/body\s*>/i.test(html)) {
      html = html.replace(/<\/body\s*>/i, JS_TAG + "\n</body>");
    } else {
      html += "\n" + JS_TAG + "\n";
    }
  }

  if (html !== original) {
    fs.writeFileSync(file, html, "utf8");
    changed++;
  }
}

console.log(
  "AI ADVISOR " + (ENABLED ? "PREVIEW INJECTION" : "DISABLED / TAGS REMOVED") +
  ": scanned " + scanned + " root HTML pages; updated " + changed + "."
);
