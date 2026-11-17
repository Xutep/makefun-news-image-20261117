# main.py — "17 November 2026 world news in one image"
# Pure stdlib (zlib + struct). Draws a 1024x1024 news-summary infographic
# to /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png). Deterministic:
# no time, no randomness, no network; two runs write byte-identical output.
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font: 5x7
# Each glyph is 7 rows of 5 bits, '#' = on, '.' = off. Written fresh here.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '+': ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '*': ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def wrap(text, max_chars):
    words = text.split(' ')
    lines, cur = [], ''
    for word in words:
        trial = word if not cur else cur + ' ' + word
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = color

    def rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:(yy * self.w + x1) * 3] = color * (x1 - x0)

    def hline(self, x, y, length, color, thick=1):
        self.rect(x, y, length, thick, color)

    def vline(self, x, y, length, color, thick=1):
        self.rect(x, y, thick, length, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.rect(x0 - thick // 2, y0 - thick // 2, thick, thick, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.set(xx, yy, color)
                else:
                    if abs(d2 - r * r) <= r * 2:
                        self.set(xx, yy, color)

    def triangle(self, pts, color):
        # Filled triangle via scanline over its bounding box (barycentric test).
        (x0, y0), (x1, y1), (x2, y2) = pts
        d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if d == 0:
            return
        for yy in range(min(y0, y1, y2), max(y0, y1, y2) + 1):
            for xx in range(min(x0, x1, x2), max(x0, x1, x2) + 1):
                a = ((y1 - y2) * (xx - x2) + (x2 - x1) * (yy - y2)) / d
                b = ((y2 - y0) * (xx - x2) + (x0 - x2) * (yy - y2)) / d
                c = 1 - a - b
                if a >= 0 and b >= 0 and c >= 0:
                    self.set(xx, yy, color)

    def glyph(self, x, y, ch, scale, color):
        rows = FONT.get(ch.upper(), FONT[' '])
        for r, row in enumerate(rows):
            for c, bit in enumerate(row):
                if bit == '1':
                    self.rect(x + c * scale, y + r * scale, scale, scale, color)

    def text(self, x, y, s, scale, color):
        for ch in s:
            self.glyph(x, y, ch, scale, color)
            x += 6 * scale
        return x

    def text_center(self, cx, y, s, scale, color):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, color)

    def para(self, x, y, s, scale, color, max_chars, line_h):
        yy = y
        for line in wrap(s, max_chars):
            self.text(x, yy, line, scale, color)
            yy += line_h
        return yy


def write_png(canvas, path):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', canvas.w, canvas.h, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', comp)
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)
    return len(png)

# ---------------------------------------------------------------- palette
PAPER = bytes((245, 240, 230))
NAVY = bytes((18, 33, 61))
INK = bytes((24, 30, 44))
WHITE = bytes((255, 255, 255))
GOLD = bytes((217, 164, 65))
RED = bytes((178, 44, 36))
TEAL = bytes((14, 124, 123))
BLUE = bytes((36, 90, 158))
GREEN = bytes((46, 125, 50))
ORANGE = bytes((214, 106, 24))
PURPLE = bytes((96, 63, 141))
BROWN = bytes((122, 79, 40))
GREY = bytes((110, 116, 128))
CARD = bytes((255, 255, 255))
LINE = bytes((205, 198, 184))

# ---------------------------------------------------------------- pictograms
# Each draws a small scene inside a square icon area (x, y, size s).


