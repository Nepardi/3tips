import json
import re
import sys

with open('tips.json', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Raw content: {len(content)} characters")
print(f"\n--- First 500 chars ---")
print(content[:500])
print(f"--- End preview ---\n")

# Try parsing as-is first
try:
    data = json.loads(content)
    print("✓ Direct parse succeeded!")
except json.JSONDecodeError:
    print("Direct parse failed, trying to extract JSON...")
    
    # Hae JSON-objekti regexillä
    match = re.search(r'\{[\s\S]*\}', content)
    if not match:
        print("ERROR: No JSON object found in response")
        with open('debug_full_response.json', 'w') as f:
            f.write(content)
        exit(1)
    
    json_str = match.group()
    
    # Poista kontrollimerkit stringien sisältä
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
        print("✓ Extracted and parsed JSON!")
    except json.JSONDecodeError as e:
        print(f"ERROR: Still cannot parse JSON: {e}")
        with open('debug_extracted.json', 'w') as f:
            f.write(json_str)
        exit(1)

# Tarkista mitä avaimia vastauksessa on
print(f"Response keys: {list(data.keys())}")

# Etsi tips tai vastaava
if 'tips' in data:
    tips = data['tips']
elif 'message' in data and 'content' in data:
    print("Got chat-style response, extracting from message.content")
    # API palautti chat-muodon, yritä parsia
    content_text = data.get('message', {}).get('content', content)
    match = re.search(r'\{[\s\S]*\}', content_text)
    if match:
        data = json.loads(match.group())
        tips = data.get('tips', [])
    else:
        tips = []
else:
    available_keys = list(data.keys())
    print(f"ERROR: Expected 'tips' key but got: {available_keys}")
    
    # Tallenna debug-tiedosto
    with open('wrong_structure.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print("Saved response to wrong_structure.json for inspection")
    exit(1)

if not isinstance(tips, list):
    print(f"ERROR: 'tips' is not a list, it's a {type(tips).__name__}")
    exit(1)

print(f"✓ Found {len(tips)} tips")

# Generoi HTML
html = '<!DOCTYPE html><html><head><meta charset="UTF-8">'
html += '<style>body{font-family:sans-serif;max-width:800px;margin:40px auto;line-height:1.6;}</style>'
html += '</head><body><h1>Miniature Model Building Tips</h1>'

for i, t in enumerate(tips, 1):
    if isinstance(t, dict):
        title = str(t.get('title', f'Tip {i}'))
        text = str(t.get('text', 'No content'))
    else:
        title = f'Tip {i}'
        text = str(t)
    html += f'<article><h2>{title}</h2><p>{text}</p></article>'

html += '</body></html>'

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ Generated index.html successfully")
