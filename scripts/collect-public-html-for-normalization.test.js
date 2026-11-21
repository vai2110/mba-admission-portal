const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { collectPublicHtmlFiles } = require("./collect-public-html-for-normalization");

const fixture = path.join(__dirname, "__normalize-collection-fixture__");
const outside = path.join(__dirname, "__normalize-collection-outside__");
fs.rmSync(fixture, { recursive: true, force: true });
fs.rmSync(outside, { recursive: true, force: true });
fs.mkdirSync(path.join(fixture, "mba-colleges", "iima", "fees"), { recursive: true });
fs.mkdirSync(path.join(fixture, "mba-colleges", ".private"), { recursive: true });
fs.mkdirSync(path.join(fixture, "mba-colleges", "node_modules", "sample"), { recursive: true });
fs.mkdirSync(path.join(fixture, "iim-ahmedabad", "courses-fees"), { recursive: true });
fs.mkdirSync(path.join(fixture, "college-cms", "content", "sample"), { recursive: true });
fs.mkdirSync(outside, { recursive: true });
fs.writeFileSync(path.join(fixture, "index.html"), "root");
fs.writeFileSync(path.join(fixture, "profile.html"), "root profile");
fs.writeFileSync(path.join(fixture, "404.html"), "excluded");
fs.writeFileSync(path.join(fixture, "mba-colleges", "iima", "index.html"), "nested profile");
fs.writeFileSync(path.join(fixture, "mba-colleges", "iima", "fees", "index.html"), "nested fees");
fs.writeFileSync(path.join(fixture, "mba-colleges", ".private", "index.html"), "hidden");
fs.writeFileSync(path.join(fixture, "mba-colleges", "node_modules", "sample", "index.html"), "ignored dependency");
fs.writeFileSync(path.join(fixture, "iim-ahmedabad", "courses-fees", "index.html"), "not allowlisted");
fs.writeFileSync(path.join(fixture, "college-cms", "content", "sample", "overview.html"), "cms source");
fs.writeFileSync(path.join(outside, "index.html"), "outside target");
fs.symlinkSync(outside, path.join(fixture, "mba-colleges", "linked-root"), "dir");

assert.deepStrictEqual(
  collectPublicHtmlFiles(fixture, ["mba-colleges"], ["404.html"]),
  ["index.html", "mba-colleges/iima/fees/index.html", "mba-colleges/iima/index.html", "profile.html"]
);
assert.deepStrictEqual(
  collectPublicHtmlFiles(fixture, ["mba-colleges/linked-root"], ["404.html"]),
  ["index.html", "profile.html"],
  "allowlisted symlink roots must not be traversed outside the site"
);
assert.throws(() => collectPublicHtmlFiles(fixture, ["../outside"]), /safe relative directory/);
fs.rmSync(fixture, { recursive: true, force: true });
fs.rmSync(outside, { recursive: true, force: true });
console.log("Public HTML normalization collection tests passed.");
