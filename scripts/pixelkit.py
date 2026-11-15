"""pixelkit: a tiny pixel-art SVG toolkit (stdlib only).

GitHub strips custom CSS/JS and web fonts from READMEs, so every heading here
is drawn as plain <path> pixels from the 5x7 bitmap font below. Everything is
original art; the palette is Sweetie-16 by GrafxKid.
"""

from xml.sax.saxutils import escape

# --- palette (Sweetie-16) ---------------------------------------------------
INK = "#1a1c2c"      # screen background
PLUM = "#5d275d"
RED = "#b13e53"
ORANGE = "#ef7d57"
YELLOW = "#ffcd75"
LIME = "#a7f070"
GREEN = "#38b764"
TEAL = "#257179"
NAVY = "#29366f"
BLUE = "#3b5dc9"
SKY = "#41a6f6"
CYAN = "#73eff7"
WHITE = "#f4f4f4"
MIST = "#94b0c2"
SLATE = "#566c86"
DUSK = "#333c57"

RAINBOW = [RED, ORANGE, YELLOW, LIME, CYAN, SKY, MIST]

# --- 5x7 font ---------------------------------------------------------------
_F = {
    "A": ".###. #...# #...# ##### #...# #...# #...#",
    "B": "####. #...# #...# ####. #...# #...# ####.",
    "C": ".###. #...# #.... #.... #.... #...# .###.",
    "D": "####. #...# #...# #...# #...# #...# ####.",
    "E": "##### #.... #.... ####. #.... #.... #####",
    "F": "##### #.... #.... ####. #.... #.... #....",
    "G": ".###. #...# #.... #.### #...# #...# .###.",
    "H": "#...# #...# #...# ##### #...# #...# #...#",
    "I": "##### ..#.. ..#.. ..#.. ..#.. ..#.. #####",
    "J": "..### ...#. ...#. ...#. ...#. #..#. .##..",
    "K": "#...# #..#. #.#.. ##... #.#.. #..#. #...#",
    "L": "#.... #.... #.... #.... #.... #.... #####",
    "M": "#...# ##.## #.#.# #.#.# #...# #...# #...#",
    "N": "#...# ##..# #.#.# #..## #...# #...# #...#",
    "O": ".###. #...# #...# #...# #...# #...# .###.",
    "P": "####. #...# #...# ####. #.... #.... #....",
    "Q": ".###. #...# #...# #...# #.#.# #..#. .##.#",
    "R": "####. #...# #...# ####. #.#.. #..#. #...#",
    "S": ".#### #.... #.... .###. ....# ....# ####.",
    "T": "##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
    "U": "#...# #...# #...# #...# #...# #...# .###.",
    "V": "#...# #...# #...# #...# #...# .#.#. ..#..",
    "W": "#...# #...# #...# #.#.# #.#.# ##.## #...#",
    "X": "#...# #...# .#.#. ..#.. .#.#. #...# #...#",
    "Y": "#...# #...# .#.#. ..#.. ..#.. ..#.. ..#..",
    "Z": "##### ....# ...#. ..#.. .#... #.... #####",
    "0": ".###. #...# #..## #.#.# ##..# #...# .###.",
    "1": "..#.. .##.. ..#.. ..#.. ..#.. ..#.. .###.",
    "2": ".###. #...# ....# ...#. ..#.. .#... #####",
    "3": "####. ....# ....# .###. ....# ....# ####.",
    "4": "...#. ..##. .#.#. #..#. ##### ...#. ...#.",
    "5": "##### #.... ####. ....# ....# #...# .###.",
    "6": ".###. #.... #.... ####. #...# #...# .###.",
    "7": "##### ....# ...#. ..#.. .#... .#... .#...",
    "8": ".###. #...# #...# .###. #...# #...# .###.",
    "9": ".###. #...# #...# .#### ....# ....# .###.",
    " ": "..... ..... ..... ..... ..... ..... .....",
    ".": "..... ..... ..... ..... ..... .##.. .##..",
    ",": "..... ..... ..... ..... .##.. ..#.. .#...",
    ":": "..... .##.. .##.. ..... .##.. .##.. .....",
    "!": "..#.. ..#.. ..#.. ..#.. ..#.. ..... ..#..",
    "?": ".###. #...# ....# ...#. ..#.. ..... ..#..",
    "-": "..... ..... ..... .###. ..... ..... .....",
    "_": "..... ..... ..... ..... ..... ..... #####",
    "+": "..... ..#.. ..#.. ##### ..#.. ..#.. .....",
    "=": "..... ..... ##### ..... ##### ..... .....",
    "/": "....# ....# ...#. ..#.. .#... #.... #....",
    "(": "...#. ..#.. .#... .#... .#... ..#.. ...#.",
    ")": ".#... ..#.. ...#. ...#. ...#. ..#.. .#...",
    "'": "..#.. ..#.. .#... ..... ..... ..... .....",
    "%": "##..# ##..# ...#. ..#.. .#... #..## #..##",
    "#": ".#.#. .#.#. ##### .#.#. ##### .#.#. .#.#.",
    "&": ".##.. #..#. #.#.. .#... #.#.# #..#. .##.#",
    "*": "..... #.#.# .###. ##### .###. #.#.# .....",
    "@": ".###. #...# #.### #.#.# #.### #.... .###.",
    "<": "...#. ..#.. .#... #.... .#... ..#.. ...#.",
    ">": ".#... ..#.. ...#. ....# ...#. ..#.. .#...",
    # custom glyphs
    "~": "..... .#.#. ##### ##### .###. ..#.. .....",  # heart
    "^": "#.... ##... ###.. ####. ###.. ##... #....",  # menu cursor
    "|": "..#.. ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
}
FONT = {k: v.split() for k, v in _F.items()}
CHAR_W, CHAR_H, ADVANCE = 5, 7, 6


