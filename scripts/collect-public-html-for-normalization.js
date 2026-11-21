const fs = require("fs");
const path = require("path");

const IGNORED_DIRS = new Set([".git", ".vercel", "node_modules", "college-cms"]);

function collectPublicHtmlFiles(root, nestedRoots = ["mba-colleges"], excludedFiles = ["404.html"]) {
  const rootPath = path.resolve(root);
  const excluded = new Set(excludedFiles.map(file => String(file).replace(/\\/g, "/")));
  const files = [];
  const addHtml = (absolutePath) => {
    const relative = path.relative(rootPath, absolutePath).split(path.sep).join("/");
    if (!relative || relative.startsWith("../") || path.isAbsolute(relative)) return;
    if (excluded.has(relative) || excluded.has(path.posix.basename(relative))) return;
    files.push(relative);
  };

  for (const entry of fs.readdirSync(rootPath, { withFileTypes: true })) {
    if (entry.isFile() && entry.name.toLowerCase().endsWith(".html")) {
      addHtml(path.join(rootPath, entry.name));
    }
  }

  function walkNested(directory) {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      if (entry.name.startsWith(".") || IGNORED_DIRS.has(entry.name) || entry.isSymbolicLink()) continue;
      const absolutePath = path.join(directory, entry.name);
      if (entry.isDirectory()) walkNested(absolutePath);
      else if (entry.isFile() && entry.name.toLowerCase().endsWith(".html")) addHtml(absolutePath);
    }
  }

  for (const nestedRoot of nestedRoots) {
    const relativeRoot = String(nestedRoot || "").replace(/\\/g, "/");
    const normalizedRoot = path.posix.normalize(relativeRoot);
    if (!relativeRoot || relativeRoot.startsWith("/") || normalizedRoot === "." || normalizedRoot === ".." || normalizedRoot.startsWith("../")) {
      throw new Error("Nested normalization root must be a safe relative directory");
    }
    const absoluteRoot = path.resolve(rootPath, normalizedRoot);
    if (absoluteRoot !== rootPath && !absoluteRoot.startsWith(rootPath + path.sep)) {
      throw new Error("Nested normalization root must remain inside the site root");
    }
    if (fs.existsSync(absoluteRoot) && fs.statSync(absoluteRoot).isDirectory()) walkNested(absoluteRoot);
  }

  return [...new Set(files)].sort();
}

module.exports = { collectPublicHtmlFiles };
