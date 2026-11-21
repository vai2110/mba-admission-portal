const assert = require("assert");
const { parseCsv, normalizeInternalUrl, validateMap } = require("./validate-url-migration-map");

const quoted = parseCsv('a,b\r\n1,"field with, comma"\r\n2,"double ""quote"""');
assert.deepStrictEqual(quoted, [["a", "b"], ["1", "field with, comma"], ["2", 'double "quote"']]);
assert.throws(() => parseCsv('a,b\n1,"unfinished'), /Unclosed quoted CSV field/);

assert.strictEqual(normalizeInternalUrl("https://www.collegedecoded.in/mba-colleges/iima"), "/mba-colleges/iima");
assert.strictEqual(normalizeInternalUrl("/mba-colleges/iima/mba"), "/mba-colleges/iima/mba");
assert.strictEqual(normalizeInternalUrl("/mba-colleges/iima/mba?year=2027"), null);
assert.strictEqual(normalizeInternalUrl("https://example.com/college"), null);

const valid = [
  "current_url,route_or_file,content_type,entity_or_topic,proposed_url,decision,redirect_target",
  'https://collegedecoded.in/iim-a,iima.html,profile,IIM A,/mba-colleges/iim-a,MIGRATE,/mba-colleges/iim-a',
  'https://collegedecoded.in/iim-a-mba,iima-mba.html,programme,"IIM A, MBA",/mba-colleges/iim-a/mba,MIGRATE,/mba-colleges/iim-a/mba'
].join("\n");
assert.deepStrictEqual(validateMap(valid).errors, []);
assert.strictEqual(validateMap(valid).rows, 2);

const duplicateSource = [
  "current_url,route_or_file,content_type,entity_or_topic,proposed_url,decision,redirect_target",
  "https://collegedecoded.in/iim-a,iima.html,profile,IIM A,/mba-colleges/iim-a,KEEP,",
  "https://collegedecoded.in/iim-a,iima-2.html,profile,IIM A,/mba-colleges/iim-a-2,KEEP,"
].join("\n");
assert.ok(validateMap(duplicateSource).errors.some(e => e.includes("Duplicate current_url")));

const unsafeTarget = [
  "current_url,route_or_file,content_type,entity_or_topic,proposed_url,decision,redirect_target",
  "https://collegedecoded.in/iim-a,iima.html,profile,IIM A,/mba-colleges/iim-a?x=1,MIGRATE,/wrong-target"
].join("\n");
const unsafe = validateMap(unsafeTarget);
assert.ok(unsafe.errors.some(e => e.includes("proposed_url must be an internal slashless path")));
assert.ok(unsafe.errors.some(e => e.includes("redirect_target differs from proposed_url")));

const duplicateTarget = [
  "current_url,route_or_file,content_type,entity_or_topic,proposed_url,decision,redirect_target",
  "https://collegedecoded.in/iim-a,iima.html,profile,IIM A,/mba-colleges/iim-a,KEEP,",
  "https://collegedecoded.in/iim-b,iimb.html,profile,IIM B,/mba-colleges/iim-a,KEEP,"
].join("\n");
assert.ok(validateMap(duplicateTarget).errors.some(e => e.includes("Duplicate proposed_url without explicit merge/redirect")));

console.log("URL migration manifest validator tests passed.");
