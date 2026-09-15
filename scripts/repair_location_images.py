from pathlib import Path

page = Path('mba-colleges-by-location.html')
html = page.read_text(encoding='utf-8')

old = 'https://commons.wikimedia.org/wiki/Special:Redirect/file/Amanora%20Skyline.jpg?width=1000'
new = 'https://commons.wikimedia.org/wiki/Special:Redirect/file/Skyline%20of%20Pune%20from%20unknown%20place.jpg?width=1000'

if old in html:
    html = html.replace(old, new)
    page.write_text(html, encoding='utf-8')
    print('Repaired Pune destination image URL.')
else:
    print('Pune image URL already repaired or not present.')
