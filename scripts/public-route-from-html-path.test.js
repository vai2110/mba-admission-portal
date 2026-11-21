const assert = require("assert");
const { publicRouteFromHtmlPath, publicHrefFromRoute } = require("./public-route-from-html-path");
const IIMA = "iim-ahmedabad";

assert.strictEqual(publicRouteFromHtmlPath("index.html"), "/");
assert.strictEqual(publicRouteFromHtmlPath("iim-ahmedabad.html"), "/iim-ahmedabad");
assert.strictEqual(publicRouteFromHtmlPath(`mba-colleges/${IIMA}/index.html`), `/mba-colleges/${IIMA}`);
assert.strictEqual(publicRouteFromHtmlPath(`mba-colleges/${IIMA}/fees/index.html`), `/mba-colleges/${IIMA}/fees`);
assert.strictEqual(publicRouteFromHtmlPath("exams/cat-2027.html"), "/exams/cat-2027");
assert.strictEqual(publicRouteFromHtmlPath(`mba-colleges\\${IIMA}\\index.html`), `/mba-colleges/${IIMA}`);
assert.throws(() => publicRouteFromHtmlPath("../outside.html"), /inside the site root/);
assert.throws(() => publicRouteFromHtmlPath("/absolute.html"), /relative to the site root/);
assert.throws(() => publicRouteFromHtmlPath("image.png"), /\.html file path/);

// Root pages retain their existing relative-link convention; nested routes use
// root-relative hrefs so browser resolution cannot drift by directory depth.
assert.strictEqual(publicHrefFromRoute(`/mba-colleges/${IIMA}/mba`, "", "iim-ahmedabad.html"), `mba-colleges/${IIMA}/mba`);
assert.strictEqual(publicHrefFromRoute(`/mba-colleges/${IIMA}/mba`, "", `mba-colleges/${IIMA}/index.html`), `/mba-colleges/${IIMA}/mba`);
assert.strictEqual(publicHrefFromRoute("/", "#faq", `mba-colleges/${IIMA}/index.html`), "/#faq");
assert.strictEqual(publicHrefFromRoute(`/${IIMA}`, "?year=2026", `mba-colleges/${IIMA}/fees/index.html`), `/${IIMA}?year=2026`);
console.log("Public route path helper tests passed.");
