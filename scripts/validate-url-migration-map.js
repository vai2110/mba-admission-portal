#!/usr/bin/env node
/**
 * Validate a proposed old-to-new URL migration CSV before any route changes.
 * The manifest is a review artifact; this script never rewrites pages or redirects.
 */
const fs = require("fs");
const path = require("path");

const REQUIRED_HEADERS = ["current_url", "route_or_file", "content_type", "entity_or_topic", "proposed_url", "decision"];

function parseCsv(input) {
  const rows = [];
  let row = [], field = "", quoted = false;
  for (let i = 0; i < input.length; i++) {
    const ch = input[i];
    if (quoted) {
      if (ch === '"') {
        if (input[i + 1] === '"') { field += '"'; i++; }
        else quoted = false;
      } else field += ch;
    } else if (ch === '"') {
      if (field.length) throw new Error("Unexpected quote inside an unquoted CSV field");
      quoted = true;
    } else if (ch === ",") {
      row.push(field); field = "";
    } else if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && input[i + 1] === "\n") i++;
      row.push(field); field = "";
      if (row.some(v => v.trim() !== "")) rows.push(row);
      row = [];
    } else field += ch;
  }
  if (quoted) throw new Error("Unclosed quoted CSV field");
  row.push(field);
  if (row.some(v => v.trim() !== "")) rows.push(row);
  return rows;
}

function normalizeInternalUrl(value, { allowQuery = false } = {}) {
  const raw = String(value || "").trim();
  if (!raw) return null;
  let pathname;
  if (/^https?:\/\//i.test(raw)) {
    let parsed;
    try { parsed = new URL(raw); } catch (_) { return null; }
    if (!/^collegedecoded\.in$|^www\.collegedecoded\.in$/i.test(parsed.hostname)) return null;
    if (!allowQuery && (parsed.search || parsed.hash)) return null;
    pathname = parsed.pathname;
    if (allowQuery) pathname += parsed.search;
  } else {
    if (!raw.startsWith("/") || raw.startsWith("//")) return null;
    if (!allowQuery && /[?#]/.test(raw)) return null;
    pathname = allowQuery ? raw.split("#", 1)[0] : raw;
  }
  if (!pathname) return "/";
  if (pathname !== "/" && pathname.endsWith("/")) return null;
  return pathname;
}

function validateMap(input) {
  const errors = [], warnings = [];
  let records;
  try { records = parseCsv(input); }
  catch (err) { return { errors: [err.message], warnings, rows: 0 }; }
  if (!records.length) return { errors: ["CSV is empty"], warnings, rows: 0 };
  // Excel and some export tools prepend a UTF-8 BOM to the first header.
  const headers = records[0].map((h, i) => (i === 0 ? h.replace(/^\uFEFF/, "") : h).trim());
  const headerCounts = new Map();
  headers.forEach(h => headerCounts.set(h, (headerCounts.get(h) || 0) + 1));
  for (const [header, count] of headerCounts) if (count > 1) errors.push(`Duplicate CSV header: ${header}`);
  const missingHeaders = REQUIRED_HEADERS.filter(h => !headers.includes(h));
  if (missingHeaders.length) errors.push(`Missing required headers: ${missingHeaders.join(", ")}`);
  if (missingHeaders.length) return { errors, warnings, rows: 0 };
  const index = Object.fromEntries(headers.map((h, i) => [h, i]));
  const sources = new Map(), targets = new Map();
  let rows = 0;
  for (let line = 2; line <= records.length; line++) {
    const cells = records[line - 1];
    if (cells.every(v => String(v || "").trim() === "")) continue;
    rows++;
    if (cells.length !== headers.length) {
      errors.push(`Row ${line}: expected ${headers.length} columns, found ${cells.length}`);
      continue;
    }
    const get = name => String(cells[index[name]] || "").trim();
    const source = get("current_url"), file = get("route_or_file"), type = get("content_type"), entity = get("entity_or_topic"), targetRaw = get("proposed_url"), decision = get("decision"), redirectRaw = index.redirect_target !== undefined ? get("redirect_target") : "";
    if (!source) errors.push(`Row ${line}: current_url is blank`);
    else {
      const normalizedSource = normalizeInternalUrl(source, { allowQuery: true });
      if (!normalizedSource) errors.push(`Row ${line}: current_url must be a valid internal URL/path`);
      else {
        sources.set(normalizedSource, [...(sources.get(normalizedSource) || []), line]);
      }
    }
    if (!file) errors.push(`Row ${line}: route_or_file is blank`);
    if (!type) errors.push(`Row ${line}: content_type is blank`);
    if (!entity) errors.push(`Row ${line}: entity_or_topic is blank`);
    if (!decision) errors.push(`Row ${line}: decision is blank`);
    const removeDecision = /remove|410/i.test(decision);
    let target = null;
    if (targetRaw) {
      target = normalizeInternalUrl(targetRaw);
      if (!target) errors.push(`Row ${line}: proposed_url must be an internal slashless path with no query/hash`);
      else targets.set(target, [...(targets.get(target) || []), { line, decision }]);
    } else if (!removeDecision) errors.push(`Row ${line}: proposed_url is required unless the decision is REMOVE/410`);
    if (/redirect/i.test(decision) && !redirectRaw) errors.push(`Row ${line}: redirect_target is required for a REDIRECT decision`);
    if (redirectRaw) {
      const redirect = normalizeInternalUrl(redirectRaw);
      if (!redirect) errors.push(`Row ${line}: redirect_target must be an internal slashless path with no query/hash`);
      if (target && redirect && redirect !== target) errors.push(`Row ${line}: redirect_target differs from proposed_url`);
    }
  }
  if (rows === 0) warnings.push("No mapping rows supplied; template-only CSV is not ready for migration");
  for (const [source, lineNumbers] of sources) if (lineNumbers.length > 1) errors.push(`Duplicate current_url ${source} at rows ${lineNumbers.join(", ")}`);
  for (const [target, entries] of targets) if (entries.length > 1 && entries.some(e => !/merge|redirect|consolidat/i.test(e.decision))) errors.push(`Duplicate proposed_url ${target} without explicit merge/redirect decision at rows ${entries.map(e => e.line).join(", ")}`);
  return { errors, warnings, rows };
}

if (require.main === module) {
  const file = process.argv[2] || path.join(__dirname, "..", "docs", "seo", "url-migration-inventory-template.csv");
  let content;
  try { content = fs.readFileSync(file, "utf8"); }
  catch (err) { console.error(JSON.stringify({ file, errors: [err.message], warnings: [], rows: 0 }, null, 2)); process.exitCode = 1; }
  if (content !== undefined) {
    const result = validateMap(content);
    console.log(JSON.stringify({ file, ...result }, null, 2));
    if (result.errors.length || result.rows === 0) process.exitCode = 1;
  }
}

module.exports = { parseCsv, normalizeInternalUrl, validateMap };
