from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path('.')
FILES = sorted(ROOT.glob('kj-somaiya-institute-of-management*.html'))

DISCUSSION = '''
<div class="source-note"><strong>How to read this cutoff:</strong> KJSIM's current official admission page says merit-based shortlisting uses institute cutoffs, but the page reviewed does not publish one fixed numeric cutoff. The figures below are therefore <strong>community/third-party reference points, not official KJSIM cutoffs</strong>.</div>
<div class="data-grid cutoff-grid">
  <div class="data-card"><span class="data-label">CAT</span><strong>~82–87 percentile</strong><p>PaGaLGuY's 2026 expected range. Older student discussions also mention CAT cutoffs around the low-80s in earlier cycles.</p></div>
  <div class="data-card"><span class="data-label">XAT</span><strong>~70–85 percentile</strong><p>PaGaLGuY's 2026 expected range. A 2026 Reddit conversion post reports an 87.5 XAT percentile converting KJSIM after the interview.</p></div>
  <div class="data-card"><span class="data-label">CMAT</span><strong>~94–98 percentile</strong><p>PaGaLGuY's 2026 expected range. A March 2026 Reddit discussion reported a student-facing reference of about 98.xx for CMAT shortlisting.</p></div>
  <div class="data-card"><span class="data-label">NMAT</span><strong>~223–230</strong><p>PaGaLGuY's 2026 expected score range. Treat this only as a planning benchmark because KJSIM's official page does not publish a fixed number.</p></div>
</div>
<h3>What students are actually discussing</h3>
<div class="discussion-box">
  <p><strong>Reddit — April 2026:</strong> one candidate reported converting KJSIM with 87.5 XAT after a 77 CAT score and described the interview process and ROI concerns. This is an individual experience, not a cutoff rule.</p>
  <p><strong>Reddit — March 2026:</strong> a discussion around CMAT shortlisting included a user-reported reference of about 98.xx. Again, this should not be treated as an institute notification.</p>
  <p><strong>PaGaLGuY — 2026:</strong> the KJSIM college page lists expected 2026 ranges of CAT 82–87, XAT 70–85, CMAT 94–98 and NMAT 223–230.</p>
</div>
<div class="discussion-links"><a href="https://www.reddit.com/r/CATpreparation/comments/1smpoz7/875_ile_in_xat_3_years_gap_terrible_interview/" target="_blank" rel="noopener">Reddit: 87.5 XAT KJSIM conversion experience ↗</a><a href="https://www.reddit.com/r/NMATpreparation/comments/1rox2td/kj_somaiya/" target="_blank" rel="noopener">Reddit: KJSIM CMAT shortlisting discussion ↗</a><a href="https://www.pagalguy.com/colleges/kj-somaiya-institute-of-management-studies-and-research-simsr-mumbai" target="_blank" rel="noopener">PaGaLGuY: KJSIM cutoff reference page ↗</a></div>
<div class="warning-box"><h3>Do not confuse a reference percentile with a guaranteed call</h3><p>KJSIM also uses profile-based shortlisting and evaluates academics, work experience and the subsequent PSA/WAT/PI process. A candidate near a community-reported number can therefore receive a different outcome from another candidate with a similar score.</p></div>
'''