def text_width(s, scale=1):
    return (len(s) * ADVANCE - 1) * scale if s else 0


def _runs_path(rows, x, y, s):
    """Merge horizontal runs of '#' into one compact path string."""
    d = []
    for r, row in enumerate(rows):
        c = 0
        while c < len(row):
            if row[c] == "#":
                start = c
                while c < len(row) and row[c] == "#":
                    c += 1
                d.append(f"M{x + start * s} {y + r * s}h{(c - start) * s}v{s}h{-(c - start) * s}z")
            else:
                c += 1
    return "".join(d)


def text(s, x, y, scale=2, fill=WHITE, anchor="start", shadow=None, extra=""):
    """Render a string in the pixel font. anchor: start | middle | end."""
    s = s.upper()
    w = text_width(s, scale)
    if anchor == "middle":
        x -= w // 2
    elif anchor == "end":
        x -= w
    rows = ["".join((FONT.get(ch, FONT["?"])[r] + ".") for ch in s) for r in range(CHAR_H)]
    d = _runs_path(rows, x, y, scale)
    out = ""
    if shadow:
        out += f'<path d="{_runs_path(rows, x + scale, y + scale, scale)}" fill="{shadow}"/>'
    return out + f'<path d="{d}" fill="{fill}"{extra}/>'


def sprite(rows, colors, x, y, scale=3, extra=""):
    """Render a char-map sprite. colors maps char -> fill; '.' is transparent."""
    out = []
    for ch, fill in colors.items():
        mask = ["".join("#" if c == ch else "." for c in row) for row in rows]
        d = _runs_path(mask, x, y, scale)
        if d:
            out.append(f'<path d="{d}" fill="{fill}"/>')
    return f"<g{extra}>{''.join(out)}</g>"


