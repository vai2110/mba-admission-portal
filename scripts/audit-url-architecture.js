#!/usr/bin/env node
/**
 * Read-only URL architecture audit.
 * Scans public HTML files recursively and checks route/canonical/link consistency.
 * Intentionally excludes CMS source content and hidden/build dependency directories.
 * This is an audit tool only; it does not rewrite URLs or files.
 */
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const IGNORE_DIRS = new Set([".git", ".vercel", "node_modules", "college-cms"]);

function routeFromHtmlPath(relativePath) {
  const normalized = relativePath.split(path.sep).join("/");
  if (normalized === "index.html") return "/";
  if (normalized.endsWith("/index.html")) return "/" + normalized.slice(0, -"index.html".length).replace(/\/$/, "");
  return "/" + normalized.replace(/\.html$/i, "");
}

function extractCanonical(html) {
  const tags = html.match(/<link\b[^>]*>/gi) || [];
  for (const tag of tags) {
    if (!/\brel\s*=\s*["'][^"']*canonical[^"']*["']/i.test(tag)) continue;
    const match = tag.match(/\bhref\s*=\s*["']([^"']+)["']/i);
    if (match) return match[1];
  }
  return null;
}

function collectHtmlFiles(dir, root = dir, files = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith(".") || IGNORE_DIRS.has(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) collectHtmlFiles(full, root, files);
    else if (entry.isFile() && entry.name.toLowerCase().endsWith(".html")) {
      files.push(path.relative(root, full));
    }
  }
  return files;
}

function resolveLocalHref(href, sourceRelative) {
  if (!href || href.startsWith("#") || /^(mailto:|tel:|javascript:|data:)/i.test(href)) return null;
  let pathname = href;
  if (/^(https?:)?\/\//i.test(href)) {
    let parsed;
    try { parsed = new URL(href); } catch (_) { return null; }
    if (!/(^|\.)collegedecoded\.in$/i.test(parsed.hostname)) return null;
    pathname = parsed.pathname;
  }
  pathname = pathname.split(/[?#]/, 1)[0];
  if (!pathname) return null;
  const base = pathname.startsWith("/")
    ? pathname.slice(1)
    : path.posix.normalize(path.posix.join(path.posix.dirname(sourceRelative.split(path.sep).join("/")), pathname));
  return base.replace(/^\.\/?/, "").replace(/\/$/, "");
}

function findTargetFile(root, target) {
  // An empty target is the site root (e.g. href="/"); resolve it to index.html.
  // Non-HTML file paths are static assets and must be checked as exact files,
  // rather than being incorrectly treated as route directories.
  let cleanTarget = String(target || "").split(String.fromCharCode(92)).join("/");
  while (cleanTarget.endsWith("/")) cleanTarget = cleanTarget.slice(0, -1);
  const hasNonHtmlExtension = Boolean(path.posix.extname(cleanTarget)) && !cleanTarget.toLowerCase().endsWith(".html");
  const candidates = !cleanTarget
    ? ["index.html"]
    : hasNonHtmlExtension
      ? [cleanTarget]
      : cleanTarget.toLowerCase().endsWith(".html")
        ? [cleanTarget]
        : [cleanTarget + ".html", path.join(cleanTarget, "index.html")];

  const rootPath = path.resolve(root);
  for (const candidate of candidates) {
    const absolute = path.resolve(rootPath, candidate);
    // Do not allow a URL path traversal to count a file outside the site root.
    if (absolute !== rootPath && !absolute.startsWith(rootPath + path.sep)) continue;
    if (fs.existsSync(absolute) && fs.statSync(absolute).isFile()) return candidate;
  }
  return null;
}

function getTagAttribute(tag, attribute) {
  const pattern = new RegExp("(?:^|\\s)" + attribute + "\\s*=\\s*(?:[\"']([^\"']*)[\"']|([^\\s>]+))", "i");
  const match = tag.match(pattern);
  return match ? (match[1] !== undefined ? match[1] : match[2]) : null;
}

function extractAssetReferences(html) {
  const references = [];
  const assetTagNames = new Set(["img", "script", "source", "video", "audio", "iframe", "embed", "track"]);
  const tags = html.match(/<(img|script|source|video|audio|iframe|embed|track|object|link)\b[^>]*>/gi) || [];
  const assetLinkRels = new Set(["stylesheet", "icon", "shortcut icon", "apple-touch-icon", "manifest", "preload", "prefetch", "modulepreload"]);

  for (const tag of tags) {
    const tagName = (tag.match(/^<([a-z0-9]+)/i) || [])[1]?.toLowerCase();
    if (!tagName) continue;
    const add = (attribute, value) => {
      if (!value || /^(?:data:|#|mailto:|tel:|javascript:)/i.test(value)) return;
      references.push({ tagName, attribute, value });
    };

    if (assetTagNames.has(tagName)) {
      add("src", getTagAttribute(tag, "src"));
      if (tagName === "video") add("poster", getTagAttribute(tag, "poster"));
      if (tagName === "object") add("data", getTagAttribute(tag, "data"));
    }
    if (tagName === "img" || tagName === "source") {
      const srcset = getTagAttribute(tag, "srcset");
      if (srcset && !/(?:^|,)\s*data:/i.test(srcset) {
        for (const candidate of srcset.split(",")) {
          const parts = candidate.trim().split(/\s+/);
          if (parts.length >= 2) add("srcset", parts[0]);
        }
      }
    }
    if (tagName === "link") {
      const rel = (getTagAttribute(tag, "rel") || "").toLowerCase().split(/\s+/);
      if (rel.some(token => assetLinkRels.has(token))) add("href", getTagAttribute(tag, "href"));
    }
  }
  return references;
}

function audit(root = ROOT) {
  const files = collectHtmlFiles(root);
  const canonicalGroups = new Map();
  const issues = [];
  for (const relative of files) {
    const full = path.join(root, relative);
    const html = fs.readFileSync(full, "utf8");
    const canonical = extractCanonical(html);
    if (!canonical) issues.push({ type: "missing-canonical", file: relative });
    else {
      canonicalGroups.set(canonical, [...(canonicalGroups.get(canonical) || []), relative]);
      const expected = "https://collegedecoded.in" + routeFromHtmlPath(relative);
      if (canonical !== expected) issues.push({ type: "canonical-route-mismatch", file: relative, canonical, expected });
    }
    const anchors = html.match(/<a\b[^>]*\bhref\s*=\s*["']([^"']+)["'][^>]*>/gi) || [];
    for (const anchor of anchors) {
      const match = anchor.match(/\bhref\s*=\s*["']([^"']+)["']/i);
      if (!match) continue;
      const target = resolveLocalHref(match[1], relative);
      if (target === null) continue;
      if (!findTargetFile(root, target)) issues.push({ type: "broken-local-link", file: relative, href: match[1], resolvedTarget: target });
    }
    for (const reference of extractAssetReferences(html)) {
      const target = resolveLocalHref(reference.value, relative);
      if (target === null) continue;
      if (!findTargetFile(root, target)) {
        issues.push({ type: "broken-local-asset", file: relative, tag: reference.tagName, attribute: reference.attribute, href: reference.value, resolvedTarget: target });
      }
    }
  }
  for (const [canonical, sources] of canonicalGroups) {
    if (sources.length > 1) issues.push({ type: "duplicate-canonical", canonical, files: sources });
  }
  const counts = issues.reduce((acc, issue) => {
    acc[issue.type] = (acc[issue.type] || 0) + 1;
    return acc;
  }, {});
  return { root, htmlFilesScanned: files.length, issueCount: issues.length, counts, issues };
}

if (require.main === module) {
  const result = audit();
  console.log(JSON.stringify(result, null, 2));
  if (result.issueCount) process.exitCode = 1;
}

module.exports = { routeFromHtmlPath, extractCanonical, collectHtmlFiles, resolveLocalHref, findTargetFile, extractAssetReferences, audit };
