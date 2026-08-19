import os
import json

def update_html():
    raw = os.getenv("AI_OUTPUT")

    if not raw:
        print("AI_OUTPUT is empty — OpenAI call failed.")
        return

    try:
        parsed = json.loads(raw)
    except Exception:
        print("AI_OUTPUT is not valid JSON.")
        print("Raw:", raw)
        return

    if "finnish" not in parsed or "english" not in parsed:
        print("Parsed JSON missing expected keys.")
        print("Parsed:", parsed)
        return

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
