import json
import re
import os
import time
import urllib.parse
import shutil
import random
from datetime import datetime
try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system('pip install requests')
    import requests

# ========== TOPIC IMAGE MAPPING ==========
TOPIC_IMAGE_KEYS = {
    'MATERIALS_SUPPLIES': 'materials',
    'TOOLS_TECHNIQUES': 'tools',
    'PAINTING_FINISHING': 'painting',
    'ASSEMBLY_CONSTRUCTION': 'assembly',
    'TROUBLESHOOTING_PROTIPS': 'troubleshooting'
}

# ========== SYSTEM PROMPT ==========
SYSTEM_PROMPT = """You are an expert scale model builder with over 30 years of experience. Your expertise covers plastic model kits from major manufacturers including Tamiya, Revell, Airfix, Meng, AFV Club, Dragon, Trumpeter, Eduard, ICM, Zvezda, Italeri, Hobby Boss, MiniArt, Arma Hobby, Clear Prop Models, Special H, Academy, Roden, and PAV. You know paints and finishes from Vallejo Model Air and Model Color, AK Interactive, AMMO by Mig Jimenez, Tamiya acrylics and enamels, Citadel, Humbrol, LifeColor, and Alclad II. You specialize in airbrushing equipment from Iwata, Harder and Steenbeck, Badger, and Paasche. You master weathering techniques using washes, filters, chipping, streaking, pigments, oil paints, and enamel effects. You are proficient with tools including GodHand nippers, Tamiya plastic cement, CA glue, photo-etch bending tools, sanding sticks, scribing tools, and dental instruments. You know finishing techniques like gloss coat before decals, flat coat after weathering, varnish types, decal setting solutions, and paint consistency testing. Always provide specific actionable advice with real brand names, product names, exact measurements, ratios and pressures. Avoid vague advice like 'be patient' or 'practice makes perfect'. Each tip should teach one specific technique. Write in clear direct English. Keep each tip text between 80-150 words. Titles should be descriptive and specific."""
# ========== LOCK FILE MECHANISM ==========
LOCK_FILE = '.workflow.lock'

def acquire_lock(timeout=3600):
    """Try to acquire lock, return True if successful"""
    start = time.time()
    while os.path.exists(LOCK_FILE):
        # Check if lock is stale (> 1 hour old)
        try:
            with open(LOCK_FILE, 'r') as f:
                lock_time = datetime.fromisoformat(f.read().strip())
            age = datetime.now() - lock_time
            if age.total_seconds() > timeout:
                print(f"Stale lock detected ({age.seconds}s old), removing it")
                os.remove(LOCK_FILE)
                break
        except:
            pass
        
        if time.time() - start > timeout:
            print("Could not acquire lock, another workflow may be running")
            exit(0)
        
        time.sleep(10)
    
    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(datetime.now().isoformat())
        print("Lock acquired successfully")
        return True
    except Exception as e:
        print(f"Failed to create lock file: {e}")
        return False

def release_lock():
    """Remove lock file when done"""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
            print("Lock released")
    except:
        pass

# Acquire lock at start
if not acquire_lock():
    print("Exiting because another workflow instance is running")
    exit(0)

# Ensure lock is released on exit
import atexit
atexit.register(release_lock)
# ========== STEP 0: ARCHIVE OLD TIPS ==========
if os.path.exists('index.html'):
    if not os.path.exists('archive'):
        os.makedirs('archive')

    archive_timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
    archive_filename = f'archive/{archive_timestamp}.html'

    shutil.copy2('index.html', archive_filename)

    # Fix paths for archive subfolder
    with open(archive_filename, 'r', encoding='utf-8') as f:
        archived_content = f.read()
    archived_content = archived_content.replace('src="images/', 'src="../images/')
    archived_content = archived_content.replace('href="archive/index.html"', 'href="index.html"')
    with open(archive_filename, 'w', encoding='utf-8') as f:
        f.write(archived_content)

    print(f"Archived old tips to: {archive_filename}")

# ========== STEP 1: SELECT TOPIC ==========
with open('topics.json', 'r', encoding='utf-8') as f:
    topics_data = json.load(f)

topic_index = topics_data['next_topic'] - 1
topic_name = topics_data['topics'][topic_index]
prompt = topics_data['prompts'][topic_name]

topics_data['next_topic'] = (topics_data['next_topic'] % len(topics_data['topics'])) + 1

with open('topics.json', 'w', encoding='utf-8') as f:
    json.dump(topics_data, f, indent=2)

print(f"Topic: {topic_name}")
print(f"Next topic index: {topics_data['next_topic']}")

