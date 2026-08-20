import json
import re
from datetime import datetime

with open('tips.json', 'rb') as f:
    raw_bytes = f.read()

# Clean the JSON
filtered = bytearray()
for byte in raw_bytes:
    if byte >= 0x20 or byte in (0x09, 0x0A, 0x0D):
        filtered.append(byte)

text = filtered.decode('utf-8', errors='ignore')
text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
text = re.sub(r'\[\d*[a-zA-Z]', '', text)
text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

while '  ' in text:
    text = text.replace('  ', ' ')

try:
    data = json.loads(text)
except json.JSONDecodeError as e:
    print(f"ERROR: {e}")
    exit(1)

if 'tips' not in data:
    print("Missing 'tips' key!")
    exit(1)

tips = data['tips']
print(f"OK: Found {len(tips)} tips")

# Modern HTML with nice styling
html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Scale Model Building Tips</title>
<style>
/* Color Variables */
:root {
  --primary: #6d4aff;
  --primary-dark: #573dd4;
  --primary-light: #8a77ff;
  --bg-color: #f8f9fc;
  --card-bg: #ffffff;
  --text-main: #1a1a2e;
  --text-muted: #6c757d;
  --border-color: #e9ecef;
  --shadow: rgba(109, 74, 255, 0.15);
  --gradient-start: #6d4aff;
  --gradient-end: #a855f7;
}

/* Base styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  background: linear-gradient(135deg, var(--bg-color) 0%, #e8f5ff 100%);
  min-height: 100vh;
  color: var(--text-main);
  line-height: 1.6;
}

.container {
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 20px;
}

/* Header */
header {
  text-align: center;
  margin-bottom: 50px;
}

h1 {
  font-size: 2.5em;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 10px;
  background: linear-gradient(135deg, var(--gradient-start), var(--gradient-end));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  color: var(--text-muted);
  font-size: 1.1em;
}

/* Date badge */
.date-badge {
  display: inline-block;
  background: linear-gradient(135deg, var(--primary), var(--gradient-end));
  color: white;
  padding: 8px 20px;
  border-radius: 20px;
  font-size: 0.9em;
  font-weight: 600;
  margin-top: 15px;
  box-shadow: 0 4px 15px var(--shadow);
}

/* Card container */
.cards {
  display: grid;
  gap: 25px;
}

/* Tip card */
.card {
  background: var(--card-bg);
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 4px 20px var(--shadow);
  border-left: 5px solid var(--primary);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 30px var(--shadow);
}

.card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, var(--gradient-start), var(--gradient-end));
  opacity: 0;
  transition: opacity 0.3s ease;
}

.card:hover::before {
  opacity: 1;
}

/* Tip number */
.tip-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: white;
  border-radius: 50%;
  font-weight: 700;
  font-size: 0.9em;
  margin-right: 15px;
  flex-shrink: 0;
}

/* Title row */
.title-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 15px;
}

.card h2 {
  flex-grow: 1;
  font-size: 1.4em;
  font-weight: 600;
  color: var(--text-main);
  line-height: 1.3;
}

/* Text content */
.card p {
  color: var(--text-muted);
  font-size: 1.05em;
  line-height: 1.7;
  padding-left: 47px;
  text-align: justify;
}

/* Footer */
footer {
  text-align: center;
  margin-top: 60px;
  padding-top: 30px;
  border-top: 1px solid var(--border-color);
  color: var(--text-muted);
  font-size: 0.9em;
}

/* Responsive */
@media (max-width: 768px) {
  .container {
    padding: 20px 15px;
  }
  
  h1 {
    font-size: 1.8em;
  }
  
  .card {
    padding: 20px;
  }
  
  .card h2 {
    font-size: 1.2em;
  }
  
  .card p {
    padding-left: 0;
    padding-top: 10px;
  }
  
  .tip-number {
    display: none;
  }
}

/* Animation */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.card {
  animation: fadeInUp 0.5s ease forwards;
}

.card:nth-child(1) { animation-delay: 0.1s; }
.card:nth-child(2) { animation-delay: 0.2s; }
.card:nth-child(3) { animation-delay: 0.3s; }
</style>
</head>
<body>
<div class="container">
<header>
<h1>🛠️ Scale Model Building Tips</h1>
<p class="subtitle">Practical advice for scale model builders</p>
<div class="date-badge">'''

html += datetime.now().strftime('%B %d, %Y')

html += '''</div>
</header>

<div class="cards">'''

for i, t in enumerate(tips, 1):
    title = str(t.get('title', f'Tip {i}'))
    text_content = str(t.get('text', ''))
    
    html += f'''
<article class="card">
<div class="title-row">
<span class="tip-number">{i}</span>
<h2>{title}</h2>
</div>
<p>{text_content}</p>
</article>
'''

html += '''
</div>

<footer>
<p>Generated automatically by GitHub Actions &middot; Powered by Ollama</p>
</footer>
</div>
</body>
</html>'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("OK: index.html created with new styling!")
