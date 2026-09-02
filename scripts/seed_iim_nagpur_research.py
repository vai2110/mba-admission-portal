import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / 'data/college-production-state.json'

SOURCES = [
    {
        'url': 'https://www.iimnagpur.ac.in/admissions/mba/admissions-policy/',
        'title': 'Admissions Policy | IIM Nagpur',
        'supports': 'MBA 2026-28 admission stages, CAT 2025 cut-offs, 340 seats, eligibility, selection weights and offer process.',
        'text': '''MBA 2026-28 is IIM Nagpur\'s two-year full-time residential flagship programme. Batch size is 340 students. Admission is conducted in three stages: Stage 1 CAT 2025 eligibility screening; Stage 2 shortlisting for Personal Interview using CAT score and profile; Stage 3 final selection using Final Score. CAT 2025 minimum overall/sectional cut-offs: General 95/70/70/70; EWS 85/55/55/55; NC-OBC 85/55/55/55; SC 65/40/40/40; ST 40/30/30/30; DAP 40/25/25/25. Final Score weightage: CAT 45%, PI 25%, Past Academic Performance 6%, Work Experience 9%, Academic Diversity 5%, Gender Diversity 10%. Offer acceptance fee is Rs.1,00,000 and is adjusted towards Term I fees. The policy states that candidates must have positive scores in all CAT sections and that selection is category-wise based on Final Score.'''
    },
    {
        'url': 'https://www.iimnagpur.ac.in/admissions/mba/fees-financial-aid-scholarship/',
        'title': 'Fees, Financial Aid & Scholarship | IIM Nagpur',
        'supports': 'MBA 2026-28 fee, acceptance fee, scholarships and financial-aid information.',
        'text': '''The total fee for the MBA 2026-28 programme is Rs.21,00,000. The fee payable at acceptance of the admission offer is Rs.1,00,000 and is adjusted towards the Term I fee. IIM Nagpur lists Merit Scholarship and Need-cum-Merit Scholarship schemes for MBA students; the published page states 10 Merit and 10 Need-cum-Merit scholarships and describes eligibility conditions.'''
    },
    {
        'url': 'https://www.iimnagpur.ac.in/programmes/mba/about-mba/',
        'title': 'About MBA | IIM Nagpur',
        'supports': 'MBA duration, residential format, pedagogy, immersion and internship structure.',
        'text': '''IIM Nagpur describes the MBA as a two-year full-time residential Master in Business Administration programme, popularly known as PGP. The programme combines lectures, classroom discussions, case studies, individual and group projects, term papers, role plays and business games. It includes three terms a year, an international immersion after the first year, field immersion and a summer internship.'''
    },
    {
        'url': 'https://www.iimnagpur.ac.in/programmes/mba/curriculum/',
        'title': 'Curriculum | IIM Nagpur',
        'supports': 'MBA curriculum structure and representative elective areas.',
        'text': '''IIM Nagpur states that its MBA curriculum is benchmarked against leading management institutes and uses lectures, case studies, projects, simulations and industry interaction. Areas and electives include Decision Science & Information Systems, Economics, Finance & Accounting, General Management, Marketing, Organizational Behaviour and HRM, Production & Operations, and Strategy & Entrepreneurship. Examples include Business Data Mining and Decision Models, Advance Analytics, Corporate Valuation, Financial Statement Analysis, FinTech, Investment Banking, B2B Marketing, Digital Marketing and E-commerce, Supply Chain Management, Operations Strategy, Management Consulting and Strategy in Action. Electives may change by academic year.'''
    },
    {
        'url': 'https://www.iimnagpur.ac.in/programmes/mba/placements/placement-reports/final-placement-reports/',
        'title': 'Final Placement Reports | IIM Nagpur',
        'supports': 'Official placement-report archive and availability of audited/final reports.',
        'text': '''The official placement archive lists the Final Placement Report 2023-25, Audited Final Placement Report 2022-24, Audited Final Placement Report 2021-23 and earlier reports.'''
    },
    {
        'url': 'https://www.iimnagpur.ac.in/wp-content/uploads/2025/05/Finals-Report-2023-25_compressed-1.pdf',
        'title': 'Final Placement Report 2023-25 | IIM Nagpur',
        'supports': 'Latest published final placement statistics for MBA 2023-25.',
        'text': '''For MBA 2023-25, 264 students participated. Average CTC was Rs.18,07,253 and median CTC was Rs.17,03,700. Highest CTC was Rs.69,57,000. Top 10% average was Rs.31,73,293; top 25% average Rs.25,14,420; top 50% average Rs.21,59,734. There were 89 new recruiters and 4 international offers. Nearly 58% of students opted for roles in Strategy & Consulting, Product Management, IT & Analytics and Sales & Marketing. Major sectors included BFSI, ITES, FMCG/FMCD, Consulting and Manufacturing.'''
    },
    {
        'url': 'https://www.iimnagpur.ac.in/wp-content/uploads/2024/06/Final-Placement-Report-2022-24-R28-June-1.pdf',
        'title': 'Final Placement Report 2022-24 | IIM Nagpur',
        'supports': 'MBA 2022-24 placement statistics.',
        'text': '''For MBA 2022-24, 255 students participated. Average CTC was Rs.16,29,241 (Rs.16.29 LPA) and median CTC was Rs.16,00,000. Highest CTC was Rs.38,40,000. Top 10% average was Rs.24,27,600; top 25% average Rs.22,04,189; top 50% average Rs.19,49,267. There were 62 new recruiters.'''
    },
    {
        'url': 'https://www.iimnagpur.ac.in/wp-content/uploads/2025/02/IIM-Nagpur_Annual-Report-2022-23_Combined.pdf',
        'title': 'Annual Report 2022-23 | IIM Nagpur',
        'supports': 'MBA 2021-23 final placement statistics and programme context.',
        'text': '''For MBA 2021-23, IIM Nagpur reported more than 100 participating firms. Average CTC rose 10.05% to Rs.16.74 LPA, median CTC was Rs.16.85 LPA and the highest offer was Rs.64 LPA. The institute reported strong participation from IT/ITES, BFSI and Consulting, with more than 70% of students opting for companies in those sectors.'''
    },
    {
        'url': 'https://www.iimnagpur.ac.in/programmes/executive-mba-hybrid-at-nagpur-and-pune/about-executive-mba-hybrid/',
        'title': 'About Executive MBA (Hybrid) | IIM Nagpur',
        'supports': 'Executive MBA (Hybrid) programme identity and eligibility.',
        'text': '''IIM Nagpur\'s two-year Executive MBA programme in hybrid mode is designed for mid- to senior-level executives. Published eligibility requires working professionals with minimum 50% marks or equivalent in graduation and minimum 3 years of work experience.'''
    },
    {
        'url': 'https://www.iimnagpur.ac.in/programmes/blended-mba-for-working-professionals/about-blended-mba-for-working-professionals/',
        'title': 'About Blended MBA for Working Professionals | IIM Nagpur',
        'supports': 'Blended MBA for Working Professionals programme information.',
        'text': '''IIM Nagpur offers a Blended MBA for Working Professionals designed for professionals seeking leadership, strategic decision-making and business-acumen development without disrupting their careers. The programme uses a blended format and integrates core management areas with emerging topics such as digital transformation, artificial intelligence and sustainability.'''
    }
]