# ========== STEP 1b: LOAD IMAGES FOR CURRENT TOPIC ==========
topic_img_key = TOPIC_IMAGE_KEYS.get(topic_name, topic_name.lower())

# Header image
header_image = f'images/header_{topic_img_key}.jpg'
header_image_exists = os.path.exists(header_image)
if header_image_exists:
    print(f"Header image found: {header_image}")
else:
    print(f"No header image found (expected: {header_image})")

# Card images — load all available, shuffle for variety
card_images = []
for i in range(1, 6):
    img_path = f'images/{topic_img_key}_{i}.jpg'
    if os.path.exists(img_path):
        card_images.append(img_path)

random.shuffle(card_images)
print(f"Card images found: {len(card_images)}")

def get_card_image(index):
    """Return image path for card index, or None."""
    if card_images:
        return card_images[index % len(card_images)]
    return None

# ========== STEP 2: CALL OLLAMA API (WITH RETRY) ==========
max_retries = 3
tips = None

for attempt in range(1, max_retries + 1):
    print(f"Calling Ollama API (attempt {attempt}/{max_retries})...")

    try:
        full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"

        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'qwen3:8b',
                'prompt': full_prompt,
                'format': 'json',
                'stream': False,
                'options': {
                    'temperature': 0.8
                }
            },
            timeout=300
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

        # Handle both formats: ['tips'] or ['tip1', 'tip2', ...]
    if 'tips' in data:
        found_tips = data['tips']
    elif all(k.startswith('tip') and k[3:].isdigit() for k in data.keys()):
        # Convert {'tip1': ..., 'tip2': ...} to list
        tip_keys = sorted([k for k in data.keys() if k.startswith('tip')], 
                         key=lambda x: int(x[3:]))
        found_tips = [data[k] for k in tip_keys]
    else:
        print(f"Attempt {attempt}: Unexpected JSON structure! Keys: {list(data.keys())}")
        continue

    print(f"Attempt {attempt}: Found {len(found_tips)} tips")

    if len(found_tips) >= 5:
        tips = found_tips[:5]
        break
    elif attempt < max_retries:
        print(f"Only {len(found_tips)} tips, retrying...")
    else:
        print(f"WARNING: Only {len(found_tips)} tips after {max_retries} attempts, using what we have")
        tips = found_tips

for tip in tips:
    if 'title' in tip:
        tip['title'] = remove_artifacts(str(tip['title']))
    if 'text' in tip:
        tip['text'] = remove_artifacts(str(tip['text']))
# ========== SANITY CHECK: FILTER BAD TIPS ==========
BANNED_PHRASES = [
    'glue to paint', 'paint on glue', 'glue the paint',
    'soak in thinner overnight', 'spray undiluted',
    'dip entire model in', 'melt with acetone',
    'use acetone on plastic', 'heat gun on plastic',
    'superglue on clear parts', 'ca glue on canopy'
]

VALID_BRANDS = [
    'tamiya', 'vallejo', 'ak interactive', 'ammo', 'revell',
    'airfix', 'meng', 'iwata', 'harder', 'steubenbeck',
    'citadel', 'humbrol', 'lifecolor', 'alclad',
    'mr. hobby', 'mr hobby', 'scale75', 'eduard',
    'godhand', 'evergreen', 'microscale', 'mr. mark',
    'clear prop', 'arma hobby'
]

good_tips = []
for tip in tips:
    text_lower = str(tip.get('text', '')).lower()
    title = str(tip.get('title', ''))
    
    # 1. Hylkää kielletyt fraasit
    rejected = False
    for phrase in BANNED_PHRASES:
        if phrase in text_lower:
            print(f"  REJECTED tip '{title}': banned phrase '{phrase}'")
            rejected = True
            break
    if rejected:
        continue
    
    # 2. Varoita jos ei yhtään brändiä
    has_brand = any(b in text_lower for b in VALID_BRANDS)
    if not has_brand:
        print(f"  WARNING: tip '{title}' has no brand references")
    
    # 3. Varoita jos teksti on liian lyhyt (< 50 sanaa)
    word_count = len(text_lower.split())
    if word_count < 50:
        print(f"  WARNING: tip '{title}' is only {word_count} words")
    
    good_tips.append(tip)

if good_tips:
    tips = good_tips
    print(f"Sanity check: {len(tips)} tips passed")
else:
    print("Sanity check: ALL tips rejected, keeping originals")
print(f"OK: Using {len(tips)} tips")

