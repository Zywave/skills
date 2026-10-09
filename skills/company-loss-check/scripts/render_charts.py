#!/usr/bin/env python3
"""Render the two company loss check charts from a profile JSON.

Usage: python render_charts.py profile.json charts.png

Left panel: total reported loss by line of business, labeled with how many
records carry an amount. Right panel: recent years as record counts split into
"with amount" and "no amount". Neutral palette, no logo, one axis per panel.
"""
import json
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, MUTED, GRID = "#1f1f1e", "#6b6a66", "#e1e0d9"
BAR, BAR_LIGHT = "#2a78d6", "#b5d4f4"


def money(n):
    if n >= 1e9:
        return f"${n / 1e9:.2f}B"
    if n >= 1e6:
        return f"${n / 1e6:.1f}M"
    if n >= 1e3:
        return f"${n / 1e3:.0f}K"
    return f"${n:.0f}"


def main(src, out):
    with open(src) as f:
        p = json.load(f)
    lines = sorted(p.get("lines", []), key=lambda r: r.get("total_loss") or 0, reverse=True)[:6]
    years = sorted(p.get("years", []), key=lambda r: r["year"])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1.15, 1]})
    fig.patch.set_facecolor("white")

    labels = [r["name"] for r in lines][::-1]
    vals = [(r.get("total_loss") or 0) for r in lines][::-1]
    ax1.barh(labels, vals, color=BAR, height=0.55)
    top = max(vals) if vals and max(vals) > 0 else 1
    for i, r in enumerate(lines[::-1]):
        tl = r.get("total_loss")
        amt = money(tl) if tl is not None and r.get("contributing", 0) > 0 else "no amount recorded"
        ax1.text((tl or 0) + top * 0.02, i,
                 f"{amt}  ({r.get('contributing', 0)} of {r.get('cases', 0)} with amount)",
                 va="center", fontsize=8.5, color=INK)
    ax1.set_xlim(0, top * 1.75)
    ax1.set_title("Reported loss by line of business", loc="left", fontsize=11, color=INK, pad=22)
    ax1.xaxis.set_visible(False)

    x = [r["year"] for r in years]
    with_amt = [r.get("contributing", 0) for r in years]
    no_amt = [max(r.get("cases", 0) - r.get("contributing", 0), 0) for r in years]
    ax2.bar(x, with_amt, color=BAR, width=0.6, label="With amount")
    ax2.bar(x, no_amt, bottom=with_amt, color=BAR_LIGHT, width=0.6, label="No amount")
    ax2.set_xticks(x)
    ax2.set_xticklabels([str(v) for v in x], rotation=45, fontsize=8)
    ax2.set_title("Case records by year", loc="left", fontsize=11, color=INK, pad=22)
    ax2.legend(frameon=False, fontsize=8, loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2)
    ax2.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax2.set_axisbelow(True)

    for ax in (ax1, ax2):
        for side in ("top", "right", "left" if ax is ax1 else "bottom"):
            ax.spines[side].set_visible(False)
        for side in ("bottom",) if ax is ax1 else ("left",):
            ax.spines[side].set_color(GRID)
        ax.tick_params(colors=MUTED, labelsize=8.5)

    name = p.get("company", {}).get("name", "")
    fig.suptitle(f"{name}: publicly reported losses", x=0.01, ha="left", fontsize=12, color=INK)
    fig.text(0.01, 0.01, "Source: Zywave loss data. Publicly reported events, generally $1M or more. "
             "Lines of business show likely coverage, not what paid.", fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(out, dpi=160)
    print(out)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
