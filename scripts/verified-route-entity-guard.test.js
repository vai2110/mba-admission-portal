const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { parseCsv } = require("./validate-url-migration-map");

const ROOT = path.resolve(__dirname, "..");
const SAMPLE_FILES = [
  "docs/seo/content-verified-route-sample.csv",
  "docs/seo/content-verified-route-sample-02.csv",
  "docs/seo/content-verified-route-sample-03.csv"
];

function sourceSlugFromUrl(value) {
  const pathname = String(value || "").trim()
    .replace(/^https?:\/\/[^/]+/i, "")
    .split(/[?#]/, 1)[0]
    .replace(/^\/+|\/+$/g, "");
  return pathname.split("/").pop();
}

function expectedTargetForSample(pageType, sourceSlug) {
  if (pageType === "College profile") {
    return "/mba-colleges/" + sourceSlug;
  }
  if (pageType === "Flagship programme") {
    const collegeSlug = sourceSlug.replace(/-(?:mba-pgp|mba)$/i, "");
    return "/mba-colleges/" + collegeSlug + "/mba";
  }
  if (pageType === "Placements") {
    const collegeSlug = sourceSlug.replace(/-placements$/i, "");
    return "/mba-colleges/" + collegeSlug + "/placements";
  }
  if (pageType === "Exam") {
    return "/exams/" + sourceSlug;
  }
  return null;
}

let checked = 0;
let skipped = 0;
for (const file of SAMPLE_FILES) {
  const rows = parseCsv(fs.readFileSync(path.join(ROOT, file), "utf8"));
  assert.ok(rows.length > 1, file + " should contain sample rows");
  const headers = rows[0].map(h => h.trim());
  const idx = Object.fromEntries(headers.map((h, i) => [h, i]));
  for (let i = 1; i < rows.length; i++) {
    const cells = rows[i];
    if (cells.every(cell => String(cell || "").trim() === "")) continue;
    const pageType = String(cells[idx.page_type] || "").trim();
    const source = String(cells[idx.current_url] || "").trim();
    const target = String(cells[idx.proposed_target] || "").trim();
    if (!target) {
      skipped++;
      continue;
    }
    const sourceSlug = sourceSlugFromUrl(source);
    const expected = expectedTargetForSample(pageType, sourceSlug);
    if (!expected) {
      skipped++;
      continue;
    }
    assert.strictEqual(target, expected, file + " row " + (i + 1) + " route/entity mismatch: " + source + " -> " + target + " (expected " + expected + ")");
    checked++;
  }
}
assert.ok(checked > 0, "At least one entity-specific route must be checked");
console.log("Verified route entity guard passed: " + checked + " profile/programme/placement/exam routes aligned; " + skipped + " hub or review rows left for manual taxonomy QA.");