# ========== STEP 4: GENERATE HTML ==========
topic_display = {
    'MATERIALS_SUPPLIES': 'Materials & Supplies',
    'TOOLS_TECHNIQUES': 'Tools & Techniques',
    'PAINTING_FINISHING': 'Painting & Weathering',
    'ASSEMBLY_CONSTRUCTION': 'Assembly & Construction',
    'TROUBLESHOOTING_PROTIPS': 'Troubleshooting & Pro Tips'
}.get(topic_name, topic_name)

current_date = datetime.now().strftime('%B %d, %Y')

# Build hero image section (empty if no image)
hero_html = ''
if header_image_exists:
    hero_html = f'''<div class="hero-image">
<img src="{header_image}" alt="{topic_display}">
</div>'''

# Build card HTML
cards_html = ''
for i, t in enumerate(tips, 1):
    title = str(t.get('title', f'Tip {i}'))
    text_content = str(t.get('text', ''))
    card_img = get_card_image(i - 1)
    card_img_html = ''
    if card_img:
        card_img_html = f'''<div class="card-image">
<img src="{card_img}" alt="">
</div>'''
    search_query = urllib.parse.quote(f"scale model {title}")
    search_url = f"https://www.google.com/search?q={search_query}"
    cards_html += f'''<article class="card">
{card_img_html}
<div class="title-row">
<span class="tip-number">{i}</span>
<h2>{title}</h2>
</div>
<p>{text_content}</p>
<a class="search-link" href="{search_url}" target="_blank" rel="noopener noreferrer">&#128269; Search for more</a>
</article>'''

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
  --warning-bg: #fff3cd;
  --warning-border: #ffc107;
  --warning-text: #856404;
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
header {{ text-align: center; margin-bottom: 30px; }}
h1 {{
  font-size: 2.5em; font-weight: 700; color: var(--text-main);
  margin-bottom: 10px;
  background: linear-gradient(135deg, var(--gradient-start), var(--gradient-end));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}}
.subtitle {{ color: var(--text-muted); font-size: 1.1em; }}
.badges {{ display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }}
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
.hero-image {{
  width: 100%;
  height: 320px;
  overflow: hidden;
  border-radius: 16px;
  margin: 25px 0;
  box-shadow: 0 4px 25px var(--shadow);
  position: relative;
}}
.hero-image img {{
  width: 100%; height: 100%;
  object-fit: cover;
}}
.hero-image::after {{
  content: ''; position: absolute; bottom: 0; left: 0;
  width: 100%; height: 70px;
  background: linear-gradient(to top, rgba(0,0,0,0.35), transparent);
  pointer-events: none;
}}
.disclaimer {{
  background: var(--warning-bg);
  border: 1px solid var(--warning-border);
  border-left: 5px solid var(--warning-border);
  border-radius: 10px;
  padding: 15px 20px;
  margin: 20px 0 30px 0;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}}
