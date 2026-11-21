const assert = require("assert");
const { publicRouteFromHtmlPath } = require("./public-route-from-html-path");

assert.strictEqual(publicRouteFromHtmlPath("index.html"), "/");
assert.strictEqual(publicRouteFromHtmlPath("iim-ahmedabad.html"), "/iim-ahmedabad");
assert.strictEqual(publicRouteFromHtmlPath("mba-colleges/iim-ahmedabad/index.html"), "/mba-colleges/iim-ahmedabad");
assert.strictEqual(publicRouteFromHtmlPath("mba-colleges/iim-ahmedabad/fees/index.html"), "/mba-colleges/iim-ahmedabad/fees");
assert.strictEqual(publicRouteFromHtmlPath("exams/cat-2027.html"), "/exams/cat-2027");
assert.strictEqual(publicRouteFromHtmlPath("mba-colleges\\iim-ahmedabad\\index.html"), "/mba-colleges/iim-ahmedabad");
assert.throws(() => publicRouteFromHtmlPath("../outside.html"), /inside the site root/);
assert.throws(() => publicRouteFromHtmlPath("/absolute.html"), /relative to the site root/);
assert.throws(() => publicRouteFromHtmlPath("image.png"), /\.html file path/);
console.log("Public route path helper tests passed.");