def main():
    state = json.loads(STATE.read_text(encoding='utf-8'))
    rec = state.setdefault('colleges', {}).setdefault('25', {})
    if rec.get('research_pack'):
        print('IIM Nagpur research pack already seeded')
        return
    rec['course_plan'] = [
        {'name': 'MBA'},
        {'name': 'Executive MBA (Hybrid)'},
        {'name': 'Blended MBA for Working Professionals'}
    ]
    rec['course_filenames'] = [
        'indian-institute-of-management-nagpur-mba.html',
        'indian-institute-of-management-nagpur-executive-mba-hybrid.html',
        'indian-institute-of-management-nagpur-blended-mba-for-working-professionals.html'
    ]
    rec['research_pack'] = {
        'summary': 'IIM Nagpur offers a two-year full-time residential flagship MBA, plus Executive MBA (Hybrid) and Blended MBA for Working Professionals. Official MBA 2026-28 fee is Rs.21,00,000; batch size is 340; CAT 2025 cut-offs and final-selection weights are specified in the admissions policy. Official placement reports provide comparable MBA placement data for 2023-25, 2022-24 and 2021-23.',
        'sources': [{k: x[k] for k in ('url','title','supports')} for x in SOURCES],
        'source_material': '\n\n'.join(f"SOURCE URL: {x['url']}\nTITLE: {x['title']}\nCONTENT: {x['text']}" for x in SOURCES)
    }
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('Seeded IIM Nagpur official research pack')

if __name__ == '__main__':
    main()