.disclaimer-icon {{
  flex-shrink: 0;
  font-size: 1.3em;
  margin-top: 2px;
}}
.disclaimer-text {{
  font-size: 0.9em;
  color: var(--warning-text);
  line-height: 1.5;
}}
.disclaimer-text strong {{
  display: block;
  margin-bottom: 3px;
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
.btn-archive {{
  background: white; color: var(--primary); border: 2px solid var(--primary);
  box-shadow: none;
}}
.btn-archive:hover {{
  background: var(--primary); color: white;
}}
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
.card-image {{
  width: 100%;
  height: 220px;
  overflow: hidden;
  border-radius: 12px;
  margin-bottom: 18px;
  position: relative;
}}
.card-image img {{
  width: 100%; height: 100%;
  object-fit: cover;
  transition: transform 0.4s ease;
}}
.card:hover .card-image img {{
  transform: scale(1.06);
}}
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
.search-link {{
  display: inline-block; margin-top: 10px; margin-left: 47px;
  font-size: 0.85em; color: var(--primary);
  text-decoration: none; font-weight: 600;
  transition: color 0.3s ease;
}}
.search-link:hover {{
  color: var(--primary-dark); text-decoration: underline;
}}
footer {{
  text-align: center; margin-top: 60px; padding-top: 30px;
  border-top: 1px solid var(--border-color);
  color: var(--text-muted); font-size: 0.9em;
}}
@media (max-width: 768px) {{
  .container {{ padding: 20px 15px; }}
  h1 {{ font-size: 1.8em; }}
  .hero-image {{ height: 200px; }}
  .card {{ padding: 20px; }}
  .card-image {{ height: 160px; }}
  .card h2 {{ font-size: 1.2em; }}
  .card p {{ padding-left: 0; padding-top: 10px; }}
  .tip-number {{ display: none; }}
  .disclaimer {{ flex-direction: column; gap: 8px; }}
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
  .actions, footer, .date-badge, .topic-badge, .btn-archive, .disclaimer {{ display: none !important; }}
  body {{ background: white !important; padding: 0 !important; }}
  .container {{ max-width: 100% !important; padding: 20px !important; margin: 0 !important; }}
  h1 {{ font-size: 2em !important; -webkit-text-fill-color: #1a1a2e !important; background: none !important; }}
  .hero-image {{ height: 120px; border-radius: 8px; }}
  .card-image {{ height: 100px; border-radius: 8px; }}
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
<h1>&#128295; Scale Model Building Tips</h1>
<p class="subtitle">Practical advice for scale model builders</p>
<div class="badges">
<div class="topic-badge">&#128203; {topic_display}</div>
<div class="date-badge">{current_date}</div>
</div>
</header>
{hero_html}
<div class="disclaimer">
<div class="disclaimer-icon">&#9888;&#65039;</div>
<div class="disclaimer-text">
<strong>AI-Generated Content</strong>
These tips are automatically generated by an AI language model via Ollama. While the content aims to be helpful and accurate, it may contain errors or outdated information. Always verify advice against reliable sources before applying it to your projects.
</div>
</div>
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
<a class="btn btn-archive" href="archive/index.html">
<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<path d="M21 8v13H3V8"></path>
<path d="M1 3h22v5H1z"></path>
<path d="M10 12h4"></path>
</svg>
View Archive
</a>
</div>
<div class="cards">
{cards_html}
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

# ========== STEP 5: GENERATE ARCHIVE INDEX PAGE ==========
archive_files = []
if os.path.exists('archive'):
    for f in sorted(os.listdir('archive'), reverse=True):
        if f.endswith('.html') and f != 'index.html':
            name_without_ext = f.replace('.html', '')
            try:
                parts = name_without_ext.split('_')
                date_part = parts[0]
                time_part = parts[1] if len(parts) > 1 else ''
                time_formatted = f'{time_part[:2]}:{time_part[2:]}' if len(time_part) >= 4 else time_part

                with open(f'archive/{f}', 'r', encoding='utf-8') as af:
                    content = af.read()
                    topic_match = re.search(r'topic-badge[^>]*>([^<]+)', content)
                    topic_text = topic_match.group(1).strip() if topic_match else 'Unknown'

                archive_files.append({
                    'filename': f,
                    'date': date_part,
                    'time': time_formatted,
                    'topic': topic_text,
                    'display': f'{date_part} {time_formatted} - {topic_text}'
                })
            except:
                archive_files.append({
                    'filename': f,
                    'date': name_without_ext,
                    'time': '',
                    'topic': 'Unknown',
                    'display': name_without_ext
                })

# ========== ENFORCE MAX 100 FILES IN ARCHIVE ==========
MAX_ARCHIVE_FILES = 100
if len(archive_files) > MAX_ARCHIVE_FILES:
    files_to_delete = archive_files[MAX_ARCHIVE_FILES:]
    for item in files_to_delete:
        try:
            os.remove(f"archive/{item['filename']}")
            print(f"Deleted old archive: {item['filename']}")
        except Exception as e:
            print(f"Warning: Could not delete {item['filename']}: {e}")

    archive_files = archive_files[:MAX_ARCHIVE_FILES]
    print(f"Archive cleaned: removed {len(files_to_delete)} old files, keeping {len(archive_files)}")

archive_count = len(archive_files)
print(f"Archive contains {archive_count} old tip sets")

archive_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tips Archive - Scale Model Building</title>
<style>
:root {{
  --primary: #6d4aff;
  --primary-dark: #573dd4;
  --bg-color: #f8f9fc;
  --card-bg: #ffffff;
  --text-main: #1a1a2e;
  --text-muted: #6c757d;
  --border-color: #e9ecef;
  --shadow: rgba(109, 74, 255, 0.15);
  --gradient-start: #6d4aff;
  --gradient-end: #a855f7;
  --warning-bg: #fff3cd;
  --warning-border: #ffc107;
  --warning-text: #856404;
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
header {{ text-align: center; margin-bottom: 40px; }}
h1 {{
  font-size: 2.5em; font-weight: 700;
  background: linear-gradient(135deg, var(--gradient-start), var(--gradient-end));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  margin-bottom: 10px;
}}
.subtitle {{ color: var(--text-muted); font-size: 1.1em; }}
.archive-count {{
  display: inline-block;
  background: linear-gradient(135deg, var(--primary), var(--gradient-end));
  color: white; padding: 8px 20px; border-radius: 20px;
  font-size: 0.9em; font-weight: 600; margin-top: 15px;
  box-shadow: 0 4px 15px var(--shadow);
}}
.disclaimer {{
  background: var(--warning-bg);
  border: 1px solid var(--warning-border);
  border-left: 5px solid var(--warning-border);
  border-radius: 10px;
  padding: 15px 20px;
  margin: 20px 0 30px 0;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}}
.disclaimer-icon {{
  flex-shrink: 0;
  font-size: 1.3em;
  margin-top: 2px;
}}
.disclaimer-text {{
  font-size: 0.9em;
  color: var(--warning-text);
  line-height: 1.5;
}}
.disclaimer-text strong {{
  display: block;
  margin-bottom: 3px;
}}
.actions {{ text-align: center; margin: 30px 0; }}
.btn {{
  display: inline-block;
  background: white; color: var(--primary);
  border: 2px solid var(--primary);
  padding: 12px 30px; border-radius: 25px;
  text-decoration: none; font-weight: 600;
  transition: all 0.3s ease;
}}
.btn:hover {{
  background: var(--primary); color: white;
  transform: translateY(-2px);
}}
.archive-list {{ display: grid; gap: 15px; }}
.archive-item {{
  background: var(--card-bg); border-radius: 12px; padding: 20px 25px;
  box-shadow: 0 2px 10px var(--shadow);
  border-left: 4px solid var(--primary);
  transition: all 0.3s ease;
  display: flex; align-items: center; justify-content: space-between;
}}
.archive-item:hover {{
  transform: translateX(5px);
  box-shadow: 0 4px 15px var(--shadow);
}}
.archive-item-info {{ flex-grow: 1; }}
.archive-item-date {{
  font-weight: 600; color: var(--text-main); font-size: 1.1em;
}}
.archive-item-topic {{
  color: var(--text-muted); font-size: 0.95em; margin-top: 5px;
}}
.archive-item-link {{
  background: var(--primary); color: white;
  padding: 8px 20px; border-radius: 20px;
  text-decoration: none; font-size: 0.9em; font-weight: 600;
  white-space: nowrap; margin-left: 20px;
  transition: all 0.3s ease;
}}
.archive-item-link:hover {{
  background: var(--primary-dark);
}}
.empty-message {{
  text-align: center; color: var(--text-muted);
  font-size: 1.1em; padding: 40px;
}}
footer {{
  text-align: center; margin-top: 60px; padding-top: 30px;
  border-top: 1px solid var(--border-color);
  color: var(--text-muted); font-size: 0.9em;
}}
@keyframes fadeInUp {{
  from {{ opacity: 0; transform: translateY(20px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}
.archive-item {{ animation: fadeInUp 0.4s ease forwards; }}
@media (max-width: 768px) {{
  .container {{ padding: 20px 15px; }}
  h1 {{ font-size: 1.8em; }}
  .archive-item {{
    flex-direction: column; align-items: flex-start; gap: 10px;
  }}
  .archive-item-link {{ margin-left: 0; }}
  .disclaimer {{ flex-direction: column; gap: 8px; }}
}}
</style>
</head>
<body>
<div class="container">
<header>
<h1>&#128194; Tips Archive</h1>
<p class="subtitle">Previous Scale Model Building Tips</p>
<div class="archive-count">{archive_count} archived tip sets</div>
</header>
<div class="disclaimer">
<div class="disclaimer-icon">&#9888;&#65039;</div>
<div class="disclaimer-text">
<strong>AI-Generated Content</strong>
All archived tips were generated by an AI language model via Ollama. The content may contain errors or outdated information. Always verify advice against reliable sources.
</div>
</div>
<div class="actions">
<a class="btn" href="../index.html">
<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;">
<line x1="19" y1="12" x2="5" y2="12"></line>
<polyline points="12 19 5 12 12 5"></polyline>
</svg>
Back to Current Tips
</a>
</div>
<div class="archive-list">'''

if archive_files:
    for item in archive_files:
        archive_html += f'''
<div class="archive-item">
<div class="archive-item-info">
<div class="archive-item-date">{item['date']} {item['time']}</div>
<div class="archive-item-topic">{item['topic']}</div>
</div>
<a class="archive-item-link" href="{item['filename']}">View Tips</a>
</div>'''
else:
    archive_html += '''
<div class="empty-message">
No archived tips yet. Archive will grow automatically as new tips are generated.
</div>'''

archive_html += '''
</div>
<footer>
<p>Scale Model Building Tips Archive &middot; Powered by Ollama</p>
</footer>
</div>
</body>
</html>'''

with open('archive/index.html', 'w', encoding='utf-8') as f:
    f.write(archive_html)

print(f"OK: archive/index.html created with {archive_count} entries")
