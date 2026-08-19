import json
import re

# Read file
with open('tips.json', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Raw content ({len(content)} chars):")
print(content[:300])
print("...\n")

# Method 1: Try direct parse (if pure JSON)
try:
    data = json.loads(content)
    print("✓ Direct JSON parse succeeded!")
except json.JSONDecodeError:
    print("Direct parse failed, extracting JSON with regex...")
    
    # Method 2: Extract JSON object with regex
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if not match:
        print("ERROR: No JSON found!")
        exit(1)
    
    json_str = match.group()
    
    # Fix whitespace issues
    json_str = json_str.replace('\n', ' ').replace('\r', '').replace('\t', ' ')
    json_str = re.sub(r'[ \t]+', ' ', json_str)
    
    try:
        data = json.loads(json_str)
        print("✓ Regex extraction succeeded!")
    except json.JSONDecodeError as e:
        print(f"ERROR: Could not parse extracted JSON: {e}")
        with open('debug_extracted.json', 'w') as f:
            f.write(json_str)
        exit(1)

# Check structure
print(f"Keys in response: {list(data.keys())}")

if 'tips' not in data:
    print(f"ERROR: Missing 'tips' key!")
    with open('debug_no_tips.json', 'w') as f:
        json.dump(data, f, indent=2)
    exit(1)

tips = data['tips']
print(f"✓ Found {len(tips)} tips")

# Validate each tip
for i, tip in enumerate(tips):
    if not isinstance(tip, dict):
        print(f"Tip {i} is not a dict: {type(tip)}")
        continue
    if 'title' not in tip or 'text' not in tip:
        print(f"Tip {i} missing title/text keys: {list(tip.keys())}")

# Generate HTML
html = '<!DOCTYPE html><html><head><meta charset="UTF-8">'
html += '<style>body{font-family:Arial,sans-serif;max-width:800px;margin:40px auto;line-height:1.6;background:#f5f5f5;padding:20px}'
html += 'h1{color:#333;border-bottom:2px solid #6d4aff;padding-bottom:10px}'
html += 'article{background:white;padding:20px;margin:15px 0;border-radius:5px;box-shadow:0 1px 3px rgba(0,0,0,0.1)}'
html += 'h2{color:#6d4aff;margin-top:0;font-size:1.3em}</style>'
html += '</head><body><h1>Miniature Model Building Tips</h1>'

for i, t in enumerate(tips, 1):
    title = str(t.get('title', f'Tip {i}'))
    text = str(t.get('text', 'No content'))
    html += f'<article><h2>{title}</h2><p>{text}</p></article>'

html += '</body></html>'

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ Generated index.html with styling!")