def rect(x, y, w, h, fill, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"{extra}/>'


def frame(x, y, w, h, color=SLATE, t=3, fill=None):
    """Chunky pixel border with clipped corners."""
    out = rect(x + t, y + t, w - 2 * t, h - 2 * t, fill) if fill else ""
    return out + (
        rect(x + t, y, w - 2 * t, t, color) + rect(x + t, y + h - t, w - 2 * t, t, color)
        + rect(x, y + t, t, h - 2 * t, color) + rect(x + w - t, y + t, t, h - 2 * t, color)
    )


def bar(x, y, w, h, pct, fill, back=DUSK):
    return rect(x, y, w, h, back) + rect(x, y, round(w * max(0, min(1, pct))), h, fill)


def stars(w, h, n=40, seed=7):
    """Deterministic twinkling starfield (no RNG so rebuilds are diff-stable)."""
    out, a = [], seed
    for i in range(n):
        a = (a * 1103515245 + 12345) & 0x7FFFFFFF
        x = 8 + a % (w - 16)
        a = (a * 1103515245 + 12345) & 0x7FFFFFFF
        y = 8 + a % (h - 16)
        sz = 3 if i % 5 == 0 else 2
        col = [MIST, SLATE, CYAN, YELLOW][i % 4]
        cls = f"tw{i % 3}"
        out.append(f'<rect class="{cls}" x="{x - x % 2}" y="{y - y % 2}" width="{sz}" height="{sz}" fill="{col}"/>')
    return "".join(out)


BASE_CSS = """
.blink{animation:blink 1.1s steps(1) infinite}
.blink2{animation:blink 1.1s steps(1) .55s infinite}
.bob{animation:bob 1.2s steps(2) infinite}
.tw0{animation:tw 2.3s steps(1) infinite}
.tw1{animation:tw 3.1s steps(1) .7s infinite}
.tw2{animation:tw 1.9s steps(1) 1.1s infinite}
.f1{animation:fa 1.6s steps(1) infinite}
.f2{animation:fb 1.6s steps(1) infinite}
.wink{animation:wink 4.2s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
@keyframes bob{50%{transform:translateY(-3px)}}
@keyframes tw{50%{opacity:.25}}
@keyframes fa{50%{opacity:0}}
@keyframes fb{0%{opacity:0}50%{opacity:1}100%{opacity:0}}
@keyframes wink{0%,93%{opacity:0}94%,100%{opacity:1}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}.f2,.wink{opacity:0}}
"""


def svg(w, h, body, title, bg=INK, border=DUSK, scanlines=True, css=""):
    """Wrap body in a self-contained 'screen' that reads on light and dark pages."""
    lines = ""
    if scanlines:
        lines = (
            '<pattern id="sl" width="4" height="4" patternUnits="userSpaceOnUse">'
            '<rect width="4" height="1" fill="#000" opacity=".16"/></pattern>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-label="{escape(title)}" shape-rendering="crispEdges">'
        f"<title>{escape(title)}</title><style>{BASE_CSS}{css}</style><defs>{lines}"
        f'<clipPath id="scr"><rect width="{w}" height="{h}" rx="10"/></clipPath></defs>'
        f'<g clip-path="url(#scr)"><rect width="{w}" height="{h}" fill="{bg}"/>{body}'
        + (f'<rect width="{w}" height="{h}" fill="url(#sl)"/>' if scanlines else "")
        + f'</g><rect x="1.5" y="1.5" width="{w - 3}" height="{h - 3}" rx="9" fill="none" '
        f'stroke="{border}" stroke-width="3" shape-rendering="auto"/></svg>\n'
    )


# --- sprites ----------------------------------------------------------------
# Biscuit: original mascot. An orange cat in a chef's hat, because cats
# "make biscuits" and so does the developer.
CAT_COLORS = {"W": WHITE, "L": MIST, "O": ORANGE, "C": YELLOW, "K": INK, "P": RED, "S": RED}
CAT_BODY = [
    "....WWWWW.......",
    "...WWWWWWW......",
    "...WWWWWWW......",
    ".O..WWWWW..O....",
    ".OO.LLLLL.OO....",
    ".OOOOOOOOOOO....",
    ".OSOSOOOSOSO....",
    ".OOKOOOOOKOO....",
    ".OOOOOPOOOOO....",
    ".OCCOOOOOCCO....",
    "..OOOOOOOOO.....",
    "..OOCCCCCOO.....",
    ".OOOCCCCCOOO....",
    ".OOOCCCCCOOO....",
    ".OOOOCCCOOOO....",
    ".OOCCOOOCCOO....",
]
CAT_TAIL_A = [
    "................", "................", "................", "................",
    "................", "................", "................", "................",
    "................", "................", "................", "................",
    "..............O.", ".............OO.", "............OOO.", "............OO..",
]
CAT_TAIL_B = [
    "................", "................", "................", "................",
    "................", "................", "................", "................",
    "................", "................", "..............S.", "..............O.",
    "..............O.", ".............OO.", "............OOO.", "............OO..",
]
CAT_BLINK = [
    "................", "................", "................", "................",
    "................", "................", "................",
    "...O.....O......",
]

CUPCAKE = [
    "...R....",
    "..PPP...",
    ".PPPPP..",
    "PPWPPPP.",
    "PPPPPWP.",
    ".YYYYY..",
    ".YCYCY..",
    "..YYY...",
]
CUPCAKE_COLORS = {"R": RED, "P": WHITE, "W": CYAN, "Y": YELLOW, "C": ORANGE}

TROPHY = [
    ".YYYYYYYY.",
    "YYYYYYYYYY",
    "Y.YYWYYY.Y",
    "Y.YYWYYY.Y",
    ".YYYWYYYY.",
    "..YYYYYY..",
    "...YYYY...",
    "....OO....",
    "....OO....",
    "..OOOOOO..",
    ".OOOOOOOO.",
]
TROPHY_COLORS = {"Y": YELLOW, "W": WHITE, "O": ORANGE}

FLAG = [
    "KGGGG.",
    "KGGGGG",
    "KGGGG.",
    "K.....",
    "K.....",
    "K.....",
]


def cat(x, y, scale=3):
    """Animated Biscuit: tail flick (2 frames) + occasional blink."""
    return (
        sprite(CAT_BODY, CAT_COLORS, x, y, scale)
        + sprite(CAT_TAIL_A, CAT_COLORS, x, y, scale, ' class="f1"')
        + sprite(CAT_TAIL_B, CAT_COLORS, x, y, scale, ' class="f2" opacity="0"')
        + sprite(CAT_BLINK, CAT_COLORS, x, y, scale, ' class="wink" opacity="0"')
    )
