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

if (process.env.ENABLE_AI_ADVISOR !== "true") {
  console.log("AI ADVISOR INJECTION SKIPPED: set ENABLE_AI_ADVISOR=true for this deployment.");
  process.exit(0);
}

let changed = 0;
let scanned = 0;

for (const name of fs.readdirSync(ROOT)) {
  if (!name.toLowerCase().endsWith(".html") || EXCLUDED.has(name.toLowerCase())) continue;
  const file = path.join(ROOT, name);
  if (!fs.statSync(file).isFile()) continue;
  scanned++;
  let html = fs.readFileSync(file, "utf8");
  if (html.includes("data-collegedecoded-advisor=\"js\"")) continue;

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
  fs.writeFileSync(file, html, "utf8");
  changed++;
}

console.log("AI ADVISOR INJECTION: scanned " + scanned + " root HTML pages; updated " + changed + ".");
