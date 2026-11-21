const fs = require("fs");
const path = require("path");

const CANONICAL_ORIGIN = "https://collegedecoded.in";

function getAttribute(tag, name) {
  const attrPattern = /([a-z][a-z0-9_-]*)\s*=\s*(?:"([^"]*)"|'([^']*)')/gi;
  for (const match of tag.matchAll(attrPattern)) {
    if (match[1].toLowerCase() === name.toLowerCase()) return match[2] ?? match[3] ?? "";
  }
  return "";
}

function isPublishedCmsProfile(root, slug) {
  const normalizedSlug = String(slug || "").trim();
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(normalizedSlug)) return false;

  const source = path.join(root, "college-cms", "content", normalizedSlug, "overview.html");
  if (!fs.existsSync(source) || !fs.statSync(source).isFile()) return false;

  let html;
  try {
    html = fs.readFileSync(source, "utf8");
  } catch (_) {
    return false;
  }

  const canonicalTags = (html.match(/<link\b[^>]*>/gi) || []).filter(tag =>
    getAttribute(tag, "rel").toLowerCase().split(/\s+/).includes("canonical")
  );
  if (canonicalTags.length !== 1) return false;
  const canonical = getAttribute(canonicalTags[0], "href").trim().replace(/\/+$/, "");
  if (canonical !== CANONICAL_ORIGIN + "/" + normalizedSlug) return false;

  const robotsTags = (html.match(/<meta\b[^>]*>/gi) || []).filter(tag =>
    ["robots", "googlebot"].includes(getAttribute(tag, "name").toLowerCase())
  );
  if (robotsTags.some(tag => getAttribute(tag, "content").toLowerCase().split(/[\s,]+/).includes("noindex"))) {
    return false;
  }
  if (/data-collegedecoded-legacy-redirect\b/i.test(html)) return false;
  if (/\b(?:window\.)?location\.(?:replace|assign)\s*\(/i.test(html)) return false;
  if (/\bwindow\.location\s*=/i.test(html)) return false;
  return true;
}

module.exports = { isPublishedCmsProfile };
