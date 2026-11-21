const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { isPublishedCmsProfile } = require("./cms-profile-route");

const root = fs.mkdtempSync(path.join(os.tmpdir(), "cms-route-test-"));
function writeProfile(slug, html) {
  const file = path.join(root, "college-cms", "content", slug, "overview.html");
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, html, "utf8");
}
function selfCanonical(slug, robots = "") {
  return '<html><head><link rel="canonical" href="https://collegedecoded.in/' + slug + '">' + robots + '</head><body>Profile content</body></html>';
}
try {
  writeProfile("live-profile", selfCanonical("live-profile"));
  assert.strictEqual(isPublishedCmsProfile(root, "live-profile"), true, "self-canonical indexable profile should be valid");

  writeProfile("noindex-profile", selfCanonical("noindex-profile", '<meta name="robots" content="noindex,follow">'));
  assert.strictEqual(isPublishedCmsProfile(root, "noindex-profile"), false, "noindex profile should not be a link target");

  writeProfile("redirect-profile", '<meta name="robots" content="noindex"><link rel="canonical" href="https://collegedecoded.in/mba-colleges-by-location"><script data-collegedecoded-legacy-redirect>location.replace("/mba-colleges-by-location")</script>');
  assert.strictEqual(isPublishedCmsProfile(root, "redirect-profile"), false, "redirect wrapper should not be treated as a published profile");

  writeProfile("wrong-canonical", selfCanonical("another-profile"));
  assert.strictEqual(isPublishedCmsProfile(root, "wrong-canonical"), false, "non-self canonical should not be a valid profile");

  writeProfile("duplicate-canonical", selfCanonical("duplicate-canonical") + '<link rel="canonical" href="https://collegedecoded.in/duplicate-canonical">');
  assert.strictEqual(isPublishedCmsProfile(root, "duplicate-canonical"), false, "duplicate canonicals should fail profile validation");

  writeProfile("attribute-order", '<link href="https://collegedecoded.in/attribute-order" rel="canonical"><meta content="index,follow" name="robots">');
  assert.strictEqual(isPublishedCmsProfile(root, "attribute-order"), true, "attribute order should not affect canonical or robots detection");

  assert.strictEqual(isPublishedCmsProfile(root, "missing-profile"), false, "missing CMS page should fail");
  assert.strictEqual(isPublishedCmsProfile(root, "../outside"), false, "unsafe slug should fail");
  console.log("CMS profile route tests passed: 8 assertions");
} finally {
  fs.rmSync(root, { recursive: true, force: true });
}
