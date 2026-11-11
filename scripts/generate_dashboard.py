import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from datetime import datetime, timezone
from xml.sax.saxutils import escape

USER = os.getenv("GITHUB_USERNAME", "Luis-Eduardo-S-Proencio")
TOKEN = os.getenv("GITHUB_TOKEN", "")
OUT = Path("assets/dashboard.svg")

LANG_COLORS = {
    "JavaScript": "#E8D94F", "HTML": "#F0643B", "CSS": "#398BCB",
    "Python": "#3976A8", "TypeScript": "#3178C6", "Java": "#E76F00",
    "C#": "#8B65B5", "PHP": "#777BB4", "Shell": "#89E051",
    "Go": "#00ADD8", "Rust": "#DEA584", "C++": "#F34B7D",
    "C": "#555555", "Vue": "#41B883", "Jupyter Notebook": "#DA5B0B"
}

def get_json(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-profile-dashboard",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode("utf-8"))

def esc(value):
    return escape(str(value))

def make_svg(repo_count, stars, commits, language_bytes):
    # Imita a composição da imagem de referência: preto, três métricas e barras.
    width = 1000
    ordered = sorted(language_bytes.items(), key=lambda x: x[1], reverse=True)[:7]
    total = sum(language_bytes.values())
    if total:
        langs = [(name, value / total * 100) for name, value in ordered]
    else:
        langs = []

    height = 445 + max(0, len(langs) - 3) * 52
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#000000"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif}</style>',
        '<text x="20" y="38" fill="#F0F0F0" font-size="23" font-weight="700">Resumo geral</text>',
    ]
    metrics = [
        (34, "Commits", commits, "#58A6FF", "⌁"),
        (365, "Repositórios", repo_count, "#A78BFA", "▧"),
        (696, "Estrelas", stars, "#F1C40F", "☆"),
    ]
    for x, label, value, color, symbol in metrics:
        out += [
            f'<text x="{x}" y="100" fill="{color}" font-size="25">{symbol}</text>',
            f'<text x="{x}" y="151" fill="#F4F4F4" font-size="31" font-weight="600">{esc(value)}</text>',
            f'<text x="{x}" y="207" fill="#D0D0D0" font-size="20">{esc(label)}</text>',
        ]
    out += [
        '<line x1="20" y1="258" x2="980" y2="258" stroke="#242424" stroke-width="1"/>',
        '<text x="20" y="322" fill="#F0F0F0" font-size="23" font-weight="700">Linguagens mais utilizadas</text>',
    ]

    if not langs:
        out.append('<text x="20" y="380" fill="#BDBDBD" font-size="18">Não foi possível obter dados de linguagens.</text>')
    else:
        for i, (name, pct) in enumerate(langs):
            y = 380 + i * 82
            color = LANG_COLORS.get(name, "#9B83D5")
            bar_w = 960 * pct / 100
            out += [
                f'<text x="20" y="{y}" fill="#EAEAEA" font-size="21" font-weight="600">{esc(name)}</text>',
                f'<text x="980" y="{y}" text-anchor="end" fill="#D0D0D0" font-size="20">{pct:.1f}%</text>',
                f'<rect x="20" y="{y+18}" width="960" height="14" rx="7" fill="#252525"/>',
                f'<rect x="20" y="{y+18}" width="{bar_w:.2f}" height="14" rx="7" fill="{color}"/>',
            ]

    out.append(f'<text x="20" y="{height-16}" fill="#777777" font-size="12">Atualizado em {datetime.now(timezone.utc).strftime("%d/%m/%Y")} · Dados públicos do GitHub</text>')
    out.append('</svg>')
    return "\n".join(out)

def main():
    encoded_user = urllib.parse.quote(USER, safe="")
    repos = get_json(f"https://api.github.com/users/{encoded_user}/repos?per_page=100&type=owner")
    repos = [r for r in repos if not r.get("fork", False)]
    stars = sum(int(r.get("stargazers_count", 0)) for r in repos)

    language_bytes = {}
    for repo in repos:
        url = f"https://api.github.com/repos/{encoded_user}/{urllib.parse.quote(repo['name'], safe='')}/languages"
        try:
            for language, size in get_json(url).items():
                language_bytes[language] = language_bytes.get(language, 0) + int(size)
        except Exception as e:
            print(f"Aviso ao consultar {repo['name']}: {e}")

    commits = "—"
    try:
        q = urllib.parse.quote(f"author:{USER}")
        result = get_json(f"https://api.github.com/search/commits?q={q}&per_page=1")
        commits = f'{result.get("total_count", 0):,}'.replace(",", ".")
    except Exception as e:
        print(f"Aviso: contagem de commits indisponível: {e}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(make_svg(len(repos), stars, commits, language_bytes), encoding="utf-8")
    print(f"Dashboard atualizado em {OUT}")

if __name__ == "__main__":
    main()
