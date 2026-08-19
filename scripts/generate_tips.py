import os
import json

def update_html():
    raw = os.getenv("AI_OUTPUT")
    data = json.loads(raw)

    # OpenAI palauttaa yhden siistin JSON-objektin
    content = data["choices"][0]["message"]["content"]

    parsed = json.loads(content)

    fi_tips = parsed["finnish"]
    en_tips = parsed["english"]

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
