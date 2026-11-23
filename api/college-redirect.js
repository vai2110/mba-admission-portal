'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();

function parseCsvLine(line) {
  const values = [];
  let value = '';
  let quoted = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (quoted && line[i + 1] === '"') { value += '"'; i++; }
      else quoted = !quoted;
    } else if (ch === ',' && !quoted) {
      values.push(value);
      value = '';
    } else {
      value += ch;
    }
  }
  values.push(value);
  return values;
}

function slugify(value) {
  return String(value || '')
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/&/g, ' and ')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

module.exports = (req, res) => {
  res.setHeader('Cache-Control', 'public, max-age=300, s-maxage=3600');
  const requested = String((req.query && (req.query.college || req.query.slug)) || '').trim();
  if (!requested) {
    res.setHeader('Location', '/colleges');
    return res.status(308).end();
  }

  const csvPath = path.join(ROOT, 'colleges.csv');
  if (!fs.existsSync(csvPath)) return res.status(404).send('College not found');

  const lines = fs.readFileSync(csvPath, 'utf8').replace(/^\uFEFF/, '').split(/\r?\n/);
  const rows = lines.slice(1).filter(Boolean);
  const wanted = slugify(requested);
  let target = null;

  for (const line of rows) {
    const columns = parseCsvLine(line);
    const name = columns[1] || '';
    const profileSlug = columns[7] || '';
    if (wanted === slugify(profileSlug) || wanted === slugify(name)) {
      target = profileSlug;
      break;
    }
  }

  if (!target || !/^[a-z0-9-]+$/.test(target)) {
    return res.status(404).send('College profile not found');
  }

  const targetFile = path.join(ROOT, target + '.html');
  if (!fs.existsSync(targetFile)) {
    return res.status(404).send('College profile is not available');
  }

  res.setHeader('Location', '/' + target);
  return res.status(308).end();
};
