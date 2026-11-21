const assert = require("assert");
const path = require("path");
const { routeFromHtmlPath, extractCanonical, resolveLocalHref, findTargetFile } = require("./audit-url-architecture");

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
const fs = require("fs");
fs.mkdirSync(path.join(fixture, "nested"), { recursive: true });
fs.writeFileSync(path.join(fixture, "nested", "index.html"), "fixture");
assert.strictEqual(findTargetFile(fixture, "nested"), path.join("nested", "index.html"));
fs.rmSync(fixture, { recursive: true, force: true });

console.log("URL architecture audit unit tests passed.");
