from pathlib import Path

AGENT = Path('scripts/college_queue_agent.py')

POPULAR = {
    'SVKM`s Narsee Monjee Institute of Management Studies': 'NMIMS',
    'Management Development Institute': 'MDI Gurgaon',
    'XLRI - Xavier School of Management': 'XLRI',
    'Symbiosis Institute of Business Management': 'SIBM Pune',
    'S. P. Jain Institute of Management and Research': 'SPJIMR',
    'Indian Institute of Foreign Trade': 'IIFT',
    'Institute of Management Technology': 'IMT Ghaziabad',
    'Institute of Management Technology, Nagpur': 'IMT Nagpur',
    'Birla Institute of Management Technology': 'BIMTECH',
    'T. A. Pai Management Institute Manipal': 'TAPMI Manipal',
    'Fore School of Management': 'FORE School of Management',
    'K.J.Somaiya Institute of Management': 'KJ Somaiya Institute of Management',
    'Loyola Institute of Business Administration': 'LIBA Chennai',
    'National Institute of Technology Tiruchirappalli': 'NIT Trichy',
    'National Institute of Technology Calicut': 'NIT Calicut',
    'Malaviya National Institute of Technology': 'MNIT Jaipur',
    'Jamia Millia Islamia': 'JMI',
    'Banaras Hindu University': 'BHU',
    'Aligarh Muslim University': 'AMU',
    'Guru Gobind Singh Indraprastha University': 'GGSIPU',
    'Babasheb Bhimrao Ambedkar University': 'BBAU',
    'Atal Bihari Vajpayee Indian Institute of Information Technology and Management': 'ABV-IIITM Gwalior',
    'Indian Institute of Technology (Indian School of Mines)': 'IIT (ISM) Dhanbad',
    'Kalinga Institute of Industrial Technology': 'KIIT',
    'Koneru Lakshmaiah Education Foundation University (K L College of Engineering)': 'KL University',
    'Jagan Institute of Management Studies': 'JIMS Rohini',
    'Pandit Deendayal Energy University': 'PDEU',
    'Thiagarajar School of Management': 'TSM Madurai',
    'New Delhi Institute of Management': 'NDIM Delhi',
    'Institute of Rural Management Anand': 'IRMA',
    'National Institute of Agricultural Extension Management': 'MANAGE Hyderabad',
    'Bharathidasan Institute of Management': 'BIM Trichy',
    'Birla Institute of Technology': 'BIT Mesra',
    'Indian Institute of Technology Jodhpur': 'IIT Jodhpur',
}


def popular_name(official):
    if official in POPULAR:
        return POPULAR[official]
    if official.startswith('Indian Institute of Management, '):
        return 'IIM ' + official.split(',', 1)[1].strip()
    if official.startswith('Indian Institute of Management '):
        return 'IIM ' + official[len('Indian Institute of Management '):].split('(')[0].strip()
    if official.startswith('Indian Institute of Technology '):
        return 'IIT ' + official[len('Indian Institute of Technology '):].split('(')[0].strip()
    if official.startswith('National Institute of Technology '):
        return 'NIT ' + official[len('National Institute of Technology '):].strip()
    return official


def main():
    text = AGENT.read_text(encoding='utf-8')

    # Idempotency guard: if the current agent already contains the popular-name
    # selection logic, this workflow step must be a safe no-op.
    if "official_name = row['college_name']" in text and "rec['popular_name'] = college" in text:
        print('Popular-name production-agent block already applied; skipping.')
        return

    if 'def popular_name(' not in text:
        marker = '\ndef loadq():'
        injection = '\n\nPOPULAR = ' + repr(POPULAR) + '''\n\n\ndef popular_name(official):\n    if official in POPULAR:\n        return POPULAR[official]\n    if official.startswith('Indian Institute of Management, '):\n        return 'IIM ' + official.split(',', 1)[1].strip()\n    if official.startswith('Indian Institute of Management '):\n        return 'IIM ' + official[len('Indian Institute of Management '):].split('(')[0].strip()\n    if official.startswith('Indian Institute of Technology '):\n        return 'IIT ' + official[len('Indian Institute of Technology '):].split('(')[0].strip()\n    if official.startswith('National Institute of Technology '):\n        return 'NIT ' + official[len('National Institute of Technology '):].strip()\n    return official\n'''
        if marker not in text:
            raise SystemExit('Production-agent insertion point was not found; refusing unsafe patch.')
        text = text.replace(marker, injection + marker, 1)

    old_variants = [
        "    rank = int(row['rank'])\n    college = row['college_name']\n    official_url = row['official_url'].rstrip('/')\n    domain = urlparse(official_url).netloc\n    rec = s.setdefault('colleges', {}).setdefault(str(rank), {})\n    print(f'Next college: #{rank} {college}')\n",
        "    rank = int(row['rank'])\n    college = row['college_name']\n    official_url = row['official_url'].rstrip('/')\n    domain = urlparse(official_url).netloc\n    rec = s.setdefault('colleges', {}).setdefault(str(rank), {})\n    if rec.get('held'):\n        print(f'Revisiting previously held college: #{rank} {college}')\n        rec.pop('held', None)\n        rec.pop('hold_reason', None)\n        rec.pop('hold_timestamp_utc', None)\n        saves(s)\n    print(f'Next college: #{rank} {college}')\n"
    ]
    new = "    rank = int(row['rank'])\n    official_name = row['college_name']\n    official_url = row['official_url'].rstrip('/')\n    domain = urlparse(official_url).netloc\n    rec = s.setdefault('colleges', {}).setdefault(str(rank), {})\n    if rec.get('held'):\n        print(f'Revisiting previously held college: #{rank} {official_name}')\n        rec.pop('held', None)\n        rec.pop('hold_reason', None)\n        rec.pop('hold_timestamp_utc', None)\n        saves(s)\n    college = rec.get('popular_name') or popular_name(official_name)\n    rec['popular_name'] = college\n    print(f'Next college: #{rank} {college} (official: {official_name})')\n"
    for old in old_variants:
        if old in text:
            text = text.replace(old, new, 1)
            break
    else:
        raise SystemExit('Expected production-agent college-selection block was not found; refusing unsafe patch.')

    AGENT.write_text(text, encoding='utf-8')
    print('Popular-name SEO rules applied safely.')


if __name__ == '__main__':
    main()
