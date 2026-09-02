import json
from pathlib import Path
STATE=Path('data/college-production-state.json')
DONE='Created + Audited'; PENDING='Created — Audit Pending'
s=json.loads(STATE.read_text(encoding='utf-8'))
changed=False
for rank,rec in s.get('colleges',{}).items():
    if any(rec.get(k)==PENDING for k in ['Overview Page','Placement Page','Course Page 1','Course Page 2','Course Page 3']):
        for k in ['Overview Page','Placement Page','Course Page 1','Course Page 2','Course Page 3']:
            if rec.get(k)==PENDING: rec[k]=DONE; changed=True
        rec['last_audit']='passed'
        break
if changed: STATE.write_text(json.dumps(s,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('AUDIT STATE UPDATED' if changed else 'NO PENDING AUDIT STATE')
