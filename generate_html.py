import json
import re

with open('tips.json', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Raw content length: {len(content)}")
print(f"First 200 chars: {content[:200]}")

# Hae JSON-objektia regexillä
match = re.search(r'\{.*\}', content, re.DOTALL)

if not match:
    print("ERROR: No JSON object found!")
    exit(1)

json_str = match.group()
print(f"Parsed JSON: {json_str[:100]}")

try:
    data = json.loads(json_str)
except json.JSONDecodeError as e:
    print(f"JSON decode error: {e}")
    exit(1)

if 'tips' not in data:
    print(f"ERROR: 'tips' key missing! Keys: {list(data.keys())}")
    exit(1)

html = '<html><body><h1>Vinkit</h1>'
for t in data['tips']:
    title = t.get('title', 'Nimetön')
    text = t.get('text', 'Ei tekstiä')
    html += f'<h2>{title}</h2><p>{text}</p>'
html += '</body></html>'

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("SUCCESS: Generated index.html")
