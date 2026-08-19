import json

with open('tips.json', 'rb') as f:
    raw_bytes = f.read()

# Convert to text, removing ALL control characters (bytes 0x00-0x1F except tab/newline)
print(f"Raw bytes: {len(raw_bytes)}")

# Filter out control characters but keep printable ASCII + valid JSON chars
filtered = bytearray()
for byte in raw_bytes:
    # Allow: 0x09 (tab), 0x0A (LF), 0x0D (CR), 0x20+ (printable)
    if byte >= 0x20 or byte in (0x09, 0x0A, 0x0D):
        filtered.append(byte)
    # Otherwise skip it (control char)

text = filtered.decode('utf-8')

# Now replace remaining newlines/tabs with space
text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

# Collapse spaces
while '  ' in text:
    text = text.replace('  ', ' ')

print(f"After cleaning: {len(text)} chars")
print(f"Preview: {text[:200]}...")

try:
    data = json.loads(text)
    print("✓ JSON parsed!")
except json.JSONDecodeError as e:
    print(f"ERROR: {e}")
    print(f"Context around error:")
    pos = max(0, e.pos - 40)
    end = min(len(text), e.pos + 40)
    print(f"...{text[pos:end]}...")
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

print("✅ SUCCESS!")
