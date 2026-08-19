import json

with open('tips.json', 'rb') as f:
    content = f.read().decode('utf-8')

print(f"Raw: {len(content)} chars")

# Aggressive removal: replace ALL newline/carriage/tab characters with space
# This works because JSON doesn't allow literal newlines inside strings anyway
cleaned = content.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

# Collapse multiple spaces to single space
while '  ' in cleaned:
    cleaned = cleaned.replace('  ', ' ')

print(f"Cleaned: {len(cleaned)} chars")
print(f"Preview: {cleaned[:200]}...")

try:
    data = json.loads(cleaned)
    print("✓ JSON parsed!")
except json.JSONDecodeError as e:
    print(f"ERROR: {e}")
    # Show problem area
    pos = max(0, e.pos - 30)
    end = min(len(cleaned), e.pos + 30)
    print(f"Problem at pos {e.pos}: ...{cleaned[pos:end]}...")
    with open('debug_fail.json', 'w') as f:
        f.write(cleaned)
    exit(1)

# Validate structure
if 'tips' not in data:
    print(f"Missing 'tips' key. Got: {list(data.keys())}")
    exit(1)

tips = data['tips']
print(f"✓ Found {len(tips)} tips")

# Generate styled HTML
html = '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">'
html += '<style>'
html += 'body{font-family:Arial,sans-serif;max-width:800px;margin:40px auto;line-height:1.6;background:#f5f5f5;padding:20px}'
html += 'h1{color:#333;border-bottom:3px solid #6d4aff;padding-bottom:12px}'
html += 'article{background:white;padding:24px;margin:16px 0;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1)}'
html += 'h2{color:#6d4aff;margin:0 0 12px 0;font-size:1.4em}'
html += 'p{margin:0;color:#444}'
html += '</style></head><body>'
html += '<h1>Miniature Model Building Tips</h1>'

for i, t in enumerate(tips, 1):
    title = str(t.get('title', f'Tip {i}'))
    text = str(t.get('text', ''))
    html += f'<article><h2>{title}</h2><p>{text}</p></article>'

html += '</body></html>'

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ SUCCESS: index.html created!")
