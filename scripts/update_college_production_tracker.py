import csv, json
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

ROOT=Path(__file__).resolve().parents[1]
QUEUE=ROOT/'data/college-queue.csv'; STATE=ROOT/'data/college-production-state.json'
OUT=ROOT/'college-production-tracker.xlsx'; CSV_OUT=ROOT/'college-production-tracker.csv'
PAGE_COLS=['Overview Page','Placement Page','Course Page 1','Course Page 2','Course Page 3']; DONE='Created + Audited'; PENDING='Pending'

def loadq():
    with QUEUE.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def loads():
    try: return json.loads(STATE.read_text(encoding='utf-8'))
    except Exception: return {}
def rows():
    q=loadq(); s=loads(); legacy={int(x) for x in s.get('legacy_completed_ranks',list(range(1,22)))}; out=[]
    for r in q:
        rank=int(r['rank']); rec=s.get('colleges',{}).get(str(rank),{}); vals=[rec.get(c,DONE if rank in legacy else PENDING) for c in PAGE_COLS]
        out.append([r['college_name'],*vals])
    return out

def build():
    data=rows(); headers=['College Name',*PAGE_COLS]
    with CSV_OUT.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f); w.writerow(headers); w.writerows(data)
    wb=Workbook(); ws=wb.active; ws.title='College Queue'; ws.append(headers)
    for r in data: ws.append(r)
    out=wb.create_sheet('Completed Outside 100'); out.append(['College Name','Status','Pages']); out.append(['SIBM Bengaluru',DONE,'Overview; MBA; MBA Business Analytics; MBA Executive; Placements'])
    legend=wb.create_sheet('Status Legend'); legend.append(['Status','Meaning'])
    for a,b in [(PENDING,'Not started'),('Creating','Currently being created'),('Created — Audit Pending','Created but audit is not yet passed'),(DONE,'Created and audit passed'),('Needs Review','Blocked or failed validation')]: legend.append([a,b])
    navy='17336F'; green='15803D'; amber='B45309'; blue='2563EB'; red='B91C1C'; gray='64748B'; border='DCE3EB'; white='FFFFFF'; thin=Side(style='thin',color=border)
    for sh in wb.worksheets:
        sh.sheet_view.showGridLines=False
        for c in sh[1]: c.font=Font(bold=True,color=white); c.fill=PatternFill('solid',fgColor=navy); c.alignment=Alignment(wrap_text=True,vertical='center'); c.border=Border(bottom=thin)
        sh.row_dimensions[1].height=28
        for row in sh.iter_rows(min_row=2):
            for c in row: c.alignment=Alignment(wrap_text=True,vertical='top'); c.border=Border(bottom=thin)
    for i,w in enumerate([42,24,24,24,24,24],1): ws.column_dimensions[get_column_letter(i)].width=w
    ws.freeze_panes='B2'; ws.auto_filter.ref=f'A1:F{ws.max_row}'
    from openpyxl.formatting.rule import FormulaRule
    rng=f'B2:F{ws.max_row}'
    for formula,fill,font in [('B2="Created + Audited"','DCFCE7',green),('B2="Pending"','F8FAFC',gray),('B2="Creating"','FEF3C7',amber),('B2="Created — Audit Pending"','DBEAFE',blue),('B2="Needs Review"','FEE2E2',red)]: ws.conditional_formatting.add(rng,FormulaRule(formula=[formula],fill=PatternFill('solid',fgColor=fill),font=Font(color=font,bold=True)))
    wb.save(OUT)

if __name__=='__main__': build()
