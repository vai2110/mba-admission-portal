#!/usr/bin/env node
"use strict";

// Minify only first-party browser assets after all content-generation steps.
// Keep filenames stable so existing HTML references, cache-busting query strings,
// and script load order remain unchanged. Build tooling under scripts/ is excluded.
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const root = process.cwd();
const excludedDirs = new Set([
  ".git", ".github", "node_modules", "scripts", "api", "integrations",
  "college-cms", "config", "data", "news"
]);
const excludedFiles = new Set(["service-worker.js"]);
const targets = [];

function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith(".") && entry.isDirectory()) continue;
    const full = path.join(dir, entry.name);
    const rel = path.relative(root, full).split(path.sep).join("/");
    if (entry.isDirectory()) {
      if (!excludedDirs.has(entry.name)) walk(full);
      continue;
    }
    if (!entry.isFile() || excludedFiles.has(entry.name)) continue;
    if (/\.min\.(?:js|css)$/i.test(entry.name)) continue;
    if (/\.(?:js|css)$/i.test(entry.name)) targets.push({ full, rel, ext: path.extname(entry.name).toLowerCase() });
  }
}

walk(root);
let processed = 0;
let failed = 0;

for (const file of targets) {
  const temp = file.full + ".minify-tmp";
  const args = file.ext === ".js"
    ? [file.full, "--format", "comments=false", "--output", temp]
    : ["-o", temp, file.full];
  const command = file.ext === ".js" ? "terser" : "cleancss";
  const result = spawnSync(command, args, { encoding: "utf8" });

  if (result.error || result.status !== 0 || !fs.existsSync(temp)) {
    failed++;
    console.error("MINIFY FAILED:", file.rel, result.error?.message || result.stderr || "unknown error");
    if (fs.existsSync(temp)) fs.unlinkSync(temp);
    continue;
  }

  const originalSize = fs.statSync(file.full).size;
  const minifiedSize = fs.statSync(temp).size;
  // Do not replace an asset if minification unexpectedly increases its size.
  if (minifiedSize <= originalSize) {
    fs.renameSync(temp, file.full);
    processed++;
  } else {
    fs.unlinkSync(temp);
  }
  if (processed && processed % 100 === 0) console.log("Minified first-party assets:", processed);
}

console.log(`ASSET MINIFICATION: ${processed} files reduced; ${targets.length} checked; ${failed} failures.`);
if (failed) process.exitCode = 1;
