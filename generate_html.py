import json
import re

with open('tips.json', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Raw: {len(content)} chars")

# Hae JSON-osa
match = re.search(r'\{[\s\S]*\}', content)
if not match:
    print("ERROR: No JSON found")
    exit(1)

json_str = match.group()

# Poista kontrollimerkit stringin sisästä
def fix_json(s):
    result = []
    in_string = False
    for c in s:
        if c == '"' and (not result or result[-1] != '\\'):
            in_string = not in_string
            result.append(c)
        elif in_string and c in '\n\r\t':
            result.append(' ')
        elif not in_string and c in '\n\r\t':
            result.append(' ')
        else:
            result.append(c)
    return ''.join(result)

json_str = fix_json(json_str)

try:
    data = json.loads(json_str)
except json.JSONDecodeError as e:
    print(f"JSON error: {e}")
    with open('error.json', 'w') as f:
        f.write(json_str)
    exit(1)

if 'tips' not in data:
    print("Missing 'tips' key")
    exit(1)

tips = data['tips']

html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Model Tips</title>'
html += '<style>body{font-family:sans-serif;max-width:800px;margin:40px auto}</style>'
html += '</head><body><h1>Miniature Model Tips</h1>'

for i, t in enumerate(tips, 1):
    title = str(t.get('title', f'Tip {i}'))
    text = str(t.get('text', ''))
    html += f'<article><h2>{title}</h2><p>{text}</p></article>'

html += '</body></html>'

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✓ Generated {len(tips)} tips")
