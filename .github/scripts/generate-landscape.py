#!/usr/bin/env python3
"""Render the public GitHub contribution calendar as the profile landscape."""

from __future__ import annotations

import html
import re
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path

USERNAME = "ANU5565"
SOURCE_URL = f"https://github.com/users/{USERNAME}/contributions"
OUTPUT = Path("landscape.svg")

WIDTH = 1200
HEIGHT = 680
BACKGROUND = "#080f1b"
TEXT = "#e9f2ff"
MUTED = "#9eb1ca"
ACCENTS = ["#203148", "#285c68", "#328e98", "#40bcae", "#57dfc2", "#6df0c7"]


def fetch_contributions() -> list[tuple[date, int]]:
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "ANU5565-profile-landscape"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        page = response.read().decode("utf-8")

    tooltips = {
        target: html.unescape(text)
        for target, text in re.findall(
            r'<tool-tip[^>]+for="([^"]+)"[^>]*>(.*?)</tool-tip>',
            page,
            flags=re.DOTALL,
        )
    }
    cells: list[tuple[date, int]] = []
    for cell in re.finditer(
        r'<td[^>]+data-date="([^"]+)"[^>]+id="([^"]+)"[^>]+data-level="(\d+)"[^>]*>',
        page,
    ):
        day = date.fromisoformat(cell.group(1))
        tooltip = tooltips.get(cell.group(2), "")
        count_match = re.search(r"([\d,]+) contributions?", tooltip)
        count = int(count_match.group(1).replace(",", "")) if count_match else 0
        cells.append((day, count))

    if not cells:
        raise RuntimeError("GitHub returned no contribution cells")
    return cells


def brick(x: float, y: float, height: float, fill: str, title: str) -> str:
    top = f"{x:.1f},{y:.1f} {x + 16:.1f},{y + 5:.1f} {x + 31:.1f},{y - 4:.1f} {x + 15:.1f},{y - 9:.1f}"
    left = f"{x:.1f},{y:.1f} {x + 16:.1f},{y + 5:.1f} {x + 16:.1f},{y + height:.1f} {x:.1f},{y + height - 5:.1f}"
    right = f"{x + 16:.1f},{y + 5:.1f} {x + 31:.1f},{y - 4:.1f} {x + 31:.1f},{y + height - 9:.1f} {x + 16:.1f},{y + height:.1f}"
    return (
        f'<g><title>{html.escape(title)}</title>'
        f'<polygon points="{top}" fill="{fill}" stroke="{BACKGROUND}" stroke-width=".7"/>'
        f'<polygon points="{left}" fill="{fill}" opacity=".65"/>'
        f'<polygon points="{right}" fill="{fill}" opacity=".4"/></g>'
    )


def render(cells: list[tuple[date, int]]) -> str:
    grouped: dict[date, dict[int, tuple[date, int]]] = defaultdict(dict)
    for day, count in cells:
        week_start = day.fromordinal(day.toordinal() - day.weekday() - 1)
        grouped[week_start][day.weekday()] = (day, count)

    weeks = sorted(grouped.items())
    total = sum(count for _, count in cells)
    start = cells[0][0].isoformat()
    end = cells[-1][0].isoformat()
    max_count = max(count for _, count in cells)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" font-family="Arial,Helvetica,sans-serif">',
        f'<rect width="{WIDTH}" height="{HEIGHT}" rx="24" fill="{BACKGROUND}"/>',
        f'<text x="40" y="50" font-size="14" fill="#57dfc2" font-weight="700">THE CONTRIBUTION MOSAIC</text>',
        f'<text x="40" y="94" font-size="36" fill="{TEXT}" font-weight="700">Built brick by brick.</text>',
        f'<text x="40" y="126" font-size="16" fill="{MUTED}">{len(cells)} days. {total:,} contributions. A year of building.</text>',
    ]

    for column, (week_start, week) in enumerate(weeks):
        for row in range(7):
            if row not in week:
                continue
            day, count = week[row]
            x = 70 + column * 17 + row * 17
            y = 282 + row * 35 - column * 1.15
            height = 8 + (count / max_count * 78 if max_count else 0)
            level = min(5, int(count / max_count * 5) + (1 if count else 0)) if max_count else 0
            parts.append(brick(x, y, height, ACCENTS[level], f"{day.isoformat()}: {count} contributions"))

    parts.extend(
        [
            f'<text x="44" y="590" font-size="30" fill="{TEXT}" font-weight="700">REMEMBER WHY YOU STARTED 🧘🏻‍♂️</text>',
            f'<text x="44" y="632" font-size="24" fill="#57dfc2" font-weight="700">BUILDING • LEARNING • EXPERIMENTING</text>',
            f'<text x="1155" y="648" font-size="13" fill="{MUTED}" text-anchor="end">{start} — {end}</text>',
            "</svg>",
        ]
    )
    return "".join(parts) + "\n"


if __name__ == "__main__":
    OUTPUT.write_text(render(fetch_contributions()), encoding="utf-8")