PLACEMENT = '''
<div class="answer-box placement-answer"><strong>Latest official picture</strong><p>For MBA 2024–26, KJSIM reports a <strong>₹29.30 LPA highest package</strong>, <strong>₹12 LPA median CTC</strong> and <strong>210 recruiters</strong>. For the 2025–27 internship cycle, the institute reports <strong>126 recruiters</strong> and a <strong>₹3 lakh highest stipend</strong>.</p></div>
<div class="data-grid placement-grid">
  <div class="data-card"><span class="data-label">Highest CTC</span><strong>₹29.30 LPA</strong><p>Top reported package for MBA 2024–26. It represents the upper end, not the typical outcome.</p></div>
  <div class="data-card"><span class="data-label">Median CTC</span><strong>₹12 LPA</strong><p>The more useful headline figure for judging the middle of the reported salary distribution.</p></div>
  <div class="data-card"><span class="data-label">Recruiters</span><strong>210</strong><p>Reported final-placement recruiter participation for MBA 2024–26.</p></div>
  <div class="data-card"><span class="data-label">Internships</span><strong>126 recruiters</strong><p>Reported for the 2025–27 internship cycle, with ₹3 lakh highest stipend.</p></div>
</div>
<h3>Placement numbers students should compare</h3>
<div class="table-wrapper"><table><tr><th>Metric</th><th>Latest reported figure</th><th>How to interpret it</th></tr><tr><td>Highest CTC</td><td>₹29.30 LPA</td><td>Top-end outcome; not representative of the batch.</td></tr><tr><td>Median CTC</td><td>₹12 LPA</td><td>Better benchmark for a typical middle outcome than the highest package.</td></tr><tr><td>Final recruiters</td><td>210</td><td>Shows breadth of corporate participation; does not indicate how many students each recruiter hired.</td></tr><tr><td>Internship recruiters</td><td>126</td><td>Indicates the scale of summer internship participation.</td></tr><tr><td>Highest internship stipend</td><td>₹3 lakh</td><td>Top stipend; should not be treated as the average stipend.</td></tr><tr><td>Top 10% internship average</td><td>₹1,43,950</td><td>Useful for understanding the upper segment of internship outcomes.</td></tr><tr><td>Top 20% internship average</td><td>₹1,14,394</td><td>Shows how the upper-quartile internship outcomes compare with the top stipend.</td></tr></table></div>
<h3>What kind of corporate exposure does KJSIM provide?</h3>
<p>The institute's Professional Development &amp; Placement model includes guest lectures, corporate competitions, corporate projects, full-time summer internships and final placements. That means placement preparation is not limited to the final recruitment season; students are exposed to employers and applied projects during the programme as well.</p>
<div class="placement-path"><div><strong>1. Industry exposure</strong><span>Guest lectures, competitions and corporate interaction.</span></div><div><strong>2. Applied work</strong><span>Corporate projects and summer internships.</span></div><div><strong>3. Recruitment</strong><span>Final placement process with participating employers.</span></div><div><strong>4. Role-level evaluation</strong><span>Compare functions, role quality and salary—not recruiter count alone.</span></div></div>
<h3>Recruiters and roles: what students should check</h3>
<p>Recent third-party placement coverage lists recruiters such as <strong>Mercedes-Benz, Cisco, J.P. Morgan, Salesforce, Wipro, Maruti Suzuki, Piramal Pharma and General Mills</strong>. These names are useful for understanding employer breadth, but recruiter participation can vary by batch and hiring requirement.</p>
<p>Before judging placement quality, check the role offered, location, fixed versus variable pay, batch size, number of offers, internship-to-PPO conversion where available, and the programme from which the recruiter hired. A famous recruiter name alone does not establish a better outcome.</p>
<div class="source-note"><strong>Source discipline:</strong> salary and recruiter-count figures above are anchored to KJSIM's current Professional Development &amp; Placement page. The recruiter examples are presented as recent third-party reporting and should not be read as a guaranteed recruiter list for every batch.</div>
<div class="discussion-links"><a href="https://kjsim.somaiya.edu/en/professional-development-placement/" target="_blank" rel="noopener">KJSIM official placement page ↗</a><a href="https://www.careers360.com/colleges/k-j-somaiya-institute-of-management-mumbai/placement" target="_blank" rel="noopener">Careers360 placement reporting ↗</a><a href="https://collegedunia.com/college/18230-kj-somaiya-institute-of-management-mumbai/placement" target="_blank" rel="noopener">CollegeDunia placement reporting ↗</a></div>
'''

