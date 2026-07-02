"""
Sun Horizon Card Generator
Generates a horizon card image (similar to lovelace-horizon-card) for use with a Discord bot.

Requirements:
    pip install Pillow

Usage:
    from sun_card import generate_sun_card
    from datetime import datetime, time

    img = generate_sun_card(
        dawn=time(5, 30),
        sunrise=time(6, 10),
        solar_noon=time(12, 45),
        sunset=time(19, 20),
        dusk=time(19, 58),
        now=datetime.now(),          # or pass a specific datetime
        location_name="New York",    # optional label
    )
    img.save("sun_card.png")

    # For Discord (discord.py / nextcord / etc.):
    # import io, discord
    # buf = io.BytesIO()
    # img.save(buf, format="PNG")
    # buf.seek(0)
    # await channel.send(file=discord.File(buf, filename="sun_card.png"))
"""

import math
from datetime import datetime, time, date, timedelta
from PIL import Image, ImageDraw, ImageFont


# ── Dimensions ────────────────────────────────────────────────────────────────
W, H = 800, 300
HORIZON_Y = 200          # y-pixel of the flat horizon line
CURVE_PEAK = 60          # how many px above horizon the sun arc peaks
PADDING_X = 60           # left/right margin before the arc starts/ends

# ── Colours (light theme) ─────────────────────────────────────────────────────
SKY_TOP        = (135, 193, 240, 0)   # light blue sky top
SKY_MID        = (186, 220, 245, 0)   # lighter near horizon
GROUND_TOP     = (161, 196, 120, 0)   # grass green at horizon
GROUND_BOT     = (120, 160,  80, 0)   # slightly darker grass
HORIZON_COLOR  = (255, 255, 255)   # horizon line
SUN_COLOR      = (255, 210,  50,)   # sun fill
SUN_OUTLINE    = (240, 160,   0,)   # sun ring
SUN_GLOW       = (255, 230, 120)   # glow halo
DAWN_COLOR     = (255, 180,  80, 120)   # orange tint for dawn/dusk zones
TEXT_DARK      = (50,  60,  80)
TEXT_MID       = (90, 110, 140)
TEXT_LIGHT     = (255, 255, 255)
CARD_BG        = (245, 248, 252)
ARC_COLOR      = (200, 220, 240)        # dashed arc line
BELOW_ARC      = (160, 190, 220, 80)    # arc below horizon (faint)
LABEL_BG       = (255, 255, 255, 200)
DAWN_DUSK_COLOR = (160, 185, 210)  # muted moon-grey blue



def _time_to_minutes(t: time) -> float:
    """Convert a time object to minutes since midnight."""
    return t.hour * 60 + t.minute + t.second / 60


def _minutes_fraction(minutes: float) -> float:
    """Fraction of the day (0‒1)."""
    return minutes / (24 * 60)


def _sun_x(fraction: float) -> float:
    """Map a day-fraction to an x pixel position along the arc."""
    return PADDING_X + fraction * (W - 2 * PADDING_X)


def _arc_y(x: float, sunrise_x: float, sunset_x: float) -> float:
    """
    Parabolic arc: peaks at solar noon between sunrise_x and sunset_x.
    Returns pixel y (lower = further down on screen).
    """
    if sunrise_x >= sunset_x:
        return HORIZON_Y
    mid_x = (sunrise_x + sunset_x) / 2
    half_span = (sunset_x - sunrise_x) / 2
    t = (x - mid_x) / half_span          # -1 at sunrise, 0 at noon, +1 at sunset
    # parabola: 0 at edges, 1 at peak  →  y goes up (smaller) at peak
    height = (1 - t * t) * CURVE_PEAK
    return HORIZON_Y - height


def _draw_gradient_rect(draw, x0, y0, x1, y1, color_top, color_bot):
    """Vertical gradient fill between two colours."""
    for y in range(int(y0), int(y1) + 1):
        frac = (y - y0) / max(y1 - y0, 1)
        r = int(color_top[0] + frac * (color_bot[0] - color_top[0]))
        g = int(color_top[1] + frac * (color_bot[1] - color_top[1]))
        b = int(color_top[2] + frac * (color_bot[2] - color_top[2]))
        draw.line([(x0, y), (x1, y)], fill=(r, g, b))


