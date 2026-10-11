# CollegeDecoded Newsroom

## Architecture
- News hub: `/news/`
- Article URLs: `/news/<slug>`
- Source of truth: `data/news.json`
- Build output: `news/index.html`, `news/<slug>.html`, `news-sitemap.xml`
- Article pages emit canonical URLs and `NewsArticle` JSON-LD. The main sitemap receives news URLs during build.
- Use **CollegeDecoded Editorial Team** as the byline; do not add personal names or invented credentials.

## Publishing
Add an object to `data/news.json` under `items`. Required fields: `slug`, `headline`, `description`, `category`, `status`, `datePublished`, `author`, `body`, and `sourceLinks`. Only `status: "published"` entries generate pages. Published stories require at least one source URL and at least one body section. Keep drafts as `draft` until editorial review is complete.

Example object (template only, not a real report):
```json
{
  "slug": "sample-mba-admission-notice",
  "headline": "MBA Admission Notice: What Applicants Need to Check",
  "description": "A student-focused summary of an official MBA admission notice, including dates and application steps.",
  "category": "MBA Admissions",
  "status": "draft",
  "datePublished": "2026-10-11T10:00:00+05:30",
  "author": "CollegeDecoded Editorial Team",
  "body": [{"heading":"What has been announced?","paragraphs":["Summarise only confirmed details from the original notice."]}],
  "sourceLinks": [{"label":"Official admission notice","url":"https://example.edu/admissions"}],
  "relatedPages": [{"label":"MBA admission guide","url":"/iim-ahmedabad"}],
  "relatedNews": [],
  "keywords": ["MBA admission", "official notice"]
}
```
Replace the example source with a verified official source before publishing.

## Google Sheets and CollegeCMS
Use Google Sheets for editorial ideas and drafts, then send rows marked `Ready for Review` to the authenticated CollegeCMS newsroom. Only the CMS Publish action writes approved stories to `data/news.json`. The website build reads only that repository file; it never imports a public spreadsheet CSV directly. This keeps a spreadsheet status change from publishing an article. Keep the spreadsheet private and follow the separate CollegeCMS `NEWSROOM-SETUP.md` for Apps Script deployment and server-side secrets.

## Internal links
Set `relatedPages` to relevant existing local pages. The build injects a contextual “Latest related news” block into those pages, and each news article links back to its selected evergreen guides. Never add unrelated links or change live slugs without a permanent redirect.

## SEO checklist
1. Verify original official notices and cite them in `sourceLinks`.
2. Distinguish confirmed facts from analysis and estimates.
3. Keep each URL stable and each headline/description unique.
4. Only update `dateModified` after meaningful editorial changes.
5. Use a stable, relevant lead image with useful alt text where possible.
6. Submit `https://collegedecoded.in/sitemap.xml` and `https://collegedecoded.in/news-sitemap.xml` in Search Console. The news sitemap contains only stories published within the last 48 hours; an empty one is normal when no recent stories exist.
7. Use Search Console URL Inspection and monitor indexing/crawl issues. Sitemap submission is not a ranking guarantee.

## Build
The existing `scripts/vercel-build.sh` will run `node scripts/build-news.js` after the current site checks. Run `node scripts/build-news.js` locally to generate news output.
