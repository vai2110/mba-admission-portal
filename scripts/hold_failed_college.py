import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / 'data/college-queue.csv'
STATE = ROOT / 'data/college-production-state.json'
TARGETS = ROOT / 'changed-html.txt'
DONE = 'Created + Audited'
COLS = ['Overview Page', 'Placement Page', 'Course Page 1', 'Course Page 2', 'Course Page 3']


def slug(s):
    import re
    return re.sub(r'[^a-z0-9]+', '-', s.lower().replace('&', ' and ')).strip('-')


def main():
    state = json.loads(STATE.read_text(encoding='utf-8'))
    with QUEUE.open(encoding='utf-8-sig', newline='') as f:
        queue = list(csv.DictReader(f))

    target_pages = {x.strip() for x in TARGETS.read_text(encoding='utf-8').splitlines() if x.strip()} if TARGETS.exists() else set()
    selected = None

    for row in queue:
        rank = str(row['rank'])
        rec = state.setdefault('colleges', {}).setdefault(rank, {})
        if all(rec.get(c) in (DONE, 'Not Applicable') for c in COLS) or rec.get('held'):
            continue
        files = {f"{slug(row['college_name'])}.html", f"{slug(row['college_name'])}-placements.html"}
        files.update(x for x in rec.get('course_filenames', []) if x)
        if target_pages and not target_pages.intersection(files):
            continue
        selected = (rank, row['college_name'], rec)
        break

    if not selected:
        print('No specific failed college matched target pages; selecting the first unheld pending college.')
        for row in queue:
            rank = str(row['rank'])
            rec = state.setdefault('colleges', {}).setdefault(rank, {})
            if all(rec.get(c) in (DONE, 'Not Applicable') for c in COLS) or rec.get('held'):
                continue
            selected = (rank, row['college_name'], rec)
            break

    if not selected:
        print('QUEUE COMPLETE')
        return

    rank, college, rec = selected
    rec['held'] = True
    rec['hold_reason'] = 'Automatic recovery hold after production failure; revisit after remaining queue colleges.'
    rec['hold_timestamp_utc'] = datetime.now(timezone.utc).isoformat()
    state['colleges'][rank] = rec
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'HOLD {rank} {college}: failure isolated; queue can continue with the next unheld college.')


if __name__ == '__main__':
    main()
