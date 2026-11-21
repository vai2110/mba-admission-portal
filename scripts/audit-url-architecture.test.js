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
fs.writeFileSync(path.join(fixture, "nested", "index.html"), "fixture");
assert.strictEqual(findTargetFile(fixture, "nested"), path.join("nested", "index.html"));
fs.rmSync(fixture, { recursive: true, force: true });


// Integration-style audit fixture: verifies canonical route mismatches, duplicate canonicals,
// and missing local links are surfaced together for nested routes.
const auditFixture = path.join(__dirname, "__url-audit-full-fixture__");
fs.mkdirSync(path.join(auditFixture, "mba-colleges", "iima"), { recursive: true });
fs.writeFileSync(path.join(auditFixture, "index.html"), '<link rel="canonical" href="https://collegedecoded.in/"><a href="/mba-colleges/iima">Profile</a>');
fs.writeFileSync(path.join(auditFixture, "mba-colleges", "iima", "index.html"), '<link rel="canonical" href="https://collegedecoded.in/mba-colleges/iima"><a href="/mba-colleges/iima/placements">Placements</a><a href="/missing-route">Broken</a>');
fs.writeFileSync(path.join(auditFixture, "mba-colleges", "iima", "placements.html"), '<link rel="canonical" href="https://collegedecoded.in/mba-colleges/iima">');
const auditResult = audit(auditFixture);
assert.strictEqual(auditResult.htmlFilesScanned, 3);
assert.ok(auditResult.counts["canonical-route-mismatch"] >= 1, "should detect wrong canonical path");
assert.ok(auditResult.counts["duplicate-canonical"] >= 1, "should detect repeated canonical URLs");
assert.ok(auditResult.counts["broken-local-link"] >= 1, "should detect missing local route target");
fs.rmSync(auditFixture, { recursive: true, force: true });

console.log("URL architecture audit unit tests passed.");
