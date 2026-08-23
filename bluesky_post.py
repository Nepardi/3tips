import json
import os
import sys

# ========== CONFIG ==========
TOPIC_IMAGE_KEYS = {
    'MATERIALS_SUPPLIES': 'materials',
    'TOOLS_TECHNIQUES': 'tools',
    'PAINTING_FINISHING': 'painting',
    'ASSEMBLY_CONSTRUCTION': 'assembly',
    'TROUBLESHOOTING_PROTIPS': 'troubleshooting'
}

TOPIC_DISPLAY = {
    'MATERIALS_SUPPLIES': 'Materials & Supplies',
    'TOOLS_TECHNIQUES': 'Tools & Techniques',
    'PAINTING_FINISHING': 'Painting & Weathering',
    'ASSEMBLY_CONSTRUCTION': 'Assembly & Construction',
    'TROUBLESHOOTING_PROTIPS': 'Troubleshooting & Pro Tips'
}

WEBSITE_URL = 'https://scalemodeltips.eu'

# ========== GET CREDENTIALS ==========
BLUESKY_HANDLE = os.environ.get('BLUESKY_HANDLE', '')
BLUESKY_PASSWORD = os.environ.get('BLUESKY_APP_PASSWORD', '')

if not BLUESKY_HANDLE or not BLUESKY_PASSWORD:
    print("Bluesky credentials not set (BLUESKY_HANDLE / BLUESKY_APP_PASSWORD)")
    print("Skipping Bluesky post.")
    sys.exit(0)

# ========== READ TIPS ==========
try:
    with open('tips.json', 'r', encoding='utf-8') as f:
        tips_data = json.load(f)
except Exception as e:
    print(f"Error reading tips.json: {e}")
    sys.exit(1)

tips = tips_data.get('tips', [])
if not tips or len(tips) == 0:
    print("No tips found in tips.json, skipping Bluesky post")
    sys.exit(0)

# ========== DETERMINE TOPIC ==========
try:
    with open('topics.json', 'r', encoding='utf-8') as f:
        topics_data = json.load(f)
    topic_count = len(topics_data['topics'])
    used_topic_index = (topics_data['next_topic'] - 2) % topic_count
    topic_name = topics_data['topics'][used_topic_index]
    topic_display = TOPIC_DISPLAY.get(topic_name, topic_name)
    topic_img_key = TOPIC_IMAGE_KEYS.get(topic_name, topic_name.lower())
except Exception:
    topic_name = ''
    topic_display = 'Scale Model'
    topic_img_key = ''

# ========== FIND IMAGE ==========
image_path = None

# Try header image first
header_path = f'images/header_{topic_img_key}.jpg'
if os.path.exists(header_path):
    image_path = header_path
else:
    # Try card images
    for i in range(1, 6):
        card_path = f'images/{topic_img_key}_{i}.jpg'
        if os.path.exists(card_path):
            image_path = card_path
            break

print(f"Image for Bluesky: {image_path or 'None'}")

# ========== BUILD POST TEXT ==========
first_tip = tips[0]
title = str(first_tip.get('title', ''))
text = str(first_tip.get('text', ''))

prefix = f"New Scale Model Tips: {topic_display}\n\n{title}\n"
suffix = f"\n\nSee all 5 tips at {WEBSITE_URL}"
max_text_len = 300 - len(prefix) - len(suffix)

if len(text) > max_text_len:
    text_teaser = text[:max_text_len - 3].rstrip() + "..."
else:
    text_teaser = text

post_text = prefix + text_teaser + suffix

print(f"Post text ({len(post_text)} chars):")
print(post_text)

# ========== POST TO BLUESKY ==========
try:
    from atproto import Client

    client = Client()
    client.login(BLUESKY_HANDLE, BLUESKY_PASSWORD)

    if image_path and os.path.exists(image_path):
        with open(image_path, 'rb') as f:
            img_data = f.read()

        # Bluesky image limit: ~1 MiB
        if len(img_data) > 1000000:
            print(f"Image too large ({len(img_data)} bytes), posting without image")
            post = client.send_post(text=post_text)
        else:
            post = client.send_image(
                text=post_text,
                image=img_data,
                image_alt=f"Scale model building tips about {topic_display}"
            )
    else:
        post = client.send_post(text=post_text)

    print(f"Posted to Bluesky successfully!")
    print(f"Post URI: {post.uri}")

except ImportError:
    print("atproto library not installed. Run: pip install atproto")
    sys.exit(1)
except Exception as e:
    print(f"Error posting to Bluesky: {e}")
    sys.exit(1)
