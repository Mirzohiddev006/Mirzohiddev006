"""Generate the green profile cards (stats, languages, streak, activity, followers).

Runs in GitHub Actions with GITHUB_TOKEN and writes SVG files into an output
directory that is published to the `output` branch next to the snake SVGs.
Only the standard library is used.

    python scripts/generate_cards.py --user Mirzohiddev006 --out dist
    python scripts/generate_cards.py --sample --out dist   # offline preview
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import urllib.request
from html import escape
from pathlib import Path

API_URL = "https://api.github.com/graphql"

BG = "#0D1117"
BORDER = "#1F6F4A"
TITLE = "#34D399"
ACCENT = "#10B981"
TEXT = "#E6EDF3"
MUTED = "#8B949E"
FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', Helvetica, Arial, sans-serif"

PROFILE_QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionYears
    }
  }
}
"""

YEAR_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


# --------------------------------------------------------------------------- data

def graphql(query: str, variables: dict, token: str) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "profile-cards-generator",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.load(resp)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]


def fetch(login: str, token: str) -> dict:
    user = graphql(PROFILE_QUERY, {"login": login}, token)["user"]

    days: dict[str, int] = {}
    for year in user["contributionsCollection"]["contributionYears"]:
        start = f"{year}-01-01T00:00:00Z"
        end = f"{year}-12-31T23:59:59Z"
        cal = graphql(YEAR_QUERY, {"login": login, "from": start, "to": end}, token)
        for week in cal["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for day in week["contributionDays"]:
                days[day["date"]] = day["contributionCount"]

    languages: dict[str, dict] = {}
    stars = 0
    for repo in user["repositories"]["nodes"]:
        stars += repo["stargazerCount"]
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            entry = languages.setdefault(name, {"size": 0, "color": edge["node"]["color"] or ACCENT})
            entry["size"] += edge["size"]

    cc = user["contributionsCollection"]
    return {
        "followers": user["followers"]["totalCount"],
        "repos": user["repositories"]["totalCount"],
        "stars": stars,
        "prs": user["pullRequests"]["totalCount"],
        "issues": user["issues"]["totalCount"],
        "commits": cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        "languages": languages,
        "days": days,
    }


def sample() -> dict:
    rng = random.Random(6)
    today = dt.date.today()
    days = {}
    for i in range(500):
        d = today - dt.timedelta(days=i)
        days[d.isoformat()] = 0 if rng.random() < 0.25 and i > 9 else rng.randint(1, 14)
    return {
        "followers": 42,
        "repos": 31,
        "stars": 18,
        "prs": 57,
        "issues": 12,
        "commits": 1460,
        "languages": {
            "TypeScript": {"size": 5_200_000, "color": "#3178c6"},
            "Python": {"size": 1_900_000, "color": "#3572A5"},
            "HTML": {"size": 900_000, "color": "#e34c26"},
            "CSS": {"size": 640_000, "color": "#563d7c"},
            "JavaScript": {"size": 420_000, "color": "#f1e05a"},
            "Shell": {"size": 30_000, "color": "#89e051"},
        },
        "days": days,
    }


# ------------------------------------------------------------------------ helpers

def fmt(n: int) -> str:
    if n >= 10_000:
        return f"{n / 1000:.1f}k".replace(".0k", "k")
    return f"{n:,}"


def card(width: int, height: int, title: str, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title>
<style>
  .t {{ font: 600 18px {FONT}; fill: {TITLE}; }}
  .l {{ font: 400 14px {FONT}; fill: {TEXT}; }}
  .v {{ font: 700 14px {FONT}; fill: {TEXT}; }}
  .m {{ font: 400 12px {FONT}; fill: {MUTED}; }}
  .big {{ font: 700 28px {FONT}; fill: {TEXT}; }}
  .fade {{ opacity: 0; animation: fade .6s ease-out forwards; }}
  @keyframes fade {{ to {{ opacity: 1; }} }}
  @keyframes grow {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
</style>
<defs>
  <linearGradient id="g" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#064E3B"/><stop offset=".5" stop-color="#059669"/><stop offset="1" stop-color="#34D399"/>
  </linearGradient>
</defs>
<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>
<clipPath id="card"><rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10"/></clipPath>
<rect x="0" y="0" width="{width}" height="4" fill="url(#g)" clip-path="url(#card)"/>
<text x="25" y="38" class="t">{escape(title)}</text>
{body}
</svg>
"""


def streaks(days: dict[str, int]) -> tuple[int, int, int]:
    dates = sorted(dt.date.fromisoformat(d) for d in days)
    if not dates:
        return 0, 0, 0
    total = sum(days.values())
    longest = run = 0
    prev = None
    for d in dates:
        if days[d.isoformat()] > 0:
            run = run + 1 if prev and (d - prev).days == 1 and days[prev.isoformat()] > 0 else 1
            longest = max(longest, run)
        else:
            run = 0
        prev = d

    today = dt.date.today()
    cursor = today if days.get(today.isoformat(), 0) > 0 else today - dt.timedelta(days=1)
    current = 0
    while days.get(cursor.isoformat(), 0) > 0:
        current += 1
        cursor -= dt.timedelta(days=1)
    return total, current, longest


# -------------------------------------------------------------------------- cards

ICONS = {
    # 16x16 paths from GitHub Octicons
    "star": "M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z",
    "commit": "M11.93 8.5a4.002 4.002 0 0 1-7.86 0H.75a.75.75 0 0 1 0-1.5h3.32a4.002 4.002 0 0 1 7.86 0h3.32a.75.75 0 0 1 0 1.5Zm-1.43-.75a2.5 2.5 0 1 0-5 0 2.5 2.5 0 0 0 5 0Z",
    "pr": "M1.5 3.25a2.25 2.25 0 1 1 3 2.122v5.256a2.251 2.251 0 1 1-1.5 0V5.372A2.25 2.25 0 0 1 1.5 3.25Zm5.677-.177L9.573.677A.25.25 0 0 1 10 .854V2.5h1A2.5 2.5 0 0 1 13.5 5v5.628a2.251 2.251 0 1 1-1.5 0V5a1 1 0 0 0-1-1h-1v1.646a.25.25 0 0 1-.427.177L7.177 3.427a.25.25 0 0 1 0-.354Z",
    "issue": "M8 9.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3ZM8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0ZM1.5 8a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0Z",
    "repo": "M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z",
    "people": "M2 5.5a3.5 3.5 0 1 1 5.898 2.549 5.508 5.508 0 0 1 3.034 4.084.75.75 0 1 1-1.482.235 4 4 0 0 0-7.9 0 .75.75 0 0 1-1.482-.236A5.507 5.507 0 0 1 3.102 8.05 3.493 3.493 0 0 1 2 5.5ZM11 4a3.001 3.001 0 0 1 2.22 5.018 5.01 5.01 0 0 1 2.56 3.012.749.749 0 0 1-.885.954.752.752 0 0 1-.549-.514 3.507 3.507 0 0 0-2.522-2.372.75.75 0 0 1-.574-.73v-.352a.75.75 0 0 1 .416-.672A1.5 1.5 0 0 0 11 5.5.75.75 0 0 1 11 4Zm-5.5-.5a2 2 0 1 0-.001 3.999A2 2 0 0 0 5.5 3.5Z",
    "fire": "M9.533.753V.752c.217 2.385 1.463 3.626 2.653 4.81C13.37 6.74 14.498 7.863 14.498 10c0 3.5-3 6-6.5 6S1.5 13.512 1.5 10c0-1.298.536-2.464 1.425-3.71.214-.299.68-.296.88.012.164.252.341.48.534.666.186.18.417.237.66.124.246-.114.433-.364.425-.689-.035-1.493.383-3.093 1.36-4.448C7.585 1.29 8.374.533 9.06.149c.205-.115.452.06.473.604Z",
}


def stats_card(d: dict) -> str:
    rows = [
        ("star", "Total stars", d["stars"]),
        ("commit", "Commits (this year)", d["commits"]),
        ("pr", "Pull requests", d["prs"]),
        ("issue", "Issues", d["issues"]),
        ("repo", "Public repositories", d["repos"]),
        ("people", "Followers", d["followers"]),
    ]
    parts = []
    for i, (icon, label, value) in enumerate(rows):
        y = 62 + i * 25
        delay = 0.1 + i * 0.12
        parts.append(
            f'<g class="fade" style="animation-delay:{delay:.2f}s" transform="translate(25,{y})">'
            f'<path d="{ICONS[icon]}" fill="{ACCENT}"/>'
            f'<text x="26" y="12.5" class="l">{label}:</text>'
            f'<text x="225" y="12.5" class="v">{fmt(value)}</text></g>'
        )
    total, _, _ = streaks(d["days"])
    ring = (
        f'<g transform="translate(375,112)">'
        f'<circle r="52" fill="none" stroke="#163A2B" stroke-width="7"/>'
        f'<circle r="52" fill="none" stroke="{ACCENT}" stroke-width="7" stroke-linecap="round" '
        f'stroke-dasharray="327" stroke-dashoffset="327" transform="rotate(-90)">'
        f'<animate attributeName="stroke-dashoffset" from="327" to="40" dur="1.2s" fill="freeze"/></circle>'
        f'<text y="6" text-anchor="middle" class="big" style="font-size:24px">{fmt(total)}</text>'
        f'<text y="26" text-anchor="middle" class="m">contributions</text></g>'
    )
    return card(495, 210, "Mirzohid's GitHub Stats", "".join(parts) + ring)


def languages_card(d: dict) -> str:
    langs = sorted(d["languages"].items(), key=lambda kv: kv[1]["size"], reverse=True)[:6]
    total = sum(v["size"] for _, v in langs) or 1
    bar_w = 300
    x = 25
    segments = []
    for name, v in langs:
        w = bar_w * v["size"] / total
        segments.append(f'<rect x="{x:.2f}" y="56" width="{w:.2f}" height="10" fill="{v["color"]}"/>')
        x += w
    bar = (
        f'<clipPath id="c"><rect x="25" y="56" width="{bar_w}" height="10" rx="5"/></clipPath>'
        f'<g clip-path="url(#c)" style="transform-origin:25px 0;animation:grow .9s ease-out">{"".join(segments)}</g>'
    )
    items = []
    for i, (name, v) in enumerate(langs):
        col, row = divmod(i, 3)
        px, py = 25 + col * 155, 100 + row * 38
        pct = 100 * v["size"] / total
        items.append(
            f'<g class="fade" style="animation-delay:{0.2 + i * 0.1:.2f}s" transform="translate({px},{py})">'
            f'<circle cx="6" cy="-4" r="6" fill="{v["color"]}"/>'
            f'<text x="18" y="0" class="l">{escape(name)}</text>'
            f'<text x="18" y="16" class="m">{pct:.1f}%</text></g>'
        )
    return card(350, 210, "Most Used Languages", bar + "".join(items))


def streak_card(d: dict) -> str:
    total, current, longest = streaks(d["days"])
    first = min(d["days"]) if d["days"] else dt.date.today().isoformat()
    cols = [
        (125, fmt(total), "Total Contributions", f"since {first[:4]}"),
        (425, str(current), "Current Streak", "days in a row"),
        (725, str(longest), "Longest Streak", "days"),
    ]
    parts = []
    for i, (cx, value, label, sub) in enumerate(cols):
        highlight = i == 1
        if highlight:
            parts.append(
                f'<circle cx="{cx}" cy="98" r="40" fill="none" stroke="{ACCENT}" stroke-width="5"/>'
                f'<g transform="translate({cx - 9},44) scale(1.15)"><circle cx="8" cy="8" r="11" fill="{BG}"/>'
                f'<path d="{ICONS["fire"]}" fill="{TITLE}"/></g>'
            )
        parts.append(
            f'<g class="fade" style="animation-delay:{0.15 + i * 0.15:.2f}s">'
            f'<text x="{cx}" y="108" text-anchor="middle" class="big">{value}</text>'
            f'<text x="{cx}" y="166" text-anchor="middle" class="v" style="fill:{TITLE if highlight else TEXT}">{label}</text>'
            f'<text x="{cx}" y="186" text-anchor="middle" class="m">{sub}</text></g>'
        )
    parts.append(f'<line x1="275" y1="60" x2="275" y2="185" stroke="#21262D"/>')
    parts.append(f'<line x1="575" y1="60" x2="575" y2="185" stroke="#21262D"/>')
    return card(850, 205, "Contribution Streak", "".join(parts))


def activity_card(d: dict) -> str:
    today = dt.date.today()
    span = 31
    series = [
        (today - dt.timedelta(days=span - 1 - i), d["days"].get((today - dt.timedelta(days=span - 1 - i)).isoformat(), 0))
        for i in range(span)
    ]
    w, h = 850, 300
    left, right, top, bottom = 55, 25, 60, 250
    peak = max([c for _, c in series] + [4])
    step = (w - left - right) / (span - 1)

    def xy(i: int, c: int) -> tuple[float, float]:
        return left + i * step, bottom - (bottom - top) * c / peak

    pts = [xy(i, c) for i, (_, c) in enumerate(series)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"M{left},{bottom} L" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + f" L{pts[-1][0]:.1f},{bottom} Z"

    grid = []
    for k in range(5):
        val = round(peak * k / 4)
        y = bottom - (bottom - top) * k / 4
        grid.append(f'<line x1="{left}" y1="{y:.1f}" x2="{w - right}" y2="{y:.1f}" stroke="#21262D"/>')
        grid.append(f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end" class="m">{val}</text>')
    labels = []
    for i, (day, _) in enumerate(series):
        if i % 5 == 0 or i == span - 1:
            x, _ = xy(i, 0)
            labels.append(f'<text x="{x:.1f}" y="{bottom + 20}" text-anchor="middle" class="m">{day.strftime("%b %d")}</text>')
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{TEXT}" stroke="{ACCENT}" stroke-width="1.5"/>' for x, y in pts)

    body = (
        '<defs><linearGradient id="a" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{ACCENT}" stop-opacity=".45"/><stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>'
        "</linearGradient></defs>"
        + "".join(grid)
        + f'<path d="{area}" fill="url(#a)" class="fade"/>'
        + f'<polyline points="{line}" fill="none" stroke="{TITLE}" stroke-width="2.5" stroke-linejoin="round" '
        f'pathLength="1" stroke-dasharray="1" stroke-dashoffset="1">'
        '<animate attributeName="stroke-dashoffset" from="1" to="0" dur="1.4s" fill="freeze"/></polyline>'
        + f'<g class="fade" style="animation-delay:1s">{dots}</g>'
        + "".join(labels)
    )
    return card(w, h, "Contributions in the Last 31 Days", body)


def followers_badge(d: dict) -> str:
    label, value = "FOLLOWERS", fmt(d["followers"])
    lw, vw = 124, 16 + 11 * len(value)
    w = lw + vw
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="28" role="img" aria-label="{label}: {value}">
<title>{label}: {value}</title>
<rect width="{lw}" height="28" fill="#064E3B"/><rect x="{lw}" width="{vw}" height="28" fill="{ACCENT}"/>
<g transform="translate(10,6)"><path d="{ICONS['people']}" fill="#fff"/></g>
<g font-family="Verdana, Geneva, DejaVu Sans, sans-serif" font-size="11" font-weight="700" fill="#fff" letter-spacing="1">
<text x="32" y="18">{label}</text>
<text x="{lw + vw / 2}" y="18" text-anchor="middle">{value}</text></g>
</svg>
"""


# --------------------------------------------------------------------------- main

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", default="Mirzohiddev006")
    parser.add_argument("--out", default="dist")
    parser.add_argument("--sample", action="store_true", help="use made-up data (offline preview)")
    args = parser.parse_args()

    if args.sample:
        data = sample()
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise SystemExit("GITHUB_TOKEN is not set")
        data = fetch(args.user, token)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "stats.svg": stats_card(data),
        "languages.svg": languages_card(data),
        "streak.svg": streak_card(data),
        "activity.svg": activity_card(data),
        "followers.svg": followers_badge(data),
    }
    for name, svg in files.items():
        (out / name).write_text(svg, encoding="utf-8")
        print(f"wrote {out / name}")


if __name__ == "__main__":
    main()
