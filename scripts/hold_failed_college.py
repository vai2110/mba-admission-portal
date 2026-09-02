import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / 'data/college-queue.csv'
STATE = ROOT / 'data/college-production-state.json'
TARGETS = ROOT / 'changed-html.txt'


def main():
    state = json.loads(STATE.read_text(encoding='utf-8'))
    with QUEUE.open(encoding='utf-8-sig', newline='') as f:
        queue = list(csv.DictReader(f))

    target_pages = {x.strip() for x in TARGETS.read_text(encoding='utf-8').splitlines() if x.strip()} if TARGETS.exists() else set()
    cols = ['Overview Page', 'Placement Page', 'Course Page 1', 'Course Page 2', 'Course Page 3']
    selected = None

    for row in queue:
        rank = str(row['rank'])
        rec = state.setdefault('colleges', {}).setdefault(rank, {})
        files = [
            f"{row['college_name'].lower().replace(' ', '-')}.html",
            f"{row['college_name'].lower().replace(' ', '-')}-placements.html",
        ]
        files.extend(rec.get('course_filenames', []))
        files = {x for x in files if x}
        if target_pages.intersection(files):
            selected = (rank, row['college_name'], rec)
            break

    if not selected:
        print('No benchmark-failed college could be mapped from changed-html.txt; leaving state unchanged.')
        return

    rank, college, rec = selected
    rec['held'] = True
    rec['hold_reason'] = 'Benchmark gate failed after recovery passes; revisit after remaining queue colleges.'
    rec['hold_timestamp_utc'] = __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
    state['colleges'][rank] = rec
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'HOLD {rank} {college}: benchmark recovery exhausted; queue will continue with the next unheld college.')


if __name__ == '__main__':
    main()
