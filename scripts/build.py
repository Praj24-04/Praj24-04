#!/usr/bin/env python3
"""Render every pixel-art SVG in assets/arcade/ from the JSON files in data/.

    python3 scripts/build.py

Edit data/profile.json, run this, commit. The Arcade workflow also runs it
daily after refreshing data/scores.json.
"""

import json
from pathlib import Path

from pixelkit import *  # noqa: F401,F403  (small script, the kit is the vocabulary)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "arcade"
W = 640


def load(name):
    return json.loads((ROOT / "data" / name).read_text())


def write(name, content):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(content)


def ground(y, h):
    """Grass + soil strip with a deterministic pebble pattern."""
    out = rect(0, y, W, 4, LIME) + rect(0, y + 4, W, 6, GREEN) + rect(0, y + 10, W, h - 10, TEAL)
    for i in range(0, W, 32):
        out += rect(i + 6, y + 16 + (i // 32 % 2) * 8, 8, 4, GREEN)
    return out


TYPE_COLS = 33  # characters per typed line at scale 3


def wrap(fact, cols=TYPE_COLS):
    """One line if it fits, else the most balanced two-line split."""
    if len(fact) <= cols:
        return [fact]
    words = fact.split()
    splits = [(" ".join(words[:i]), " ".join(words[i:])) for i in range(1, len(words))]
    return list(min(splits, key=lambda ab: max(len(ab[0]), len(ab[1]))))


def todays_trivia(s, count=6):
    """Tonight's facts for the title screen. Keyed on the save date so every
    rebuild on the same day agrees; facts too long for two lines are skipped."""
    import datetime as dt
    facts = [f for f in load("trivia.json") if len(wrap(f)) <= 2 and max(map(len, wrap(f))) <= TYPE_COLS]
    try:
        day = dt.date.fromisoformat(s.get("saved", "")).toordinal()
    except ValueError:
        day = 0
    return [facts[(day * count + i) % len(facts)] for i in range(min(count, len(facts)))]


def typed_facts(facts, y, scale, fill):
    """Typewriter effect: SMIL widens a clip rect one character at a time.
    Each fact gets a time slot; its second line starts when the first is done."""
    slot, per_char, line_h = 7.0, 0.04, (CHAR_H + 2) * scale
    total = slot * len(facts)
    out = ""
    for i, fact in enumerate(facts):
        lines = wrap(fact)
        y0 = y + (line_h // 2 if len(lines) == 1 else 0)  # centre one-liners
        t = i * slot + 0.3
        for j, line in enumerate(lines):
            w = text_width(line, scale)
            x0 = (W - w) // 2
            times, values = [0.0], [0]
            for c in range(1, len(line) + 1):
                t += per_char
                times.append(t)
                values.append(c * ADVANCE * scale)
            times.append((i + 1) * slot - 0.3)
            values.append(0)
            kt = ";".join(f"{min(v / total, 1):.4f}" for v in times)
            vs = ";".join(map(str, values))
            ly = y0 + j * line_h
            out += (
                f'<clipPath id="ty{i}_{j}"><rect x="{x0}" y="{ly}" width="0" height="{CHAR_H * scale}">'
                f'<animate attributeName="width" calcMode="discrete" dur="{total}s" '
                f'repeatCount="indefinite" keyTimes="{kt}" values="{vs}"/></rect></clipPath>'
                f'<g clip-path="url(#ty{i}_{j})">{text(line, x0, ly, scale, fill)}</g>'
            )
    return out


# --- screens ----------------------------------------------------------------
def title_screen(p, facts):
    h = 340
    b = stars(W, 290, 46)
    # HUD. 1P score = CGPA; HI score = 934 frameworks x 27 nations (PolicyIQ).
    b += text("1P", 20, 16, 2, RED) + text("009070", 52, 16, 2, WHITE)
    b += text("934027", W - 20, 16, 2, WHITE, "end") + text("HI", W - 104, 16, 2, RED, "end")
    b += text("STAGE 3-1", W // 2, 16, 2, SLATE, "middle")
    grad = (
        '<linearGradient id="lg" x1="0" y1="0" x2="0" y2="1">'
        + "".join(
            f'<stop offset="{o}" stop-color="{c}"/><stop offset="{o2}" stop-color="{c}"/>'
            for o, o2, c in [(0, 0.28, YELLOW), (0.28, 0.57, ORANGE), (0.57, 0.86, RED), (0.86, 1, PLUM)]
        )
        + "</linearGradient>"
    )
    b += f"<defs>{grad}</defs>"
    for word, y in ((p["first_name"], 40), (p["last_name"], 112)):
        b += text(word, W // 2 + 5, y + 5, 9, PLUM, "middle")
        b += text(word, W // 2, y, 9, "url(#lg)", "middle")
    b += typed_facts(facts, 197, 2.5, CYAN)
    b += text("PRESS START", W // 2, 258, 2, YELLOW, "middle", extra=' class="blink"')
    b += ground(290, 50)
    b += f'<g class="bob">{sprite(CUPCAKE, CUPCAKE_COLORS, 48, 252, 3)}</g>'
    b += sprite(CUPCAKE, CUPCAKE_COLORS, 96, 266, 3)
    b += cat(548, 242, 3)
    b += rect(96, 310, W - 192, 26, TEAL) + text("(C) 2026 PRAJ24-04 - ALL BUGS RESERVED", W // 2, 316, 2, WHITE, "middle")
    name = f'{p["first_name"]} {p["last_name"]}'.title()
    return svg(W, h, b, f"Title screen: {name}. Tonight's tech trivia, typed out one at a time: {' '.join(facts)} Press Start.")


def header(title, n, total):
    b = rect(0, 46, W, 6, BLUE) + rect(0, 46, 96, 6, YELLOW) + rect(96, 46, 48, 6, ORANGE) + rect(144, 46, 24, 6, RED)
    b += text("^", 18, 10, 4, YELLOW, extra=' class="blink"')
    b += text(title, 52, 10, 4, WHITE, shadow=PLUM)
    b += text(f"{n:02d}/{total:02d}", W - 18, 18, 2, SLATE, "end")
    return svg(W, 52, b, title.title(), scanlines=False)


def player_card(p):
    pl = p["player"]
    h = 256
    b = frame(20, 20, 150, 150, SLATE, 3, DUSK) + cat(47, 44, 6)
    b += text("PORTRAIT TBD.", 95, 180, 2, SLATE, "middle") + text("CAT FILLS IN.", 95, 198, 2, SLATE, "middle")
    x, vx = 194, 290
    b += text("^", x, 22, 3, YELLOW, extra=' class="blink"')
    b += text(f'{p["first_name"]} {p["last_name"]}', x + 24, 22, 3, YELLOW)
    rows = [
        ("CLASS", pl["class"]), ("GUILD", pl["guild"]),
        ("LEVEL", f'{pl["year"]} / {pl["years_total"]}'), ("HP", f'{pl["cgpa"]:.2f} / 10'),
        ("SKILL", pl["skill"]), ("WEAK TO", pl["weak"]), ("FUEL", pl["fuel"]),
    ]
    for i, (k, v) in enumerate(rows):
        y = 60 + i * 23
        b += text(k, x, y, 2, SLATE) + text(v, vx, y, 2, WHITE)
        if k == "LEVEL":  # one segment per year; the current year blinks
            for s in range(pl["years_total"]):
                col = GREEN if s < pl["year"] else DUSK
                cls = ' class="blink"' if s == pl["year"] - 1 else ""
                b += rect(vx + 84 + s * 40, y, 34, 14, col, cls)
            b += text("YEAR", vx + 252, y, 2, SLATE)
        if k == "HP":
            b += bar(vx + 132, y, 112, 14, pl["cgpa"] / 10, RED) + text("CGPA", vx + 252, y, 2, SLATE)
    b += rect(20, 224, W - 40, 3, DUSK)
    b += text("2P: OPEN SLOT - RECRUITERS, PRESS START", W // 2, 234, 2, CYAN, "middle", extra=' class="blink"')
    return svg(W, h, b, (
        f'Player select. Prajakta Jadhav. Class: {pl["class"].title()}. Guild: VIT Pune. '
        f'Level: year {pl["year"]} of {pl["years_total"]}. HP: CGPA {pl["cgpa"]} out of 10. '
        "Player 2 slot is open for recruiters."
    ))


def world_map(p):
    h = 250
    levels = p["world"]
    b = stars(W, h, 24, seed=11)
    xs = [64 + i * ((W - 128) // (len(levels) - 1)) for i in range(len(levels))]
    ys = [100 if i % 2 == 0 else 134 for i in range(len(levels))]
    for i in range(len(levels) - 1):  # dotted trail between nodes
        for s in range(1, 6):
            px = xs[i] + (xs[i + 1] - xs[i]) * s // 6
            py = ys[i] + (ys[i + 1] - ys[i]) * s // 6
            b += rect(px - 2, py - 2, 4, 4, SLATE if levels[i + 1]["status"] != "locked" else DUSK)
    style = {
        "boss": (YELLOW, "BOSS: LIVE", YELLOW), "cleared": (GREEN, "CLEARED", LIME),
        "current": (ORANGE, "IN PROGRESS", ORANGE), "locked": (DUSK, "LOCKED", SLATE),
    }
    for i, lv in enumerate(levels):
        col, label, lcol = style[lv["status"]]
        x, y = xs[i], ys[i]
        up = i % 2 == 0
        cls = ' class="blink"' if lv["status"] == "current" else ""
        b += rect(x - 16, y - 16, 32, 32, INK) + frame(x - 16, y - 16, 32, 32, col, 4)
        b += rect(x - 8, y - 8, 16, 16, col, cls)
        num = "?" if lv["status"] == "locked" else str(i + 1)
        b += text(num, x - 4, y - 7, 2, INK if lv["status"] != "locked" else MIST)
        half = max(text_width(lv["name"], 2), text_width(label, 2)) // 2 + 12
        tx = max(half, min(W - half, x))
        lift = 14 if lv["status"] == "current" else 0  # make room for the cat
        ny, sy = (y - 78 - lift, y - 60 - lift) if up else (y + 46, y + 64)
        b += text(lv["name"], tx, ny, 2, WHITE, "middle") + text(label, tx, sy, 2, lcol, "middle")
        if lv["status"] in ("boss", "cleared"):
            b += sprite(FLAG, {"K": MIST, "G": lcol}, x + 8, y - 34, 3)
        if lv["status"] == "current":
            b += f'<g class="bob">{cat(x - 14, y - 50, 2)}</g>'
    b += text("WORLD 1 - THINGS I ACTUALLY SHIPPED", W // 2, h - 24, 2, SLATE, "middle")
    names = ", ".join(f'{lv["name"].title()} ({style[lv["status"]][1].lower()})' for lv in levels)
    return svg(W, h, b, f"World map of projects: {names}.")


def trophy_room(p):
    h = 186
    b = ""
    n = len(p["trophies"])
    for i, (a, c, d) in enumerate(p["trophies"]):
        cx = W // n * i + W // n // 2
        b += rect(cx - 62, 70, 124, 4, SLATE) + rect(cx - 54, 74, 108, 4, DUSK)
        if a == "???":  # empty pedestal: a dim outline waiting for the next win
            b += sprite(TROPHY, {"Y": DUSK, "W": DUSK, "O": DUSK}, cx - 20, 23, 4)
            b += text(a, cx, 90, 2, SLATE, "middle", extra=' class="blink"') + text(c, cx, 110, 2, SLATE, "middle") + text(d, cx, 130, 2, SLATE, "middle")
            continue
        b += f'<g class="bob" style="animation-delay:{i * 0.3}s">{sprite(TROPHY, TROPHY_COLORS, cx - 20, 20, 4)}</g>'
        b += text(a, cx, 90, 2, YELLOW, "middle") + text(c, cx, 110, 2, WHITE, "middle") + text(d, cx, 130, 2, MIST, "middle")
    won = sum(t[0] != "???" for t in p["trophies"])
    b += text(f"TROPHIES {won}/?? - MORE DLC INCOMING", W // 2, 160, 2, SLATE, "middle")
    return svg(W, h, b, "Trophy room: " + "; ".join(" ".join(t).title() for t in p["trophies"]) + ".")


def inventory(p):
    b, y = "", 20
    colors = [ORANGE, CYAN, LIME, YELLOW]
    for ci, (cat_name, items) in enumerate(p["inventory"].items()):
        col = colors[ci % len(colors)]
        b += text(cat_name, 20, y, 2, col) + rect(20 + text_width(cat_name, 2) + 10, y + 6, W - 50 - text_width(cat_name, 2), 2, DUSK)
        y += 24
        x = 20
        for it in items:
            w = text_width(it, 2) + 22
            if x + w > W - 20:
                x, y = 20, y + 40
            b += frame(x, y, w, 32, col, 3, DUSK) + text(it, x + 11, y + 9, 2, WHITE)
            x += w + 8
        y += 50
    flat = "; ".join(f"{k.title()}: {', '.join(v)}" for k, v in p["inventory"].items())
    return svg(W, y - 4, b, f"Inventory. {flat}.")


def fmt_score(v, unit=""):
    if v is None:
        return "------"
    return f"{int(v):06d}" if not unit else f"{int(v)} {unit}"


def high_scores(s):
    rows = [
        ("1ST", "CONTRIBUTIONS/YR", fmt_score(s.get("contributions"))),
        ("2ND", "LONGEST STREAK", fmt_score(s.get("streak"), "DAYS")),
        ("3RD", "PUBLIC REPOS", fmt_score(s.get("repos"))),
        ("4TH", "STARS COLLECTED", fmt_score(s.get("stars"))),
        ("5TH", "FOLLOWERS", fmt_score(s.get("followers"))),
    ]
    if s.get("wpm"):  # row only appears once the Monkeytype secret is set
        rows.append(("6TH", "TYPING SPEED", fmt_score(s["wpm"], "WPM")))
    b = text("RANK", 24, 18, 2, SLATE) + text("STAT", 100, 18, 2, SLATE) + text("SCORE", W - 24, 18, 2, SLATE, "end")
    b += rect(24, 38, W - 48, 2, DUSK)
    for i, (rank, name, score) in enumerate(rows):
        y = 52 + i * 32
        col = RAINBOW[i % len(RAINBOW)]
        cls = ' class="blink"' if i == 0 else ""
        b += text(rank, 24, y, 3, col) + text(name, 100, y, 3, col) + text(score, W - 24, y, 3, col, "end", extra=cls)
    y = 52 + len(rows) * 32 + 6
    b += rect(24, y, W - 48, 2, DUSK)
    b += text(f'SAVED {s.get("saved", "----")} - AUTO-UPDATED BY GITHUB ACTIONS', W // 2, y + 14, 2, SLATE, "middle")
    label = ". ".join(f"{n.title()}: {sc}" for _, n, sc in rows)
    return svg(W, y + 42, b, f"High score board, auto-updated by GitHub Actions. {label}.")


def hall_of_fame(v):
    players = v.get("players", [])[-21:][::-1]
    b = text("PLAYERS WHO INSERTED A COIN", 24, 18, 2, YELLOW)
    b += text(f'COINS {v.get("coins", len(players)):04d}', W - 24, 18, 2, WHITE, "end")
    b += rect(24, 38, W - 48, 2, DUSK)
    cols = 7
    cell = (W - 48) // cols
    for i in range(len(players) + 1):
        if i >= 21:
            break
        x = 24 + (i % cols) * cell + cell // 2
        y = 54 + (i // cols) * 36
        if i < len(players):
            b += text(players[i]["initials"], x, y, 3, RAINBOW[i % len(RAINBOW)], "middle")
        else:  # the next free slot blinks, waiting for a challenger
            b += text("___", x, y, 3, SLATE, "middle", extra=' class="blink"')
    rows = min(3, len(players) // cols + 1)
    h = 54 + rows * 36 + 30
    b += text("NEWEST FIRST - YOUR INITIALS GO HERE", W // 2, h - 26, 2, SLATE, "middle")
    names = ", ".join(pl["initials"] for pl in players) or "nobody yet"
    return svg(W, h, b, f"Visitor hall of fame. Latest initials: {names}.")


def button(label, color):
    w = text_width(label, 2) + 36
    b = rect(0, 0, w, 40, INK) + frame(2, 2, w - 4, 36, color, 3, DUSK) + text(label, w // 2, 13, 2, WHITE, "middle")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} 40" width="{w}" height="40" role="img" '
        f'aria-label="{label.title()}" shape-rendering="crispEdges"><title>{label.title()}</title>'
        f'<rect width="{w}" height="40" rx="6" fill="{INK}"/>{b[len(rect(0, 0, w, 40, INK)):]}</svg>\n'
    )


def credits():
    h = 150
    b = stars(W, 100, 20, seed=3)
    b += text("THANK YOU FOR PLAYING", W // 2, 24, 4, YELLOW, "middle", shadow=PLUM)
    b += text("~", W // 2 - 60, 62, 3, RED, extra=' class="blink"') + text("~", W // 2 - 9, 62, 3, RED)
    b += text("~", W // 2 + 42, 62, 3, RED, extra=' class="blink2"')
    b += ground(108, 42)
    b += cat(120, 60, 3) + sprite(CUPCAKE, CUPCAKE_COLORS, 190, 84, 3)
    b += text("CONTINUE? 9..8..7..", W - 40, 90, 2, CYAN, "end", extra=' class="blink"')
    b += rect(84, 120, W - 168, 26, TEAL) + text("NO CATS WERE HARMED. SEVERAL WERE FED.", W // 2, 126, 2, WHITE, "middle")
    return svg(W, h, b, "Credits: thank you for playing. No cats were harmed. Several were fed.")


def replace_block(src, tag, lines):
    """Swap the text between <!--TAG:START--> and <!--TAG:END-->."""
    start, end = f"<!--{tag}:START-->", f"<!--{tag}:END-->"
    if start not in src or end not in src or not lines:
        return src
    head, rest = src.split(start, 1)
    return head + start + "\n" + "\n".join(lines) + "\n" + end + rest.split(end, 1)[1]


def update_readme(s):
    """Refresh the auto-updated text blocks in README.md."""
    readme = ROOT / "README.md"
    if not readme.exists():
        return
    src = readme.read_text()
    src = replace_block(src, "RECENT", [
        f'- **[{r["name"]}]({r["url"]})** · last save `{r["pushed"]}`' + (f'<br><sub>{r["description"]}</sub>' if r["description"] else "")
        for r in s.get("recent", [])
    ])
    readme.write_text(src)


SECTIONS = [
    ("player-select", "PLAYER SELECT"), ("main-quest", "MAIN QUEST"), ("world-map", "WORLD MAP"),
    ("inventory", "INVENTORY"), ("trophy-room", "TROPHY ROOM"), ("high-scores", "HIGH SCORES"),
    ("side-quests", "SIDE QUESTS"), ("save-point", "SAVE POINT"), ("credits", "CREDITS"),
]


def main():
    p, s, v = load("profile.json"), load("scores.json"), load("visitors.json")
    write("title.svg", title_screen(p, todays_trivia(s)))
    for i, (slug, name) in enumerate(SECTIONS, 1):
        write(f"h-{slug}.svg", header(name, i, len(SECTIONS)))
    write("player.svg", player_card(p))
    write("map.svg", world_map(p))
    write("trophies.svg", trophy_room(p))
    write("inventory.svg", inventory(p))
    write("scores.svg", high_scores(s))
    write("hall-of-fame.svg", hall_of_fame(v))
    write("end.svg", credits())
    for mode in ("light", "dark"):  # placeholder until the Arcade workflow draws the real one
        if not (OUT / f"snake-{mode}.svg").exists():
            b = text("SNAKE LOADING... RUN THE ARCADE WORKFLOW ONCE", W // 2, 22, 2, MIST, "middle", extra=' class="blink"')
            write(f"snake-{mode}.svg", svg(W, 58, b, "Contribution snake: appears after the Arcade workflow's first run."))
    palette = {"linkedin": SKY, "email": ORANGE, "portfolio": SLATE, "policyiq": GREEN, "coin": YELLOW}
    for key, label in p["buttons"].items():
        write(f"btn-{key}.svg", button(label, palette.get(key, BLUE)))
    update_readme(s)
    print(f"built {len(list(OUT.glob('*.svg')))} SVGs -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
