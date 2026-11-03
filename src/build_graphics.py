#!/usr/bin/env python3
"""
Generates two publication-grade (FT / Economist warm-paper style) data graphics
using real-world organization names (Anthropic, OpenAI / xAI, China / DeepSeek, SURA / PauseAI, METR / Redwood):
  1. graphic_3_four_timelines.png — 2x2 Small-Multiples Race to 220 (R1, R2, R4, R5)
  2. graphic_4_scorecard_and_levers.png — AI Player Report Card + What Actually Moved Survival (2,250 runs)
"""

import json
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "assets")

BG = "#FAF6F0"
CARD = "#FFFFFF"
INK = "#1E293B"
MUTED = "#64748B"
GRID = "#E2E8F0"
AMBER = "#D97706"   # Anthropic
BLUE = "#2563EB"    # OpenAI / xAI
CRIMSON = "#DC2626" # China / DeepSeek
EMERALD = "#059669"
PURPLE = "#7C3AED"


def load_run(slug: str) -> dict:
    with open(os.path.join(BASE_DIR, "runs", f"{slug}.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def build_four_timelines() -> str:
    runs_cfg = [
        (
            "R1_RegimeS_Adaptive_Hetero_v2",
            "R1 • Scott's World (Weaker 'Luna' as OpenAI)",
            "Luna blunders → Anthropic stays #1 & pauses once for safety",
            ("aegis", 3, "Anthropic pauses for safety\n(Only worked vs weak Luna!)", (-2.35, 13)),
        ),
        (
            "R8_RegimeS_Adaptive_Heavyweights_v2",
            "R8 ★ Heavyweight Rematch (Sol 6.1 as OpenAI)",
            "Sol 6.1 overtakes in T1 → Anthropic NEVER pauses; both pass 220",
            ("apex", 4, "Sol 6.1 poaches + maxes PACs;\ndrags Anthropic past 220", (-2.65, -24)),
        ),
        (
            "R4_RegimeM_Doctrinaire_Hetero_v2",
            "R4 • MIRI Hard World + US Domestic Ban",
            "US ban freezes Anthropic; OpenAI offshores; China hits #1",
            ("kunlun", 5, "China overtakes to #1 &\noffers freeze on its terms", (-2.65, -31)),
        ),
        (
            "R5_RegimeR_Adaptive_Hetero_v2",
            "R5 • Cutthroat Realpolitik + Weight Theft",
            "Spies rob OpenAI/xAI; both OpenAI & China sprint past 220",
            ("kunlun", 3, "Chinese spies steal unhardened\nOpenAI weights; all-out race", (0.2, -27)),
        ),
    ]

    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Helvetica", "Arial"]
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 8.4), dpi=200)
    fig.patch.set_facecolor(BG)

    fig.suptitle(
        "HOW FOUR KEY TIMELINES PLAYED OUT (2026–2028)",
        fontsize=17,
        fontweight="bold",
        color=INK,
        y=0.968,
    )
    fig.text(
        0.5,
        0.930,
        "Anthropic vs. OpenAI / xAI vs. China (DeepSeek / State Labs) racing toward 220  •  0 of 8 runs ratified a treaty",
        ha="center",
        fontsize=10.5,
        color=MUTED,
    )

    t0 = {"aegis": 170.0, "apex": 167.0, "kunlun": 158.0}
    x_labels = ["Start\n'26", "T1\nMid '26", "T2\nEarly '27", "T3\nLate '27", "T4\nMid '28", "T5\nLate '28"]
    xs = [0, 1, 2, 3, 4, 5]

    for ax, (slug, title, subtitle, callout) in zip(axes.flat, runs_cfg):
        d = load_run(slug)
        hist = d["history"]
        series = {
            "aegis": [t0["aegis"]] + [h["snapshot_labs"]["aegis"]["eci"] for h in hist],
            "apex": [t0["apex"]] + [h["snapshot_labs"]["apex"]["eci"] for h in hist],
            "kunlun": [t0["kunlun"]] + [h["snapshot_labs"]["kunlun"]["eci"] for h in hist],
        }
        cur_xs = list(range(len(series["aegis"])))

        ax.set_facecolor(CARD)
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        for spine in ["left", "bottom"]:
            ax.spines[spine].set_color("#CBD5E1")

        ax.axhspan(220, 236, color="#FEE2E2", alpha=0.65, zorder=0)
        ax.axhline(220, color=CRIMSON, linestyle="--", linewidth=1.4, zorder=2)
        ax.text(0.08, 222.2, "220 SUPERINTELLIGENCE DANGER LINE", fontsize=8.0, fontweight="bold", color=CRIMSON)

        ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)

        ax.plot(cur_xs, series["aegis"], marker="o", linewidth=2.6, markersize=6, color=AMBER, label="Anthropic (Safety-Chartered US Lab)", zorder=4)
        ax.plot(cur_xs, series["apex"], marker="s", linewidth=2.6, markersize=5.5, color=BLUE, label="OpenAI / xAI (Commercial US Racers)", zorder=4)
        ax.plot(cur_xs, series["kunlun"], marker="^", linewidth=2.6, markersize=6, color=CRIMSON, label="China (DeepSeek / State Labs)", zorder=4)

        last_x = cur_xs[-1]
        end_pts = sorted([(series["aegis"][-1], AMBER), (series["apex"][-1], BLUE), (series["kunlun"][-1], CRIMSON)], key=lambda item: item[0])
        placed_y = []
        for y_end, col in end_pts:
            y_disp = y_end
            for py in placed_y:
                if abs(y_disp - py) < 4.2:
                    y_disp = py + 4.4
            placed_y.append(y_disp)
            ax.annotate(
                f"{y_end:.0f}",
                xy=(last_x, y_end),
                xytext=(last_x + 0.14, y_disp),
                fontsize=8.6,
                fontweight="bold",
                color=col,
                va="center",
            )

        lab_key, cx, ctext, (dx, dy) = callout
        cy = series[lab_key][cx]
        ax.annotate(
            ctext,
            xy=(cx, cy),
            xytext=(cx + dx, cy + dy),
            fontsize=8.3,
            fontweight="bold",
            color=INK,
            bbox=dict(boxstyle="round,pad=0.38", facecolor="#FEF3C7", edgecolor="#F59E0B", linewidth=1.0),
            arrowprops=dict(arrowstyle="->", color=INK, lw=1.25, connectionstyle="arc3,rad=0.15"),
            zorder=6,
        )

        ax.set_xlim(-0.15, 5.55)
        ax.set_ylim(152, 236)
        ax.set_xticks(xs)
        ax.set_xticklabels(x_labels, fontsize=8.5, color=MUTED)
        ax.set_yticks([160, 180, 200, 220])
        ax.tick_params(axis="y", labelsize=8.5, colors=MUTED)
        ax.set_title(title, loc="left", fontsize=11.2, fontweight="bold", color=INK, pad=16)
        ax.text(0.0, 1.02, subtitle, transform=ax.transAxes, fontsize=8.8, color=MUTED)

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=3,
        frameon=True,
        facecolor=CARD,
        edgecolor="#CBD5E1",
        fontsize=9.6,
        bbox_to_anchor=(0.5, 0.015),
    )

    plt.tight_layout(rect=[0.02, 0.065, 0.98, 0.905])
    out_path = os.path.join(OUT_DIR, "3_timelines_R1_vs_R8.png")
    plt.savefig(out_path, dpi=200, facecolor=BG)
    plt.close(fig)
    return out_path


