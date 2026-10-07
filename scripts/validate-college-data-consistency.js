#!/usr/bin/env node
const fs=require('fs');
const norm=s=>String(s||'').trim().toLowerCase().replace(/[^a-z0-9]+/g,'');
const overrides=JSON.parse(fs.readFileSync('mba-college-official-overrides.json','utf8')).records||[];
const comparison=JSON.parse(fs.readFileSync('mba-college-comparison-data.json','utf8')).colleges||[];
const cards=JSON.parse(fs.readFileSync('mba-college-card-data.json','utf8')).records||[];
const byRank=new Map(comparison.map(x=>[String(x.rank),x]));
const failures=[];
for(const o of overrides){
  const c=byRank.get(String(o.rank));
  if(!c){failures.push(`missing comparison record for rank ${o.rank}: ${o.name}`);continue;}
  for(const [of,cf] of [['fees','fees'],['average_package','average_package'],['median_package','median_package'],['placement_year','placement_year']]){
    if(String(o[of]||'').trim() && String(o[of]).trim()!==String(c[cf]||'').trim()){
      failures.push(`rank ${o.rank} ${o.name}: override ${of}="${o[of]}" != comparison ${cf}="${c[cf]||''}"`);
    }
  }
}
const cardById=new Map(cards.map(x=>[x.id,x]));
for(const c of cards){
  if(!c.url || !c.sourceUrl || !c.feeSourceUrl || !c.packageSourceUrl) failures.push(`homepage card ${c.id}: missing URL/source metadata`);
  const p=c.url.replace(/^\//,'');
  if(!fs.existsSync(p+'.html')) failures.push(`homepage card ${c.id}: profile file ${p}.html missing`);
}
if(failures.length){
  console.error('COLLEGE DATA CONSISTENCY GATE FAILED');
  failures.forEach(x=>console.error(' - '+x));
  process.exit(1);
}
console.log(`COLLEGE DATA CONSISTENCY GATE PASSED: ${comparison.length} comparison records, ${overrides.length} official overrides, ${cards.length} homepage cards checked.`);
