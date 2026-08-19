import json

with open('tips.json') as f:
    data = json.load(f)

html = '<html><body><h1>Vinkit</h1>'
for t in data['tips']:
    html += f"<h2>{t['title']}</h2><p>{t['text']}</p>"
html += '</body></html>'

with open('index.html', 'w') as f:
    f.write(html)

print('Generated index.html')