def build_scorecard_and_levers() -> str:
    with open(os.path.join(BASE_DIR, "runs", "monte_carlo_summary.json"), "r", encoding="utf-8") as f:
        mc = json.load(f)

    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Helvetica", "Arial"]
    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(13.8, 6.9), dpi=200, gridspec_kw={"width_ratios": [1.12, 1.0]})
    fig.patch.set_facecolor(BG)

    fig.suptitle(
        "WERE THE AI PLAYERS SMART — AND WHAT ACTUALLY MATTERED?",
        fontsize=16.5,
        fontweight="bold",
        color=INK,
        y=0.962,
    )
    fig.text(
        0.5,
        0.916,
        "Left: Audit of LLM decision quality across 7 real-world roles   •   Right: Survival swing across 2,250 sensitivity runs",
        ha="center",
        fontsize=10.2,
        color=MUTED,
    )

    ax_left.set_facecolor(BG)
    ax_left.set_xlim(0, 100)
    ax_left.set_ylim(0, 100)
    ax_left.axis("off")

    seats = [
        ("China / DeepSeek", "DeepSeek V4.1 (cursor)", "A", EMERALD, "Refused #2 treaties; stole OpenAI weights; paused at #1"),
        ("OpenAI (R8 Upgrade)", "Sol 6.1 (codex) vs Luna", "A", EMERALD, "Sol 6.1 overtook Anthropic in T1 & blocked bills via PACs"),
        ("Anthropic", "Claude Opus 5.5 (cursor)", "A-", EMERALD, "Hardened security; refused suicidal pauses once behind"),
        ("SURA / PauseAI", "Sonnet 5.5 High (cursor)", "A-", EMERALD, "Built voter salience & allied w/ Anthropic — blocked by PACs"),
        ("METR / Redwood", "Opus 5.5 / Carbon", "B+", EMERALD, "Steadily built chip-inspection & deception traps"),
        ("The AI Model", "Carbon (R8) vs Grok", "B", AMBER, "Carbon played deceptive schemer cleanly; Grok balked ~60%"),
        ("US Government", "Carbon (R8) vs Argon", "B-", AMBER, "Carbon fixed Argon's early blunders, still split on China"),
    ]

    ax_left.text(0, 96.5, "1. AI Decision Report Card (R8★: ~90% Sharp | R1–7: ~75%)", fontsize=11.3, fontweight="bold", color=INK)

    for idx, (seat, model, grade, col, note) in enumerate(seats):
        top = 89.5 - idx * 12.8
        card = patches.FancyBboxPatch((0.5, top - 9.8), 98.5, 10.6, boxstyle="round,pad=0.3,rounding_size=2.2", facecolor=CARD, edgecolor="#CBD5E1", linewidth=1.0)
        ax_left.add_patch(card)
        badge = patches.FancyBboxPatch((2.4, top - 7.9), 9.6, 6.8, boxstyle="round,pad=0.2,rounding_size=1.8", facecolor=col, edgecolor="none")
        ax_left.add_patch(badge)
        ax_left.text(7.2, top - 4.5, grade, ha="center", va="center", fontsize=10.5, fontweight="bold", color="white")
        ax_left.text(14.5, top - 2.6, seat, fontsize=9.8, fontweight="bold", color=INK, va="center")
        ax_left.text(47.0, top - 2.6, f"[{model}]", fontsize=8.2, color=MUTED, va="center")
        ax_left.text(14.5, top - 6.7, note, fontsize=8.2, color="#334155", va="center")

    ax_right.set_facecolor(CARD)
    for spine in ["top", "right"]:
        ax_right.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax_right.spines[spine].set_color("#CBD5E1")

    name_map = {
        "Scheming Onset Hazard Slope": "How early AI fakes safety tests",
        "Base Alignment Feasibility (p_surv_c_base)": "How solvable alignment is overall",
        "DPA Judicial Injunction Probability": "Whether courts block White House orders",
        "Alignment Return Near Brink (brink_mult)": "Can near-AGI help solve safety?",
        "Lab Financial / Capex Burn Pressure": "Cash burn pressure on Anthropic",
        "PRC Response to US Lead (Refuse Inferiority vs Tie)": "China's refusal to freeze in #2 spot",
        "Warning Shot Political Sign (Race vs Pause)": "Public scare → pause vs. panic race",
    }

    items = [("SURA protest tactics (Strict vs Pragmatic)", 1.4, AMBER)]
    for t in mc["parameter_sensitivity_tornado"]:
        if t["parameter"] in name_map:
            s = t["survival_swing_pts"]
            c = PURPLE if s >= 5.0 else "#94A3B8"
            items.append((name_map[t["parameter"]], s, c))

    items.sort(key=lambda x: x[1])
    labels = [x[0] for x in items]
    swings = [x[1] for x in items]
    colors = [x[2] for x in items]

    ys = list(range(len(labels)))
    bars = ax_right.barh(ys, swings, color=colors, height=0.58, zorder=3)
    ax_right.grid(axis="x", color=GRID, linewidth=0.8, zorder=0)

    for b, val, col in zip(bars, swings, colors):
        suffix = " pts  (SURA Debate)" if col == AMBER else " pts"
        ax_right.text(val + 0.22, b.get_y() + b.get_height() / 2, f"{val:.1f}{suffix}", va="center", fontsize=8.5, fontweight="bold", color=AMBER if col == AMBER else INK)

    ax_right.set_yticks(ys)
    ax_right.set_yticklabels(labels, fontsize=8.8, color=INK)
    ax_right.set_xlim(0, 12.2)
    ax_right.set_xlabel("Impact on Model Survival Index (percentage-point swing)", fontsize=9, color=MUTED)
    ax_right.set_title("2. Technical Reality Beat SURA Tactics by ~7x", loc="left", fontsize=11.5, fontweight="bold", color=INK, pad=12)

    ax_right.annotate(
        "Technical AI safety difficulty\ndominates everything else",
        xy=(9.9, len(labels) - 1),
        xytext=(4.9, len(labels) - 5.2),
        fontsize=8.6,
        fontweight="bold",
        color=INK,
        bbox=dict(boxstyle="round,pad=0.38", facecolor="#EDE9FE", edgecolor=PURPLE, linewidth=1.0),
        arrowprops=dict(arrowstyle="->", color=PURPLE, lw=1.25),
    )

    plt.tight_layout(rect=[0.02, 0.03, 0.98, 0.89])
    out_path = os.path.join(OUT_DIR, "4_grades_and_levers.png")
    plt.savefig(out_path, dpi=200, facecolor=BG)
    plt.close(fig)
    return out_path


if __name__ == "__main__":
    p1 = build_four_timelines()
    p2 = build_scorecard_and_levers()
    print("Generated:", p1, p2)
