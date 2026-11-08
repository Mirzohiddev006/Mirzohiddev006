"""Generate the Tech Stack badges as local SVG files under assets/badges/.

shields.io badges time out on GitHub's image proxy from time to time, so the
badges are committed to the repository instead. Icons come from the
simple-icons npm package (pass its icons directory with --icons; LinkedIn,
OpenAI and Playwright only exist in older releases, so pass a second
directory with --legacy-icons, e.g. simple-icons@11).

    python scripts/generate_badges.py --icons path/to/simple-icons/icons \
        --legacy-icons path/to/simple-icons@11/icons
"""

from __future__ import annotations

import argparse
import re
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "badges"

# file name, label, simple-icons slug (or None), icon colour
BADGES = [
    ("shadcn", "shadcn/ui", "shadcnui", "FFFFFF"),
    ("tanstack-query", "TanStack Query", "reactquery", "FF4154"),
    ("zustand", "Zustand", None, None),
    ("react-hook-form", "React Hook Form", "reacthookform", "EC5990"),
    ("zod", "Zod", "zod", "3E67B1"),
    ("framer-motion", "Framer Motion", "framer", "FFFFFF"),
    ("gsap", "GSAP", "greensock", "88CE02"),
    ("fsd", "Feature-Sliced Design", None, None),
    ("pydantic", "Pydantic v2", "pydantic", "E92063"),
    ("sqlalchemy", "SQLAlchemy 2.0", "sqlalchemy", "FF6B4A"),
    ("alembic", "Alembic", None, None),
    ("postgis", "PostGIS", "postgresql", "6E9BF5"),
    ("auth", "JWT · TOTP 2FA · RBAC", "jsonwebtokens", "FFFFFF"),
    ("openapi", "OpenAPI", "openapiinitiative", "6BA539"),
    ("scraping", "Playwright scraping", "playwright", "2EAD33"),
    ("openai", "OpenAI API", "openai", "FFFFFF"),
    ("claude-api", "Claude API", "anthropic", "D97757"),
    ("claude-code", "Claude Code", "claude", "D97757"),
    ("rag", "RAG", None, None),
    ("prompt-engineering", "Prompt Engineering", None, None),
    ("gemini", "Gemini", "googlegemini", "8E75B2"),
    ("docker-compose", "Docker Compose", "docker", "2496ED"),
    ("pytest", "pytest", "pytest", "0A9EDC"),
    ("playwright", "Playwright", "playwright", "2EAD33"),
    ("msw", "MSW", "mockserviceworker", "FF6A33"),
]

FONT = "Verdana, 'DejaVu Sans', Geneva, sans-serif"
FONT_SIZE = 11
HEIGHT = 28


def text_width(label: str) -> float:
    """Width of the label in Verdana/DejaVu Sans Bold at FONT_SIZE."""
    try:
        from PIL import ImageFont

        font = ImageFont.truetype("DejaVuSans-Bold.ttf", FONT_SIZE)
        return font.getlength(label)
    except Exception:
        return 7.4 * len(label)


def icon_path(slug: str, dirs: list[Path]) -> str:
    for d in dirs:
        f = d / f"{slug}.svg"
        if f.exists():
            return re.search(r'<path d="([^"]+)"', f.read_text()).group(1)
    raise SystemExit(f"icon {slug!r} not found in {', '.join(map(str, dirs))}")


def badge(label: str, path: str | None, color: str | None) -> str:
    tw = round(text_width(label), 1)
    left = 10
    icon = ""
    if path:
        icon = f'<g transform="translate({left},7) scale(0.5833)"><path d="{path}" fill="#{color}"/></g>'
        tx = left + 14 + 7
    else:
        icon = f'<circle cx="{left + 4}" cy="14" r="4" fill="#10B981"/>'
        tx = left + 8 + 7
    w = round(tx + tw + 11)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{HEIGHT}" viewBox="0 0 {w} {HEIGHT}" role="img" aria-label="{escape(label)}">'
        f"<title>{escape(label)}</title>"
        f'<rect x=".5" y=".5" width="{w - 1}" height="{HEIGHT - 1}" rx="6" fill="#0F1A15" stroke="#1F6F4A"/>'
        f"{icon}"
        f'<text x="{tx}" y="18.2" font-family="{FONT}" font-size="{FONT_SIZE}" font-weight="700" fill="#E6EDF3" '
        f'textLength="{tw}" lengthAdjust="spacingAndGlyphs">{escape(label)}</text>'
        "</svg>\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--icons", type=Path, required=True)
    parser.add_argument("--legacy-icons", type=Path)
    args = parser.parse_args()
    dirs = [args.icons] + ([args.legacy_icons] if args.legacy_icons else [])

    OUT.mkdir(parents=True, exist_ok=True)
    for name, label, slug, color in BADGES:
        path = icon_path(slug, dirs) if slug else None
        (OUT / f"{name}.svg").write_text(badge(label, path, color), encoding="utf-8")
    print(f"wrote {len(BADGES)} badges to {OUT}")


if __name__ == "__main__":
    main()