DECISION = '''
<p>Whether KJSIM is a good choice depends on the combination of <strong>career target, entrance score, profile, financing and expected salary outcome</strong>. The highest package should not be the deciding number.</p>
<div class="decision-grid"><div class="decision-card"><strong>Choose the flagship MBA if…</strong><span>You want broad management exposure, major/minor flexibility and access to Mumbai's corporate ecosystem.</span></div><div class="decision-card"><strong>Look carefully at ROI if…</strong><span>Your financing requires a large loan. Compare the ₹12 LPA median CTC with the published programme fee and your expected living/hostel costs.</span></div><div class="decision-card"><strong>Do not decide from cutoff alone if…</strong><span>Your score is close to a community-reported range. KJSIM also considers academics, work experience and the PSA/WAT/PI process.</span></div><div class="decision-card"><strong>Ask about role quality if…</strong><span>You are comparing KJSIM with another B-school. Function, fixed pay, location and growth potential can matter more than the highest CTC.</span></div></div>
'''

FAQ_EXTRA = '''
<div class="faq-item"><h3>What is a safe CAT percentile for KJ Somaiya?</h3><p>There is no single official “safe” percentile published on the current KJSIM page. Community references for 2026 commonly place CAT expectations in the low-to-high 80s, but these are planning estimates rather than guaranteed cutoffs.</p></div>
<div class="faq-item"><h3>Can a candidate below the expected cutoff still be considered?</h3><p>For the flagship MBA, KJSIM states that candidates who do not qualify through merit-based shortlisting may be considered through profile-based criteria, subject to the institute's conditions. This makes profile strength relevant in addition to the entrance score.</p></div>
<div class="faq-item"><h3>Is ₹29.30 LPA the average salary at KJ Somaiya?</h3><p>No. ₹29.30 LPA is the highest reported CTC. The latest official placement page reports ₹12 LPA as the median CTC. These two numbers answer different questions.</p></div>
'''

CSS = '''
/* KJSIM content-depth and presentation enhancements */
.data-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:18px 0}.data-card,.decision-card{border:1px solid #d8e0ea;border-radius:12px;padding:18px;background:#fff;box-shadow:0 3px 12px rgba(20,40,70,.05)}.data-card .data-label{display:block;font-size:.78rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:#536b83;margin-bottom:7px}.data-card strong{display:block;font-size:1.28rem;color:#123b67;margin-bottom:7px}.data-card p{margin:0;line-height:1.55}.source-note{margin:18px 0;padding:14px 16px;border-left:4px solid #2b6fd6;background:#f4f8fd;border-radius:8px;line-height:1.6}.discussion-box{margin:16px 0;padding:18px;background:#fafbfd;border:1px solid #dce4ee;border-radius:10px}.discussion-box p{margin:0 0 12px}.discussion-box p:last-child{margin-bottom:0}.discussion-links{display:flex;flex-wrap:wrap;gap:9px;margin:16px 0}.discussion-links a{display:inline-block;padding:9px 12px;border:1px solid #c9d7e8;border-radius:7px;background:#fff;color:#135dcc;text-decoration:none;font-weight:600;font-size:.9rem}.placement-path{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:18px 0}.placement-path>div{padding:15px;border-radius:10px;background:#f6f8fb;border:1px solid #dce3ec}.placement-path strong,.placement-path span{display:block}.placement-path strong{margin-bottom:6px;color:#123b67}.placement-path span{font-size:.92rem;line-height:1.45}.decision-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:16px}.decision-card strong,.decision-card span{display:block}.decision-card strong{margin-bottom:7px;color:#123b67}.decision-card span{line-height:1.55}.placement-answer{margin-bottom:18px}.main-section h3{margin-top:24px}.table-wrapper table td,.table-wrapper table th{vertical-align:top}@media(max-width:800px){.data-grid,.decision-grid{grid-template-columns:1fr}.placement-path{grid-template-columns:1fr 1fr}.discussion-links{display:grid;grid-template-columns:1fr}.discussion-links a{text-align:center}}@media(max-width:520px){.placement-path{grid-template-columns:1fr}.data-card,.decision-card{padding:15px}}
'''


