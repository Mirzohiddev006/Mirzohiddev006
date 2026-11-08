"""Generate the Featured Projects cards shown in the profile README.

The cards are static, so they are committed to the repository under
assets/projects/. Edit PROJECTS and run:

    python scripts/generate_project_cards.py
"""

from __future__ import annotations

from html import escape
from pathlib import Path

BG = "#0D1117"
PANEL = "#111A16"
BORDER = "#1F6F4A"
TITLE = "#34D399"
ACCENT = "#10B981"
TEXT = "#E6EDF3"
MUTED = "#8B949E"
FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', Helvetica, Arial, sans-serif"

OUT = Path(__file__).resolve().parent.parent / "assets" / "projects"

FEATURED = {
    "file": "marketplace.svg",
    "emoji": "🛒",
    "title": "Furniture, Mattress & Craftsmen Marketplace",
    "status": "LIVE IN PRODUCTION",
    "tagline": "A listings platform for all of Uzbekistan that shows the nearest listings first.",
    "blocks": [
        ("⚙️", "Backend", ["FastAPI + SQLAlchemy", "PostGIS distance sort", "5–100 km radius filter", "RBAC · 2FA · audit log"]),
        ("🎨", "Frontend", ["React 18 + TypeScript", "Site + admin panel", "TanStack · Zustand", "OpenAPI-typed client"]),
        ("🕷️", "Data", ["OLX scraper", "Deduplication", "WebP image processing", "JSON & ZIP export"]),
        ("🚀", "Delivery", ["Docker Compose + Nginx", "GitHub Actions CI/CD", "Uptime monitoring", "Automated backups"]),
    ],
    "stack": ["React", "TypeScript", "FastAPI", "PostgreSQL", "PostGIS", "Redis", "Docker"],
}

SMALL = [
    {
        "file": "bunyodkor.svg",
        "emoji": "⚽",
        "title": "Bunyodkor CIMS",
        "status": "ACTIVE",
        "lines": [
            "Club information management system",
            "for the Bunyodkor football academy.",
        ],
        "points": ["Interactive dashboards", "Data management interfaces", "Role-based access control", "Real-time data over REST API"],
        "stack": ["React", "TypeScript", "shadcn/ui", "Zustand"],
        "cta": "Live demo  →",
    },
    {
        "file": "chatbot.svg",
        "emoji": "💬",
        "title": "AI-Powered FAQ Chatbot",
        "status": "COMPLETE",
        "lines": [
            "Knowledge-base chatbot that answers",
            "from company data instead of guessing.",
        ],
        "points": ["Retrieval-augmented generation", "Structured system prompts", "Grounded, source-based answers", "Easy knowledge-base updates"],
        "stack": ["Claude API", "RAG", "Prompt design"],
        "cta": None,
    },
]


def chip_row(items: list[str], x: float, y: float, max_x: float) -> str:
    out = []
    for item in items:
        w = 16 + 7.2 * len(item)
        if x + w > max_x:
            break
        out.append(
            f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="24" rx="12" fill="#0F2A1F" stroke="{BORDER}"/>'
            f'<text x="{x + w / 2:.1f}" y="{y + 16.5}" text-anchor="middle" class="chip">{escape(item)}</text>'
        )
        x += w + 8
    return "".join(out)


def pill(text: str, right: float, y: float) -> str:
    w = 28 + 7.5 * len(text)
    x = right - w
    return (
        f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="24" rx="12" fill="{ACCENT}"/>'
        f'<circle cx="{x + 13:.1f}" cy="{y + 12}" r="3.5" fill="#fff"><animate attributeName="opacity" values="1;.3;1" dur="1.6s" repeatCount="indefinite"/></circle>'
        f'<text x="{x + 23:.1f}" y="{y + 16.5}" class="pill">{escape(text)}</text>'
    )


def pill_left(text: str, x: float, y: float) -> str:
    return pill(text, x + 28 + 7.5 * len(text), y)


