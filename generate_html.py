import json
import re

with open('tips.json', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Raw length: {len(content)} chars")

# 1. Etsi JSON-objekti
match = re.search(r'\{[\s\S]*\}', content)
if not match:
    print("ERROR: No JSON found!")
    exit(1)

json_str = match.group()
print(f"Extracted {len(json_str)} chars of JSON")

# 2. KORJAUS: Poista kaikki rivinvaihdot ja tabit koko JSONista
# JSONissa rivinvaihdot merkkijonon sisällä eivät ole sallittuja
cleaned = json_str.replace('\n', ' ').replace('\r', '').replace('\t', ' ')

# 3. Purista ylimääräiset välilynnit
cleaned = re.sub(r'  +', ' ', cleaned)

print(f"Cleaned length: {len(cleaned)} chars")

# 4. Parsi JSON
try:
    data = json.loads(cleaned)
    print("✓ JSON parsed successfully!")
except json.JSONDecodeError as e:
    print(f"JSON error: {e}")
    print(f"Problematic section: {cleaned[max(0, e.pos-50):e.pos+50]}")
    
    # Tallenna debug-tiedostot
    with open('debug_raw.json', 'w', encoding='utf-8') as f:
        f.write(content)
    with open('debug_cleaned.json', 'w', encoding='utf-8') as f:
        f.write(cleaned)
    
    exit(1)

# 5. Tarkista rakenne
if 'tips' not in data:
    print(f"ERROR: Missing 'tips' key. Available: {list(data.keys())}")
    exit(1)

tips = data['tips']
print(f"✓ Found {len(tips)} tips")

# 6. Generoi HTML
html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Vinkit</title>'
html += '<style>body{font-family:sans-serif;max-width:800px;margin:40px auto}</style>'
html += '</head><body><h1>Pienoismallivinkit</h1>'

for i, t in enumerate(tips, 1):
    title = str(t.get('title', f'Vinkki {i}')).replace('<', '&lt;').replace('>', '&gt;')
    text = str(t.get('text', 'Ei sisältöä')).replace('<', '&lt;').replace('>', '&gt;')
    html += f'<article><h2>{title}</h2><p>{text}</p></article>'

html += '</body></html>'

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ Generated index.html")
