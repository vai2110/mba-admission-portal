const TAB_NAME = "News Queue";
const FIELDS = ["slug","headline","seoTitle","description","category","status","datePublished","dateModified","author","summary","image","imageAlt","body","sourceLinks","relatedPages","relatedNews","keywords"];
function doPost(e) {
  try {
    const p = JSON.parse((e && e.postData && e.postData.contents) || "{}");
    const expected = PropertiesService.getScriptProperties().getProperty("NEWS_SHEET_API_SECRET");
    if (!expected || !p.secret || !equalSecret_(String(p.secret), String(expected))) return out_({ok:false,error:"Unauthorized"});
    if (!Array.isArray(p.items)) return out_({ok:false,error:"items must be an array"});
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    if (!ss) throw new Error("Bind this script to the newsroom spreadsheet.");
    let sh = ss.getSheetByName(TAB_NAME);
    if (!sh) sh = ss.insertSheet(TAB_NAME);
    let headers = sh.getLastColumn() ? sh.getRange(1,1,1,sh.getLastColumn()).getDisplayValues()[0].map(String) : [];
    if (!headers.some(x => x.trim())) headers = [];
    if (!headers.length) headers = FIELDS.slice();
    else FIELDS.forEach(f => { if (!headers.includes(f)) headers.push(f); });
    sh.getRange(1,1,1,headers.length).setValues([headers]);
    sh.setFrozenRows(1);
    const slugCol = headers.indexOf("slug") + 1, rowBySlug = new Map(), last = sh.getLastRow();
    if (last > 1) sh.getRange(2,slugCol,last-1,1).getDisplayValues().forEach((r,i) => { if (r[0]) rowBySlug.set(r[0].trim(),i+2); });
    let inserted=0, updated=0, skipped=0;
    p.items.forEach(item => {
      if (!item || !item.slug || item.status !== "published") { skipped++; return; }
      const oldRow = rowBySlug.get(String(item.slug)), rowNum = oldRow || sh.getLastRow()+1;
      const row = oldRow ? sh.getRange(rowNum,1,1,headers.length).getValues()[0] : new Array(headers.length).fill("");
      FIELDS.forEach(f => { const i=headers.indexOf(f); let v=item[f]; if (Array.isArray(v) || (v && typeof v === "object")) v=JSON.stringify(v); row[i]=v == null ? "" : v; });
      sh.getRange(rowNum,1,1,headers.length).setValues([row]);
      if (oldRow) updated++; else { inserted++; rowBySlug.set(String(item.slug),rowNum); }
    });
    return out_({ok:true,inserted,updated,skipped,received:p.items.length});
  } catch (err) { return out_({ok:false,error:String(err && err.message || err)}); }
}
function equalSecret_(a,b) { if (a.length!==b.length) return false; let d=0; for(let i=0;i<a.length;i++) d|=a.charCodeAt(i)^b.charCodeAt(i); return d===0; }
function out_(v) { return ContentService.createTextOutput(JSON.stringify(v)).setMimeType(ContentService.MimeType.JSON); }
