"""Editorial (FT/Economist-style) social charts for LinkedIn.

One shared visual system across the three Week-1 posts:
  - post1_home_advantage_{light,dark,square}  (Chapter A cross-league home advantage)
  - post2_model_vs_floor                       (Chapter A model vs class-prior floor)
  - post3_underdog_share                        (Chapter B six-league unpredictability)

All numbers trace to the notebooks/docs (see comments). Palette validated with the
dataviz skill's validator (light: green #0e7a46 / slate #7a8288 / brick #c0392b;
dark: green #2fb673 / slate #868d94). Run:

    .venv\\Scripts\\python reports\\social\\make_social_charts.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.lines import Line2D

OUT = Path(__file__).resolve().parent

# fonts: serif headline, sans body (falls back cleanly if a face is missing)
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "Helvetica", "DejaVu Sans"]
SERIF = fm.FontProperties(family=["Georgia", "Times New Roman", "DejaVu Serif"])

THEMES = {
    "light": dict(surface="#fbfaf7", ink="#1a1a1a", ink2="#54585c", ink3="#8b8e92",
                  accent="#0e7a46", muted="#7a8288", ref="#cfcabd"),
    "dark":  dict(surface="#17181a", ink="#f2f0ea", ink2="#b7bcc1", ink3="#8a8f94",
                  accent="#2fb673", muted="#868d94", ref="#3d4043"),
}


def _header(fig, t, eyebrow, headline, dek, *, rule_y, eyebrow_y, head_y, head_size,
            dek_y, x=0.075):
    fig.add_artist(Line2D([x, x + 0.085], [rule_y, rule_y], transform=fig.transFigure,
                          color=t["accent"], lw=3.2, solid_capstyle="butt"))
    fig.text(x, eyebrow_y, eyebrow, color=t["ink3"], fontsize=9.5, fontweight="bold")
    fig.text(x, head_y, headline, color=t["ink"], fontsize=head_size, fontproperties=SERIF,
             fontweight="bold", linespacing=1.18, va="top")
    fig.text(x, dek_y, dek, color=t["ink2"], fontsize=11.5, linespacing=1.35, va="top")


def _footer(fig, t, lines, *, x=0.075, y0=0.058, dy=0.024, size=8.0):
    for i, ln in enumerate(lines):
        fig.text(x, y0 - i * dy, ln, color=t["ink3"], fontsize=size, va="top")


def _clean(ax, t):
    ax.set_facecolor(t["surface"])
    ax.set_xticks([])
    ax.tick_params(axis="y", length=0, pad=10)
    for s in ax.spines.values():
        s.set_visible(False)


# ---------------------------------------------------------------- Post 1
# Home points share, 2015-2018 (CLAUDE.md / notebook 02): BRA 0.652, ESP 0.600, ENG 0.585
def home_advantage(theme="light", shape="45"):
    t = THEMES[theme]
    data = [("Premier League", 0.585, False),
            ("La Liga", 0.600, False),
            ("Brasileirão", 0.652, True)]

    if shape == "45":
        fig = plt.figure(figsize=(5.4, 6.75), dpi=200)
        _header(fig, t, "HOME ADVANTAGE  ·  BRASILEIRÃO STUDY",
                "The strongest home advantage\nin world football is in Brazil",
                "Home team's share of all points won, top divisions, 2015–2018.\n"
                "An even split would be 0.50.",
                rule_y=0.945, eyebrow_y=0.912, head_y=0.86, head_size=20.5, dek_y=0.735)
        ax = fig.add_axes([0.33, 0.205, 0.60, 0.40])
        foot_y0 = 0.058
    else:  # 1:1 square
        fig = plt.figure(figsize=(5.4, 5.4), dpi=200)
        _header(fig, t, "HOME ADVANTAGE  ·  BRASILEIRÃO STUDY",
                "The strongest home advantage\nin world football is in Brazil",
                "Home team's share of all points won,\ntop divisions, 2015–2018. Even split = 0.50.",
                rule_y=0.935, eyebrow_y=0.895, head_y=0.835, head_size=18.5, dek_y=0.66)
        ax = fig.add_axes([0.33, 0.16, 0.60, 0.36])
        foot_y0 = 0.075
    fig.patch.set_facecolor(t["surface"])
    _clean(ax, t)

    ax.plot([0.50, 0.50], [-0.3, 2.3], color=t["ref"], lw=1.3, zorder=1)
    for y, (name, val, hero) in enumerate(data):
        c = t["accent"] if hero else t["muted"]
        ax.plot([0.50, val], [y, y], color=c, lw=3.4, solid_capstyle="round", zorder=2)
        ax.scatter(val, y, s=300 if hero else 235, color=c, zorder=3,
                   edgecolor=t["surface"], linewidth=2.2)
        ax.text(val + 0.006, y, f"{val:.3f}", va="center", ha="left", color=t["ink"],
                fontsize=13 if hero else 11.5, fontweight="bold" if hero else "normal")
    ax.set_xlim(0.49, 0.70)
    ax.set_ylim(-0.7, 2.7)
    ax.set_yticks(range(len(data)))
    ax.set_yticklabels([d[0] for d in data], fontsize=11.5, color=t["ink2"])
    for tick, d in zip(ax.get_yticklabels(), data):
        if d[2]:
            tick.set_color(t["ink"]); tick.set_fontweight("bold")
    ax.text(0.50, -0.55, "0.50  ·  even split", ha="center", va="top",
            color=t["ink3"], fontsize=9.5)

    _footer(fig, t, ["Data: top-division league match results, 2015–2018   ·   Chart: Gustavo Bohn",
                     "Points share = points won at home ÷ all points on offer"], y0=foot_y0)
    name = f"post1_home_advantage_{'square' if shape=='11' else theme}"
    fig.savefig(OUT / f"{name}.png", facecolor=t["surface"])
    plt.close(fig)
    return name


# ---------------------------------------------------------------- Post 2
# All reproducible: notebook 03 -> floor 1.0514, my model (Elo-only) 1.0303.
# Guessing (1 in 3) = -ln(1/3) = 1.0986, a math constant. (The pre-fix "first
# attempt" number lives only in the lessons log, so it is deliberately not charted;
# the post's text carries that confession.)
def model_vs_floor():
    t = THEMES["light"]
    floor = 1.051
    rows = [("Guessing (1 in 3)", 1.099, False),
            ("Base-rate floor", floor, False),
            ("My model", 1.030, True)]  # y = 0, 1, 2 (bottom -> top)

    fig = plt.figure(figsize=(5.4, 6.75), dpi=200)
    fig.patch.set_facecolor(t["surface"])
    _header(fig, t, "MODEL vs BASELINE  ·  BRASILEIRÃO STUDY",
            "Beat the base rate,\nor you have nothing",
            "Mean log loss over 15 Brasileirão seasons, lower is better.\n"
            "The base-rate floor just predicts each outcome's historical\n"
            "frequency; a 1-in-3 guess can't even clear it. My model does.",
            rule_y=0.945, eyebrow_y=0.912, head_y=0.86, head_size=20.5, dek_y=0.735)
    ax = fig.add_axes([0.30, 0.205, 0.63, 0.40])
    _clean(ax, t)

    ax.plot([floor, floor], [-0.4, 2.4], color=t["ref"], lw=1.3, ls=(0, (4, 3)), zorder=1)
    for y, (name, val, hero) in enumerate(rows):
        c = t["accent"] if hero else t["muted"]
        ax.scatter(val, y, s=300 if hero else 240, color=c, zorder=3,
                   edgecolor=t["surface"], linewidth=2.2)
        left = val < floor
        ax.text(val + (-0.004 if left else 0.004), y, f"{val:.3f}", va="center",
                ha="right" if left else "left", color=t["ink"],
                fontsize=13 if hero else 11.5, fontweight="bold" if hero else "normal")
    ax.set_xlim(1.012, 1.13)
    ax.set_ylim(-0.7, 2.7)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows], fontsize=11.5, color=t["ink2"])
    for tick, r in zip(ax.get_yticklabels(), rows):
        if r[2]:
            tick.set_color(t["ink"]); tick.set_fontweight("bold")
    ax.text(floor, 2.5, "the bar to clear", ha="center", va="bottom",
            color=t["ink3"], fontsize=9.5)
    ax.annotate("lower is better", xy=(1.020, -0.55), xytext=(1.066, -0.55),
                va="center", ha="left", color=t["ink3"], fontsize=9,
                arrowprops=dict(arrowstyle="->", color=t["ink3"], lw=1.1))

    _footer(fig, t, ["Log loss over 15 seasons, 2010–2024   ·   lower is better   ·   Chart: Gustavo Bohn",
                     "Base-rate floor = a no-feature model predicting each season's H/D/A rates"])
    fig.savefig(OUT / "post2_model_vs_floor.png", facecolor=t["surface"])
    plt.close(fig)
    return "post2_model_vs_floor"


# ---------------------------------------------------------------- Post 3
# Underdog points share, six leagues 2012-2025 (notebook 05):
def underdog_share():
    t = THEMES["light"]
    data = [("Brasileirão", 0.4132, True),
            ("Ligue 1", 0.3788, False),
            ("Bundesliga", 0.3651, False),
            ("La Liga", 0.3553, False),
            ("Premier League", 0.3506, False),
            ("Serie A", 0.3394, False)]
    data = data[::-1]  # plot bottom-to-top so Brazil lands on top
    eu_max = 0.3788

    fig = plt.figure(figsize=(5.4, 6.75), dpi=200)
    fig.patch.set_facecolor(t["surface"])
    _header(fig, t, "UNPREDICTABILITY  ·  SIX-LEAGUE STUDY",
            "Nowhere do underdogs win\nmore than in Brazil",
            "Share of all league points won by the pre-match underdog,\n"
            "six leagues, 2012–2025. Higher means more chaos.\n"
            "Brazil is the only league above Europe's best.",
            rule_y=0.945, eyebrow_y=0.912, head_y=0.86, head_size=20.5, dek_y=0.735)
    ax = fig.add_axes([0.33, 0.15, 0.60, 0.46])
    _clean(ax, t)

    ax.plot([eu_max, eu_max], [-0.4, 5.4], color=t["ref"], lw=1.3, zorder=1)
    for y, (name, val, hero) in enumerate(data):
        c = t["accent"] if hero else t["muted"]
        ax.scatter(val, y, s=300 if hero else 210, color=c, zorder=3,
                   edgecolor=t["surface"], linewidth=2.2)
        ax.text(val + (0.006 if hero else 0.005), y, f"{val*100:.1f}%", va="center",
                ha="left", color=t["ink"], fontsize=13 if hero else 11,
                fontweight="bold" if hero else "normal")
    ax.set_xlim(0.325, 0.45)
    ax.set_ylim(-0.7, 5.7)
    ax.set_yticks(range(len(data)))
    ax.set_yticklabels([d[0] for d in data], fontsize=11, color=t["ink2"])
    for tick, d in zip(ax.get_yticklabels(), data):
        if d[2]:
            tick.set_color(t["ink"]); tick.set_fontweight("bold")
    ax.text(eu_max, 5.55, "Europe's best (Ligue 1)", ha="center", va="bottom",
            color=t["ink3"], fontsize=9.5)

    _footer(fig, t, ["Data: football-data.co.uk, six leagues, 2012–2025 (30,560 matches)   ·   Chart: Gustavo Bohn",
                     "Underdog = the weaker side by pre-match Elo rating"])
    fig.savefig(OUT / "post3_underdog_share.png", facecolor=t["surface"])
    plt.close(fig)
    return "post3_underdog_share"


def main():
    made = [home_advantage("light", "45"), home_advantage("dark", "45"),
            home_advantage("light", "11"), model_vs_floor(), underdog_share()]
    for m in made:
        print("saved", m + ".png")


if __name__ == "__main__":
    main()