def pic_bridge(cv, x, y, s):
    # Two towers rising above a deck whose middle span has collapsed.
    cv.rect(x + s // 6, y + s // 6, s // 10, s // 4, NAVY)
    cv.rect(x + 3 * s // 4 - s // 20, y + s // 6, s // 10, s // 4, NAVY)
    cv.rect(x + s // 10, y + 2 * s // 5, s // 3, s // 10, NAVY)
    cv.rect(x + 17 * s // 30, y + 2 * s // 5, s // 3, s // 10, NAVY)
    cv.triangle([(x + s // 2 - s // 10, y + 2 * s // 5), (x + s // 2 + s // 10, y + 2 * s // 5),
                 (x + s // 2, y + 7 * s // 12)], RED)
    cv.hline(x + s // 10, y + 3 * s // 5, 4 * s // 5, NAVY, 4)
    for dx, dy in ((-s // 7, 0), (s // 7, 0), (0, -s // 7), (0, s // 10)):
        cv.line(x + s // 2 + dx, y + s // 5 + dy, x + s // 2 - dx, y + s // 5 - dy, GOLD, 3)
    cv.circle(x + s // 2, y + s // 5, s // 16, GOLD)


def pic_tanker(cv, x, y, s):
    # Ship hull on waves, flame above.
    cv.triangle([(x + s // 4, y + s // 4), (x + 3 * s // 4, y + s // 4),
                 (x + s // 2, y + s // 12)], ORANGE)
    cv.triangle([(x + 3 * s // 8, y + s // 4), (x + 5 * s // 8, y + s // 4),
                 (x + s // 2, y + s // 6)], RED)
    cv.rect(x + s // 8, y + s // 4, 3 * s // 4, s // 6, NAVY)
    cv.rect(x + s // 4, y + s // 6, s // 6, s // 6, NAVY)
    for k in range(3):
        yy = y + s // 2 + k * s // 10
        cv.line(x + s // 10, yy, x + s // 4, yy, BLUE, 3)
        cv.line(x + 3 * s // 8, yy, x + 5 * s // 8, yy, BLUE, 3)
        cv.line(x + 3 * s // 4, yy, x + 9 * s // 10, yy, BLUE, 3)


def pic_summit(cv, x, y, s):
    # Three flag poles, three flags.
    cols = (RED, BLUE, GOLD)
    for i, c in enumerate(cols):
        px = x + s // 6 + i * s // 3
        cv.vline(px, y + s // 6, 3 * s // 5, NAVY, 4)
        cv.triangle([(px, y + s // 6), (px + s // 4, y + s // 6 + s // 12),
                     (px, y + s // 6 + s // 6)], c)
    cv.hline(x + s // 10, y + 5 * s // 6, 4 * s // 5, NAVY, 4)


def pic_rocket(cv, x, y, s):
    # Rocket climbing, dashed trail, falling debris dot.
    cv.triangle([(x + s // 2 - s // 8, y + s // 4), (x + s // 2 + s // 8, y + s // 4),
                 (x + s // 2, y + s // 12)], RED)
    cv.rect(x + 3 * s // 8, y + s // 4, s // 4, s // 3, WHITE)
    cv.rect(x + 3 * s // 8, y + s // 4, s // 4, s // 8, BLUE)
    cv.triangle([(x + 3 * s // 8, y + 7 * s // 12), (x + s // 4, y + 3 * s // 4),
                 (x + 3 * s // 8, y + 2 * s // 3)], RED)
    cv.triangle([(x + 5 * s // 8, y + 7 * s // 12), (x + 3 * s // 4, y + 3 * s // 4),
                 (x + 5 * s // 8, y + 2 * s // 3)], RED)
    cv.triangle([(x + s // 2 - s // 12, y + 7 * s // 12), (x + s // 2 + s // 12, y + 7 * s // 12),
                 (x + s // 2, y + 5 * s // 6)], ORANGE)
    cv.circle(x + s // 4, y + 5 * s // 6, s // 20, GREY)
    cv.circle(x + 3 * s // 4, y + 7 * s // 8, s // 24, GREY)


def pic_bank(cv, x, y, s):
    # Bank building: pediment, columns, steps.
    cv.triangle([(x + s // 10, y + s // 4), (x + 9 * s // 10, y + s // 4),
                 (x + s // 2, y + s // 12)], NAVY)
    for i in range(3):
        cv.rect(x + s // 6 + i * s // 4, y + s // 4, s // 12, s // 3, NAVY)
    cv.hline(x + s // 10, y + 7 * s // 12, 4 * s // 5, NAVY, 5)
    cv.hline(x + s // 8, y + 2 * s // 3, 3 * s // 4 + s // 8, NAVY, 5)
    cv.text(x + s // 4, y + 3 * s // 4, '$', 2, GREEN)


def pic_border(cv, x, y, s):
    # Fence / closed border: posts, rails, big X.
    for i in range(4):
        cv.vline(x + s // 8 + i * s // 4, y + s // 6, 2 * s // 3, NAVY, 5)
    cv.hline(x + s // 12, y + s // 3, 5 * s // 6, NAVY, 5)
    cv.hline(x + s // 12, y + 3 * s // 5, 5 * s // 6, NAVY, 5)
    cv.line(x + s // 6, y + s // 6, x + 5 * s // 6, y + 5 * s // 6, RED, 5)
    cv.line(x + 5 * s // 6, y + s // 6, x + s // 6, y + 5 * s // 6, RED, 5)


def pic_scales(cv, x, y, s):
    # Scales of justice.
    cv.vline(x + s // 2, y + s // 8, 3 * s // 5, NAVY, 4)
    cv.hline(x + s // 6, y + s // 4, 2 * s // 3, NAVY, 4)
    cv.line(x + s // 6, y + s // 4, x + s // 12, y + s // 2, NAVY, 3)
    cv.line(x + s // 6, y + s // 4, x + s // 4, y + s // 2, NAVY, 3)
    cv.hline(x + s // 12 - s // 12, y + s // 2, s // 6, NAVY, 4)
    cv.line(x + 5 * s // 6, y + s // 4, x + 3 * s // 4, y + s // 2, NAVY, 3)
    cv.line(x + 5 * s // 6, y + s // 4, x + 11 * s // 12, y + s // 2, NAVY, 3)
    cv.hline(x + 3 * s // 4 - s // 12, y + s // 2, s // 6, NAVY, 4)
    cv.hline(x + s // 4, y + 3 * s // 4, s // 2, NAVY, 5)


def pic_globe(cv, x, y, s):
    # Globe with meridians and a dove-ish arc.
    cx, cy, r = x + s // 2, y + s // 2, s // 3
    cv.circle(cx, cy, r, BLUE)
    cv.circle(cx, cy, r, NAVY, fill=False)
    cv.circle(cx, cy, r // 2, WHITE, fill=False)
    cv.hline(cx - r, cy, 2 * r, WHITE, 2)
    cv.line(cx - r // 2, cy - r, cx - r // 2, cy + r, WHITE, 2)
    cv.line(cx + r // 2, cy - r, cx + r // 2, cy + r, WHITE, 2)
    cv.circle(cx + r // 3, cy - r // 3, r // 8, GOLD)


# ---------------------------------------------------------------- stories
# Eight stories from 17 November 2026, as reported that day by BBC, Reuters,
# AP, Al Jazeera, NPR and others. (kicker, accent, picture, headline, caption)
STORIES = [
    ("UKRAINE", RED, pic_bridge,
     "KERCH BRIDGE HIT AGAIN",
     "Second strike in 24 hours; a road span collapses. Zelenskyy hails an 'unprecedented operation'."),
    ("IRAN", ORANGE, pic_tanker,
     "MINES IN THE STRAIT OF HORMUZ",
     "Two tankers hit mines and catch fire, Iran's Guards say. Tehran's drones target a US radar base in Bahrain."),
    ("ASIA", BLUE, pic_summit,
     "TRUMP IN MANILA; XI-TRUMP-PUTIN SET",
     "Trump arrives for the ASEAN summit. China confirms a three-way meeting in Shenzhen on Thursday."),
    ("SPACE", PURPLE, pic_rocket,
     "VULCAN ROCKET FAILS",
     "ULA's Vulcan suffers an anomaly in flight; 40 Amazon Leo internet satellites are lost."),
    ("MARKETS", GREEN, pic_bank,
     "JPMORGAN BLAMES SOFTWARE BUG",
     "Bank says a bug, not a cyberattack, slowed banking and Zelle on Monday. Nvidia reports after the close."),
    ("EUROPE", TEAL, pic_border,
     "ESTONIA TO SHUT RUSSIA BORDER",
     "Crossings close from 1 Dec after a foiled plot to bomb a drone plant, Tallinn says."),
    ("MIDDLE EAST", BROWN, pic_scales,
     "UK SANCTIONS SETTLEMENT BUILDERS",
     "London sanctions eight firms building West Bank settlements. Israel faces election-day arrest claims."),
    ("WORLD", NAVY, pic_globe,
     "UN DEBATES BAN ON KILLER ROBOTS",
     "128 states meet in Geneva on a treaty to ban lethal autonomous weapons."),
]


def draw(cv):
    cv.rect(0, 0, W, H, PAPER)
    # Header
    cv.rect(0, 0, W, 118, NAVY)
    cv.rect(0, 118, W, 4, GOLD)
    cv.text_center(W // 2, 16, "THE WORLD IN ONE IMAGE", 4, WHITE)
    cv.text_center(W // 2, 62, "TUESDAY 17 NOVEMBER 2026", 3, GOLD)
    cv.text_center(W // 2, 94, "THE DAY'S NEWS - EIGHT STORIES THAT MATTERED", 2, WHITE)

    # Story grid: 2 columns x 4 rows.
    col_w, row_h = 488, 196
    x0, y0, gap = 16, 134, 16
    for i, (kicker, accent, pic, headline, caption) in enumerate(STORIES):
        col, row = i % 2, i // 2
        px = x0 + col * (col_w + gap)
        py = y0 + row * (row_h + 12)
        cv.rect(px, py, col_w, row_h, CARD)
        cv.rect(px, py, col_w, 3, accent)
        cv.rect(px, py, 2, row_h, LINE)
        cv.rect(px + col_w - 2, py, 2, row_h, LINE)
        cv.rect(px, py + row_h - 2, col_w, 2, LINE)
        # Icon panel
        cv.rect(px + 10, py + 10, 84, row_h - 20, accent)
        pic(cv, px + 10, py + 10, 84)
        # Number badge
        cv.circle(px + 10 + 72, py + 10 + 12, 11, WHITE)
        cv.text(px + 10 + 72 - 3, py + 10 + 5, str(i + 1), 1, NAVY)
        # Text
        tx = px + 108
        cv.text(tx, py + 14, kicker, 2, accent)
        cv.para(tx, py + 38, headline, 3, INK, 19, 24)
        head_lines = len(wrap(headline, 19))
        cap_y = py + 38 + head_lines * 24 + 6
        cv.para(tx, cap_y, caption, 2, GREY, 31, 16)

    # Footer
    fy = 962
    cv.rect(0, fy, W, 2, GOLD)
    cv.text_center(W // 2, fy + 12,
                   "AS REPORTED ON 17 NOV 2026 - BBC - REUTERS - AP - AL JAZEERA - NPR",
                   2, INK)
    cv.text_center(W // 2, fy + 34,
                   "MAKE.FUN DAILY NEWS IMAGE - ONE DAY, ONE IMAGE",
                   1, GREY)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = Canvas(W, H, PAPER)
    draw(cv)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(cv, path)
    print(f"wrote {path} ({size} bytes)")


if __name__ == "__main__":
    main()
