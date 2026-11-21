const path = require("path");

function publicRouteFromHtmlPath(filePath) {
  const input = String(filePath || "").trim().replace(/\\/g, "/");
  if (!input || input.startsWith("/")) {
    throw new Error("Expected an HTML file path relative to the site root");
  }
  const normalized = path.posix.normalize(input).replace(/^\.\//, "");
  if (normalized === "." || normalized === ".." || normalized.startsWith("../")) {
    throw new Error("HTML file path must remain inside the site root");
  }
  if (!normalized.toLowerCase().endsWith(".html")) {
    throw new Error("Expected an .html file path");
  }
  if (normalized.toLowerCase() === "index.html") return "/";
  if (normalized.toLowerCase().endsWith("/index.html")) {
    return "/" + normalized.slice(0, -"index.html".length).replace(/\/+$/, "");
  }
  return "/" + normalized.slice(0, -5);
}

module.exports = { publicRouteFromHtmlPath };
