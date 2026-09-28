const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const EXCLUDED = new Set(["404.html"]);

function cleanUrlForFile(name) {
  return name === "index.html" ? "/" : "/" + name.replace(/\.html$/i, "");
}

function isExternalUrl(href) {
  return /^(?:https?:)?\/\//i.test(href);
}

function normalizeHref(href, sourceName) {
  if (!href || href.startsWith("#") || /^(?:mailto|tel|javascript|data):/i.test(href)) return href;

  if (isExternalUrl(href)) {
    return href.replace(
      /(https?:\/\/collegedecoded\.in\/[^"'\s?#<>]+)\.html(?=([?#]|$))/gi,
      "$1"
    );
  }

  const raw = href.trim();
  const hashIndex = raw.indexOf("#");
  const queryIndex = raw.indexOf("?");
  const cut = Math.min(...[hashIndex, queryIndex].filter(x => x >= 0), raw.length);
  const pathPart = raw.slice(0, cut);
  const suffix = raw.slice(cut);
  let target;

  if (!pathPart) return href;

  if (pathPart.startsWith("/")) {
    target = pathPart.replace(/^\/+/, "");
  } else {
    const resolved = path.posix.normalize(
      path.posix.join(path.posix.dirname(sourceName), pathPart)
    );
    target = resolved.replace(/^\.\//, "");
  }

  if (target.endsWith(".html")) target = target.slice(0, -5);
  if (target === "index") target = "";
  return "/" + target + suffix;
}

function addOrReplaceCanonical(html, sourceName) {
  const canonical = "https://collegedecoded.in" + cleanUrlForFile(sourceName);
  const tag = '<link rel="canonical" href="' + canonical + '">';
  const canonicalRe = /<link\b[^>]*rel=["'][^"']*canonical[^"']*["'][^>]*>/i;
  const canonicalRe2 = /<link\b[^>]*href=["'][^"']+["'][^>]*rel=["'][^"']*canonical[^"']*["'][^>]*>/i;

  if (canonicalRe.test(html)) return html.replace(canonicalRe, tag);
  if (canonicalRe2.test(html)) return html.replace(canonicalRe2, tag);
  return html.replace(/<head\b[^>]*>/i, m => m + "\n" + tag);
}

function internalTargetExists(href, sourceName) {
  if (!href || href.startsWith("#") || /^(?:mailto|tel|javascript|data):/i.test(href)) return true;

  if (isExternalUrl(href)) {
    const isOwnDomain = /^(?:https?:)?\/\/(?:www\.)?collegedecoded\.in\b/i.test(href);
    if (!isOwnDomain) return true;
    return internalTargetExists(
      href.replace(/^https?:\/\/(?:www\.)?collegedecoded\.in/i, ""),
      sourceName
    );
  }

  const raw = href.split(/[?#]/, 1)[0];
  if (!raw || raw === "/") return true;

  let target = raw.startsWith("/")
    ? raw.slice(1)
    : path.posix.normalize(path.posix.join(path.posix.dirname(sourceName), raw));

  target = target.replace(/^\.\//, "").replace(/\/$/, "");

  if (target.endsWith(".html")) return fs.existsSync(path.join(ROOT, target));

  return fs.existsSync(path.join(ROOT, target + ".html")) ||
    fs.existsSync(path.join(ROOT, target, "index.html"));
}

function normalizeFile(html, sourceName) {
  let value = html;

  // Repair malformed legacy redirect wrappers before HTML/SEO parsing.
  value = value.replace(
    /<script data-collegedecoded-legacy-redirect>\s*<script>\s*/gi,
    '<script data-collegedecoded-legacy-redirect>\\n'
  );
  value = value.replace(/<\\/script>\s*<\\/script>/gi, '<\\/script>');

  value = value.replace(/(<a\b[^>]*\bhref=["'])([^"']+)(["'])/gi, (m, pre, href, post) => {
    const normalized = normalizeHref(href, sourceName);

    if (!internalTargetExists(normalized, sourceName)) {
      return m.replace(/\s*href=["'][^"']+["']/i, "");
    }

    return pre + normalized + post;
  });

  value = addOrReplaceCanonical(value, sourceName);
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

  const cards = rows.filter(row => {
    const slug = row[idx.profile_slug] || "";
    return slug && fs.existsSync(path.join(ROOT, slug + ".html"));
  }).map(row => {
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
  const startMarker = "<!-- CRAWLABLE_COLLEGE_DIRECTORY -->";
  const endMarker = "<!-- /CRAWLABLE_COLLEGE_DIRECTORY -->";
  const start = html.indexOf(startMarker);
  const end = html.indexOf(endMarker);
  if (start === -1 || end === -1 || end < start) return false;
  const replacement = startMarker + "\n" + cards + "\n" + endMarker;
  const updated = html.slice(0, start) + replacement + html.slice(end + endMarker.length);
  if (updated === html) return false;
  fs.writeFileSync(pagePath, updated, "utf8");
  return true;
}


function buildRelatedCollegeLinks() {
  const csvPath = path.join(ROOT, "colleges.csv");
  if (!fs.existsSync(csvPath)) return 0;
  const lines = fs.readFileSync(csvPath, "utf8").replace(/^\uFEFF/, "").trim().split(/\r?\n/);
  if (lines.length < 2) return 0;
  const headers = parseCsvLine(lines[0]).map(x => x.trim());
  const rows = lines.slice(1).map(parseCsvLine).filter(row => row.some(Boolean));
  const idx = Object.fromEntries(headers.map((h, i) => [h, i]));
  const esc = value => String(value ?? "").replace(/[&<>"']/g, ch => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[ch]));

  let changed = 0;
  for (const row of rows) {
    const slug = row[idx.profile_slug] || "";
    const state = row[idx.state] || "";
    const name = row[idx.college_name] || "College";
    if (!slug || !state) continue;
    const pagePath = path.join(ROOT, slug + ".html");
    if (!fs.existsSync(pagePath)) continue;

    let html = fs.readFileSync(pagePath, "utf8");
    const startMarker = "<!-- RELATED_COLLEGES_INTERNAL_LINKS -->";
    const endMarker = "<!-- /RELATED_COLLEGES_INTERNAL_LINKS -->";
    if (html.includes(startMarker)) continue;

    const related = rows
      .filter(other => (other[idx.state] || "") === state && (other[idx.profile_slug] || "") && (other[idx.profile_slug] || "") !== slug)
      .sort((a,b) => Number(a[idx.nirf_management_rank_2025] || 9999) - Number(b[idx.nirf_management_rank_2025] || 9999))
      .filter(other => fs.existsSync(path.join(ROOT, (other[idx.profile_slug] || "") + ".html")))
      .slice(0, 4);

    if (!related.length) continue;

    const links = related.map(other => {
      const otherSlug = other[idx.profile_slug];
      return '<li><a href="/' + esc(otherSlug) + '">' + esc(other[idx.college_name] || "College") + '</a></li>';
    }).join("");

    const block = startMarker +
      '<section class="related-colleges-internal-links" aria-labelledby="related-colleges-title" style="margin:32px auto;padding:22px;max-width:1100px;border:1px solid #dbe7f5;border-radius:14px;background:#f8fbff">' +
      '<h2 id="related-colleges-title" style="margin:0 0 8px;color:#123d85;font-size:22px">Related MBA Colleges in ' + esc(state) + '</h2>' +
      '<p style="margin:0 0 12px;color:#5d718d;font-size:13px">Explore other MBA colleges from the same state.</p>' +
      '<ul style="display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:8px 20px;margin:0;padding-left:20px">' + links + '</ul>' +
      '<p style="margin:14px 0 0"><a href="/colleges" style="font-weight:800;color:#0868f5">View all MBA colleges →</a></p>' +
      '</section>' +
      endMarker;

    const bodyIndex = html.toLowerCase().lastIndexOf("</body>");
    if (bodyIndex === -1) continue;
    html = html.slice(0, bodyIndex) + block + "\n" + html.slice(bodyIndex);
    fs.writeFileSync(pagePath, html, "utf8");
    changed++;
  }
  return changed;
}

let changed = 0;

for (const name of fs.readdirSync(ROOT)) {
  if (!name.endsWith(".html") || EXCLUDED.has(name)) continue;
  const file = path.join(ROOT, name);
  const html = fs.readFileSync(file, "utf8");
  const normalized = normalizeFile(html, name);
  if (normalized !== html) {
    fs.writeFileSync(file, normalized, "utf8");
    changed++;
  }
}
const directoryChanged = buildCrawlableCollegeDirectory();
const relatedLinksChanged = buildRelatedCollegeLinks();
console.log("Clean URL normalization complete. Pages updated:", changed, "Crawlable college directory:", directoryChanged, "Related college link blocks:", relatedLinksChanged);
