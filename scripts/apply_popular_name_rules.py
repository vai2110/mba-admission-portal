from pathlib import Path

AGENT = Path('scripts/college_queue_agent.py')

# The queue keeps official names. Production pages use the names students commonly search.
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
    'Rajagiri Business School': 'Rajagiri Business School',
    'Pandit Deendayal Energy University': 'PDEU',
    'Thiagarajar School of Management': 'TSM Madurai',
    'New Delhi Institute of Management': 'NDIM Delhi',
    'Institute of Rural Management Anand': 'IRMA',
    'National Institute of Agricultural Extension Management': 'MANAGE Hyderabad',
    'Bharathidasan Institute of Management': 'BIM Trichy',
    'Birla Institute of Technology': 'BIT Mesra',
    'Indian Institute of Technology Jodhpur': 'IIT Jodhpur',
}


def popular_name(official, url=''):
    if official in POPULAR:
        return POPULAR[official]
    if official.startswith('Indian Institute of Management, '):
        return 'IIM ' + official.split(',', 1)[1].strip()
    if official.startswith('Indian Institute of Management '):
        suffix = official[len('Indian Institute of Management '):].strip()
        return 'IIM ' + suffix.split('(')[0].strip()
    if official.startswith('Indian Institute of Technology '):
        suffix = official[len('Indian Institute of Technology '):].strip()
        return 'IIT ' + suffix.split('(')[0].strip()
    if official.startswith('National Institute of Technology '):
        return 'NIT ' + official[len('National Institute of Technology '):].strip()
    return official

text = AGENT.read_text(encoding='utf-8')
if 'def popular_name(' not in text:
    marker = '\ndef loadq():'
    injection = '''\n\nPOPULAR = ''' + repr(POPULAR) + '''\n\n\ndef popular_name(official, url=''):\n    if official in POPULAR:\n        return POPULAR[official]\n    if official.startswith('Indian Institute of Management, '):\n        return 'IIM ' + official.split(',', 1)[1].strip()\n    if official.startswith('Indian Institute of Management '):\n        suffix = official[len('Indian Institute of Management '):].strip()\n        return 'IIM ' + suffix.split('(')[0].strip()\n    if official.startswith('Indian Institute of Technology '):\n        suffix = official[len('Indian Institute of Technology '):].strip()\n        return 'IIT ' + suffix.split('(')[0].strip()\n    if official.startswith('National Institute of Technology '):\n        return 'NIT ' + official[len('National Institute of Technology '):].strip()\n    return official\n'''
    text = text.replace(marker, injection + marker, 1)
text = text.replace("    college = row['college_name']\n", "    official_name = row['college_name']\n    college = rec.get('popular_name') or popular_name(official_name, official_url)\n    rec['popular_name'] = college\n", 1)
AGENT.write_text(text, encoding='utf-8')
print('Applied popular-name SEO rules to production agent.')
