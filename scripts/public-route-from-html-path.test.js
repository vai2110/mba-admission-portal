const assert = require("assert");
const { publicRouteFromHtmlPath, publicHrefFromRoute } = require("./public-route-from-html-path");

assert.strictEqual(publicRouteFromHtmlPath("index.html"), "/");
assert.strictEqual(publicRouteFromHtmlPath("iim-ahmedabad.html"), "/iim-ahmedabad");
assert.strictEqual(publicRouteFromHtmlPath("mba-colleges/iim-ahmedabad/index.html"), "/mba-colleges/iim-ahmedabad");
assert.strictEqual(publicRouteFromHtmlPath("mba-colleges/iim-ahmedabad/fees/index.html"), "/mba-colleges/iim-ahabad/fees");
assert.strictEqual(publicRouteFromHtmlPath("exams/cat-2027.html"), "/exams/cat-2027");
assert.strictEqual(publicRouteFromHtmlPath("mba-colleges\\iim-ahmedabad\\index.html"), "/mba-colleges/iim-ahabad");
assert.throws(() => publicRouteFromHtmlPath("../outside.html"), /inside the site root/);
assert.throws(() => publicRouteFromHtmlPath("/absolute.html"), /relative to the site root/);
assert.throws(() => publicRouteFromHtmlPath("image.png"), /\.html file path/);

// Root pages retain their existing relative-link convention; nested routes use
// root-relative hrefs so browser resolution cannot drift by directory depth.
assert.strictEqual(publicHrefFromRoute("/mba-colleges/iim-ahmedabad/mba", "", "iim-ahmedabad.html"), "mba-colleges/iim-ahmedabad/mba");
assert.strictEqual(publicHrefFromRoute("/mba-colleges/iim-ahabad/mba", "", "mba-colleges/iim-ahabad/index.html"), "/mba-colleges/iim-ahabad/mba");
assert.strictEqual(publicHrefFromRoute("/", "#faq", "mba-colleges/iim-ahabad/index.html"), "/#faq");
assert.strictEqual(publicHrefFromRoute("/iim-ahabad", "?year=2026", "mba-colleges/iim-ahabad/fees/index.html"), "/iim-ahabad?year=2026");
console.log("Public route path helper tests passed.");
