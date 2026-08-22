import json
import re
import os
from datetime import datetime
try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system('pip install requests')
    import requests

# ========== STEP 1: SELECT TOPIC ==========
with open('topics.json', 'r', encoding='utf-8') as f:
    topics_data = json.load(f)

topic_index = topics_data['next_topic'] - 1
topic_name = topics_data['topics'][topic_index]
prompt = topics_data['prompts'][topic_name]

# Increment and wrap
topics_data['next_topic'] = (topics_data['next_topic'] % len(topics_data['topics'])) + 1

# Save updated topics.json
with open('topics.json', 'w', encoding='utf-8') as f:
    json.dump(topics_data, f, indent=2)

print(f"Topic: {topic_name}")
print(f"Next topic index: {topics_data['next_topic']}")

# ========== STEP 2: CALL OLLAMA API (WITH RETRY) ==========
max_retries = 3
tips = None

for attempt in range(1, max_retries + 1):
    print(f"Calling Ollama API (attempt {attempt}/{max_retries})...")

    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'llama3.1',
                'prompt': prompt,
                'format': 'json',
                'stream': False,
                'options': {
                    'temperature': 0.8
                }
            },
            timeout=180
        )
        result = response.json()
        raw_output = result.get('response', '')
        print(f"API returned {len(raw_output)} chars")

        with open('tips.json', 'w', encoding='utf-8') as f:
            f.write(raw_output)

    except Exception as e:
        print(f"ERROR calling Ollama API: {e}")
        print("Make sure Ollama is running: ollama serve")
        exit(1)

    # ========== STEP 3: CLEAN AND PARSE JSON ==========
    text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', raw_output)
    text = re.sub(r'\x1b\[K', '', text)
    text = re.sub(r'\[\d*[a-zA-Z]', '', text)

    def remove_artifacts(text):
        text = re.sub(r'\b(\w{1,8}) (\w{3,})\b',
                      lambda m: m.group(2) if len(m.group(1)) > 2 and m.group(2).lower().startswith(m.group(1).lower()) and len(m.group(1)) < len(m.group(2)) else m.group(0),
                      text)
        return text

    text = remove_artifacts(text)
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    while '  ' in text:
        text = text.replace('  ', ' ')

    match = re.search(r'\{[\s\S]*\}', text)
    if not match:
        print(f"Attempt {attempt}: No JSON found!")
        continue

    json_str = match.group()
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    json_str = re.sub(r'"\s*"', '", "', json_str)
    json_str = re.sub(r'}(\s*){', '}, {', json_str)

    try:
        data = json.loads(json_str)
        print(f"Attempt {attempt}: JSON parsed!")
    except json.JSONDecodeError as e:
        print(f"Attempt {attempt}: JSON error: {e}")
        continue

    if 'tips' not in data:
        print(f"Attempt {attempt}: Missing 'tips' key! Keys: {list(data.keys())}")
        continue

    found_tips = data['tips']
    print(f"Attempt {attempt}: Found {len(found_tips)} tips")

    if len(found_tips) >= 5:
        tips = found_tips[:5]
        break
    elif attempt < max_retries:
        print(f"Only {len(found_tips)} tips, retrying...")
    else:
        print(f"WARNING: Only {len(found_tips)} tips after {max_retries} attempts, using what we have")
        tips = found_tips

# Clean each tip's text from artifacts
for tip in tips:
    if 'title' in tip:
        tip['title'] = remove_artifacts(str(tip['title']))
    if 'text' in tip:
        tip['text'] = remove_artifacts(str(tip['text']))

print(f"OK: Using {len(tips)} tips")

