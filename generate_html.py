import json
import re
import codecs

with open('tips.json', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Raw content: {len(content)} chars")

# 1. Hae JSON-osa
match = re.search(r'\{[\s\S]*\}', content)
if not match:
    print("ERROR: No JSON found")
    exit(1)

json_str = match.group()

# 2. Aggressiivinen korjaus: Poista ALL kielletyt merkit
def fix_control_chars(s):
    """Poista kaikki kontrollimerkit paitsi \\n ja \\t escape-sekvenssejä"""
    result = []
    i = 0
    in_string = False
    
    while i < len(s):
        c = s[i]
        
        # Tunnista string boundaries
        if c == '"':
            # Tarkista onko escape
            if i > 0 and s[i-1] == '\\':
                pass  # Escape, skip
            else:
                in_string = not in_string
        
        # Kontrollimerkit STRINGIN SISÄLLÄ
        if in_string and c in '\n\r\t':
            result.append('\\u0020')  # Korvaa avaruudella
        elif not in_string and c in '\n\r\t':
            result.append(' ')  # Ulkopuolella avaruus
        else:
            result.append(c)
        
        i += 1
    
    return ''.join(result)

json_str = fix_control_chars(json_str)

# 3. Purista välilynnit
json_str = re.sub(r'[ \t]+', ' ', json_str)

print(f"After fix: {len(json_str)} chars")

# 4. Parsi JSON
try:
    data = json.loads(json_str)
    print("✓ JSON parsed!")
except json.JSONDecodeError as e:
    print(f"Still failing: {e}")
    
    # Yritä viimeinen keino: decoder virheiden kiertäminen
    try:
        json_str = codecs.decode(json_str, 'unicode_escape')
        data = json.loads(json_str)
        print("✓ Fixed with unicode_escape!")
    except:
        print("CRITICAL: Cannot parse JSON")
        
        with open('fatal_error.json', 'w') as f:
            f.write(json_str)
        exit(1)

# 5. Tarkista rakenne
if 'tips' not in data:
    print(f"Missing 'tips' key. Got: {list(data.keys())}")
    exit(1)

tips = data['tips']
print(f"✓ Found {len(tips)} tips")

# 6. Generoi HTML
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

print("✅ Done!")
