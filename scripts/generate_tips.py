import re

def generate_finnish_tips():
    return [
        "Aloita päivä yhdellä selkeällä tavoitteella.",
        "Pidä lyhyt tauko jokaisen tunnin jälkeen.",
        "Kokeile 10 minuutin siivousmetodia."
    ]

def generate_english_tips():
    return [
        "Start your day with one clear goal.",
        "Take a short break every hour.",
        "Try the 10-minute cleaning method."
    ]

def replace_section(html, section_id, tips):
    # Luo uusi HTML sisältö
    new_content = "".join([f'<div class="tip">{t}</div>' for t in tips])

    # Regex: korvaa KAIKKI sisällöt divin sisällä
    pattern = rf'<div id="{section_id}">.*?</div>'
    replacement = f'<div id="{section_id}">{new_content}</div>'

    return re.sub(pattern, replacement, html, flags=re.DOTALL)

def update_html():
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    html = replace_section(html, "tips-fi", generate_finnish_tips())
    html = replace_section(html, "tips-en", generate_english_tips())

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    update_html()
