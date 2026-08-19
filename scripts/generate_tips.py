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

def update_html():
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    fi_tips = generate_finnish_tips()
    en_tips = generate_english_tips()

    fi_html = "".join([f'<div class="tip">{t}</div>' for t in fi_tips])
    en_html = "".join([f'<div class="tip">{t}</div>' for t in en_tips])

    # Tyhjennetään vanhat vinkit ja lisätään uudet
    html = html.replace(
        '<div id="tips-fi">', f'<div id="tips-fi">{fi_html}'
    )
    html = html.replace(
        '<div id="tips-en">', f'<div id="tips-en">{en_html}'
    )

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    update_html()
