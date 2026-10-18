const GONE_SLUGS = new Set(["welingkar-mumbai-links","mba-colleges-in-kolkata","mba-colleges-in-ahmedabad","mba-colleges-in-hyderabad","mba-colleges-in-pune","mba-colleges-in-bengaluru","indian-institute-of-technology-roorkee-mba","mba-colleges-in-chennai"]);

module.exports = (req, res) => {
  const slug = String((req.query && req.query.slug) || "").replace(/^\/+|\/+$/g, "");
  if (!GONE_SLUGS.has(slug)) {
    res.setHeader("Cache-Control", "no-store");
    return res.status(404).send("Not found");
  }
  res.setHeader("Content-Type", "text/html; charset=utf-8");
  res.setHeader("X-Robots-Tag", "noindex, nofollow, noarchive");
  res.setHeader("Cache-Control", "public, max-age=300, s-maxage=3600");
  return res.status(410).send("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"robots\" content=\"noindex, nofollow\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>Page removed | CollegeDecoded</title></head><body><main><h1>This page has been permanently removed</h1><p>The requested CollegeDecoded page is no longer available.</p><a href=\"/\">Return to CollegeDecoded</a></main></body></html>");
};
