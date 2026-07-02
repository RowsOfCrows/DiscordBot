"""
Dark-themed temperature chart (Open-Meteo style)
Assumes you already have Open-Meteo data; swap in your own fetch logic.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import numpy as np
from datetime import datetime, timedelta
import io
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
import numpy as np


# ── Sample data (replace with your Open-Meteo API results) ────────────────────
# Expected format:
#   times  → list of datetime objects
#   temps  → list of floats (°C)

def graphically_represent_hourly(hourly_data):

    times = [datetime.fromisoformat(h.time) for h in hourly_data]
    temps = [h.temp for h in hourly_data]

    # ── Colour palette ─────────────────────────────────────────────────────────────
    BG        = "#0d1117"   # near-black background
    PANEL_BG  = "#0d1117"
    GRID      = "#1e2a38"   # subtle grid lines
    TICK_CLR  = "#8da5bb"   # muted blue-grey for labels
    LINE_CLR  = "#3d9be9"   # bright blue line
    DOT_CLR   = "#dff1ff"
    LEGEND_BG = "#111c27"

    # ── Figure setup ───────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(4.5, 1.5))
    fig.patch.set_facecolor(BG)
    fig.patch.set_alpha(0)      # Make figure background transparent
    ax.patch.set_alpha(0)       # Make axes background transparent
    ax.set_facecolor(PANEL_BG)

    # ── Plot the line ──────────────────────────────────────────────────────────────
    ax.plot(times, temps,
            color=LINE_CLR,
            linewidth=1.6,
            solid_capstyle="round",
            zorder=3)

    # Dot on the last data point (matches Open-Meteo style)
    ax.plot(times, temps,
            "o",
            color=DOT_CLR,
            markersize=5,
            zorder=4)

    # ── Grid ───────────────────────────────────────────────────────────────────────
    ax.yaxis.set_major_locator(ticker.MultipleLocator(5))
    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=1)
    ax.grid(axis="x", color=GRID, linewidth=0.5, linestyle=":", zorder=1)
    ax.set_axisbelow(True)

    # ── X-axis: day labels + 12:00 ticks ──────────────────────────────────────────
    # Major ticks at midnight → show date label
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))  # tick every hour
    formatter = mdates.DateFormatter("%-I%p")
    ax.xaxis.set_major_formatter(lambda x, pos: formatter(x).lower())

    # Minor ticks at noon → show "12:00"
    ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=12))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter("12:00"))

    ax.tick_params(axis="x", which="major",
                colors=TICK_CLR, labelsize=8, length=4, pad=4)
    ax.tick_params(axis="x", which="minor",
                colors=TICK_CLR, labelsize=7.5, length=2, pad=4)

    # ── Y-axis ─────────────────────────────────────────────────────────────────────
    ax.tick_params(axis="y", colors=TICK_CLR, labelsize=8, length=0, pad=6)
    ax.set_ylabel("°C", color=TICK_CLR, fontsize=9, labelpad=4, rotation=0)
    ax.yaxis.set_label_coords(-0.03, 1.02)


    for t, temp in zip(times, temps):
    #for t, temp in zip(times[::2], temps[::2]):  # every 2rd item, this is the temps on top
        ax.text(
            t, temp + 0.3,        # x position, y position (slightly above the line)
            f"{round(temp)}°",    # the label
            ha="center",          # horizontal alignment
            va="bottom",
            color="white",
            fontsize=10,
        )


    # ── Spines ─────────────────────────────────────────────────────────────────────
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Bottom spine only, styled as a thin rule
    ax.spines["bottom"].set_visible(True)
    ax.spines["bottom"].set_color(GRID)
    ax.spines["bottom"].set_linewidth(0.8)

    # ── Legend (top-right, matching screenshot) ────────────────────────────────────
    #legend = ax.legend(
    #    [ax.lines[0]],
    #    ["temperature_2m"],
    #    loc="upper right",
    #    frameon=True,
    #    framealpha=0.85,
    #    facecolor=LEGEND_BG,
    #    edgecolor=GRID,
    #    labelcolor=TICK_CLR,
    #    fontsize=8,
    #    handlelength=1.5,
    #    handleheight=0.6,
    #    borderpad=0.6,
    #    handletextpad=0.5,
    #)

    # Watermark (optional — remove if unwanted)
    #fig.text(0.99, 0.02, "Open-Meteo.com",
    #         ha="right", va="bottom",
    #         color="#3a5068", fontsize=7)

    # ── Layout & export ────────────────────────────────────────────────────────────
    plt.tight_layout(pad=0.6)
    plt.savefig("temperature_chart.png", dpi=180, bbox_inches="tight",
                facecolor=BG, transparent=True)
    plt.show()
    print("Saved → temperature_chart.png")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=180, bbox_inches="tight", facecolor=BG)
    buf.seek(0)
    plt.close()