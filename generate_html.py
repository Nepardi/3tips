import json
import re

with open('tips.json', 'rb') as f:
    raw_bytes = f.read()

# Filter out control characters (bytes 0x00-0x1F except tab, LF, CR)
filtered = bytearray()
for byte in raw_bytes:
    if byte >= 0x20 or byte in (0x09, 0x0A, 0x0D):
        filtered.append(byte)

text = filtered.decode('utf-8', errors='ignore')

# Remove ALL ANSI escape sequences (like [2D[K, [K, etc.)
# Pattern matches ESC [ ... sequence
text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
text = re.sub(r'\[\d*[a-zA-Z]', '', text)

# Replace newlines/tabs with space
text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

# Collapse multiple spaces
while '  ' in text:
    text = text.replace('  ', ' ')

print(f"After cleaning: {len(text)} chars")
print(f"Preview: {text[:300]}...")

try:
    data = json.loads(text)
    print("✓ JSON parsed!")
except json.JSONDecodeError as e:
    print(f"ERROR: {e}")
    pos = max(0, e.pos - 50)
    end = min(len(text), e.pos + 50)
    print(f"Context: ...{text[pos:end]}...")
    exit(1)

if 'tips' not in data:
    print(f"Missing 'tips' key. Keys: {list(data.keys())}")
    exit(1)

tips = data['tips']
print(f"✓ Found {len(tips)} tips")

html = '<!DOCTYPE html><html><head><meta charset="UTF-8">'
html += '<style>body{font-family:Arial,sans-serif;max-width:800px;margin:40px auto;background:#f5f5f5;padding:20px;line-height:1.6}'
html += 'h1{color:#333;border-bottom:3px solid #6d4aff;padding-bottom:12px}'
html += 'article{background:white;padding:24px;margin:16px 0;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1)}'
html += 'h2{color:#6d4aff;margin:0 0 12px;font-size:1.4em}</style>'
html += '</head><body><h1>Miniature Model Building Tips</h1>'

for i, t in enumerate(tips, 1):
    title = str(t.get('title', f'Tip {i}'))
    text_content = str(t.get('text', ''))
    html += f'<article><h2>{title}</h2><p>{text_content}</p></article>'

html += '</body></html>'

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ SUCCESS: index.html created!")
