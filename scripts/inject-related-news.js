#!/usr/bin/env node
"use strict";
const fs = require("fs");
const path = require("path");

const ROOT = process.cwd();
const SITE = "https://collegedecoded.in";
const NEWS_FILE = path.join(ROOT, "data", "news.json");
const PAGE_RE = /^iim-ahmedabad(?:-[a-z0-9-]+)?\.html$/i;

function esc(value) {
  return String(value == null ? "" : value).replace(/[&<>"']/g, ch => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[ch]));
}
function safeImage(value) {
  try {
    const url = new URL(String(value || ""));
    return url.protocol === "https:" ? url.href : "";
  } catch (_) { return ""; }
}
function dateLabel(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit", month: "short", year: "numeric", timeZone: "Asia/Kolkata"
  }).format(date);
}
function relatedToIIMA(item) {
  if (!item || item.status !== "published" || !item.slug || !item.headline) return false;
  const pages = Array.isArray(item.relatedPages) ? item.relatedPages : [];
  return pages.some(page => {
    try {
      const url = new URL(page.url, SITE);
      return url.hostname === "collegedecoded.in" &&
        (url.pathname === "/iim-ahmedabad" || url.pathname === "/iim-ahmedabad.html" ||
         url.pathname.startsWith("/iim-ahmedabad-"));
    } catch (_) { return false; }
  });
}
const css = `
/* Shared compact IIM Ahmedabad news rail */
.iima-news-rail{min-width:0;align-self:start}
.iima-rail-card{background:#fff;border:1px solid #dce4ee;border-radius:12px;overflow:hidden;box-shadow:0 5px 18px rgba(15,23,42,.045)}
.iima-rail-heading{display:flex;align-items:center;gap:8px;padding:13px 13px 12px;background:#f4f8ff;border-bottom:1px solid #e7edf5}
.iima-rail-heading>span{color:#1764df;font-size:17px;font-weight:900;line-height:1}
.iima-rail-heading h2{margin:0;color:#092653;font-size:13px;line-height:1.3;flex:1}
.iima-rail-heading>a{white-space:nowrap;color:#1764df;font-size:10px;font-weight:800}
.iima-news-item{display:grid;grid-template-columns:78px minmax(0,1fr);gap:10px;padding:11px 12px;border-bottom:1px solid #edf1f5;align-items:start}
.iima-news-item:last-child{border-bottom:0}
.iima-news-thumb{display:block;width:78px;height:66px;object-fit:cover;border-radius:7px;background:#eef3fa}
.iima-news-copy{min-width:0}
.iima-news-category{display:block;margin-bottom:4px;color:#64748b;font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:.35px}
.iima-news-title{display:block;color:#1e293b;font-size:11px;line-height:1.45;font-weight:800;overflow-wrap:anywhere}
.iima-news-title:hover{color:#1764df}
.iima-news-date{margin-top:5px;color:#64748b;font-size:9px}
.iima-news-empty{padding:12px;margin:0;color:#64748b;font-size:11px;line-height:1.5}
.iima-news-rail-inline{margin-top:16px}
@media(max-width:760px){.iima-news-item{grid-template-columns:68px minmax(0,1fr);gap:9px;padding:10px}.iima-news-thumb{width:68px;height:58px}.iima-rail-heading{padding:12px}.iima-news-title{font-size:12px}}
`;

const data = JSON.parse(fs.readFileSync(NEWS_FILE, "utf8"));
const items = Array.isArray(data) ? data : (data.items || []);
const matching = items.filter(relatedToIIMA).sort((a, b) =>
  new Date(b.datePublished || b.dateModified || 0) - new Date(a.datePublished || a.dateModified || 0)
).slice(0, 3);

const cards = matching.length ? matching.map(item => {
  const image = safeImage(item.image);
  const date = dateLabel(item.datePublished || item.dateModified);
  return '<article class="iima-news-item">' +
    (image ? '<a href="/news/' + esc(item.slug) + '" aria-label="' + esc(item.headline) + '">' +
      '<img class="iima-news-thumb" src="' + esc(image) + '" alt="' + esc(item.imageAlt || item.headline) + '" loading="lazy"></a>' : '') +
    '<div class="iima-news-copy">' +
      '<span class="iima-news-category">' + esc(item.category || "News") + '</span>' +
      '<a class="iima-news-title" href="/news/' + esc(item.slug) + '">' + esc(item.headline) + '</a>' +
      (date ? '<div class="iima-news-date">' + esc(date) + '</div>' : '') +
    '</div></article>';
}).join("\n") : '<p class="iima-news-empty">No related news published yet. New IIM Ahmedabad stories will appear here automatically.</p>';

function railMarkup(inline) {
  return '<aside class="iima-news-rail' + (inline ? ' iima-news-rail-inline' : '') + '" aria-label="Latest IIM Ahmedabad news">' +
    '<section class="iima-rail-card"><div class="iima-rail-heading"><span aria-hidden="true">▤</span>' +
    '<h2>Latest IIM Ahmedabad News</h2><a href="/news">View all →</a></div>' +
    '<div class="iima-news-list">' + cards + '</div></section></aside>';
}

const pages = fs.readdirSync(ROOT).filter(name => PAGE_RE.test(name));
let changed = 0;
for (const name of pages) {
  const file = path.join(ROOT, name);
  let html = fs.readFileSync(file, "utf8");
  const before = html;
  const listMarker = /<!-- RELATED_NEWS_START -->[\s\S]*?<!-- RELATED_NEWS_END -->/;
  if (listMarker.test(html)) {
    html = html.replace(listMarker, '<!-- RELATED_NEWS_START -->\n' + cards + '\n<!-- RELATED_NEWS_END -->');
  } else if (!html.includes('aria-label="Latest IIM Ahmedabad news"')) {
    const styleTag = '<style id="iima-related-news-shared">' + css + '</style>';
    if (html.includes("</head>")) html = html.replace("</head>", styleTag + "\n</head>");
    else continue;

    // Keep the module secondary: use the page's existing sidebar/TOC column when available.
    const sidebarPatterns = [
      /(<aside\b[^>]*class=["'][^"']*(?:sidebar|side-card|toc|on-this-page)[^"']*["'][^>]*>[\s\S]*?)(<\/aside>)/i,
      /(<div\b[^>]*class=["'][^"']*(?:sidebar|toc-sidebar|on-this-page|toc-card)[^"']*["'][^>]*>[\s\S]*?)(<\/div>)/i
    ];
    let inserted = false;
    for (const pattern of sidebarPatterns) {
      if (pattern.test(html)) {
        html = html.replace(pattern, (whole, start, close) => start + railMarkup(true) + close);
        inserted = true;
        break;
      }
    }
    // Pages without a distinct sidebar get a compact module after the hero, never a full-width news takeover.
    if (!inserted) {
      const heroClose = /(<(?:section|div)\b[^>]*class=["'][^"']*hero[^"']*["'][^>]*>[\s\S]*?<\/(?:section|div)>)/i;
      if (heroClose.test(html)) html = html.replace(heroClose, "$1\n" + railMarkup(true));
      else html = html.replace("</body>", railMarkup(true) + "\n</body>");
    }
  }
  if (html !== before) {
    fs.writeFileSync(file, html, "utf8");
    changed++;
  }
}
console.log("IIM Ahmedabad related-news module refreshed on " + changed + " page(s); " + matching.length + " related published article(s).");
