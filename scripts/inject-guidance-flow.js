const fs = require('fs');
const path = require('path');

const root = process.cwd();
const data = JSON.parse(fs.readFileSync(path.join(root, 'data', 'management-live-colleges.json'), 'utf8'));
const parents = [];
for (const item of (data.colleges || [])) {
  const url = Array.isArray(item) ? item[1] : item.url;
  if (!url) continue;
  let slug = url.replace(/\/$/, '').split('/').pop().replace(/\.html$/i, '');
  if (slug) parents.push(slug);
}
parents.push('kj-somaiya-institute-of-management', 'kiit-bhubaneswar');
const uniqueParents = [...new Set(parents)].sort((a,b) => b.length - a.length);

function related(file, text) {
  const stem = path.basename(file, '.html').toLowerCase();
  const rel = path.relative(root, file).toLowerCase().replace(/\\/g, '/');
  const segments = rel.split('/');
  const head = text.slice(0, 20000).toLowerCase();
  return uniqueParents.some(slug =>
    stem === slug ||
    stem.startsWith(slug + '-') ||
    segments.some(segment => segment === slug) ||
    rel.includes('/' + slug + '/') ||
    head.includes('collegedecoded.in/' + slug) ||
    head.includes('"' + slug + '"') ||
    head.includes('/' + slug + '/')
  );
}
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
const newCss = /<link[^>]+href=["']\/?assets\/college-guidance-test\.css(?:\?[^"']*)?["'][^>]*>\s*/gi;
const newJs = /<script[^>]+src=["']\/?assets\/college-guidance-test\.js(?:\?[^"']*)?["'][^>]*><\/script>\s*/gi;
const injection = '\n<link rel="stylesheet" href="/assets/college-guidance-test.css?v=3"><script src="/assets/college-guidance-test.js?v=3"></script>\n';
let matched = 0, changed = 0;
for (const file of walk(root)) {
  const base = path.basename(file).toLowerCase();
  if (base === '404.html' || base === 'index.html') continue;
  const text = fs.readFileSync(file, 'utf8');
  if (!related(file, text)) continue;
  if (path.basename(file).toLowerCase().startsWith('iim-ahmedabad')) continue;
  matched++;
  const cleaned = text.replace(oldCss, '').replace(oldJs, '').replace(newCss, '').replace(newJs, '');
  let next = cleaned;
  if (/<\/body>\s*<\/html>/i.test(next)) next = next.replace(/<\/body>\s*<\/html>/i, injection + '</body>\n</html>');
  else if (/<\/body>/i.test(next)) next = next.replace(/<\/body>/i, injection + '</body>');
  else next += injection;
  if (next !== text) { fs.writeFileSync(file, next); changed++; }
}
console.log('Vercel guidance injection: matched ' + matched + ' pages; changed ' + changed + ' pages.');