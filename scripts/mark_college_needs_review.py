import json
from pathlib import Path

STATE = Path('data/college-production-state.json')
PENDING = 'Created — Audit Pending'
REVIEW = 'Needs Review'
COLS = ['Overview Page', 'Placement Page', 'Course Page 1', 'Course Page 2', 'Course Page 3']

state = json.loads(STATE.read_text(encoding='utf-8'))
changed = False
selected = None

# Release only the first audit-pending college. This prevents one
# unresolved audit defect from blocking the entire production queue.
for rank in sorted(state.get('colleges', {}), key=lambda x: int(x)):
    rec = state['colleges'][rank]
    if any(rec.get(k) == PENDING for k in COLS):
        selected = rank
        for k in COLS:
            if rec.get(k) == PENDING:
                rec[k] = REVIEW
                changed = True
        rec['last_audit'] = 'failed — moved to Needs Review'
        rec['audit_block_reason'] = 'Automated benchmark gate remained unresolved after repair passes; college released from queue for later retry.'
        break

if changed:
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'COLLEGE MOVED TO NEEDS REVIEW: #{selected}')
else:
    print('NO PENDING AUDIT TRANSACTION FOUND')