# ========== STEP 4: GENERATE HTML ==========
topic_display = {
    'MATERIALS_SUPPLIES': 'Materials & Supplies',
    'TOOLS_TECHNIQUES': 'Tools & Techniques',
    'PAINTING_FINISHING': 'Painting & Weathering',
    'ASSEMBLY_CONSTRUCTION': 'Assembly & Construction',
    'TROUBLESHOOTING_PROTIPS': 'Troubleshooting & Pro Tips'
}.get(topic_name, topic_name)

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Scale Model Building Tips</title>
<style>
:root {{
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
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  background: linear-gradient(135deg, var(--bg-color) 0%, #e8f5ff 100%);
  min-height: 100vh;
  color: var(--text-main);
  line-height: 1.6;
}}
.container {{ max-width: 900px; margin: 0 auto; padding: 40px 20px; }}
header {{ text-align: center; margin-bottom: 50px; }}
h1 {{
  font-size: 2.5em; font-weight: 700; color: var(--text-main);
  margin-bottom: 10px;
  background: linear-gradient(135deg, var(--gradient-start), var(--gradient-end));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}}
.subtitle {{ color: var(--text-muted); font-size: 1.1em; }}
.date-badge {{
  display: inline-block;
  background: linear-gradient(135deg, var(--primary), var(--gradient-end));
  color: white; padding: 8px 20px; border-radius: 20px;
  font-size: 0.9em; font-weight: 600; margin-top: 15px;
  box-shadow: 0 4px 15px var(--shadow);
}}
.topic-badge {{
  display: inline-block; background: white; color: var(--primary);
  border: 2px solid var(--primary); padding: 6px 18px;
  border-radius: 20px; font-size: 0.85em; font-weight: 600;
  margin-top: 10px;
}}
.actions {{ text-align: center; margin: 30px 0; }}
.btn {{
  display: inline-block;
  background: linear-gradient(135deg, var(--primary), var(--gradient-end));
  color: white; padding: 12px 30px; border-radius: 25px;
  text-decoration: none; font-weight: 600; border: none;
  cursor: pointer; font-size: 1em; transition: all 0.3s ease;
  box-shadow: 0 4px 15px var(--shadow);
}}
.btn:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px var(--shadow); }}
.btn svg {{ vertical-align: middle; margin-right: 8px; }}
.cards {{ display: grid; gap: 25px; }}
.card {{
  background: var(--card-bg); border-radius: 16px; padding: 30px;
  box-shadow: 0 4px 20px var(--shadow); border-left: 5px solid var(--primary);
  transition: all 0.3s ease; position: relative; overflow: hidden;
}}
.card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 30px var(--shadow); }}
.card::before {{
  content: ''; position: absolute; top: 0; left: 0;
  width: 100%; height: 3px;
  background: linear-gradient(90deg, var(--gradient-start), var(--gradient-end));
  opacity: 0; transition: opacity 0.3s ease;
}}
.card:hover::before {{ opacity: 1; }}
.tip-number {{
  display: inline-flex; align-items: center; justify-content: center;
  width: 32px; height: 32px;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: white; border-radius: 50%; font-weight: 700;
  font-size: 0.9em; margin-right: 15px; flex-shrink: 0;
}}
.title-row {{ display: flex; align-items: flex-start; margin-bottom: 15px; }}
.card h2 {{
  flex-grow: 1; font-size: 1.4em; font-weight: 600;
  color: var(--text-main); line-height: 1.3;
}}
.card p {{
  color: var(--text-muted); font-size: 1.05em;
  line-height: 1.7; padding-left: 47px; text-align: justify;
}}
footer {{
  text-align: center; margin-top: 60px; padding-top: 30px;
  border-top: 1px solid var(--border-color);
  color: var(--text-muted); font-size: 0.9em;
}}
@media (max-width: 768px) {{
  .container {{ padding: 20px 15px; }}
  h1 {{ font-size: 1.8em; }}
  .card {{ padding: 20px; }}
  .card h2 {{ font-size: 1.2em; }}
  .card p {{ padding-left: 0; padding-top: 10px; }}
  .tip-number {{ display: none; }}
}}
@keyframes fadeInUp {{
  from {{ opacity: 0; transform: translateY(20px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}
.card {{ animation: fadeInUp 0.5s ease forwards; }}
.card:nth-child(1) {{ animation-delay: 0.1s; }}
.card:nth-child(2) {{ animation-delay: 0.2s; }}
.card:nth-child(3) {{ animation-delay: 0.3s; }}
.card:nth-child(4) {{ animation-delay: 0.4s; }}
.card:nth-child(5) {{ animation-delay: 0.5s; }}
@media print {{
  .actions, footer, .date-badge, .topic-badge {{ display: none !important; }}
  body {{ background: white !important; padding: 0 !important; }}
  .container {{ max-width: 100% !important; padding: 20px !important; margin: 0 !important; }}
  h1 {{ font-size: 2em !important; -webkit-text-fill-color: #1a1a2e !important; background: none !important; }}
  .card {{
    break-inside: avoid !important; page-break-inside: avoid !important;
    box-shadow: none !important; border: 1px solid #ddd !important;
  }}
  .subtitle {{ font-size: 1em !important; }}
}}
</style>
</head>
<body>
<div class="container">
<header>
<h1>🛠️ Scale Model Building Tips</h1>
<p class="subtitle">Practical advice for scale model builders</p>
<div class="topic-badge">📋 {topic_display}</div>
<div class="date-badge">{datetime.now().strftime('%B %d, %Y')}</div>
</header>
<div class="actions">
<button class="btn" onclick="window.print()">
<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<path d="M6 9V2h12v7"></path>
<rect x="6" y="14" width="12" height="8"></rect>
<line x1="6" y1="18" x2="18" y2="18"></line>
<path d="M6 14H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
</svg>
Save as PDF
</button>
</div>
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
</article>'''

html += '''
</div>
<footer>
<p>Generated automatically by GitHub Actions &middot; Powered by Ollama</p>
<p style="margin-top: 10px; font-size: 0.8em;">Use the button above to save this page as PDF</p>
</footer>
</div>
</body>
</html>'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"OK: index.html created with {len(tips)} tips on topic: {topic_display}")
