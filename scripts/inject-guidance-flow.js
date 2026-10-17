const fs = require('fs');
const path = require('path');

const root = process.cwd();

function walk(dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, {withFileTypes:true})) {
    if (entry.name === '.git' || entry.name === 'node_modules') continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(full));
    else if (entry.isFile() && entry.name.toLowerCase().endsWith('.html')) out.push(full);
  }
  return out;
}

// Sitewide advisor/guidance widgets are disabled. Remove previously injected
// references from every HTML page, including pages excluded by older injectors.
// Do not re-inject the experimental guidance widget during production builds.
const patterns = [
  /<link[^>]+href=["']\/?assets\/college-guidance\.css(?:\?[^"']*)?["'][^>]*>\s*/gi,
  /<script[^>]+src=["']\/?assets\/college-guidance\.js(?:\?[^"']*)?["'][^>]*><\/script>\s*/gi,
  /<link[^>]+href=["']\/?assets\/iima-guidance-test\.css(?:\?[^"']*)?["'][^>]*>\s*/gi,
  /<script[^>]+src=["']\/?assets\/iima-guidance-test\.js(?:\?[^"']*)?["'][^>]*><\/script>\s*/gi,
  /<link[^>]+href=["']\/?assets\/college-guidance-test\.css(?:\?[^"']*)?["'][^>]*>\s*/gi,
  /<script[^>]+src=["']\/?assets\/college-guidance-test\.js(?:\?[^"']*)?["'][^>]*><\/script>\s*/gi
];

let scanned = 0;
let changed = 0;
for (const file of walk(root)) {
  const original = fs.readFileSync(file, 'utf8');
  scanned++;
  let next = original;
  for (const pattern of patterns) next = next.replace(pattern, '');
  if (next !== original) {
    fs.writeFileSync(file, next, 'utf8');
    changed++;
  }
}

console.log('CollegeDecoded advisor/guidance cleanup: scanned ' + scanned + ' HTML pages; removed widget references from ' + changed + ' pages; no guidance widget injected.');
