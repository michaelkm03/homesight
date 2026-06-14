"""Generate static/logo.png from the HomeSight SVG design using PIL."""
from PIL import Image, ImageDraw
import math, pathlib

SCALE    = 8          # 96*8=768, 74*8=592
Y_OFF    = 6          # SVG viewBox min-y = -6, shift up
W        = 96 * SCALE
H        = 74 * SCALE
LW       = round(9.5 * SCALE)   # stroke-width 9.5
SHADOW   = (26, 92, 58, 255)    # #1a5c3a
MAIN     = (110, 231, 183, 255) # #6ee7b7

def t(x, y):
    return (round(x * SCALE), round((y + Y_OFF) * SCALE))

# SVG polyline/polygon points
shadow_line = [t(6,66), t(25,36), t(36,49), t(59,18), t(70,27), t(80,12)]
shadow_head = [t(88,0),  t(86,16), t(74,8)]
main_line   = [t(3,63),  t(22,33), t(33,46), t(56,15), t(67,24), t(77,9)]
main_head   = [t(85,-3), t(83,13), t(71,5)]

img  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

def draw_thick_line(draw, pts, color, width):
    """Draw polyline with round caps and joins using ellipses at each point."""
    draw.line(pts, fill=color, width=width)
    r = width // 2
    for x, y in pts:
        draw.ellipse((x - r, y - r, x + r, y + r), fill=color)

# Shadow layer
draw_thick_line(draw, shadow_line, SHADOW, LW)
draw.polygon(shadow_head, fill=SHADOW)

# Main teal layer
draw_thick_line(draw, main_line, MAIN, LW)
draw.polygon(main_head, fill=MAIN)

out = pathlib.Path(__file__).parent.parent / "static" / "logo.png"
img.save(out, "PNG")
print(f"Saved {out}  ({W}x{H}px)")
