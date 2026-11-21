const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { parseCsv, normalizeInternalUrl } = require("./validate-url-migration-map");

const ROOT = path.resolve(__dirname, "..");
const SAMPLE_FILES = [
  "docs/seo/content-verified-route-sample.csv",
  "docs/seo/content-verified-route-sample-02.csv",
  "docs/seo/content-verified-route-sample-03.csv"
];

const seenTargets = new Map();
let candidateCount = 0;
let reviewCount = 0;

for (const file of SAMPLE_FILES) {
  const rows = parseCsv(fs.readFileSync(path.join(ROOT, file), "utf8"));
  assert.ok(rows.length > 1, file + " should include reviewable route samples");
  const headers = rows[0].map(h => h.trim());
  const targetIndex = headers.indexOf("proposed_target");
  const decisionIndex = headers.indexOf("decision");
  const sourceIndex = headers.indexOf("current_url");
  assert.ok(targetIndex >= 0 && decisionIndex >= 0 && sourceIndex >= 0, file + " is missing required review columns");

  for (let i = 1; i < rows.length; i++) {
    const cells = rows[i];
    if (cells.every(cell => String(cell || "").trim() === "")) continue;
    assert.strictEqual(cells.length, headers.length, file + " row " + (i + 1) + " column count mismatch");
    const source = String(cells[sourceIndex] || "").trim();
    const target = String(cells[targetIndex] || "").trim();
    const decision = String(cells[decisionIndex] || "").trim();
    assert.ok(source, file + " row " + (i + 1) + " needs a source URL");
    assert.ok(decision, file + " row " + (i + 1) + " needs a decision");
    if (!target) {
      reviewCount++;
      assert.ok(/review|keep/i.test(decision), file + " row " + (i + 1) + " blank target must be an explicit review/keep decision");
      continue;
    }
    candidateCount++;
    assert.strictEqual(normalizeInternalUrl(target), target, file + " row " + (i + 1) + " target must be an internal slashless route");
    assert.ok(/^\/(?:mba-colleges|exams)\//.test(target), file + " row " + (i + 1) + " target outside the proposed architecture");
    assert.ok(!seenTargets.has(target), "Duplicate proposed route " + target + " in " + file + " and " + seenTargets.get(target));
    seenTargets.set(target, file);
  }
}

assert.ok(candidateCount > 0, "Route samples must contain proposed destinations");
console.log("Verified route sample checks passed: " + candidateCount + " slashless unique targets; " + reviewCount + " rows remain review-only.");
