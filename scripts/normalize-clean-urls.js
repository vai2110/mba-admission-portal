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


function parseCsvLine(line) {
  const values = [];
  let value = "";
  let quoted = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (quoted && line[i + 1] === '"') { value += '"'; i++; }
      else quoted = !quoted;
    } else if (ch === "," && !quoted) {
      values.push(value);
      value = "";
    } else {
      value += ch;
    }
  }
  values.push(value);
  return values;
}

function buildCrawlableCollegeDirectory() {
  const csvPath = path.join(ROOT, "colleges.csv");
  const pagePath = path.join(ROOT, "colleges.html");
  if (!fs.existsSync(csvPath) || !fs.existsSync(pagePath)) return false;

  const lines = fs.readFileSync(csvPath, "utf8").replace(/^\uFEFF/, "").trim().split(/\r?\n/);
  if (lines.length < 2) return false;

  const headers = parseCsvLine(lines[0]).map(x => x.trim());
  const rows = lines.slice(1).map(parseCsvLine).filter(row => row.some(Boolean));
  const idx = Object.fromEntries(headers.map((h, i) => [h, i]));

  const esc = value => String(value ?? "").replace(/[&<>"']/g, ch => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[ch]));

  const cards = rows.map(row => {
    const name = row[idx.college_name] || "College";
    const city = row[idx.city] || "";
    const state = row[idx.state] || "";
    const rank = row[idx.nirf_management_rank_2025] || "—";
    const slug = row[idx.profile_slug] || "";
    const href = slug ? "/" + slug : "#";
    return '<article class="college-card">' +
      '<div class="rank-badge">NIRF 2025 Management: #' + esc(rank) + '</div>' +
      '<div class="college-name"><a href="' + esc(href) + '">' + esc(name) + '</a></div>' +
      '<div class="location">📍 ' + esc(city) + ', ' + esc(state) + '</div>' +
      '<a href="' + esc(href) + '" class="college-profile-button">View College →</a>' +
      '</article>';
  }).join("\n");

  const html = fs.readFileSync(pagePath, "utf8");
  const marker = "<!-- CRAWLABLE_COLLEGE_DIRECTORY -->";
  if (!html.includes(marker)) return false;
  const replacement = marker + "\n" + cards;
  const updated = html.replace(marker, replacement);
  if (updated === html) return false;
  fs.writeFileSync(pagePath, updated, "utf8");
  return true;
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
const directoryChanged = buildCrawlableCollegeDirectory();
console.log("Clean URL normalization complete. Pages updated:", changed, "Crawlable college directory:", directoryChanged);