def section(soup, sid):
    return soup.find('section', id=sid)


def replace_section(sec, title, body):
    sec.clear()
    h2 = sec soup if False else None
    h = sec.new_tag('h2')
    h.string = title
    sec.append(h)
    frag = BeautifulSoup(body, 'html.parser')
    for node in list(frag.contents):
        sec.append(node)


def add_faqs(sec):
    if sec is None:
        return
    frag = BeautifulSoup(FAQ_EXTRA, 'html.parser')
    for node in list(frag.contents):
        sec.append(node)

for path in FILES:
    raw = path.read_text(encoding='utf-8')
    soup = BeautifulSoup(raw, 'html.parser')

    # Load enhancement stylesheet once per page.
    if not soup.find('link', href='kjsim-enhancements.css'):
        link = soup.new_tag('link', rel='stylesheet', href='kjsim-enhancements.css')
        soup.head.append(link)

    cut = section(soup, 'cutoff')
    if cut:
        replace_section(cut, 'KJ Somaiya MBA Cutoff: Official Position + Student Reference Range', DISCUSSION)

    place = section(soup, 'placements')
    if place:
        replace_section(place, 'KJ Somaiya Placements: Latest MBA Outcomes, Roles & ROI', PLACEMENT)

    # The dedicated placements page has a different section structure.
    if path.name.endswith('-placements.html'):
        latest = section(soup, 'latest')
        if latest:
            replace_section(latest, 'KJ Somaiya Placements: Latest Official Highlights', PLACEMENT)
        # Keep snapshot as a concise data table; enrich the remaining sections.
        snapshot = section(soup, 'snapshot')
        if snapshot:
            replace_section(snapshot, 'KJ Somaiya Placement Snapshot: What Each Number Means', PLACEMENT)
        recruiters = section(soup, 'recruiters')
        if recruiters:
            replace_section(recruiters, 'KJ Somaiya Recruiters, Functions & Industry Exposure', PLACEMENT)
        internships = section(soup, 'internships')
        if internships:
            replace_section(internships, 'KJ Somaiya Summer Internships: Stipend & Recruiter Data', PLACEMENT)
        yearwise = section(soup, 'yearwise')
        if yearwise:
            replace_section(yearwise, 'KJ Somaiya Placement Trends: How to Compare Batches', '''<p>KJSIM's public reporting can present different metrics for different batches. The safest comparison is to keep the <strong>batch, programme and metric definition identical</strong>.</p><div class="data-grid"><div class="data-card"><span class="data-label">Latest final placement</span><strong>2024–26</strong><p>₹29.30 LPA highest, ₹12 LPA median and 210 recruiters on the current official highlight page.</p></div><div class="data-card"><span class="data-label">Latest internship cycle</span><strong>2025–27</strong><p>126 recruiters and ₹3 lakh highest stipend on the current official page.</p></div></div><div class="warning-box"><h3>Why not publish a misleading year-wise average table?</h3><p>Older and newer reports can use different batch sizes, programme scopes and definitions. Mixing them into one trend line can make placement performance look better or worse than the underlying data supports.</p></div>''')
        interp = section(soup, 'interpretation')
        if interp:
            replace_section(interp, 'How Students Should Interpret KJ Somaiya Placements', PLACEMENT + DECISION)
        faqs = section(soup, 'faqs')
        if faqs:
            add_faqs(faqs)
    else:
        decision = section(soup, 'decision')
        if decision:
            replace_section(decision, 'Is KJ Somaiya a Good Fit for You?', DECISION)
        faqs = section(soup, 'faqs')
        if faqs:
            add_faqs(faqs)

    path.write_text(str(soup), encoding='utf-8')

Path('kjsim-enhancements.css').write_text(CSS, encoding='utf-8')
print('Enhanced:', ', '.join(p.name for p in FILES))
