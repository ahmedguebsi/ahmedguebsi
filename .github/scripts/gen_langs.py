"""
Fetches per-repo language bytes via the GitHub API (authenticated with
GITHUB_TOKEN for 5 000 req/h) and renders a tokyonight-themed SVG at
assets/top-langs.svg.  Forks and archived repos are excluded.
"""

import json
import os
import sys
from collections import defaultdict
from urllib.error import URLError
from urllib.request import Request, urlopen

USERNAME = "ahmedguebsi"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

LANG_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#2b7489",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "SCSS": "#c6538c",
    "C": "#555555",
    "C#": "#178600",
    "C++": "#f34b7d",
    "Java": "#b07219",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Shell": "#89e051",
    "Jupyter Notebook": "#DA5B0B",
    "Vue": "#41b883",
    "PHP": "#4F5D95",
    "Ruby": "#701516",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "R": "#198CE7",
    "Dockerfile": "#384d54",
}

# Tokyonight colours
BG      = "#1a1b27"
BORDER  = "#29344a"
TITLE   = "#c0caf5"
TEXT    = "#a9b1d6"
SUBTEXT = "#565f89"


def fetch(url: str):
    req = Request(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def get_repos():
    repos, page = [], 1
    while True:
        batch = fetch(
            f"https://api.github.com/users/{USERNAME}/repos"
            f"?per_page=100&page={page}&type=owner"
        )
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def aggregate_langs(repos):
    totals: dict[str, int] = defaultdict(int)
    for repo in repos:
        if repo.get("fork") or repo.get("archived"):
            continue
        try:
            langs = fetch(
                f"https://api.github.com/repos/{USERNAME}/{repo['name']}/languages"
            )
            for lang, b in langs.items():
                totals[lang] += b
        except (URLError, Exception):
            pass
    return totals


def build_svg(top: list[tuple[str, int]]) -> str:
    grand = sum(b for _, b in top)

    W       = 340
    PAD     = 20
    ROW_H   = 28
    NAME_W  = 90
    PCT_W   = 40
    BAR_MAX = W - PAD * 2 - NAME_W - PCT_W - 8
    H       = PAD * 2 + 24 + len(top) * ROW_H + 6

    rows = []
    for i, (lang, b) in enumerate(top):
        pct   = b / grand
        bw    = max(int(pct * BAR_MAX), 2)
        color = LANG_COLORS.get(lang, "#8b949e")
        y     = PAD + 30 + i * ROW_H

        rows.append(
            f'<circle cx="{PAD + 6}" cy="{y}" r="4.5" fill="{color}"/>'
            f'<text x="{PAD + 16}" y="{y + 4}" fill="{TEXT}" font-size="11"'
            f' font-family="ui-monospace,SFMono-Regular,monospace">{lang}</text>'
            f'<rect x="{PAD + NAME_W}" y="{y - 5}" width="{bw}" height="8"'
            f' fill="{color}" rx="3" opacity="0.85"/>'
            f'<text x="{W - PAD}" y="{y + 4}" fill="{SUBTEXT}" font-size="10"'
            f' font-family="ui-monospace,SFMono-Regular,monospace"'
            f' text-anchor="end">{pct * 100:.1f}%</text>'
        )

    return (
        f'<svg width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="{W}" height="{H}" rx="6" fill="{BG}"'
        f' stroke="{BORDER}" stroke-width="1"/>'
        f'<text x="{PAD}" y="{PAD + 15}" fill="{TITLE}" font-size="14"'
        f' font-weight="600" font-family="ui-monospace,SFMono-Regular,monospace">'
        f'Most Used Languages</text>'
        + "".join(rows)
        + "</svg>"
    )


def main():
    repos  = get_repos()
    totals = aggregate_langs(repos)

    top = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:8]
    if not top:
        print("No public language data found — SVG not updated.")
        sys.exit(0)

    svg = build_svg(top)

    os.makedirs("assets", exist_ok=True)
    with open("assets/top-langs.svg", "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"assets/top-langs.svg written ({len(top)} languages)")


if __name__ == "__main__":
    main()
