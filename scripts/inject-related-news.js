#!/usr/bin/env node
"use strict";
const fs = require("fs");
const path = require("path");

const ROOT = process.cwd();
const SITE = "https://collegedecoded.in";
const NEWS_FILE = path.join(ROOT, "data", "news.json");
const PAGE_FILE = path.join(ROOT, "iim-ahmedabad.html");

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
        (url.pathname === "/iim-ahmedabad" || url.pathname.startsWith("/iim-ahmedabad-"));
    } catch (_) { return false; }
  });
}

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

let html = fs.readFileSync(PAGE_FILE, "utf8");
const marker = /<!-- RELATED_NEWS_START -->[\s\S]*?<!-- RELATED_NEWS_END -->/;
if (!marker.test(html)) {
  throw new Error("Related-news marker not found in iim-ahmedabad.html; refusing to overwrite page content.");
}
html = html.replace(marker, "<!-- RELATED_NEWS_START -->\n" + cards + "\n<!-- RELATED_NEWS_END -->");
fs.writeFileSync(PAGE_FILE, html, "utf8");
console.log("IIM Ahmedabad related news refreshed: " + matching.length + " published article(s).");
