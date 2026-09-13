import json, os, re
from urllib.parse import urlparse

DATA='mba-cutoff-data.json'
with open(DATA,encoding='utf-8') as f: d=json.load(f)
files=set(os.listdir('.'))
report=[]
for exam, block in d.get('exams',{}).items():
    for row in block.get('rows',[]):
        p=row.get('page','')
        is_local=bool(p) and not urlparse(p).scheme and not p.startswith('//')
        exists=is_local and p in files
        report.append({"exam":exam,"college":row.get('college'),"page":p,"local":is_local,"exists":exists})
missing=[r for r in report if r['local'] and not r['exists']]
external=[r for r in report if not r['local']]
out={"total_rows":len(report),"local_rows":sum(r['local'] for r in report),"local_missing":len(missing),"external_rows":len(external),"missing":missing,"external":external}
with open('cutoff-page-link-audit.json','w',encoding='utf-8') as f: json.dump(out,f,indent=2,ensure_ascii=False)
print(json.dumps(out,indent=2,ensure_ascii=False))
