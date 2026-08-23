import json
import os
import sys
from datetime import datetime

# ========== FIX WINDOWS CONSOLE ENCODING ==========
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

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
HASHTAGS = '\n\n#scalemodels #hobby #pienoismallit'

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

header_path = f'images/header_{topic_img_key}.jpg'
if os.path.exists(header_path):
    image_path = header_path
else:
    for i in range(1, 6):
        card_path = f'images/{topic_img_key}_{i}.jpg'
        if os.path.exists(card_path):
            image_path = card_path
            break

print(f"Image for Bluesky: {image_path or 'None'}")

# ========== BUILD POST TEXT WITH FACETS ==========
first_tip = tips[0]
title = str(first_tip.get('title', ''))
text_content = str(first_tip.get('text', ''))

prefix = f"New: {topic_display}\n\n{title}\n\n"
suffix = "\n\nFull 5 tips:"
max_text_len = 300 - len(prefix) - len(suffix) - len(WEBSITE_URL) - 2 - len(HASHTAGS)

if len(text_content) > max_text_len:
    text_teaser = text_content[:max_text_len - 3].rstrip() + "..."
else:
    text_teaser = text_content

post_text = prefix + text_teaser + suffix + f" {WEBSITE_URL}" + HASHTAGS

# Calculate byte positions for facets
def byte_pos(text, substring):
    """Calculate byte position of substring in text."""
    char_pos = text.rfind(substring)
    if char_pos == -1:
        return -1, -1
    bytes_before = len(text[:char_pos].encode('utf-8'))
    bytes_len = len(substring.encode('utf-8'))
    return bytes_before, bytes_before + bytes_len

url_start_byte, url_end_byte = byte_pos(post_text, WEBSITE_URL)

print(f"Post text ({len(post_text)} chars):")
print(post_text)

# ========== POST TO BLUESKY ==========
try:
    from atproto import Client, models

    client = Client()
    client.login(BLUESKY_HANDLE, BLUESKY_PASSWORD)
    print(f"Logged in as {BLUESKY_HANDLE}")

    # Create facets list
    facets = []

    # URL facet
    if url_start_byte >= 0:
        url_facet = models.AppBskyRichtextFacet.Main(
            index=models.AppBskyRichtextFacet.ByteSlice(byte_start=url_start_byte, byte_end=url_end_byte),
            features=[
                models.AppBskyRichtextFacet.Link(uri=WEBSITE_URL)
            ]
        )
        facets.append(url_facet)

    # Hashtag facets
    for tag in ['#scalemodels', '#hobby', '#pienoismallit']:
        tag_start, tag_end = byte_pos(post_text, tag)
        if tag_start >= 0:
            tag_facet = models.AppBskyRichtextFacet.Main(
                index=models.AppBskyRichtextFacet.ByteSlice(byte_start=tag_start, byte_end=tag_end),
                features=[
                    models.AppBskyRichtextFacet.Tag(tag=tag.lstrip('#'))
                ]
            )
            facets.append(tag_facet)

    # Build post record
    created_at = client.get_current_time_iso()

    if image_path and os.path.exists(image_path):
        with open(image_path, 'rb') as f:
            img_data = f.read()

        if len(img_data) > 1000000:
            print(f"Image too large ({len(img_data)} bytes), posting without image")
            post_record = models.AppBskyFeedPost.Record(
                text=post_text,
                facets=facets,
                created_at=created_at
            )
        else:
            uploaded_img = client.upload_blob(img_data)
            post_record = models.AppBskyFeedPost.Record(
                text=post_text,
                facets=facets,
                embed=models.AppBskyEmbedImages.Main(
                    images=[
                        models.AppBskyEmbedImages.Image(
                            alt=f"Scale model building tips about {topic_display}",
                            image=uploaded_img.blob
                        )
                    ]
                ),
                created_at=created_at
            )
    else:
        post_record = models.AppBskyFeedPost.Record(
            text=post_text,
            facets=facets,
            created_at=created_at
        )

    # Create the post
    post_response = client.app.bsky.feed.post.create(client.me.did, post_record)

    print(f"Posted to Bluesky successfully!")
    print(f"Post URI: {post_response.uri}")

except ImportError:
    print("atproto library not installed. Run: pip install atproto")
    sys.exit(1)
except Exception as e:
    print(f"Error posting to Bluesky: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
