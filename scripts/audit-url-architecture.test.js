const assert = require("assert");
const path = require("path");
const { routeFromHtmlPath, extractCanonical, resolveLocalHref, findTargetFile, audit } = require("./audit-url-architecture");
const fs = require("fs");

assert.strictEqual(routeFromHtmlPath("index.html"), "/");
assert.strictEqual(routeFromHtmlPath("iim-ahmedabad.html"), "/iim-ahmedabad");
assert.strictEqual(routeFromHtmlPath(path.join("mba-colleges", "iim-ahmedabad", "index.html")), "/mba-colleges/iim-ahmedabad");
assert.strictEqual(routeFromHtmlPath(path.join("mba-colleges", "iim-ahmedabad", "placements.html")), "/mba-colleges/iim-ahmedabad/placements");

assert.strictEqual(extractCanonical('<head><link href="https://collegedecoded.in/x" rel="canonical"></head>'), "https://collegedecoded.in/x");
assert.strictEqual(extractCanonical('<head><link rel="stylesheet" href="/style.css"></head>'), null);

assert.strictEqual(resolveLocalHref("../fees.html?year=2026#top", "mba-colleges/iim-ahmedabad/mba/index.html"), "mba-colleges/iim-ahmedabad/fees.html");
assert.strictEqual(resolveLocalHref("/mba-colleges/iim-ahmedabad/placements", "iim-ahmedabad.html"), "mba-colleges/iim-ahmedabad/placements");
assert.strictEqual(resolveLocalHref("https://collegedecoded.in/mba-colleges/iim-ahmedabad/fees?x=1", "index.html"), "mba-colleges/iim-ahmedabad/fees");
assert.strictEqual(resolveLocalHref("https://example.com/page", "index.html"), null);
assert.strictEqual(resolveLocalHref("#faq", "index.html"), null);

const fixture = path.join(__dirname, "__url-audit-test-fixture__");
fs.mkdirSync(path.join(fixture, "nested"), { recursive: true });
fs.mkdirSync(path.join(fixture, "assets"), { recursive: true });
fs.writeFileSync(path.join(fixture, "index.html"), "home fixture");
fs.writeFileSync(path.join(fixture, "nested", "index.html"), "fixture");
fs.writeFileSync(path.join(fixture, "assets", "brochure.pdf"), "PDF fixture");
assert.strictEqual(findTargetFile(fixture, ""), "index.html", "root href must resolve to the site index");
assert.strictEqual(findTargetFile(fixture, "nested"), path.join("nested", "index.html"));
assert.strictEqual(findTargetFile(fixture, "assets/brochure.pdf"), path.join("assets", "brochure.pdf"), "static asset links must resolve exact files");
assert.strictEqual(findTargetFile(fixture, "assets/missing.pdf"), null, "missing static assets must be reported");
assert.strictEqual(findTargetFile(fixture, "../outside.pdf"), null, "path traversal must not resolve outside the site root");
fs.rmSync(fixture, { recursive: true, force: true });


// Integration-style audit fixture: verifies canonical route mismatches, duplicate canonicals,
// and missing local links are surfaced together for nested routes.
const auditFixture = path.join(__dirname, "__url-audit-full-fixture__");
fs.mkdirSync(path.join(auditFixture, "mba-colleges", "iima"), { recursive: true });
fs.mkdirSync(path.join(auditFixture, "assets"), { recursive: true });
fs.writeFileSync(path.join(auditFixture, "assets", "hero.jpg"), "Image fixture");
fs.writeFileSync(path.join(auditFixture, "assets", "app.js"), "Script fixture");
fs.writeFileSync(path.join(auditFixture, "assets", "styles.css"), "CSS fixture");
fs.writeFileSync(path.join(auditFixture, "assets", "brochure.pdf"), "PDF fixture");
fs.writeFileSync(path.join(auditFixture, "index.html"), '<link rel="canonical" href="https://collegedecoded.in/"><link rel="stylesheet" href="/assets/styles.css"><script src="/assets/app.js"></script><script src="/assets/missing.js"></script><img src="/assets/hero.jpg" srcset="/assets/hero.jpg 1x, /assets/missing-hero.jpg 2x"><a href="/mba-colleges/iima">Profile</a><a href="/">Home</a><a href="/assets/brochure.pdf">PDF</a><a href="/assets/missing.pdf">Missing PDF</a>');
fs.writeFileSync(path.join(auditFixture, "mba-colleges", "iima", "index.html"), '<link rel="canonical" href="https://collegedecoded.in/mba-colleges/iima"><img src="../../assets/hero.jpg"><a href="/mba-colleges/iima/placements">Placements</a><a href="/missing-route">Broken</a>');
fs.writeFileSync(path.join(auditFixture, "mba-colleges", "iima", "placements.html"), '<link rel="canonical" href="https://collegedecoded.in/mba-colleges/iima">');
const auditResult = audit(auditFixture);
assert.strictEqual(auditResult.htmlFilesScanned, 3);
assert.ok(auditResult.counts["canonical-route-mismatch"] >= 1, "should detect wrong canonical path");
assert.ok(auditResult.counts["duplicate-canonical"] >= 1, "should detect repeated canonical URLs");
assert.ok(auditResult.counts["broken-local-link"] >= 1, "should detect missing local route target");
assert.ok(!auditResult.issues.some(issue => issue.type === "broken-local-link" && issue.href === "/"), "homepage href should resolve to index.html, not be flagged broken");
assert.ok(!auditResult.issues.some(issue => issue.type === "broken-local-link" && issue.href === "/assets/brochure.pdf"), "existing static asset must not be flagged broken");
assert.ok(auditResult.issues.some(issue => issue.type === "broken-local-link" && issue.href === "/assets/missing.pdf"), "missing static asset must be flagged broken");
assert.ok(auditResult.counts["broken-local-asset"] >= 1, "missing image/script references must be detected as broken local assets");
assert.ok(auditResult.issues.some(issue => issue.type === "broken-local-asset" && issue.href === "/assets/missing.js"), "missing script must be reported");
assert.ok(!auditResult.issues.some(issue => issue.type === "broken-local-asset" && issue.href === "/assets/hero.jpg"), "existing image assets must not be reported");
assert.ok(!auditResult.issues.some(issue => issue.type === "broken-local-asset" && issue.href === "../../assets/hero.jpg"), "nested relative asset paths must resolve correctly");
fs.rmSync(auditFixture, { recursive: true, force: true });

console.log("URL architecture audit unit tests passed.");
