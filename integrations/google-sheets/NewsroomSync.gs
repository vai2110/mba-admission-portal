const TAB_NAME = "News Queue";
const FIELDS = ["topic","sourceUrl","slug","headline","seoTitle","description","category","status","datePublished","dateModified","author","summary","image","imageAlt","body","sourceLinks","relatedPages","relatedNews","keywords","editorialNote"];
const META_FIELDS = ["publishedUrl","cmsStatusUpdatedAt","cmsCommit","reviewNotes","generationError"];
const ALL_FIELDS = FIELDS.concat(META_FIELDS);

function doPost(e) {
  try {
    const p = JSON.parse((e && e.postData && e.postData.contents) || "{}");
    const expected = PropertiesService.getScriptProperties().getProperty("NEWS_SHEET_API_SECRET");
    if (!expected || !p.secret || !equalSecret_(String(p.secret), String(expected))) return out_({ok:false,error:"Unauthorized"});
    const sh = getSheet_();
    ensureHeaders_(sh);
    const headers = sh.getRange(1,1,1,sh.getLastColumn()).getDisplayValues()[0].map(String);
    const action = String(p.action || "");
    if (action === "getDrafts") return getDrafts_(sh, headers);
    if (action === "updateStatus") return updateStatus_(sh, headers, p);
    // Backwards-compatible website -> Sheet sync of already-published articles.
    if (!Array.isArray(p.items)) return out_({ok:false,error:"Expected action getDrafts/updateStatus or an items array"});
    const rowBySlug = rowMap_(sh, headers);
    let inserted=0, updated=0, skipped=0;
    p.items.forEach(item => {
      if (!item || !item.slug || item.status !== "published") { skipped++; return; }
      const key = String(item.slug).trim().toLowerCase();
      const oldRow = rowBySlug.get(key), rowNum = oldRow || sh.getLastRow()+1;
      const row = oldRow ? sh.getRange(rowNum,1,1,headers.length).getValues()[0] : new Array(headers.length).fill("");
      FIELDS.forEach(field => {
        const col=headers.indexOf(field); if(col<0) return;
        let value=item[field];
        // Preserve the manual-entry fields when syncing older published payloads that do not include them.
        if ((field === "topic" || field === "sourceUrl") && value == null && oldRow) return;
        if (Array.isArray(value) || (value && typeof value === "object")) value=JSON.stringify(value);
        if (field === "status") value="Published";
        row[col]=value == null ? "" : value;
      });
      setCell_(row,headers,"publishedUrl","https://collegedecoded.in/news/"+key);
      setCell_(row,headers,"cmsStatusUpdatedAt",new Date().toISOString());
      sh.getRange(rowNum,1,1,headers.length).setValues([row]);
      if(oldRow) updated++; else {inserted++;rowBySlug.set(key,rowNum);}
    });
    return out_({ok:true,inserted,updated,skipped,received:p.items.length});
  } catch (err) { return out_({ok:false,error:String(err && err.message || err)}); }
}

function getSheet_() {
  const ss=SpreadsheetApp.getActiveSpreadsheet();
  if(!ss) throw new Error("Bind this script to the newsroom spreadsheet.");
  let sh=ss.getSheetByName(TAB_NAME);
  if(!sh) sh=ss.insertSheet(TAB_NAME);
  return sh;
}
function ensureHeaders_(sh) {
  let headers=sh.getLastColumn()?sh.getRange(1,1,1,sh.getLastColumn()).getDisplayValues()[0].map(String):[];
  if(!headers.some(x=>x.trim())) headers=[];
  if(!headers.length) headers=ALL_FIELDS.slice();
  else ALL_FIELDS.forEach(field=>{if(!headers.includes(field))headers.push(field);});
  sh.getRange(1,1,1,headers.length).setValues([headers]);
  sh.setFrozenRows(1);
}
function rowMap_(sh,headers) {
  const col=headers.indexOf("slug")+1, map=new Map(), last=sh.getLastRow();
  if(last>1) sh.getRange(2,col,last-1,1).getDisplayValues().forEach((r,i)=>{if(r[0])map.set(String(r[0]).trim().toLowerCase(),i+2);});
  return map;
}
function getDrafts_(sh,headers) {
  const last=sh.getLastRow(), result=[];
  if(last<2) return out_({ok:true,items:[]});
  const rows=sh.getRange(2,1,last-1,headers.length).getValues();
  rows.forEach((row,index)=>{
    const item={};
    headers.forEach((h,i)=>{if(h)item[h]=row[i] == null ? "" : row[i];});
    const status=String(item.status||"").trim();
    if(status!=="Generate Draft" && status!=="Ready for Review" && status!=="In CMS Review") return;
    if(status==="Generate Draft" && (!String(item.topic||"").trim() || !String(item.sourceUrl||"").trim())) return;
    ["body","sourceLinks","relatedPages","relatedNews","keywords"].forEach(field=>{
      const value=item[field];
      if(typeof value==="string" && value.trim()){
        try{item[field]=JSON.parse(value);}catch(e){if(field==="relatedNews"||field==="keywords")item[field]=value.split("|").map(x=>x.trim()).filter(Boolean);}
      }
    });
    item.sourceRow=index+2;
    result.push(item);
  });
  return out_({ok:true,items:result});
}
function updateStatus_(sh,headers,p) {
  const lookup=String(p.slug||"").trim().toLowerCase();
  let rowNum=Number(p.sourceRow);
  if(!Number.isInteger(rowNum)||rowNum<2) {
    if(!lookup) throw new Error("slug or sourceRow is required to update a newsroom row.");
    const rowBySlug=rowMap_(sh,headers);
    rowNum=rowBySlug.get(lookup);
  }
  if(!rowNum || rowNum>sh.getLastRow()) throw new Error("No News Queue row found for slug/row: "+lookup+"/"+p.sourceRow);
  const row=sh.getRange(rowNum,1,1,headers.length).getValues()[0];
  if(p.item && typeof p.item==="object") {
    FIELDS.forEach(field=>{
      const col=headers.indexOf(field);if(col<0||p.item[field]===undefined)return;
      let value=p.item[field];
      if(Array.isArray(value)||(value&&typeof value==="object"))value=JSON.stringify(value);
      row[col]=value==null?"":value;
    });
  }
  const status=String(p.status||"");
  if(!["Ready for Review","In CMS Review","Needs Changes","Published"].includes(status)) throw new Error("Unsupported status: "+status);
  setCell_(row,headers,"status",status);
  setCell_(row,headers,"cmsStatusUpdatedAt",new Date().toISOString());
  if(p.generationError!==undefined)setCell_(row,headers,"generationError",String(p.generationError).slice(0,2000));
  if(status==="Ready for Review")setCell_(row,headers,"generationError","");
  if(p.publishedUrl)setCell_(row,headers,"publishedUrl",String(p.publishedUrl));
  if(p.cmsCommit)setCell_(row,headers,"cmsCommit",String(p.cmsCommit));
  if(p.notes!==undefined)setCell_(row,headers,"reviewNotes",String(p.notes).slice(0,2000));
  sh.getRange(rowNum,1,1,headers.length).setValues([row]);
  return out_({ok:true,status,row:rowNum});
}
function setCell_(row,headers,field,value){const col=headers.indexOf(field);if(col>=0)row[col]=value;}
function equalSecret_(a,b){if(a.length!==b.length)return false;let d=0;for(let i=0;i<a.length;i++)d|=a.charCodeAt(i)^b.charCodeAt(i);return d===0;}
function out_(v){return ContentService.createTextOutput(JSON.stringify(v)).setMimeType(ContentService.MimeType.JSON);}
