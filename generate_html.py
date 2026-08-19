import json
import re

with open('tips.json', 'r', encoding='utf-8') as f:
    content = f.read().strip()

print(f"Raw content length: {len(content)}")
print(f"First 200 chars: {content[:200]}")

# Poista kaikki JSON-objektin ulkopuolinen teksti
match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)

if not match:
    print("ERROR: No JSON object found!")
    # Yritä etsiä mitä tahansa accoladejä
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if not match:
        print("Still no luck. Content:", content)
        exit(1)

json_str = match.group()
print(f"\nExtracted JSON (first 100 chars): {json_str[:100]}")

# Yritä parsia JSONia
try:
    data = json.loads(json_str)
except json.JSONDecodeError as e:
    print(f"JSON decode error: {e}")
    print("Trying to fix JSON...")
    
    # Yritä korjata yleisiä virheitä
    json_str = json_str.replace('\n', ' ').replace('\\', '\\\\')
    
    try:
        data = json.loads(json_str)
    except:
        print("Failed to fix JSON. Saving raw for debugging:")
        with open('tips_debug.json', 'w') as f:
            f.write(content)
        exit(1)

# Tarkista että 'tips' on olemassa
if 'tips' not in data:
    print(f"ERROR: 'tips' key missing! Available keys: {list(data.keys())}")
    exit(1)

print(f"Found {len(data['tips'])} tips")

html = '<html><body><h1>Vinkit</h1>'
for i, t in enumerate(data['tips']):
    title = t.get('title', f'Tipp {i+1}')
    text = t.get('text', 'No text provided')
    html += f'<h2>{title}</h2><p>{text}</p>'
html += '</body></html>'

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("SUCCESS: Generated index.html")