def shell(width: int, height: int, label: str, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">
<title>{escape(label)}</title>
<style>
  .h {{ font: 700 21px {FONT}; fill: {TEXT}; }}
  .s {{ font: 400 14px {FONT}; fill: {MUTED}; }}
  .bt {{ font: 700 14px {FONT}; fill: {TITLE}; }}
  .li {{ font: 400 13px {FONT}; fill: {TEXT}; }}
  .chip {{ font: 600 12px {FONT}; fill: {TITLE}; }}
  .pill {{ font: 700 11px {FONT}; fill: #fff; letter-spacing: .6px; }}
  .cta {{ font: 700 13px {FONT}; fill: {TITLE}; }}
  .in {{ opacity: 0; animation: in .6s ease-out forwards; }}
  @keyframes in {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
</style>
<defs>
  <linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#064E3B"/><stop offset=".5" stop-color="#059669"/><stop offset="1" stop-color="#34D399"/></linearGradient>
  <radialGradient id="glow" cx="1" cy="0" r=".9"><stop offset="0" stop-color="{ACCENT}" stop-opacity=".18"/><stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></radialGradient>
  <clipPath id="card"><rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="14"/></clipPath>
</defs>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="14" fill="{BG}" stroke="{BORDER}"/>
<g clip-path="url(#card)"><rect width="{width}" height="{height}" fill="url(#glow)"/><rect width="{width}" height="5" fill="url(#g)"/></g>
{body}
</svg>
"""


def featured_card(p: dict) -> str:
    w, h = 850, 330
    body = [
        f'<text x="28" y="50" class="h">{p["emoji"]}  {escape(p["title"])}</text>',
        pill(p["status"], w - 28, 31),
        f'<text x="28" y="78" class="s">{escape(p["tagline"])}</text>',
    ]
    bw, gap = (w - 56 - 3 * 14) / 4, 14
    for i, (emoji, name, items) in enumerate(p["blocks"]):
        x = 28 + i * (bw + gap)
        rows = "".join(
            f'<circle cx="{x + 20:.1f}" cy="{138 + j * 26}" r="3" fill="{ACCENT}"/>'
            f'<text x="{x + 31:.1f}" y="{142.5 + j * 26}" class="li" style="font-size:12.5px">{escape(item)}</text>'
            for j, item in enumerate(items)
        )
        body.append(
            f'<g class="in" style="animation-delay:{0.1 + i * 0.12:.2f}s">'
            f'<rect x="{x:.1f}" y="96" width="{bw:.1f}" height="148" rx="10" fill="{PANEL}" stroke="#1B3B2D"/>'
            f'<text x="{x + 14:.1f}" y="120" class="bt">{emoji} {escape(name)}</text>{rows}</g>'
        )
    body.append(f'<line x1="28" y1="266" x2="{w - 28}" y2="266" stroke="#1B3B2D"/>')
    body.append(chip_row(p["stack"], 28, 284, w - 28))
    return shell(w, h, p["title"], "".join(body))


def small_card(p: dict) -> str:
    w, h = 415, 330
    body = [
        f'<text x="24" y="50" class="h" style="font-size:19px">{p["emoji"]}  {escape(p["title"])}</text>',
        pill_left(p["status"], 24, 66),
    ]
    for i, line in enumerate(p["lines"]):
        body.append(f'<text x="24" y="{118 + i * 20}" class="s">{escape(line)}</text>')
    for j, item in enumerate(p["points"]):
        y = 176 + j * 24
        body.append(
            f'<g class="in" style="animation-delay:{0.1 + j * 0.1:.2f}s">'
            f'<path d="M24 {y - 4} l4 4 l8 -9" fill="none" stroke="{ACCENT}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<text x="44" y="{y + 0.5}" class="li">{escape(item)}</text></g>'
        )
    body.append(f'<line x1="24" y1="266" x2="{w - 24}" y2="266" stroke="#1B3B2D"/>')
    body.append(chip_row(p["stack"], 24, 284, w - 24))
    if p["cta"]:
        body.append(f'<text x="{w - 24}" y="82.5" text-anchor="end" class="cta">{escape(p["cta"])}</text>')
    return shell(w, h, p["title"], "".join(body))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / FEATURED["file"]).write_text(featured_card(FEATURED), encoding="utf-8")
    for p in SMALL:
        (OUT / p["file"]).write_text(small_card(p), encoding="utf-8")
    for f in sorted(OUT.glob("*.svg")):
        print(f"wrote {f}")


if __name__ == "__main__":
    main()
