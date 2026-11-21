const assert = require("assert");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const cluster = [
  { file: "mba-colleges/iim-ahmedabad/index.html", source: "iim-ahmedabad.html", canonical: "https://collegedecoded.in/mba-colleges/iim-ahmedabad" },
  { file: "mba-colleges/iim-ahmedabad/mba/index.html", source: "iim-ahmedabad-mba-pgp.html", canonical: "https://collegedecoded.in/mba-colleges/iim-ahmedabad/mba" },
  { file: "mba-colleges/iim-ahmedabad/placements/index.html", source: "iim-ahmedabad-placements.html", canonical: "https://collegedecoded.in/mba-colleges/iim-ahmedabad/placements" },
  { file: "mba-colleges/iim-ahmedabad/fees/index.html", source: "iim-ahmedabad-courses-fees.html", canonical: "https://collegedecoded.in/mba-colleges/iim-ahmedabad/fees" }
];
const expectedRoutes = cluster.map(p => new URL(p.canonical).pathname);
const stripTags = value => value.replace(/<[^>]*>/g, " ").replace(/&amp;/gi, "&").replace(/&nbsp;/gi, " ").replace(/&#39;/gi, "'").replace(/&quot;/gi, '"').replace(/\s+/g, " ").trim();
const attr = (tag, name) => {
  const m = tag.match(new RegExp("\\b" + name + "\\s*=\\s*([\"'])(.*?)\\1", "i"));
  return m ? m[2] : "";
};
function canonicalTags(html) {
  return (html.match(/<link\b[^>]*>/gi) || []).filter(tag => /\brel\s*=\s*["'][^"']*canonical[^"']*["']/i.test(tag));
}
function extractTitle(html) {
  return stripTags((html.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i) || [,""])[1]);
}
function extractH1(html) {
  return stripTags((html.match(/<h1\b[^>]*>([\s\S]*?)<\/h1>/i) || [,""])[1]);
}
const oldPaths = new Set([
  "/iim-ahmedabad", "/iim-ahmedabad.html",
  "/iim-ahmedabad-mba-pgp", "/iim-ahmedabad-mba-pgp.html",
  "/iim-ahmedabad-placements", "/iim-ahmedabad-placements.html",
  "/iim-ahmedabad-courses-fees", "/iim-ahmedabad-courses-fees.html",
  "/iim-ahmedabad/courses-fees", "/iim-ahmedabad/courses-fees.html"
]);
for (const page of cluster) {
  const previewPath = path.join(ROOT, page.file);
  const sourcePath = path.join(ROOT, page.source);
  assert.ok(fs.existsSync(previewPath), "Missing preview route: " + page.file);
  assert.ok(fs.existsSync(sourcePath), "Missing source page: " + page.source);
  const html = fs.readFileSync(previewPath, "utf8");
  const source = fs.readFileSync(sourcePath, "utf8");
  const canonicals = canonicalTags(html);
  assert.strictEqual(canonicals.length, 1, page.file + " must contain exactly one canonical");
  assert.strictEqual(attr(canonicals[0], "href"), page.canonical, page.file + " canonical must match route");
  const robots = (html.match(/<meta\b[^>]*>/gi) || []).find(tag => attr(tag, "name").toLowerCase() === "robots");
  assert.ok(robots && /noindex/i.test(attr(robots, "content")), page.file + " must remain noindex");
  const ogTag = (html.match(/<meta\b[^>]*property=["']og:url["'][^>]*>/i) || [""])[0];
  assert.strictEqual(attr(ogTag, "content"), page.canonical, page.file + " OG URL mismatch");
  assert.strictEqual(extractTitle(html), extractTitle(source), page.file + " title/content source drift");
  assert.strictEqual(extractH1(html), extractH1(source), page.file + " H1/content source drift");
  const visibleText = stripTags(html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, " ").replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, " "));
  assert.ok(visibleText.split(/\s+/).length >= 700, page.file + " should retain substantial source content");
  const nav = (html.match(/<nav class=["']cd-url-preview["'][\s\S]*?<\/nav>/i) || [""])[0];
  const navHrefs = [...nav.matchAll(/href=["']([^"']+)["']/gi)].map(m => m[1]);
  assert.deepStrictEqual([...new Set(navHrefs)].sort(), [...expectedRoutes].sort(), page.file + " cluster navigation mismatch");
  const hrefs = [...html.matchAll(/\bhref\s*=\s*(["'])(.*?)\1/gi)].map(m => m[2]);
  for (const href of hrefs) {
    try {
      const url = new URL(href, "https://collegedecoded.in");
      if (url.hostname === "collegedecoded.in" || url.hostname === "www.collegedecoded.in") {
        assert.ok(!oldPaths.has(url.pathname), page.file + " has an unreplaced flat IIM route in href: " + href);
      }
    } catch (_) { /* malformed/non-URL hrefs are covered by the broader HTML gate */ }
  }
}
const sitemap = fs.readFileSync(path.join(ROOT, "sitemap.xml"), "utf8");
for (const page of cluster) assert.ok(!sitemap.includes(page.canonical), "Noindex preview route must stay out of sitemap: " + page.canonical);
console.log("IIM Ahmedabad URL migration preview route checks passed.");
