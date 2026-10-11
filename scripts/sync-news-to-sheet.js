#!/usr/bin/env node
"use strict";
const fs = require("node:fs");
const path = require("node:path");
async function main() {
  const endpoint = process.env.NEWS_SHEET_WEBAPP_URL;
  const secret = process.env.NEWS_SHEET_API_SECRET;
  if (!endpoint || !secret) {
    console.log("Google Sheets sync skipped: configure NEWS_SHEET_WEBAPP_URL and NEWS_SHEET_API_SECRET repository secrets after deploying the Apps Script endpoint.");
    return;
  }
  const registry = JSON.parse(fs.readFileSync(path.join(process.cwd(),"data","news.json"),"utf8"));
  const items = (Array.isArray(registry) ? registry : registry.items || []).filter(x => x && x.status === "published").map(x => ({
    slug:x.slug, headline:x.headline, seoTitle:x.seoTitle || "", description:x.description || "",
    category:x.category || "", status:"published", datePublished:x.datePublished || "",
    dateModified:x.dateModified || x.datePublished || "", author:x.author || "CollegeDecoded Editorial Team",
    summary:x.summary || "", image:x.image || "", imageAlt:x.imageAlt || "", body:x.body || [],
    sourceLinks:x.sourceLinks || [], relatedPages:x.relatedPages || [], relatedNews:x.relatedNews || [], keywords:x.keywords || []
  }));
  const response = await fetch(endpoint,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({secret,items}),redirect:"follow"});
  const raw = await response.text();
  if (!response.ok) throw new Error("Sheets endpoint returned HTTP "+response.status+": "+raw.slice(0,300));
  let result;
  try { result=JSON.parse(raw); } catch { throw new Error("Sheets endpoint returned non-JSON response: "+raw.slice(0,300)); }
  if (!result.ok) throw new Error("Sheets sync failed: "+(result.error || "unknown error"));
  console.log("Google Sheets sync complete: "+JSON.stringify({publishedItemsSent:items.length,inserted:result.inserted,updated:result.updated,skipped:result.skipped}));
}
main().catch(e => { console.error(e.message); process.exitCode=1; });
