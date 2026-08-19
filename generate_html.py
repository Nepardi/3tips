import json
import re
import sys

with open('tips.json', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Raw content: {len(content)} characters")

# Try to find JSON anywhere in response
match = re.search(r'\{[\s\S]*\}', content)
if not match:
    print("ERROR: No JSON found in response")
    exit(1)

json_str = match.group()

# Fix control characters inside strings
def fix_json(s):
    result = []
    in_string = False
    for i, c in enumerate(s):
        if c == '"' and (i == 0 or s[i-1] != '\\'):
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
json_str = re.sub(r'[ \t]+', ' ', json_str)

try:
    data = json.loads(json_str)
except json.JSONDecodeError as e:
    print(f"JSON error: {e}")
    print(f"Problematic section: {json_str[max(0,e.pos-30):e.pos+30]}")
    with open('debug_failed.json', 'w') as f:
        f.write(json_str)
    exit(1)

# Find tips key
if 'tips' in data:
    tips = data['tips']
else:
    print(f"Missing 'tips' key. Available keys: {list(data.keys())}")
    with open('debug_wrong_key.json', 'w') as f:
        json.dump(data, f, indent=2)
    exit(1)

if not isinstance(tips, list):
    print(f"ERROR: 'tips' is {type(tips)}, expected list")
    exit(1)

print(f"✓ Found {len(tips)} tips")

# Generate HTML
html = '<!DOCTYPE html><html><head><meta charset="UTF-8">'
html += '<style>body{font-family:sans-serif;max-width:800px;margin:40px auto;line-height:1.6;}</style>'
html += '</head><body><h1>Miniature Model Building Tips</h1>'

for i, t in enumerate(tips, 1):
    if isinstance(t, dict):
        title = str(t.get('title', f'Tip {i}'))
        text = str(t.get('text', ''))
    else:
        title = f'Tip {i}'
        text = str(t)
    html += f'<article><h2>{title}</h2><p>{text}</p></article>'

html += '</body></html>'

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ Generated index.html")
