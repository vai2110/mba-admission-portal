#!/usr/bin/env node
const fs=require('fs');
const norm=s=>String(s||'').trim().toLowerCase().replace(/[^a-z0-9]+/g,'');
const numbers=(v,field='')=>(String(v||'').replace(/,/g,'').match(/\d+(?:\.\d+)?/g)||[]).map(Number).filter(n=>!(field==='fees'&&n>=1900&&n<=2100)).join('|');
const overrides=JSON.parse(fs.readFileSync('mba-college-official-overrides.json','utf8')).records||[];
const comparison=JSON.parse(fs.readFileSync('mba-college-comparison-data.json','utf8')).colleges||[];
const cards=JSON.parse(fs.readFileSync('mba-college-card-data.json','utf8')).records||[];
const failures=[];
function bestComparison(o){
  const candidates=comparison.filter(x=>String(x.rank)===String(o.rank));
  if(!candidates.length)return null;
  const on=norm(o.name); let best=null,bestScore=-1;
  for(const c of candidates){
    const cn=norm(c.name); let score=cn===on?100:0;
    if(cn.includes(on)||on.includes(cn))score+=50;
    const ot=on.match(/.{1,4}/g)||[],ct=cn.match(/.{1,4}/g)||[];
    score+=ot.filter(t=>ct.includes(t)).length;
    if(score>bestScore){bestScore=score;best=c;}
  }
  return best;
}
for(const o of overrides){
  if(!o.verified_current)continue;
  const c=bestComparison(o);
  if(!c){failures.push(`missing comparison record for rank ${o.rank}: ${o.name}`);continue;}
  for(const [of,cf] of [['fees','fees'],['average_package','average_package'],['median_package','median_package']]){
    if(String(o[of]||'').trim()&&numbers(o[of],of)!==numbers(c[cf],cf))failures.push(`rank ${o.rank} ${o.name}: override ${of}="${o[of]}" != comparison ${cf}="${c[cf]||''}"`);
  }
  if(String(o.placement_year||'').trim()&&String(o.placement_year).trim()!==String(c.placement_year||'').trim())failures.push(`rank ${o.rank} ${o.name}: placement_year mismatch`);
}
for(const c of cards){
  if(!c.url||!c.sourceUrl||!c.feeSourceUrl||!c.packageSourceUrl)failures.push(`homepage card ${c.id}: missing URL/source metadata`);
  const p=c.url.replace(/^\//,'');
  if(!fs.existsSync(p+'.html'))failures.push(`homepage card ${c.id}: profile file ${p}.html missing`);
}
if(failures.length){console.error('COLLEGE DATA CONSISTENCY GATE FAILED');failures.forEach(x=>console.error(' - '+x));process.exit(1);}
console.log(`COLLEGE DATA CONSISTENCY GATE PASSED: ${comparison.length} comparison records, ${overrides.length} official overrides, ${cards.length} homepage cards checked.`);
