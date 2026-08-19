import random

def update_html():
    finnish_pool = [
        "Kokeile kevyttä viilausta ennen maalausta — lopputulos on siistimpi.",
        "Pese osat miedolla saippualla, jotta maali tarttuu paremmin.",
        "Käytä ohuita maalikerroksia, ne kuivuvat tasaisemmin.",
        "Maskaa teipillä ennen ruiskumaalausta, rajat pysyvät terävinä.",
        "Käytä cocktailtikkuja pienosien käsittelyyn."
    ]

    english_pool = [
        "Use thin paint layers for a smoother finish.",
        "Wash parts with mild soap to improve paint adhesion.",
        "Mask edges with hobby tape for crisp paint lines.",
        "Sand lightly to remove mold lines before painting.",
        "Use toothpicks to hold small parts while painting."
    ]

    fi_tips = random.sample(finnish_pool, 3)
    en_tips = random.sample(english_pool, 3)

    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    fi_html = "".join([f'<div class="tip">{t}</div>' for t in fi_tips])
    en_html = "".join([f'<div class="tip">{t}</div>' for t in en_tips])

    html = html.replace('<div id="tips-fi"></div>', f'<div id="tips-fi">{fi_html}</div>')
    html = html.replace('<div id="tips-en"></div>', f'<div id="tips-en">{en_html}</div>')

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    update_html()
