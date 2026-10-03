"""
Genera portadas e imágenes de artista originales (gráficos abstractos, no fotos)
en un estilo moderno minimalista claro, coherente por género musical.
"""
import json
import math
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

GENERO_COLOR = {
    "Rock": "#D64545",
    "Indie Pop": "#7B61FF",
    "Electrónica": "#1FA7B0",
    "Folk": "#B5834D",
    "Jazz": "#C99A2E",
    "Reggae": "#2F9E44",
    "Clásica": "#4C5B8C",
    "Blues": "#1F6FB2",
    "Metal alternativo": "#5B4B8A",
    "Alternativo / Trip-hop": "#2F8F6E",
    "R&B / Lo-fi": "#B23A6E",
    "Rock alternativo": "#C1502E",
    "Pop": "#D6A518",
    "Post-punk": "#3A3D42",
    "Indie rock": "#1F6FB2",
}

BG_BASE = (247, 245, 242)  # off-white cálido


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def tint(color, amount):
    """Mezcla un color con blanco (amount=1 -> blanco puro)."""
    r, g, b = color
    return tuple(int(c + (255 - c) * amount) for c in (r, g, b))


def soft_background(size, accent):
    """Fondo con degradado radial suave desde una esquina, tonos claros."""
    w, h = size
    img = Image.new("RGB", size, BG_BASE)
    overlay = Image.new("L", size, 0)
    odraw = ImageDraw.Draw(overlay)
    cx, cy = w * 0.18, h * 0.12
    maxr = math.hypot(w, h)
    steps = 160
    for i in range(steps, 0, -1):
        r = maxr * i / steps
        alpha = int(70 * (1 - i / steps))
        odraw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=alpha)
    tinted = Image.new("RGB", size, tint(accent, 0.82))
    img = Image.composite(tinted, img, overlay)
    return img


def draw_monogram_card(nombre, genero, out_path, size=640):
    accent = hex_to_rgb(GENERO_COLOR.get(genero, "#4C5B8C"))
    img = soft_background((size, size), accent)
    draw = ImageDraw.Draw(img, "RGBA")

    # anillo decorativo
    margin = int(size * 0.10)
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        outline=accent + (255,), width=6,
    )

    # círculo principal (avatar) con relleno tenue
    pad = int(size * 0.16)
    circ_box = [pad, pad, size - pad, size - pad]
    draw.ellipse(circ_box, fill=tint(accent, 0.55) + (255,))

    # puntos decorativos tipo "constelación" alrededor
    import random
    rnd = random.Random(sum(bytearray(nombre.encode())))
    for _ in range(14):
        ang = rnd.uniform(0, 2 * math.pi)
        rad = rnd.uniform(size * 0.36, size * 0.46)
        px = size / 2 + math.cos(ang) * rad
        py = size / 2 + math.sin(ang) * rad
        r = rnd.uniform(3, 7)
        draw.ellipse([px - r, py - r, px + r, py + r], fill=accent + (160,))

    # iniciales
    palabras = [p for p in nombre.replace("de ", "").split(" ") if p]
    iniciales = "".join(p[0] for p in palabras[:2]).upper()
    font_size = int(size * 0.30)
    font = ImageFont.truetype(FONT_BOLD, font_size)
    bbox = draw.textbbox((0, 0), iniciales, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        (size / 2 - tw / 2 - bbox[0], size / 2 - th / 2 - bbox[1]),
        iniciales, font=font, fill=accent + (255,),
    )

    # etiqueta de género (pill) abajo
    label = genero.upper()
    fsmall = ImageFont.truetype(FONT_BOLD, int(size * 0.045))
    lb = draw.textbbox((0, 0), label, font=fsmall)
    lw, lh = lb[2] - lb[0], lb[3] - lb[1]
    px0 = size / 2 - lw / 2 - 18
    py0 = size - int(size * 0.14)
    px1 = size / 2 + lw / 2 + 18
    py1 = py0 + lh + 16
    draw.rounded_rectangle([px0, py0, px1, py1], radius=(py1 - py0) / 2, fill=accent + (255,))
    draw.text((size / 2 - lw / 2 - lb[0], py0 + 8 - lb[1]), label, font=fsmall, fill=(255, 255, 255, 255))

    img = img.filter(ImageFilter.SMOOTH_MORE)
    img.save(out_path, "PNG", optimize=True)


def draw_album_cover(titulo, artista, genero, out_path, size=640):
    accent = hex_to_rgb(GENERO_COLOR.get(genero, "#4C5B8C"))
    img = soft_background((size, size), accent)
    draw = ImageDraw.Draw(img, "RGBA")

    # "disco de vinilo" asomando en una esquina
    vr = size * 0.62
    vcx, vcy = size * 0.82, size * 0.86
    draw.ellipse([vcx - vr, vcy - vr, vcx + vr, vcy + vr], fill=(30, 30, 32, 255))
    for frac in (0.82, 0.64, 0.46):
        r = vr * frac
        draw.ellipse([vcx - r, vcy - r, vcx + r, vcy + r], outline=(70, 70, 74, 255), width=2)
    r_label = vr * 0.30
    draw.ellipse([vcx - r_label, vcy - r_label, vcx + r_label, vcy + r_label], fill=accent + (255,))
    r_hole = vr * 0.05
    draw.ellipse([vcx - r_hole, vcy - r_hole, vcx + r_hole, vcy + r_hole], fill=BG_BASE + (255,))

    # bloque de acento superior-izquierdo (tarjeta de título)
    bx0, by0 = size * 0.08, size * 0.08
    bw, bh = size * 0.62, size * 0.30
    draw.rounded_rectangle([bx0, by0, bx0 + bw, by0 + bh], radius=18, fill=(255, 255, 255, 210))
    draw.rounded_rectangle([bx0, by0, bx0 + bw, by0 + bh], radius=18, outline=accent + (255,), width=3)

    ftitle = ImageFont.truetype(FONT_BOLD, int(size * 0.062))
    fartist = ImageFont.truetype(FONT_REG, int(size * 0.040))

    def wrap(text, font, maxw):
        words = text.split(" ")
        lines, cur = [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            tb = draw.textbbox((0, 0), trial, font=font)
            if tb[2] - tb[0] <= maxw or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    lines = wrap(titulo, ftitle, bw - 40)[:2]
    ty = by0 + 22
    for ln in lines:
        draw.text((bx0 + 20, ty), ln, font=ftitle, fill=(40, 40, 42, 255))
        tb = draw.textbbox((0, 0), ln, font=ftitle)
        ty += (tb[3] - tb[1]) + 10
    draw.text((bx0 + 20, ty + 6), artista, font=fartist, fill=accent + (255,))

    img = img.filter(ImageFilter.SMOOTH_MORE)
    img.save(out_path, "PNG", optimize=True)


def main():
    # NOTA: las portadas de discos ahora son fotografías reales (provistas por
    # el usuario), no gráficos generados. Este script solo genera los avatares
    # abstractos de artista; draw_album_cover() queda como utilidad de respaldo.
    root = BASE
    with open(os.path.join(root, "artistasApp", "data", "artistas.json"), encoding="utf-8") as f:
        artistas = json.load(f)

    out_art = os.path.join(root, "static", "img", "artistas")
    os.makedirs(out_art, exist_ok=True)

    for a in artistas:
        draw_monogram_card(a["nombre"], a["genero"], os.path.join(out_art, a["imagen"]))
        print("OK artista:", a["imagen"])


if __name__ == "__main__":
    main()
