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

const oldCss = /<link[^>]+href=["']\/?assets\/college-guidance\.css(?:\?[^"']*)?["'][^>]*>\s*/gi;
const oldJs = /<script[^>]+src=["']\/?assets\/college-guidance\.js(?:\?[^"']*)?["'][^>]*><\/script>\s*/gi;
const oldIimaCss = /<link[^>]+href=["']\/?assets\/iima-guidance-test\.css(?:\?[^"']*)?["'][^>]*>\s*/gi;
const oldIimaJs = /<script[^>]+src=["']\/?assets\/iima-guidance-test\.js(?:\?[^"']*)?["'][^>]*><\/script>\s*/gi;
const newCss = /<link[^>]+href=["']\/?assets\/college-guidance-test\.css(?:\?[^"']*)?["'][^>]*>\s*/gi;
const newJs = /<script[^>]+src=["']\/?assets\/college-guidance-test\.js(?:\?[^"']*)?["'][^>]*><\/script>\s*/gi;
const injection = '\n<link rel="stylesheet" href="/assets/college-guidance-test.css?v=4"><script src="/assets/college-guidance-test.js?v=4"></script>\n';

let matched = 0, changed = 0;
for (const file of walk(root)) {
  const base = path.basename(file).toLowerCase();
  const excluded = new Set([
    '404.html',
    'index.html',
    'about.html',
    'about-us.html',
    'collegedecoded-team.html',
    'college-page-audit-dashboard.html',
    'content-audit.html',
    'github-direct-edit-test.html',
    'college.html',
    'colleges.html',
    'irma-deploy-trigger.html'
  ]);
  if (excluded.has(base)) continue;

  const text = fs.readFileSync(file, 'utf8');
  matched++;

  const cleaned = text
    .replace(oldCss, '')
    .replace(oldJs, '')
    .replace(oldIimaCss, '')
    .replace(oldIimaJs, '')
    .replace(newCss, '')
    .replace(newJs, '');

  let next = cleaned;
  if (/<\/body>\s*<\/html>/i.test(next)) {
    next = next.replace(/<\/body>\s*<\/html>/i, injection + '</body>\n</html>');
  } else if (/<\/body>/i.test(next)) {
    next = next.replace(/<\/body>/i, injection + '</body>');
  } else {
    next += injection;
  }

  if (next !== text) {
    fs.writeFileSync(file, next);
    changed++;
  }
}

console.log('CollegeDecoded universal guidance injection: matched ' + matched + ' pages; changed ' + changed + ' pages.');