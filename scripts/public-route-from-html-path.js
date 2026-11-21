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

// Nested clean routes must use root-relative internal hrefs. Relative hrefs from
// directory-index pages are resolved by browsers against the route directory,
// which can silently send users to the wrong URL.
function publicHrefFromRoute(route, suffix, sourceHtmlPath) {
  const routeInput = String(route || "/");
  const routePath = routeInput === "/"
    ? "/"
    : "/" + routeInput.replace(/^\/+/, "").replace(/\/+$/, "");
  const source = String(sourceHtmlPath || "").replace(/\\/g, "/");
  const isNestedSource = source && path.posix.dirname(source) !== ".";
  if (isNestedSource || routePath === "/") return routePath + String(suffix || "");
  return routePath.slice(1) + String(suffix || "");
}


// Normalize the final index segment after a href has been resolved against its
// source file. This prevents nested index.html links from becoming /index routes.
function stripIndexRouteSegment(target) {
  const value = String(target || "");
  if (value === "index") return "";
  if (value.endsWith("/index")) return value.slice(0, -"/index".length);
  return value;
}

module.exports = { publicRouteFromHtmlPath, publicHrefFromRoute, stripIndexRouteSegment };
