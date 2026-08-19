import json
import re

with open('tips.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Find JSON object
match = re.search(r'\{[\s\S]*\}', content)
if not match:
    print("ERROR: No JSON found!")
    exit(1)

json_str = match.group()

# Remove newlines and tabs
cleaned = json_str.replace('\n', ' ').replace('\r', '').replace('\t', ' ')
cleaned = re.sub(r'  +', ' ', cleaned)

try:
    data = json.loads(cleaned)
except json.JSONDecodeError as e:
    print(f"JSON error: {e}")
    with open('debug_error.json', 'w') as f:
        f.write(cleaned)
    exit(1)

if 'tips' not in data:
    print(f"ERROR: Missing 'tips' key")
    exit(1)

# Generate HTML
html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Model Building Tips</title>'
html += '<style>body{font-family:sans-serif;max-width:800px;margin:40px auto;line-height:1.6}</style>'
html += '</head><body><h1>Miniature Model Building Tips</h1>'

for i, t in enumerate(data['tips'], 1):
    title = t.get('title', f'Tip {i}')
    text = t.get('text', 'No content')
    html += f'<article><h2>{title}</h2><p>{text}</p></article>'

html += '</body></html>'

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✓ Generated index.html with {len(data['tips'])} tips")
