import re

with open('data/raw/prezip_list.html', 'r') as f:
    content = f.read()

# Find all zip file links
links = re.findall(r'href="([^"]+\.zip)"', content)
for link in links:
    if 'T100' in link or 'T_100' in link or 'SEGMENT' in link.upper():
        print(link)