def _draw_sun(img: Image.Image, cx: float, cy: float, above_horizon: bool):
    """Draw the sun circle with a soft glow using alpha compositing."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    r_glow = 26
    r_sun  = 16

    # Glow (only when above horizon)
    if above_horizon:
        for i in range(r_glow, r_sun - 1, -1):
            alpha = int(180 * (1 - (i - r_sun) / (r_glow - r_sun + 1)))
            d.ellipse(
                [cx - i, cy - i, cx + i, cy + i],
                fill=(*SUN_GLOW, alpha)
            )

    # Main disc
    d.ellipse(
        [cx - r_sun, cy - r_sun, cx + r_sun, cy + r_sun],
        fill=(*SUN_COLOR, 255),
        outline=(*SUN_OUTLINE, 255),
        width=2,
    )

    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGBA"), (0, 0))


def _load_font(size: int):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _load_font_bold(size: int):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _centered_text(draw, text, cx, y, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((cx - tw / 2, y), text, font=font, fill=fill)


def generate_sun_card(
    dawn: time,
    sunrise: time,
    solar_noon: time,
    sunset: time,
    dusk: time,
    now: datetime = None,
    location_name: str = "",
) -> Image.Image:
    """
    Generate a 800×320 PIL Image of the sun horizon card.

    Parameters
    ----------
    dawn        : civil dawn time
    sunrise     : sunrise time
    solar_noon  : solar noon time
    sunset      : sunset time
    dusk        : civil dusk time
    now         : datetime to use as "current moment" (default: datetime.now())
    location_name : optional string shown in the top-left corner

    Returns
    -------
    PIL.Image.Image  (mode "RGB", size 800×320)
    """
    if now is None:
        now = datetime.now()

    # Convert all times to minutes
    dawn_m    = _time_to_minutes(dawn)
    sunrise_m = _time_to_minutes(sunrise)
    noon_m    = _time_to_minutes(solar_noon)
    sunset_m  = _time_to_minutes(sunset)
    dusk_m    = _time_to_minutes(dusk)
    now_m     = _time_to_minutes(now.time())

    # x positions
    dawn_x    = _sun_x(_minutes_fraction(dawn_m))
    sunrise_x = _sun_x(_minutes_fraction(sunrise_m))
    noon_x    = _sun_x(_minutes_fraction(noon_m))
    sunset_x  = _sun_x(_minutes_fraction(sunset_m))
    dusk_x    = _sun_x(_minutes_fraction(dusk_m))
    now_x     = _sun_x(_minutes_fraction(now_m))

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")

    # ── Sky gradient ──────────────────────────────────────────────────────────
    #_draw_gradient_rect(draw, 0, 0, W, HORIZON_Y, SKY_TOP, SKY_MID)

    # ── Dawn / Dusk tinted zones ──────────────────────────────────────────────
    # Dawn zone (dawn → sunrise)
    # Left side (edge → sunrise, fading inward)
    DAWN_DUSK_COLOR = (160, 185, 210) 

    for x in range(0, int(sunrise_x) + 1):
        frac = x / max(sunrise_x, 1)
        alpha = int(120 * (1 - frac))  # strongest at edge, fades toward sunrise
        draw.line([(x, 0), (x, H)], fill=(*DAWN_DUSK_COLOR, alpha))


    # Right side (sunset → edge, fading outward)
    for x in range(int(sunset_x), W):
        frac = (x - sunset_x) / max(W - sunset_x, 1)
        alpha = int(120 * frac)  # fades from sunset → edge
        draw.line([(x, 0), (x, H)], fill=(*DAWN_DUSK_COLOR, alpha))

    # ── Ground gradient ───────────────────────────────────────────────────────
    #_draw_gradient_rect(draw, 0, HORIZON_Y, W, H, GROUND_TOP, GROUND_BOT)

    # ── Dashed arc (the sun's path) ───────────────────────────────────────────
    arc_points = []
    for px in range(int(PADDING_X), int(W - PADDING_X) + 1):
        py = _arc_y(px, sunrise_x, sunset_x)
        arc_points.append((px, py))

    # Draw as dashes
    dash_len, gap_len = 6, 4
    i = 0
    while i < len(arc_points) - 1:
        p1 = arc_points[i]
        p2 = arc_points[min(i + dash_len, len(arc_points) - 1)]
        color = ARC_COLOR if p1[1] < HORIZON_Y else (180, 190, 200)
        draw.line([p1, p2], fill=color, width=2)
        i += dash_len + gap_len

    # ── Horizon line ──────────────────────────────────────────────────────────
    draw.line([(0, HORIZON_Y), (W, HORIZON_Y)], fill=HORIZON_COLOR, width=2)

    # ── Vertical event markers ────────────────────────────────────────────────
    marker_events = [
        (dawn_x,    "Dawn",    dawn),
        (sunrise_x, "Sunrise", sunrise),
        (noon_x,    "Noon",    solar_noon),
        (sunset_x,  "Sunset",  sunset),
        (dusk_x,    "Dusk",    dusk),
    ]

    font_sm   = _load_font(11)
    font_md   = _load_font(13)
    font_bold = _load_font_bold(13)
    font_time = _load_font(12)

    #for mx, label, t in marker_events:
    #    # Dashed vertical line
    #    for y in range(HORIZON_Y - 10, HORIZON_Y + 40, 6):
    #        draw.line([(mx, y), (mx, y + 3)], fill=(150, 170, 190), width=1)
    #    # Label above
    #    _centered_text(draw, label, mx, HORIZON_Y + 42, font_sm, TEXT_MID)
    #    # Time below label
    #    t_str = t.strftime("%-I:%M %p") if hasattr(t, 'strftime') else str(t)
    #    _centered_text(draw, t_str, mx, HORIZON_Y + 56, font_time, TEXT_DARK)

    for mx, label, t in marker_events:
        is_up = label in ("Sunrise", "Sunset")

        if is_up:
            y_start = HORIZON_Y - 40
            y_end   = HORIZON_Y
        else:
            y_start = HORIZON_Y - 10
            y_end   = HORIZON_Y + 40

        # Dashed vertical line
        for y in range(y_start, y_end, 6):
            draw.line([(mx, y), (mx, y + 3)], fill=(150, 170, 190), width=1)

        t_str = t.strftime("%-I:%M %p") if hasattr(t, 'strftime') else str(t)

        if is_up:
            # place text ABOVE the line
            _centered_text(draw, label, mx, y_start - 18, font_sm, TEXT_MID)
            _centered_text(draw, t_str, mx, y_start - 4, font_time, TEXT_DARK)
        else:
            # original placement BELOW
            _centered_text(draw, label, mx, HORIZON_Y + 42, font_sm, TEXT_MID)
            _centered_text(draw, t_str, mx, HORIZON_Y + 56, font_time, TEXT_DARK)

    # ── Sun position ──────────────────────────────────────────────────────────
    now_arc_y = _arc_y(now_x, sunrise_x, sunset_x)
    above = sunrise_m <= now_m <= sunset_m

    if above:
        sun_cy = now_arc_y
    else:
        # Sun is below horizon — show it slightly below
        sun_cy = HORIZON_Y + 22

    _draw_sun(img, now_x, sun_cy, above_horizon=above)

    # ── "Now" time label near sun ─────────────────────────────────────────────
    now_str = now.strftime("%-I:%M %p")
    label_x = now_x
    label_y = sun_cy - 40 if above else sun_cy + 18

    # Small pill background
    bbox = draw.textbbox((0, 0), now_str, font=font_bold)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = 5
    rx0, ry0 = label_x - tw / 2 - pad, label_y - 1
    rx1, ry1 = label_x + tw / 2 + pad, label_y + th + pad
    draw.rounded_rectangle([rx0, ry0, rx1, ry1], radius=6, fill=(255, 255, 255, 220))
    _centered_text(draw, now_str, label_x, label_y, font_bold, TEXT_DARK)

    # ── Card header ───────────────────────────────────────────────────────────
    font_title = _load_font_bold(16)
    font_date  = _load_font(13)

    header = location_name if location_name else "☀  Sun Position"
    draw.text((18, 14), header, font=font_title, fill=TEXT_DARK)

    date_str = now.strftime("%A, %B %-d")
    draw.text((18, 35), date_str, font=font_date, fill=TEXT_MID)

    # Day length
    day_len_mins = sunset_m - sunrise_m
    day_h, day_m = int(day_len_mins // 60), int(day_len_mins % 60)
    daylen_str = f"Daylight: {day_h}h {day_m:02d}m"
    draw.text((W - 18 - draw.textlength(daylen_str, font=font_date), 14),
              daylen_str, font=font_date, fill=TEXT_MID)

    return img


# ── Quick demo ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from datetime import time as t

    img = generate_sun_card(
        dawn        = t(5, 48),
        sunrise     = t(6, 22),
        solar_noon  = t(13,  5),
        sunset      = t(19, 47),
        dusk        = t(20, 21),
        now         = datetime.now(),
        location_name = "☀  My Location",
    )
    img.save("sun_card_demo.png")
    print("Saved sun_card_demo.png")