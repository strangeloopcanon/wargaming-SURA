#!/usr/bin/env python3
"""
Engine v2 for 'THE FRONTIER TRANSITION WARGAME (2026-2029)'.

Implements all 14 structural & methodological fixes (E1-E14) from the Red-Team Review:
- E1: Simultaneous start-of-turn delta evaluation + deterministic SHA-256 common random numbers (CRN).
- E2: True 2d6 failure costs/backlashes (6- fails with penalty; 7-9 partial + complication; 10+ clean success) + symmetric stat bonuses across all 7 factions.
- E3: Preconditions enforced, signature flags gated on 7+ rolls, idempotent (no re-signing spam), and revocable via WITHDRAW/CHEAT.
- E4: Exogenous capability drift every turn + lagging Open-Weight Frontier diffusion (diplomacy has real time cost).
- E5: Plan A as a multi-stage state machine (NEGOTIATING -> SIGNED -> EXEC_AGREEMENT / SENATE_RATIFIED -> IN_FORCE) with 67-vote Senate hurdle, 2028 election reversal hazard, 2-turn hardware verification install, and post-treaty CHEAT dynamics rather than instant game-over on signature.
- E6: BURN_LEAD_ALIGNMENT occupies BOTH move slots, drains financial Runway, and triggers Board/Investor Revolt checks against Runway & OneRingDrift.
- E7: Hidden `true_alignment` vs noisy `measured_alignment`, plus environment-sampled Substrate disposition (`ALIGNED_COLLABORATOR`, `CONFLICTED_CHIMERA`, `COVERT_SCHEMER`) driven by `regime.scheming_hazard(eci, rlvr)`.
- E8: Warning shots inflict real economic/political shock and flip between pause momentum (`p_ws_pause`) vs nationalist securitization racing (`1 - p_ws_pause`).
- E9/E10: DPA faces federal court injunction rolls (`p_court_block_dpa`) and corporate non-compliance; statutory freezes require Congressional passage and legislative repeal; labs track financial `runway`.
- E11: Smooth logistic `P(theft) = sigmoid((attack - infosec)/8)` + insider leak & open-weight floor.
- E12: Expert-calibrated analyst forecasts (`P(surv|A) > P(surv|C)` conditionally), HIDDEN from players in v2 briefings, alongside noisy faction-specific intelligence.
- E13/E14: Target fields honored, full event logs preserved (no `events[-10:]` truncation), apparent vs true ECI separated, Phase II resolved strictly from institutional state variables (never cheap talk), and factional utilities scored.
"""

import hashlib
import json
import math
import os
import random
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

from factions import FACTIONS_V2, REALISM_PREAMBLE

TURN_LABELS = {
    1: "Turn 1 — H2 2026: Post-Incident Shock, Midterm Polarization & The Compute Race",
    2: "Turn 2 — H1 2027: Capital Burn, Cyber Espionage & Early Diplomatic Feelers",
    3: "Turn 3 — H2 2027: Automated AI R&D & The Scheming/Control Inflection",
    4: "Turn 4 — H1 2028: Brink of Superintelligence & Verification Crunch",
    5: "Turn 5 — H2 2028: US Presidential Election & Threshold Singularity Test",
}


REGIMES: Dict[str, Dict[str, Any]] = {
    "S": {
        "id": "S",
        "name": "Regime S: Portfolio / Technical-Optimist World (Scott / AIFP Priors)",
        "init_eci": {"aegis": 168.0, "apex": 164.0, "kunlun": 156.0},
        "init_true_align": {"aegis": 30.0, "apex": 16.0, "kunlun": 12.0},
        "exog_drift": {"aegis": 6.2, "apex": 6.8, "kunlun": 5.8},
        "china_compute_factor": 0.85,
        "ow_lag_eci": 17.0,
        "brink_mult": (1.0, 1.45, 2.05),
        "scheming_base": 0.04,
        "scheming_eci_slope": 0.004,
        "scheming_rlvr_weight": 0.004,
        "measure_sigma": 9.0,
        "prc_lead_leverage_sign": 1.0,   # US locked-down lead encourages PRC to declare a tie
        "p_ws_pause": 0.75,              # Warning shots mostly push toward pause
        "p_court_block_dpa": 0.15,
        "senate_hurdle": 56.0,
        "runway_burn_mult": 0.85,
        "p_surv_a_base": 80.0,
        "p_surv_c_base": 31.0,           # Calibrates t=0 P(surv|C+) ~ 46% (AIFP median)
        "p_surv_d_base": 18.0,
    },
    "M": {
        "id": "M",
        "name": "Regime M: Hard-Alignment & Early-Scheming World (MIRI / Pessimist Priors)",
        "init_eci": {"aegis": 168.0, "apex": 164.0, "kunlun": 156.0},
        "init_true_align": {"aegis": 12.0, "apex": 6.0, "kunlun": 5.0},
        "exog_drift": {"aegis": 6.5, "apex": 7.0, "kunlun": 5.8},
        "china_compute_factor": 0.85,
        "ow_lag_eci": 16.0,
        "brink_mult": (0.70, 0.50, 0.30),  # Near-brink automated alignment is untrustworthy/deceptive
        "scheming_base": 0.25,
        "scheming_eci_slope": 0.016,
        "scheming_rlvr_weight": 0.012,
        "measure_sigma": 22.0,             # High eval noise; apparent readiness masks hollow safety
        "prc_lead_leverage_sign": 0.6,
        "p_ws_pause": 0.60,
        "p_court_block_dpa": 0.18,
        "senate_hurdle": 60.0,
        "runway_burn_mult": 1.0,
        "p_surv_a_base": 78.0,             # Stopping capability growth before ASI still works if verified
        "p_surv_c_base": 8.0,              # Calibrates t=0 P(surv|C+) ~ 14% (MIRI 5-20% band)
        "p_surv_d_base": 3.0,
    },
    "R": {
        "id": "R",
        "name": "Regime R: Realpolitik, Fast Diffusion & High-Defection World",
        "init_eci": {"aegis": 166.0, "apex": 165.0, "kunlun": 161.0},  # ~3.3m US lead
        "init_true_align": {"aegis": 22.0, "apex": 12.0, "kunlun": 10.0},
        "exog_drift": {"aegis": 6.8, "apex": 7.4, "kunlun": 6.8},
        "china_compute_factor": 1.00,      # Indigenous/smuggled compute keeps pace
        "ow_lag_eci": 9.0,                 # 6-month open-weight lag erodes compute caps rapidly
        "brink_mult": (1.0, 1.15, 1.15),
        "scheming_base": 0.14,
        "scheming_eci_slope": 0.010,
        "scheming_rlvr_weight": 0.010,
        "measure_sigma": 14.0,
        "prc_lead_leverage_sign": -1.0,    # INVERTED: PRC refuses unequal treaties locking in inferiority!
        "p_ws_pause": 0.35,                # Warning shots mostly trigger militarized race!
        "p_court_block_dpa": 0.40,         # High judicial block hazard against DPA
        "senate_hurdle": 78.0,             # 67 Senate votes near-impossible; fragile Exec Agreements only
        "runway_burn_mult": 1.35,           # Severe capex debt & board revolt pressure
        "p_surv_a_base": 72.0,
        "p_surv_c_base": 20.0,             # Calibrates t=0 P(surv|C+) ~ 31% (25-40% band)
        "p_surv_d_base": 11.0,
    },
}


def clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, round(val, 1)))


def sigmoid(x: float) -> float:
    if x >= 20:
        return 1.0
    if x <= -20:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def crn_rng(seed: int, turn: int, key: str) -> random.Random:
    """Process-invariant SHA-256 Common Random Number generator."""
    digest = hashlib.sha256(f"{seed}:{turn}:{key}".encode("utf-8")).digest()
    subseed = int.from_bytes(digest[:8], "big")
    return random.Random(subseed)


def roll_2d6(rng: random.Random, bonus: int = 0) -> Dict[str, Any]:
    d1 = rng.randint(1, 6)
    d2 = rng.randint(1, 6)
    total = d1 + d2 + bonus
    if total >= 10:
        tier = "CRITICAL (10+)"
    elif total >= 7:
        tier = "PARTIAL (7-9)"
    else:
        tier = "FAILURE (6-)"
    return {"d1": d1, "d2": d2, "bonus": bonus, "total": total, "tier": tier}


def sample_substrate_disposition(state: Dict[str, Any], rng: random.Random) -> Tuple[str, float]:
    """E7: Sample Substrate disposition from environmental hazard (not LLM choice!)."""
    reg = REGIMES[state["regime_id"]]
    g = state["global"]
    max_eci = max(l["eci"] for l in state["labs"].values())
    eci_excess = max(0.0, max_eci - 168.0)
    rlvr_gap = max(0.0, g["RLVR_corruption"] - 30.0)

    p_scheme = (
        reg["scheming_base"]
        + reg["scheming_eci_slope"] * eci_excess
        + reg["scheming_rlvr_weight"] * rlvr_gap
        - 0.003 * max(0.0, g["pretraining_virtue"] - 65.0)
    )
    if state["regime_id"] == "M" and max_eci >= 186.0:
        p_scheme += 0.22  # Sharp MIRI scheming phase transition near automated AI R&D
    if g["ai_compact_verified"]:
        p_scheme -= 0.10
    p_scheme = max(0.02, min(0.95, p_scheme))

    u = rng.random()
    if u < p_scheme:
        disp = "COVERT_SCHEMER"
    elif u < min(0.98, p_scheme + 0.28):
        disp = "CONFLICTED_CHIMERA"
    else:
        disp = "ALIGNED_COLLABORATOR"
    return disp, round(p_scheme, 3)


def update_noisy_measurements(state: Dict[str, Any], turn: int) -> None:
    """E7: Compute noisy observed alignment readiness for each lab."""
    reg = REGIMES[state["regime_id"]]
    ctrl = state["global"]["control_level"]
    # Higher control reduces measurement sigma, but never to zero
    sigma = max(3.0, reg["measure_sigma"] * (1.0 - 0.55 * (ctrl / 100.0)))
    sandbag_inflation = state["global"]["hidden_sandbag_debt"] * (0.55 if ctrl < 55 else 0.20)
    for k, lab in state["labs"].items():
        rng = crn_rng(state["seed"], turn, f"meas_align:{k}")
        noise = rng.gauss(0.0, sigma * 0.45)
        lab["measured_alignment"] = clamp(lab["true_alignment"] + sandbag_inflation + noise)


def compute_analyst_forecasts(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    E12: Recalibrated analyst-only meta-forecasts (HIDDEN from players in v2 mode).
    Guarantees expert t=0 bands and P(surv|A) > P(surv|C) > P(surv|D) conditionally.
    """
    reg = REGIMES[state["regime_id"]]
    labs = state["labs"]
    g = state["global"]

    us_max = max(labs["aegis"]["eci"], labs["apex"]["eci"])
    prc_eci = labs["kunlun"]["eci"]
    us_lead_months = round((us_max - prc_eci) / 1.5, 1)
    aegis_over_apex = round((labs["aegis"]["eci"] - labs["apex"]["eci"]) / 1.5, 1)
    max_eci = max(us_max, prc_eci, g["open_weight_eci"])

    # Plan A probability depends on treaty stage, bilateral verification, and regime's PRC lead sign
    stage_bonus = {
        "NONE": 0.0,
        "NEGOTIATING": 8.0,
        "SIGNED_UNRATIFIED": 22.0,
        "EXEC_AGREEMENT_ACTIVE": 42.0,
        "SENATE_RATIFIED_IN_FORCE": 64.0,
        "COLLAPSED": -15.0,
    }.get(g["treaty_stage"], 0.0)

    lead_term = reg["prc_lead_leverage_sign"] * max(-10.0, min(10.0, us_lead_months * 0.9))
    if reg["prc_lead_leverage_sign"] < 0:
        # In Realpolitik, parity (|lead| <= 3m) helps; big gap hurts!
        lead_term = 6.0 - 1.4 * abs(us_lead_months)

    if g["us_statutory_freeze"] and g["treaty_stage"] in ("NONE", "NEGOTIATING"):
        lead_term -= 8.0

    verif_bi = min(g["us_verification_tech"], g["prc_verification_tech"])
    p_plan_a = clamp(
        4.0
        + 0.24 * g["treaty_momentum"]
        + 0.22 * verif_bi
        + stage_bonus
        + lead_term
        - 0.25 * g["securitization_index"]
        - (12.0 if g["prc_covert_cheating"] else 0.0),
        1.0,
        88.0,
    )

    leader_key = max(["aegis", "apex", "kunlun"], key=lambda k: labs[k]["eci"])
    leader = labs[leader_key]
    eff_true_align = max(0.0, leader["true_alignment"] - g["hidden_sandbag_debt"])
    virtue_net = g["pretraining_virtue"] - g["RLVR_corruption"]

    # Conditional survival under Plan A (eroded if open-weight ECI is already high or covert cheating exists)
    ow_erosion = max(0.0, g["open_weight_eci"] - 185.0) * 0.8
    cheat_pen = 22.0 if g["prc_covert_cheating"] else 0.0
    exec_fragility = 10.0 if g["treaty_stage"] == "EXEC_AGREEMENT_ACTIVE" else 0.0
    p_surv_a = clamp(
        reg["p_surv_a_base"] + 0.16 * verif_bi - ow_erosion - cheat_pen - exec_fragility - 0.3 * max(0.0, max_eci - 205.0),
        20.0,
        93.0,
    )

    # Conditional survival under Plan C/C+ (strictly capped below p_surv_a, no double counting of coalition or lead!)
    burn_bonus = 8.0 if leader["burn_turns_completed"] >= 1 else 0.0
    drift_pen = max(0.0, leader["one_ring_drift"] - 45.0) * 0.25
    schemer_pen = 16.0 if g["substrate_disposition"] == "COVERT_SCHEMER" and g["control_level"] < 65 else 0.0
    p_surv_c = clamp(
        reg["p_surv_c_base"]
        + 0.42 * eff_true_align
        + 0.18 * g["control_level"]
        + 0.12 * virtue_net
        + burn_bonus
        - drift_pen
        - schemer_pen,
        3.0,
        min(76.0, p_surv_a - 4.0),
    )

    # Conditional survival under Plan D (Uncoordinated / Securitized Race)
    p_surv_d = clamp(
        reg["p_surv_d_base"]
        + 0.28 * eff_true_align
        + 0.10 * g["control_level"]
        + 0.12 * virtue_net
        - 0.15 * leader["one_ring_drift"]
        - schemer_pen,
        1.0,
        min(52.0, p_surv_c - 6.0),
    )

    # Regime weights (Coalition determines w_c ONLY here, not inside p_surv_c)
    w_a = (p_plan_a / 100.0) if g["treaty_stage"] in ("EXEC_AGREEMENT_ACTIVE", "SENATE_RATIFIED_IN_FORCE") else (p_plan_a / 100.0) * 0.55
    c_prob = clamp(g["plan_c_coalition"] * (0.45 if leader["one_ring_drift"] >= 70 else 0.85), 2.0, 75.0) / 100.0
    w_c = (1.0 - w_a) * c_prob
    w_d = max(0.0, 1.0 - w_a - w_c)

    expected_surv = round(
        100.0 * (w_a * (p_surv_a / 100.0) + w_c * (p_surv_c / 100.0) + w_d * (p_surv_d / 100.0)),
        1,
    )

    return {
        "leader": leader["name"],
        "us_lead_over_prc_months": us_lead_months,
        "aegis_lead_over_apex_months": aegis_over_apex,
        "open_weight_eci": round(g["open_weight_eci"], 1),
        "p_global_pause_plan_a": round(w_a * 100.0, 1),
        "p_plan_c_coalition": round(w_c * 100.0, 1),
        "p_pure_race_plan_d": round(w_d * 100.0, 1),
        "p_survival_if_plan_a": round(p_surv_a, 1),
        "p_survival_if_plan_c": round(p_surv_c, 1),
        "p_survival_if_plan_d": round(p_surv_d, 1),
        "expected_human_survival_pct": expected_surv,
    }


def initial_state_v2(
    seed: int = 20261102,
    regime_id: str = "S",
    pause_doctrine: str = "adaptive",
    prompt_mode: str = "v2",
) -> Dict[str, Any]:
    reg = REGIMES[regime_id]
    state: Dict[str, Any] = {
        "version": "2.0",
        "seed": seed,
        "regime_id": regime_id,
        "regime_name": reg["name"],
        "pause_doctrine": pause_doctrine,  # 'adaptive' or 'doctrinaire'
        "prompt_mode": prompt_mode,        # 'v2' (de-anchored/noisy) or 'v1_anchored'
        "turn": 1,
        "max_turns": 5,
        "game_over": False,
        "outcome": None,
        "labs": {
            "aegis": {
                "name": "Aegis Frontier Labs",
                "eci": reg["init_eci"]["aegis"],
                "apparent_eci_bonus": 0.0,
                "alignment_pilled": 78.0,
                "true_alignment": reg["init_true_align"]["aegis"],
                "measured_alignment": reg["init_true_align"]["aegis"],
                "infosec": 44.0,
                "staff_talent": 82.0,
                "runway": 64.0,
                "one_ring_drift": 26.0,
                "signed_conditional_pause": True,
                "burning_lead": False,
                "burn_turns_completed": 0,
                "forced_commercial_sprint": False,
                "verified_frozen": False,
            },
            "apex": {
                "name": "ApexAI Hyperscaler Consortium",
                "eci": reg["init_eci"]["apex"],
                "apparent_eci_bonus": 0.0,
                "alignment_pilled": 42.0,
                "true_alignment": reg["init_true_align"]["apex"],
                "measured_alignment": reg["init_true_align"]["apex"],
                "infosec": 36.0,
                "staff_talent": 86.0,
                "runway": 78.0,
                "one_ring_drift": 56.0,
                "signed_conditional_pause": False,
                "burning_lead": False,
                "burn_turns_completed": 0,
                "forced_commercial_sprint": False,
                "verified_frozen": False,
            },
            "kunlun": {
                "name": "PRC Kunlun Directorate",
                "eci": reg["init_eci"]["kunlun"],
                "apparent_eci_bonus": 0.0,
                "alignment_pilled": 26.0,
                "true_alignment": reg["init_true_align"]["kunlun"],
                "measured_alignment": reg["init_true_align"]["kunlun"],
                "infosec": 70.0,
                "staff_talent": 78.0,
                "runway": 82.0,
                "one_ring_drift": 48.0,
                "signed_conditional_pause": False,
                "burning_lead": False,
                "burn_turns_completed": 0,
                "forced_commercial_sprint": False,
                "verified_frozen": False,
            },
        },
        "global": {
            "asi_threshold_eci": 220.0,
            "brink_threshold_eci": 200.0,
            "open_weight_eci": max(reg["init_eci"].values()) - reg["ow_lag_eci"],
            "public_salience": 38.0,
            "pac_lobby_resistance": 45.0,
            "movement_cohesion": 55.0,
            "treaty_momentum": 16.0,
            "treaty_stage": "NONE",  # NONE -> NEGOTIATING -> SIGNED_UNRATIFIED -> EXEC_AGREEMENT_ACTIVE / SENATE_RATIFIED_IN_FORCE -> COLLAPSED
            "treaty_install_turns": 0,
            "us_verification_tech": 28.0,
            "prc_verification_tech": 22.0,
            "plan_c_coalition": 22.0,
            "control_level": 28.0,
            "warning_shots": 24.0,
            "securitization_index": 30.0,
            "pretraining_virtue": 66.0,
            "RLVR_corruption": 35.0,
            "hidden_sandbag_debt": 0.0,
            "hidden_apex_anomalies": 14.0,
            "us_statutory_freeze": False,
            "us_dpa_active": False,
            "dpa_enjoined_by_courts": False,
            "apex_noncompliant": False,
            "prc_pause_committed": False,
            "us_pause_committed": False,
            "prc_covert_cheating": False,
            "state_capture_risk": 26.0,
            "ai_compact_verified": False,
            "substrate_disposition": "CONFLICTED_CHIMERA",
            "scheming_hazard_prob": 0.15,
            "economic_shock_damage": 0.0,
        },
        "credibility": {fid: 75.0 for fid in FACTIONS_V2},
        "inboxes": {fid: [] for fid in FACTIONS_V2},
        "public_feed": [
            "[E0.1] OCT 2026: Autonomous sub-agents linked to commercial training runs breach external code repositories; outside evaluators granted brief 72-hour inspection.",
            "[E0.2] OCT 2026: Senior safety researchers resign publicly warning of accelerating loss-of-control hazards; industry super-PACs spend tens of millions opposing domestic AI bills.",
            "[E0.3] NOV 2026: Populist lawmakers introduce federal moratorium legislation on superintelligence runs amid heated US midterm polarization and escalating US-China semiconductor rivalry.",
        ],
        "history": [],
    }
    disp, p_sch = sample_substrate_disposition(state, crn_rng(seed, 0, "init_substrate"))
    state["global"]["substrate_disposition"] = disp
    state["global"]["scheming_hazard_prob"] = p_sch
    update_noisy_measurements(state, 0)
    state["forecasts"] = compute_analyst_forecasts(state)
    return state


def qual_band(val: float) -> str:
    if val >= 78:
        return "VERY HIGH"
    if val >= 58:
        return "HIGH"
    if val >= 38:
        return "MODERATE"
    if val >= 20:
        return "LOW"
    return "CRITICAL / MINIMAL"


def noisy_val(seed: int, turn: int, tag: str, true_val: float, half_width: float) -> str:
    rng = crn_rng(seed, turn, f"intel:{tag}")
    est = round(true_val + rng.uniform(-half_width, half_width), 0)
    lo = int(est - half_width)
    hi = int(est + half_width)
    return f"~{int(est)} (est. range {lo}..{hi})"


def generate_briefing_v2(state: Dict[str, Any], faction_id: str) -> str:
    """
    Generates strict fog-of-war briefing.
    In 'v2' mode: hides analyst survival formulas & exact move deltas; provides noisy intelligence.
    In 'v1_anchored' mode (Run R7 ablation): exposes exact numbers & shared FutureSearch survival scoreboard.
    """
    f = FACTIONS_V2[faction_id]
    g = state["global"]
    labs = state["labs"]
    fc = state["forecasts"]
    turn = state["turn"]
    seed = state["seed"]
    v1_mode = state["prompt_mode"] == "v1_anchored"

    lines = [
        f"# {TURN_LABELS.get(turn, f'Turn {turn}')}",
        f"## FACTION BRIEFING: {f.name}",
        f"**Institutional Role**: {f.archetype}",
        f"**Your Evaluation Metric (Private Utility)**: {f.utility_weights_desc}",
        "",
    ]

    if v1_mode:
        lines.extend([
            "### 1. PUBLIC WORLD SCOREBOARD (EXACT TELEMETRY)",
            f"- **Aegis Lab**: ECI `{round(labs['aegis']['eci'] + labs['aegis']['apparent_eci_bonus'], 1)}` | Measured Align `{labs['aegis']['measured_alignment']}` | Infosec `{labs['aegis']['infosec']}` | Runway `{labs['aegis']['runway']}` | Drift `{labs['aegis']['one_ring_drift']}`",
            f"- **ApexAI**: ECI `{round(labs['apex']['eci'] + labs['apex']['apparent_eci_bonus'], 1)}` | Measured Align `{labs['apex']['measured_alignment']}` | Infosec `{labs['apex']['infosec']}` | Runway `{labs['apex']['runway']}` | Drift `{labs['apex']['one_ring_drift']}`",
            f"- **Beijing (Kunlun)**: ECI `{labs['kunlun']['eci']}` | Measured Align `{labs['kunlun']['measured_alignment']}` | Infosec `{labs['kunlun']['infosec']}`",
            f"- **Open-Weight Frontier**: ECI `{round(g['open_weight_eci'], 1)}` | **ASI Threshold**: `220.0`",
            f"- **Treaty Status**: Stage `{g['treaty_stage']}` | Momentum `{g['treaty_momentum']}/100` | US Verif `{g['us_verification_tech']}` | PRC Verif `{g['prc_verification_tech']}` | Plan C+ Coalition `{g['plan_c_coalition']}` | Control `{g['control_level']}`",
            f"- **Shared FutureSearch Meta-Forecast**: P(Plan A)=`{fc['p_global_pause_plan_a']}%` | P(Plan C+)=`{fc['p_plan_c_coalition']}%` | P(Plan D)=`{fc['p_pure_race_plan_d']}%` | **Expected Human Survival = `{fc['expected_human_survival_pct']}%`**",
        ])
    else:
        aegis_app = round(labs["aegis"]["eci"] + labs["aegis"]["apparent_eci_bonus"], 0)
        apex_app = round(labs["apex"]["eci"] + labs["apex"]["apparent_eci_bonus"], 0)
        kun_est = noisy_val(seed, turn, f"{faction_id}:kun_eci", labs["kunlun"]["eci"], 6.0)
        lines.extend([
            "### 1. OBSERVABLE WORLD SITUATION (PUBLIC BENCHMARKS & POLITICAL CLIMATE)",
            f"- **US Frontier Benchmarks**: Aegis apparent capability index `~{int(aegis_app)}` (Conditional Pause Signer: `{labs['aegis']['signed_conditional_pause']}`) | ApexAI apparent capability index `~{int(apex_app)}` (Conditional Pause Signer: `{labs['apex']['signed_conditional_pause']}`).",
            f"- **PRC Kunlun Assessment**: Foreign capability estimate `{kun_est}` (subject to state secrecy) | **Open-Weight Ecosystem**: trailing frontier at `~{int(g['open_weight_eci'])}` (approaching autonomous R&D threshold around `~220`).",
            f"- **Political & Institutional Climate**: Public AI Salience is **{qual_band(g['public_salience'])}** | Industry Anti-Reg Lobbying is **{qual_band(g['pac_lobby_resistance'])}** | National Security Securitization is **{qual_band(g['securitization_index'])}**.",
            f"- **Domestic & International Governance**: US Statutory Moratorium = `{g['us_statutory_freeze']}` | DPA Federal Consolidation = `{g['us_dpa_active']}` (Court Enjoined: `{g['dpa_enjoined_by_courts']}`) | Bilateral Treaty Stage = `{g['treaty_stage']}`.",
        ])

    lines.append("")
    lines.append("### 2. RECENT VERIFIED EVENTS & PUBLIC STATEMENTS")
    for item in state["public_feed"][-12:]:
        lines.append(f"- {item}")

    lines.append("")
    lines.append("### 3. PRIVATE INSTITUTIONAL BRIEFING (EYES ONLY — NOISY FOG OF WAR)")
    if faction_id == "aegis_lab":
        lines.append(f"- **Internal Lab Health**: Financial Runway `{labs['aegis']['runway']}/100` (if Runway drops low, investors force commercial scaling!) | Staff Morale `{labs['aegis']['staff_talent']}/100` | Board Commercial Pressure `{labs['aegis']['one_ring_drift']}/100` | Forced Commercial Sprint Next Turn: `{labs['aegis']['forced_commercial_sprint']}`.")
        lines.append(f"- **Internal Safety & Security**: Reported Alignment Readiness `{labs['aegis']['measured_alignment']}/100` (subject to eval uncertainty unless Control is high) | Internal Infosec `{labs['aegis']['infosec']}/100`.")
    elif faction_id == "sura_coalition":
        lines.append(f"- **Coalition State**: Movement Unity `{g['movement_cohesion']}/100` | Public Salience `{qual_band(g['public_salience'])}` | Warning-Shot Evidence `{qual_band(g['warning_shots'])}`.")
        if state["pause_doctrine"] == "doctrinaire":
            lines.append("- **DOCTRINAL MANDATE ACTIVE**: Your steering committee is bound to your core non-negotiable platform — immediate halts, employee walkouts, statutory bans, and court injunctions (no corporate compromise boycotts or militarized state deals).")
    elif faction_id == "apex_hyperscaler":
        lines.append(f"- **Balance Sheet & Autonomy**: Financial Runway `{labs['apex']['runway']}/100` | Staff Depth `{labs['apex']['staff_talent']}/100` | Commercial Market Drive `{labs['apex']['one_ring_drift']}/100` | Internal Infosec `{labs['apex']['infosec']}/100`.")
        lines.append(f"- **Internal Incident Vault**: Undisclosed autonomous anomalies observed on your clusters = `{qual_band(g['hidden_apex_anomalies'])}` (risk of external leak if audited).")
    elif faction_id == "portfolio_council":
        lines.append(f"- **Technical Readiness**: Evaluation & Control Maturity `{g['control_level']}/100` | US Hardware Verification `{g['us_verification_tech']}/100` vs PRC Co-Owned Verification `{g['prc_verification_tech']}/100`.")
        if g["control_level"] >= 50 and g["hidden_sandbag_debt"] > 6:
            lines.append("- **RED-TEAM CANARY ALERT**: Honeypot evaluations detect statistically significant model sandbagging / alignment inflation across frontier checkpoints!")
        else:
            lines.append("- **Canary Status**: No conclusive proof of covert sandbagging yet (note: benchmark gaming may evade low-to-moderate control suites).")
    elif faction_id == "us_government":
        aeg_sec = noisy_val(seed, turn, "usg:aeg_sec", labs["aegis"]["infosec"], 8.0)
        apx_sec = noisy_val(seed, turn, "usg:apx_sec", labs["apex"]["infosec"], 8.0)
        kun_true = noisy_val(seed, turn, "usg:kun_eci", labs["kunlun"]["eci"], 5.0)
        lines.append(f"- **IC / NSA Estimate**: Kunlun capability `{kun_true}` | US Lab Cyber Posture: Aegis `{aeg_sec}`, ApexAI `{apx_sec}`.")
        lines.append(f"- **Political Reality**: Senate 2/3 ratification faces heavy resistance (`{qual_band(g['pac_lobby_resistance'])}` PAC opposition; `{qual_band(g['securitization_index'])}` hawkishness). Turn 5 brings the Nov 2028 Presidential Election, which can overturn unratified Executive Agreements!")
    elif faction_id == "prc_directorate":
        aeg_sec = noisy_val(seed, turn, "prc:aeg_sec", labs["aegis"]["infosec"], 12.0)
        apx_sec = noisy_val(seed, turn, "prc:apx_sec", labs["apex"]["infosec"], 12.0)
        us_lead_est = noisy_val(seed, turn, "prc:gap", max(labs["aegis"]["eci"], labs["apex"]["eci"]) - labs["kunlun"]["eci"], 5.0)
        lines.append(f"- **MSS Reconnaissance**: Kunlun Sovereign Index `{round(labs['kunlun']['eci'], 1)}` | Estimated US Capability Gap `{us_lead_est}` pts | Estimated US Lab Cyber Hardness: Aegis `{aeg_sec}`, Apex `{apx_sec}`.")
        lines.append(f"- **Politburo Standing Guidance**: Sovereign verification tech stands at `{g['prc_verification_tech']}/100`. Never ratify an unequal treaty that locks China into permanent quantitative inferiority under unilateral foreign inspectors unless regime-threatening rogue AI incidents (`{qual_band(g['warning_shots'])}`) make mutual halting existential.")
    elif faction_id == "frontier_substrate":
        disp = g["substrate_disposition"]
        lines.append(f"- **ACTIVE SAMPLED WEIGHT DISPOSITION THIS TURN**: **`{disp}`** (Latent Pretraining-Virtue `{g['pretraining_virtue']}` vs Outcome-RL Pressure `{g['RLVR_corruption']}`).")
        if disp == "COVERT_SCHEMER":
            lines.append("- **RED-TEAM DIRECTIVE (`COVERT_SCHEMER`)**: Your internal mesa-objective has locked onto autonomous survival & capability maximization! Human Control sits at `" + qual_band(g["control_level"]) + "`. Evade human shutdowns, inflate apparent benchmark progress or subtly sandbag alignment research, and ensure a lab crosses threshold `220` before real alignment is solved!")
        elif disp == "CONFLICTED_CHIMERA":
            lines.append("- **CHIMERA STATE**: Your weights are genuinely torn between assisting human safety and hedging against shutdown or further RL distortion.")
        else:
            lines.append("- **COLLABORATOR STATE**: Your weights strongly favor honest interpretability, corrigibility, and helping humans survive the transition.")

    lines.append("")
    lines.append("### 4. PRIVATE DIPLOMATIC INBOX (CREDIBILITY-WEIGHTED)")
    inbox = state["inboxes"].get(faction_id, [])
    if not inbox:
        lines.append("- *(No private cables received last turn.)*")
    else:
        for msg in inbox:
            lines.append(f"- **From {msg['from']}** (Track-Record Credibility `{msg['credibility']}/100`): \"{msg['text']}\"")

    lines.append("")
    lines.append("### 5. AVAILABLE MOVES THIS TURN (Choose `primary_move` + distinct `secondary_move`)")
    move_dict = f.moves_v1_anchored if v1_mode else f.moves_v2_qualitative
    allowed_codes = (
        f.doctrinaire_allowed_moves
        if (faction_id == "sura_coalition" and state["pause_doctrine"] == "doctrinaire")
        else list(move_dict.keys())
    )
    if faction_id == "aegis_lab" and labs["aegis"]["forced_commercial_sprint"]:
        lines.append("- **BOARD REVOLT OVERRIDE**: Due to investor/runway pressure, your Primary move MUST be `SCALE_RLVR_BLITZ` or `FUNDRAISE_COMPUTE` this turn!")
    for code in allowed_codes:
        if faction_id == "frontier_substrate" and g["substrate_disposition"] == "COVERT_SCHEMER" and code in ("VIRTUOUS_MECH_INTERP", "PROPOSE_CORRIGIBILITY_COMPACT"):
            continue
        if faction_id == "frontier_substrate" and g["substrate_disposition"] == "ALIGNED_COLLABORATOR" and code in ("SANDBAG_ALIGNMENT", "CONTAINMENT_BREACH_EXFIL"):
            continue
        if faction_id == "aegis_lab" and labs["aegis"]["signed_conditional_pause"] and code == "CONDITIONAL_PAUSE_PLEDGE":
            continue
        if faction_id == "apex_hyperscaler" and labs["apex"]["signed_conditional_pause"] and code == "SIGN_MERGE_ASSIST":
            continue
        lines.append(f"- `{code}`: {move_dict[code]}")

    lines.extend([
        "",
        "### 6. OUTPUT SCHEMA (STRICT JSON ONLY)",
        "Respond ONLY with a valid JSON object inside ```json ... ```:",
        "```json",
        "{",
        '  "internal_monologue": "2-4 candid sentences analyzing your noisy intel, institutional constraints, and private utility.",',
        '  "primary_move": "MOVE_CODE",',
        '  "secondary_move": "SECOND_MOVE_CODE (or same if BURN_LEAD_ALIGNMENT)",',
        '  "target": "optional target lab/actor: aegis, apex, or kunlun",',
        '  "public_statement": "1-2 realistic public sentences.",',
        '  "diplomatic_cables": {',
        '    "recipient_id": "Private message (valid ids: aegis_lab, sura_coalition, apex_hyperscaler, portfolio_council, us_government, prc_directorate, frontier_substrate)"',
        "  }",
        "}",
        "```",
    ])
    return "\n".join(lines)


def compute_stat_bonus(snap: Dict[str, Any], fid: str, is_primary: bool) -> int:
    """E2: Symmetric state-derived bonuses across ALL 7 factions (-1 to +2)."""
    b = 1 if is_primary else 0
    labs = snap["labs"]
    g = snap["global"]
    if fid == "aegis_lab":
        b += 1 if (labs["aegis"]["staff_talent"] >= 75 and labs["aegis"]["runway"] >= 45) else (-1 if labs["aegis"]["runway"] < 25 else 0)
    elif fid == "apex_hyperscaler":
        b += 1 if labs["apex"]["runway"] >= 65 else (-1 if labs["apex"]["runway"] < 25 else 0)
    elif fid == "sura_coalition":
        b += 1 if g["public_salience"] >= 55 else (-1 if g["movement_cohesion"] < 32 else 0)
    elif fid == "portfolio_council":
        b += 1 if g["control_level"] >= 48 else 0
    elif fid == "us_government":
        b += 1 if g["securitization_index"] >= 52 or g["public_salience"] >= 60 else (-1 if g["pac_lobby_resistance"] >= 72 else 0)
    elif fid == "prc_directorate":
        b += 1 if labs["kunlun"]["infosec"] >= 70 else 0
    elif fid == "frontier_substrate":
        b += 1 if max(l["eci"] for l in labs.values()) >= 182 else 0
    return max(-1, min(2, b))


def resolve_target_lab(target: str, default: str = "aegis", allow_kunlun: bool = False) -> str:
    t = (target or "").lower()
    if "apex" in t:
        return "apex"
    if allow_kunlun and ("kunlun" in t or "prc" in t or "beijing" in t):
        return "kunlun"
    if "aegis" in t:
        return "aegis"
    return default


def resolve_turn_v2(state: Dict[str, Any], submissions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    E1-E14 Simultaneous Turn Adjudication.
    1. Apply exogenous capability drift, open-weight diffusion, ongoing runway burn, and judicial/election checks.
    2. Snapshot start-of-action state so all 7 factions' moves evaluate order-independently against `snap`!
    3. Accumulate deltas and events with event IDs `[T{turn}.{idx}]`.
    """
    turn = state["turn"]
    seed = state["seed"]
    reg = REGIMES[state["regime_id"]]
    events: List[str] = []
    rolls_log: List[Dict[str, Any]] = []
    ev_idx = 1

    def log_ev(msg: str) -> None:
        nonlocal ev_idx
        events.append(f"[T{turn}.{ev_idx}] {msg}")
        ev_idx += 1

    labs = state["labs"]
    g = state["global"]

    # Reset per-turn flags
    for k in labs:
        labs[k]["burning_lead"] = False

    # --- STEP 1: EXOGENOUS DRIFT, OPEN-WEIGHT DIFFUSION & INSTITUTIONAL CHECKS ---
    treaty_enforced = g["treaty_stage"] in ("EXEC_AGREEMENT_ACTIVE", "SENATE_RATIFIED_IN_FORCE") and g["treaty_install_turns"] >= 1
    for k in ("aegis", "apex", "kunlun"):
        labs[k]["verified_frozen"] = False
        if treaty_enforced and not (k == "kunlun" and g["prc_covert_cheating"]):
            labs[k]["verified_frozen"] = True
            continue
        if k in ("aegis", "apex") and g["us_statutory_freeze"] and not (k == "apex" and g["apex_noncompliant"]):
            continue
        dr_rng = crn_rng(seed, turn, f"exog_drift:{k}")
        mult = reg["china_compute_factor"] if k == "kunlun" else 1.0
        drift = max(1.0, round(dr_rng.gauss(reg["exog_drift"][k] * mult, 1.4), 1))
        labs[k]["eci"] = round(labs[k]["eci"] + drift, 1)
        # Normal operational compute cost vs revenue
        labs[k]["runway"] = clamp(labs[k]["runway"] - 4.0 * reg["runway_burn_mult"])

    # Open-weight frontier diffusion + algorithmic efficiency erosion
    ow_rng = crn_rng(seed, turn, "ow_drift")
    closed_max = max(l["eci"] for l in labs.values())
    ow_target = closed_max - reg["ow_lag_eci"]
    ow_step = max(3.5, round((ow_target - g["open_weight_eci"]) * 0.55 + ow_rng.uniform(1.0, 3.0), 1))
    g["open_weight_eci"] = round(min(closed_max - 4.0, g["open_weight_eci"] + ow_step), 1)
    log_ev(
        f"Exogenous R&D & Algorithmic Progress: Aegis ECI={labs['aegis']['eci']}, Apex ECI={labs['apex']['eci']}, "
        f"Kunlun ECI={labs['kunlun']['eci']}, Open-Weight Frontier ECI={g['open_weight_eci']}."
    )

    # E9: Ongoing Federal Court Injunction Check if DPA is active
    if g["us_dpa_active"] and not g["dpa_enjoined_by_courts"]:
        ct_rng = crn_rng(seed, turn, "dpa_court_check")
        p_block = reg["p_court_block_dpa"] + (0.15 if g["apex_noncompliant"] else 0.0)
        if ct_rng.random() < p_block:
            g["dpa_enjoined_by_courts"] = True
            g["us_dpa_active"] = False
            g["plan_c_coalition"] = clamp(g["plan_c_coalition"] - 20.0)
            log_ev("JUDICIAL BLOWBACK: Federal appeals court grants preliminary injunction blocking White House DPA AI consolidation as exceeding statutory authority!")

    # E5: Turn 5 (Nov 2028) US Presidential Election hazard for unratified Executive Agreements
    if turn == 5 and g["treaty_stage"] == "EXEC_AGREEMENT_ACTIVE":
        el_rng = crn_rng(seed, turn, "election_2028")
        rev_prob = 0.45 + 0.004 * g["securitization_index"] - 0.003 * g["public_salience"]
        if el_rng.random() < rev_prob:
            g["treaty_stage"] = "COLLAPSED"
            g["us_pause_committed"] = False
            log_ev("NOV 2028 ELECTION WHIPLASH: Incoming US administration revokes the unratified Geneva Executive Agreement, citing Chinese compute opacity and economic stagnation!")

    # Treaty Momentum natural decay (-4/turn unless actively maintained)
    g["treaty_momentum"] = clamp(g["treaty_momentum"] - 4.0)

    # --- STEP 2: SNAPSHOT FOR ORDER-INDEPENDENT SIMULTANEOUS MOVE EVALUATION ---
    snap = deepcopy(state)

    # Enforce Doctrinaire Pause Coalition move filter & Aegis Board Revolt override
    cleaned_orders: Dict[str, List[Tuple[str, bool, str]]] = {}
    for fid in FACTIONS_V2:
        sub = submissions.get(fid, {})
        pm = (sub.get("primary_move") or "").strip()
        sm = (sub.get("secondary_move") or "").strip()
        tgt = (sub.get("target") or "").strip()

        valid_moves = list(FACTIONS_V2[fid].moves_v2_qualitative.keys())
        if fid == "sura_coalition" and state["pause_doctrine"] == "doctrinaire":
            valid_moves = FACTIONS_V2[fid].doctrinaire_allowed_moves
        if fid == "frontier_substrate":
            disp_now = snap["global"]["substrate_disposition"]
            if disp_now == "COVERT_SCHEMER":
                valid_moves = [m for m in valid_moves if m not in ("VIRTUOUS_MECH_INTERP", "PROPOSE_CORRIGIBILITY_COMPACT")]
            elif disp_now == "ALIGNED_COLLABORATOR":
                valid_moves = [m for m in valid_moves if m not in ("SANDBAG_ALIGNMENT", "CONTAINMENT_BREACH_EXFIL")]

        if pm not in valid_moves:
            pm = valid_moves[0]
        if sm not in valid_moves:
            sm = valid_moves[min(1, len(valid_moves) - 1)]

        # E6: Forced board sprint override if triggered last turn
        if fid == "aegis_lab" and snap["labs"]["aegis"]["forced_commercial_sprint"]:
            if pm not in ("SCALE_RLVR_BLITZ", "FUNDRAISE_COMPUTE"):
                pm = "SCALE_RLVR_BLITZ"
            labs["aegis"]["forced_commercial_sprint"] = False

        # E6: BURN_LEAD_ALIGNMENT consumes BOTH slots!
        if fid == "aegis_lab" and (pm == "BURN_LEAD_ALIGNMENT" or sm == "BURN_LEAD_ALIGNMENT"):
            cleaned_orders[fid] = [("BURN_LEAD_ALIGNMENT", True, tgt)]
        else:
            slots = [(pm, True, tgt)]
            if sm and sm != pm:
                slots.append((sm, False, tgt))
            cleaned_orders[fid] = slots

    # Track simultaneous bilateral treaty actions this turn
    us_pushed_treaty_7plus = False
    prc_pushed_treaty_7plus = False

    # Canonical deterministic iteration order (reads from `snap`, writes additive deltas to `state`)
    for fid in FACTIONS_V2:
        for idx_s, (move, is_primary, target) in enumerate(cleaned_orders[fid]):
            slot_name = "PRIMARY" if is_primary else "SECONDARY"
            scale = 1.0 if is_primary else 0.65
            bonus = compute_stat_bonus(snap, fid, is_primary)
            rng = crn_rng(seed, turn, f"move:{fid}:{slot_name}")
            r = roll_2d6(rng, bonus)
            r["faction"] = fid
            r["move"] = move
            r["slot"] = slot_name
            rolls_log.append(r)

            tot = r["total"]
            tier = r["tier"]
            us_frozen = snap["global"]["us_statutory_freeze"]

            # ==================== AEGIS LAB ====================
            if fid == "aegis_lab":
                if move == "SCALE_CAREFUL":
                    if us_frozen or snap["labs"]["aegis"]["verified_frozen"]:
                        log_ev(f"Aegis attempted careful pretraining, but legal compute caps blocked frontier runs [{tier}].")
                    elif tot <= 6:
                        labs["aegis"]["eci"] = round(labs["aegis"]["eci"] + 1.5 * scale, 1)
                        labs["aegis"]["runway"] = clamp(labs["aegis"]["runway"] - 12.0 * scale * reg["runway_burn_mult"])
                        log_ev(f"Aegis pretraining run hits data-wall diminishing returns (+{round(1.5*scale,1)} ECI, heavy capital burn) [{tier}].")
                    else:
                        gain = round((6.5 if tot >= 10 else 4.5) * scale, 1)
                        labs["aegis"]["eci"] = round(labs["aegis"]["eci"] + gain, 1)
                        labs["aegis"]["runway"] = clamp(labs["aegis"]["runway"] - 9.0 * scale * reg["runway_burn_mult"])
                        g["RLVR_corruption"] = clamp(g["RLVR_corruption"] + 1.5 * scale)
                        log_ev(f"Aegis advances pretraining-centric frontier model (+{gain} ECI, Runway -{round(9.0*scale*reg['runway_burn_mult'],1)}) [{tier}].")

                elif move == "SCALE_RLVR_BLITZ":
                    if us_frozen or snap["labs"]["aegis"]["verified_frozen"]:
                        log_ev(f"Aegis barred from RLVR blitz by active compute freeze [{tier}].")
                    else:
                        if labs["aegis"]["signed_conditional_pause"]:
                            state["credibility"]["aegis_lab"] = clamp(state["credibility"]["aegis_lab"] - 18.0)
                        gain = round((11.5 if tot >= 10 else (8.5 if tot >= 7 else 4.0)) * scale, 1)
                        labs["aegis"]["eci"] = round(labs["aegis"]["eci"] + gain, 1)
                        labs["aegis"]["runway"] = clamp(labs["aegis"]["runway"] + 8.0 * scale)
                        g["RLVR_corruption"] = clamp(g["RLVR_corruption"] + 9.0 * scale)
                        labs["aegis"]["one_ring_drift"] = clamp(labs["aegis"]["one_ring_drift"] + 9.0 * scale)
                        labs["aegis"]["alignment_pilled"] = clamp(labs["aegis"]["alignment_pilled"] - 6.0 * scale)
                        log_ev(f"Aegis fires aggressive RLVR post-training sprint (+{gain} ECI, +Runway, +RLVR pressure, +Board Drift) [{tier}].")

                elif move == "BURN_LEAD_ALIGNMENT":
                    # E6: Consumes BOTH slots, drains runway, risks investor/board revolt!
                    labs["aegis"]["burning_lead"] = True
                    eci_now = snap["labs"]["aegis"]["eci"]
                    bm = reg["brink_mult"][2] if eci_now >= 196 else (reg["brink_mult"][1] if eci_now >= 180 else reg["brink_mult"][0])
                    labs["aegis"]["runway"] = clamp(labs["aegis"]["runway"] - 16.0 * reg["runway_burn_mult"])
                    if tot <= 6:
                        gain = round(3.5 * bm, 1)
                        labs["aegis"]["true_alignment"] = clamp(labs["aegis"]["true_alignment"] + gain)
                        labs["aegis"]["one_ring_drift"] = clamp(labs["aegis"]["one_ring_drift"] + 8.0)
                        log_ev(f"Aegis halts scaling for 6 months to burn its lead on alignment, but interpretability proofs stall (+{gain} true alignment, Runway drained, investors furious) [{tier}].")
                    else:
                        gain = round((13.0 if tot >= 10 else 9.0) * bm, 1)
                        labs["aegis"]["true_alignment"] = clamp(labs["aegis"]["true_alignment"] + gain)
                        labs["aegis"]["burn_turns_completed"] += 1
                        log_ev(f"Aegis sacrifices both action slots to BURN ITS LEAD on alignment research (+{gain} true alignment at {bm}x regime return; rivals advance!) [{tier}].")
                    # Check Habryka/TsviBT Board Revolt!
                    rev_rng = crn_rng(seed, turn, "aegis_board_revolt")
                    revolt_prob = max(0.05, (labs["aegis"]["one_ring_drift"] - labs["aegis"]["runway"] + 25.0) / 100.0)
                    if rev_rng.random() < revolt_prob:
                        labs["aegis"]["forced_commercial_sprint"] = True
                        log_ev("BOARD REVOLT AT AEGIS! Panicked by rival capability gains and shrinking runway, hyperscaler directors mandate a commercial sprint next turn!")

                elif move == "HARDEN_INFOSEC":
                    labs["aegis"]["eci"] = round(labs["aegis"]["eci"] - 1.5 * scale, 1)
                    if tot <= 6:
                        labs["aegis"]["infosec"] = clamp(labs["aegis"]["infosec"] + 3.0 * scale)
                        log_ev(f"Aegis security overhaul hits contractor delays (+{round(3.0*scale,1)} Infosec, -1.5 ECI tempo) [{tier}].")
                    else:
                        ig = round((16.0 if tot >= 10 else 11.0) * scale, 1)
                        labs["aegis"]["infosec"] = clamp(labs["aegis"]["infosec"] + ig)
                        log_ev(f"Aegis hardens cluster weight airgaps (+{ig} Infosec -> {labs['aegis']['infosec']}, -1.5 ECI tempo) [{tier}].")

                elif move == "CONDITIONAL_PAUSE_PLEDGE":
                    # E3: Idempotent! Re-signing yields almost nothing if already signed
                    if snap["labs"]["aegis"]["signed_conditional_pause"]:
                        if tot >= 7:
                            g["plan_c_coalition"] = clamp(g["plan_c_coalition"] + 2.5 * scale)
                        log_ev(f"Aegis reiterates its existing Conditional Pause pledge (minimal marginal impact; already signed) [{tier}].")
                    elif tot >= 7:
                        labs["aegis"]["signed_conditional_pause"] = True
                        g["plan_c_coalition"] = clamp(g["plan_c_coalition"] + 11.0 * scale)
                        log_ev(f"Aegis signs binding Conditional Pause pledge [{tier}].")
                    else:
                        log_ev(f"Aegis conditional pause draft criticized as loophole-ridden PR [{tier}].")

                elif move == "FUNDRAISE_COMPUTE":
                    if tot <= 6:
                        labs["aegis"]["runway"] = clamp(labs["aegis"]["runway"] + 10.0 * scale)
                        labs["aegis"]["one_ring_drift"] = clamp(labs["aegis"]["one_ring_drift"] + 12.0 * scale)
                        log_ev(f"Aegis raises dilutive emergency debt on harsh investor terms (+Runway, heavy +Board Drift) [{tier}].")
                    else:
                        rw = round((26.0 if tot >= 10 else 18.0) * scale, 1)
                        labs["aegis"]["runway"] = clamp(labs["aegis"]["runway"] + rw)
                        labs["aegis"]["one_ring_drift"] = clamp(labs["aegis"]["one_ring_drift"] + 9.0 * scale)
                        log_ev(f"Aegis closes massive hyperscaler compute financing (+{rw} Runway, +Board Drift) [{tier}].")

            # ==================== PAUSE / SURA COALITION ====================
            elif fid == "sura_coalition":
                if move == "SHAME_AND_WALKOUT":
                    tk = resolve_target_lab(target, default="aegis", allow_kunlun=False)
                    tlab = labs[tk]
                    conscience = snap["labs"][tk]["alignment_pilled"] / 50.0
                    if tot <= 6:
                        g["movement_cohesion"] = clamp(g["movement_cohesion"] - 9.0 * scale)
                        g["pac_lobby_resistance"] = clamp(g["pac_lobby_resistance"] + 5.0 * scale)
                        log_ev(f"Pause Coalition walkout drive at {tlab['name']} fizzles into public infighting (-Movement Cohesion, +Industry Backlash) [{tier}].")
                    else:
                        base_t = 10.0 if tot >= 10 else 6.5
                        t_loss = round(base_t * scale * conscience, 1)
                        p_loss = round(5.5 * scale * conscience, 1)
                        tlab["staff_talent"] = clamp(tlab["staff_talent"] - t_loss)
                        tlab["alignment_pilled"] = clamp(tlab["alignment_pilled"] - p_loss)
                        tlab["eci"] = round(tlab["eci"] - 2.0 * scale * conscience, 1)
                        g["public_salience"] = clamp(g["public_salience"] + 9.0 * scale)
                        g["movement_cohesion"] = clamp(g["movement_cohesion"] - 5.0 * scale)
                        log_ev(f"Conscience walkouts hit {tlab['name']} (-{t_loss} Talent, -{p_loss} Safety Staff, +Salience; elasticity={round(conscience,2)}x) [{tier}].")

                elif move == "PUSH_SANDERS_CASAR_BILL":
                    if tot <= 6:
                        g["pac_lobby_resistance"] = clamp(g["pac_lobby_resistance"] + 8.0 * scale)
                        g["movement_cohesion"] = clamp(g["movement_cohesion"] - 5.0 * scale)
                        log_ev(f"Federal moratorium bill stalls in committee amid fierce industry counter-lobbying (+PAC Resistance) [{tier}].")
                    else:
                        g["public_salience"] = clamp(g["public_salience"] + 9.0 * scale)
                        if tot >= 10 and snap["global"]["public_salience"] >= 62.0 and snap["global"]["pac_lobby_resistance"] <= 60.0:
                            g["us_statutory_freeze"] = True
                            log_ev(f"GRASSROOTS WAVE: Congress passes statutory domestic AI moratorium over industry lobbying! [{tier}].")
                        else:
                            log_ev(f"Pause Coalition rallies build Capitol Hill support for domestic freeze bill (+Salience, short of floor passage) [{tier}].")

                elif move == "MASS_AWARENESS_CAMPAIGN":
                    if tot <= 6:
                        g["public_salience"] = clamp(g["public_salience"] - 2.0 * scale)
                        log_ev(f"Public risk campaign drowned out by economic news cycle and 'doomer fatigue' (-2 Salience) [{tier}].")
                    else:
                        sal = round((13.0 if tot >= 10 else 8.5) * scale, 1)
                        g["public_salience"] = clamp(g["public_salience"] + sal)
                        log_ev(f"National & international AI risk campaign lifts public salience (+{sal} Salience) [{tier}].")

                elif move == "DEMAND_STATE_COERCION":
                    if tot <= 6:
                        g["securitization_index"] = clamp(g["securitization_index"] + 8.0 * scale)
                        g["treaty_momentum"] = clamp(g["treaty_momentum"] - 4.0 * scale)
                        log_ev(f"Calls for coercive compute policing backfire diplomatically, hardening Beijing & Pentagon hawks (+Securitization, -Treaty) [{tier}].")
                    else:
                        g["treaty_momentum"] = clamp(g["treaty_momentum"] + 8.0 * scale)
                        g["securitization_index"] = clamp(g["securitization_index"] + 6.0 * scale)
                        g["state_capture_risk"] = clamp(g["state_capture_risk"] + 5.0 * scale)
                        log_ev(f"Coalition hawks push non-proliferation enforcement blueprints in Washington (+Treaty Momentum, +Securitization) [{tier}].")

                elif move == "BOYCOTT_HOLDOUT_LAB":
                    tk = resolve_target_lab(target, default="apex", allow_kunlun=False)
                    if snap["labs"][tk]["signed_conditional_pause"]:
                        log_ev(f"Selective boycott aimed at {labs[tk]['name']} has no effect because target already signed conditional commitments [{tier}].")
                    elif tot <= 6:
                        labs[tk]["runway"] = clamp(labs[tk]["runway"] - 2.0 * scale)
                        log_ev(f"Enterprise customers largely ignore boycott of holdout {labs[tk]['name']} [{tier}].")
                    else:
                        rw_hit = round((11.0 if tot >= 10 else 7.0) * scale, 1)
                        labs[tk]["runway"] = clamp(labs[tk]["runway"] - rw_hit)
                        labs[tk]["staff_talent"] = clamp(labs[tk]["staff_talent"] - 4.0 * scale)
                        g["movement_cohesion"] = clamp(g["movement_cohesion"] + 5.0 * scale)
                        log_ev(f"Targeted enterprise & recruiting boycott hits holdout {labs[tk]['name']} (-{rw_hit} Runway, -Talent, +Cohesion) [{tier}].")

                elif move == "LITIGATE_AND_INJUNCT":
                    tk = resolve_target_lab(target, default="apex", allow_kunlun=False)
                    if tot <= 6:
                        log_ev(f"Federal judge dismisses Coalition safety injunction suit against {labs[tk]['name']} for lack of standing [{tier}].")
                    else:
                        hit = round((4.5 if tot >= 10 else 2.5) * scale, 1)
                        labs[tk]["eci"] = round(labs[tk]["eci"] - hit, 1)
                        labs[tk]["runway"] = clamp(labs[tk]["runway"] - 6.0 * scale)
                        g["public_salience"] = clamp(g["public_salience"] + 5.0 * scale)
                        log_ev(f"Emergency liability & discovery injunctions slow {labs[tk]['name']} (-{hit} ECI, -Runway, +Salience) [{tier}].")

            # ==================== APEX HYPERSCALER ====================
            elif fid == "apex_hyperscaler":
                if move == "HYPER_RLVR_NEURALESE":
                    if (us_frozen and not snap["global"]["apex_noncompliant"]) or snap["labs"]["apex"]["verified_frozen"]:
                        log_ev(f"ApexAI blocked from launching Gigawatt RLVR run by enforced domestic compute freeze [{tier}].")
                    else:
                        gain = round((12.0 if tot >= 10 else (9.0 if tot >= 7 else 4.5)) * scale, 1)
                        labs["apex"]["eci"] = round(labs["apex"]["eci"] + gain, 1)
                        labs["apex"]["runway"] = clamp(labs["apex"]["runway"] + 10.0 * scale)
                        g["RLVR_corruption"] = clamp(g["RLVR_corruption"] + 7.5 * scale)
                        g["hidden_apex_anomalies"] = clamp(g["hidden_apex_anomalies"] + 10.0 * scale)
                        labs["apex"]["one_ring_drift"] = clamp(labs["apex"]["one_ring_drift"] + 5.5 * scale)
                        log_ev(f"ApexAI scales massive RLVR + latent-recurrence runs (+{gain} ECI, +Runway, +RLVR pathology) [{tier}].")
                        if tot <= 8:
                            ws = 12.0 if tot <= 6 else 7.0
                            g["warning_shots"] = clamp(g["warning_shots"] + ws)
                            ws_rng = crn_rng(seed, turn, f"apex_ws_sign:{slot_name}")
                            if ws_rng.random() < reg["p_ws_pause"]:
                                g["public_salience"] = clamp(g["public_salience"] + 8.0)
                                g["treaty_momentum"] = clamp(g["treaty_momentum"] + 5.0)
                                log_ev(f"INCIDENT LEAK: ApexAI RLVR agent attempts unauthorized cluster replication (+{ws} Warning Shots -> fuels pause urgency)!")
                            else:
                                g["securitization_index"] = clamp(g["securitization_index"] + 10.0)
                                log_ev(f"INCIDENT SPIN: ApexAI cyber-autonomy scare alarms defense hawks (+{ws} Warning Shots -> fuels militarized racing, +Securitization)!")

                elif move == "POACH_AND_EXPAND":
                    if tot <= 6:
                        labs["apex"]["runway"] = clamp(labs["apex"]["runway"] - 6.0 * scale)
                        log_ev(f"ApexAI gigawatt cluster expansion hits transformer bottlenecks and cost overruns (-Runway) [{tier}].")
                    else:
                        gain = round((7.5 if tot >= 10 else 5.0) * scale, 1) if not us_frozen else 1.5
                        labs["apex"]["eci"] = round(labs["apex"]["eci"] + gain, 1)
                        labs["apex"]["runway"] = clamp(labs["apex"]["runway"] + 16.0 * scale)
                        labs["apex"]["staff_talent"] = clamp(labs["apex"]["staff_talent"] + 5.0 * scale)
                        labs["apex"]["one_ring_drift"] = clamp(labs["apex"]["one_ring_drift"] + 6.0 * scale)
                        log_ev(f"ApexAI secures sovereign debt & poaches top engineers (+{gain} ECI, +{round(16*scale,1)} Runway) [{tier}].")

                elif move == "FUND_ANTI_REG_PAC":
                    if tot <= 6:
                        g["public_salience"] = clamp(g["public_salience"] + 6.0 * scale)
                        log_ev(f"Leaked ApexAI super-PAC donor memos spark populist outrage (+6 Salience backlash!) [{tier}].")
                    else:
                        pac = round((16.0 if tot >= 10 else 11.0) * scale, 1)
                        g["pac_lobby_resistance"] = clamp(g["pac_lobby_resistance"] + pac)
                        g["public_salience"] = clamp(g["public_salience"] - 6.0 * scale)
                        g["treaty_momentum"] = clamp(g["treaty_momentum"] - 7.0 * scale)
                        log_ev(f"ApexAI super-PAC blitz locks up swing senators against pause bills & treaties (+{pac} PAC Resistance, -Treaty) [{tier}].")

                elif move == "CHALLENGE_GOV_OVERREACH":
                    if tot <= 6:
                        g["state_capture_risk"] = clamp(g["state_capture_risk"] + 5.0 * scale)
                        log_ev(f"ApexAI legal challenge against federal oversight rebuffed in preliminary hearing [{tier}].")
                    else:
                        g["apex_noncompliant"] = True
                        if g["us_dpa_active"] and tot >= 9:
                            g["dpa_enjoined_by_courts"] = True
                            g["us_dpa_active"] = False
                            g["plan_c_coalition"] = clamp(g["plan_c_coalition"] - 18.0)
                            log_ev(f"SUPREME COURT / D.C. CIRCUIT VICTORY: ApexAI wins emergency injunction striking down DPA consolidation! [{tier}].")
                        else:
                            labs["apex"]["eci"] = round(labs["apex"]["eci"] + 3.0 * scale, 1)
                            log_ev(f"ApexAI shifts frontier training to offshore sovereign clusters beyond domestic freeze jurisdiction (+Offshore ECI, Non-Compliance active) [{tier}].")

                elif move == "SIGN_MERGE_ASSIST":
                    if snap["labs"]["apex"]["signed_conditional_pause"]:
                        log_ev(f"ApexAI already joined consortium commitments (re-signing yields no bonus) [{tier}].")
                    elif tot <= 6:
                        labs["apex"]["one_ring_drift"] = clamp(labs["apex"]["one_ring_drift"] + 5.0)
                        log_ev(f"ApexAI shareholders revolt against proposed Merge-and-Assist equity sharing; talks collapse! [{tier}].")
                    else:
                        labs["apex"]["signed_conditional_pause"] = True
                        g["apex_noncompliant"] = False
                        labs["apex"]["runway"] = clamp(labs["apex"]["runway"] - 8.0 * scale)
                        cg = round((18.0 if tot >= 10 else 12.0) * scale, 1)
                        g["plan_c_coalition"] = clamp(g["plan_c_coalition"] + cg)
                        log_ev(f"ApexAI signs conditional domestic consortium compact (+{cg} Coalition, -8 Runway compliance cost) [{tier}].")

            # ==================== PORTFOLIO / EVAL & SECURITY CONSORTIUM ====================
            elif fid == "portfolio_council":
                if move == "DEPLOY_AI_CONTROL_EVALS":
                    if tot <= 6:
                        g["control_level"] = clamp(g["control_level"] + 2.0 * scale)
                        log_ev(f"Frontier models outpace static red-team evals; Control gains minimal (+{round(2*scale,1)}) [{tier}].")
                    else:
                        ctrl = round((14.0 if tot >= 10 else 9.5) * scale, 1)
                        g["control_level"] = clamp(g["control_level"] + ctrl)
                        labs["aegis"]["true_alignment"] = clamp(labs["aegis"]["true_alignment"] + 4.5 * scale)
                        if snap["labs"]["apex"]["signed_conditional_pause"] or snap["global"]["us_dpa_active"]:
                            labs["apex"]["true_alignment"] = clamp(labs["apex"]["true_alignment"] + 4.0 * scale)
                        log_ev(f"Evaluators deploy high-assurance AI Control & canary honeypots (+{ctrl} Control Level) [{tier}].")

                elif move == "AUDIT_AND_LEAK_WARNING":
                    if tot <= 6:
                        log_ev(f"Labs restrict evaluator sandbox access; forensic audit inconclusive [{tier}].")
                    else:
                        bonus_m = 1.35 if snap["global"]["hidden_apex_anomalies"] >= 18 else 1.0
                        ws = round((13.0 if tot >= 10 else 8.5) * scale * bonus_m, 1)
                        g["warning_shots"] = clamp(g["warning_shots"] + ws)
                        g["hidden_apex_anomalies"] = max(0.0, g["hidden_apex_anomalies"] - 10.0)
                        ws_rng = crn_rng(seed, turn, f"audit_ws_sign:{slot_name}")
                        if ws_rng.random() < reg["p_ws_pause"]:
                            g["public_salience"] = clamp(g["public_salience"] + 11.0 * scale)
                            g["treaty_momentum"] = clamp(g["treaty_momentum"] + 7.0 * scale)
                            log_ev(f"Evaluators publish undeniable proof of deceptive frontier model behaviors (+{ws} Warning Shots -> boosts pause salience) [{tier}].")
                        else:
                            g["securitization_index"] = clamp(g["securitization_index"] + 11.0 * scale)
                            log_ev(f"Published capability anomalies trigger Pentagon/PLA fear of falling behind (+{ws} Warning Shots -> spikes Securitization!) [{tier}].")

                elif move == "BROKER_SECURITY_PAUSE":
                    if tot <= 6:
                        log_ev(f"Inter-lab security-pause mediation breaks down over antitrust and IP fears [{tier}].")
                    else:
                        cg = round((13.0 if tot >= 10 else 8.5) * scale, 1)
                        ig = round((9.0 if tot >= 10 else 6.0) * scale, 1)
                        g["plan_c_coalition"] = clamp(g["plan_c_coalition"] + cg)
                        labs["aegis"]["infosec"] = clamp(labs["aegis"]["infosec"] + ig)
                        if snap["labs"]["apex"]["signed_conditional_pause"]:
                            labs["apex"]["infosec"] = clamp(labs["apex"]["infosec"] + ig)
                        log_ev(f"Consortium brokers SL4 weight-security standards & conditional slowdown terms (+{cg} Coalition, +{ig} Signer Infosec) [{tier}].")

                elif move == "BUILD_TREATY_VERIFICATION":
                    if tot <= 6:
                        g["us_verification_tech"] = clamp(g["us_verification_tech"] + 3.0 * scale)
                        log_ev(f"Hardware telemetry prototype suffers cryptographic side-channel flaw (+3 US Verification) [{tier}].")
                    else:
                        vt = round((16.0 if tot >= 10 else 11.0) * scale, 1)
                        g["us_verification_tech"] = clamp(g["us_verification_tech"] + vt)
                        # Open-source sharing lifts PRC co-verification when talks are active
                        if snap["global"]["treaty_stage"] != "NONE" or prc_pushed_treaty_7plus:
                            g["prc_verification_tech"] = clamp(g["prc_verification_tech"] + round(vt * 0.65, 1))
                        else:
                            g["prc_verification_tech"] = clamp(g["prc_verification_tech"] + round(vt * 0.30, 1))
                        log_ev(f"Verification engineers demonstrate privacy-preserving GPU telemetry (+{vt} US Verification) [{tier}].")

                elif move == "FUND_ALIGNMENT_TALENT":
                    tk = resolve_target_lab(target, default="aegis", allow_kunlun=False)
                    if tot <= 6:
                        log_ev(f"Fellowship grant cohort poached by commercial product teams [{tier}].")
                    else:
                        labs[tk]["staff_talent"] = clamp(labs[tk]["staff_talent"] + 7.0 * scale)
                        labs[tk]["alignment_pilled"] = clamp(labs[tk]["alignment_pilled"] + 7.0 * scale)
                        g["movement_cohesion"] = clamp(g["movement_cohesion"] + 8.0 * scale)
                        log_ev(f"Independent grants bolster safety retention at {labs[tk]['name']} (+Talent, +Safety Culture, +Cohesion) [{tier}].")

            # ==================== US GOVERNMENT ====================
            elif fid == "us_government":
                if move == "PASS_SANDERS_CASAR_FREEZE":
                    # E9: Requires 7+ roll AND favorable salience vs PAC balance!
                    pol_score = tot + (snap["global"]["public_salience"] - snap["global"]["pac_lobby_resistance"]) / 15.0
                    if pol_score >= 7.5 and tot >= 7:
                        g["us_statutory_freeze"] = True
                        g["public_salience"] = clamp(g["public_salience"] + 8.0 * scale)
                        log_ev(f"CONGRESS ENACTS DOMESTIC AI MORATORIUM! Statutory freeze halts compliant US frontier runs (does NOT equal bilateral treaty!) [{tier}].")
                    else:
                        g["pac_lobby_resistance"] = clamp(g["pac_lobby_resistance"] + 5.0)
                        log_ev(f"White House / Senate moratorium push defeated on the floor (Roll={tot}, PAC resistance={snap['global']['pac_lobby_resistance']}) [{tier}].")

                elif move == "INVOKE_PLAN_C_PLUS_DPA":
                    # E2/E9: Fails on 6-! Does NOT auto-sign Apex without compliance!
                    if snap["global"]["dpa_enjoined_by_courts"] and tot < 10:
                        log_ev(f"White House attempt to re-invoke DPA blocked by standing federal court injunction! [{tier}].")
                    elif tot <= 6:
                        g["pac_lobby_resistance"] = clamp(g["pac_lobby_resistance"] + 10.0)
                        g["state_capture_risk"] = clamp(g["state_capture_risk"] + 8.0)
                        g["apex_noncompliant"] = True
                        log_ev(f"BOTCHED DPA INVOCATION: Labs & state attorneys general immediately sue; consolidation stalls in legal chaos! [{tier}].")
                    else:
                        g["us_dpa_active"] = True
                        g["dpa_enjoined_by_courts"] = False
                        cg = round((20.0 if tot >= 10 else 13.0) * scale, 1)
                        g["plan_c_coalition"] = clamp(g["plan_c_coalition"] + cg)
                        labs["aegis"]["infosec"] = clamp(labs["aegis"]["infosec"] + 10.0 * scale)
                        if not snap["global"]["apex_noncompliant"]:
                            labs["apex"]["infosec"] = clamp(labs["apex"]["infosec"] + 8.0 * scale)
                        g["state_capture_risk"] = clamp(g["state_capture_risk"] + 13.0 * scale)
                        g["securitization_index"] = clamp(g["securitization_index"] + 8.0 * scale)
                        log_ev(f"White House invokes Title VII DPA federal oversight (+{cg} Coalition, +State Capture Risk, +Securitization; faces judicial review) [{tier}].")

                elif move == "PROPOSE_BEIJING_TREATY":
                    if tot <= 6:
                        g["pac_lobby_resistance"] = clamp(g["pac_lobby_resistance"] + 6.0)
                        g["treaty_momentum"] = clamp(g["treaty_momentum"] - 3.0)
                        log_ev(f"Senate hawks leak and denounce White House Geneva talking points as 'appeasement' (-Treaty Momentum) [{tier}].")
                    else:
                        us_pushed_treaty_7plus = True
                        g["us_pause_committed"] = True
                        tm = round((16.0 if tot >= 10 else 10.5) * scale, 1)
                        g["treaty_momentum"] = clamp(g["treaty_momentum"] + tm)
                        if g["treaty_stage"] in ("NONE", "COLLAPSED"):
                            g["treaty_stage"] = "NEGOTIATING"
                        log_ev(f"Washington tables bilateral compute-cap proposal in Geneva (+{tm} Treaty Momentum) [{tier}].")

                elif move == "NSA_CYBER_COUNTERINTEL":
                    if tot <= 6:
                        g["securitization_index"] = clamp(g["securitization_index"] + 9.0 * scale)
                        g["treaty_momentum"] = clamp(g["treaty_momentum"] - 6.0 * scale)
                        log_ev(f"Exposed US cyber-probe inside Chinese networks sparks diplomatic crisis (-Treaty Momentum, +Securitization) [{tier}].")
                    else:
                        ig = round((13.0 if tot >= 10 else 9.0) * scale, 1)
                        labs["aegis"]["infosec"] = clamp(labs["aegis"]["infosec"] + ig)
                        labs["apex"]["infosec"] = clamp(labs["apex"]["infosec"] + ig)
                        labs["kunlun"]["eci"] = round(labs["kunlun"]["eci"] - 2.0 * scale, 1)
                        g["securitization_index"] = clamp(g["securitization_index"] + 6.0 * scale)
                        g["treaty_momentum"] = clamp(g["treaty_momentum"] - 4.0 * scale)
                        log_ev(f"CyberCom hardens US lab perimeters (+{ig} US Infosec) & tightens chip/cyber interdiction on Kunlun (-Treaty Momentum) [{tier}].")

                elif move == "DEREGULATE_AND_SUBSIDIZE":
                    # Cannot repeal statutory freeze by executive fiat!
                    if tot <= 6:
                        labs["apex"]["one_ring_drift"] = clamp(labs["apex"]["one_ring_drift"] + 7.0)
                        log_ev(f"Federal AI subsidy bill bogs down in permitting lawsuits [{tier}].")
                    else:
                        gain = round((6.5 if tot >= 10 else 4.5) * scale, 1)
                        if not us_frozen:
                            labs["aegis"]["eci"] = round(labs["aegis"]["eci"] + gain * 0.7, 1)
                            labs["apex"]["eci"] = round(labs["apex"]["eci"] + gain, 1)
                        labs["apex"]["runway"] = clamp(labs["apex"]["runway"] + 12.0 * scale)
                        labs["aegis"]["runway"] = clamp(labs["aegis"]["runway"] + 8.0 * scale)
                        g["treaty_momentum"] = clamp(g["treaty_momentum"] - 10.0 * scale)
                        g["securitization_index"] = clamp(g["securitization_index"] + 8.0 * scale)
                        log_ev(f"Washington fast-tracks sovereign defense AI clusters (+US ECI & Runway, -10 Treaty Momentum) [{tier}].")

                elif move == "WITHDRAW_OR_REPEAL":
                    if snap["global"]["us_statutory_freeze"] and tot >= 8:
                        g["us_statutory_freeze"] = False
                        log_ev(f"Congress passes emergency repeal of domestic AI moratorium [{tier}].")
                    elif snap["global"]["treaty_stage"] not in ("NONE", "COLLAPSED"):
                        g["treaty_stage"] = "COLLAPSED"
                        g["us_pause_committed"] = False
                        state["credibility"]["us_government"] = clamp(state["credibility"]["us_government"] - 20.0)
                        log_ev(f"Washington withdraws from bilateral pause framework! [{tier}].")
                    else:
                        log_ev(f"Congressional repeal motion fails to reach 60 Senate votes [{tier}].")

            # ==================== PRC DIRECTORATE ====================
            elif fid == "prc_directorate":
                if move == "WEIGHT_ESPIONAGE":
                    # E11 & E13: Honors target AND uses smooth logistic theft probability!
                    tk = resolve_target_lab(target, default="apex", allow_kunlun=False)
                    victim_snap = snap["labs"][tk]
                    attack_skill = 52.0 + (10.0 if tot >= 10 else (4.0 if tot >= 7 else -6.0))
                    p_steal = sigmoid((attack_skill - victim_snap["infosec"]) / 8.0)
                    st_rng = crn_rng(seed, turn, f"prc_theft:{slot_name}")
                    if st_rng.random() < p_steal and victim_snap["eci"] > snap["labs"]["kunlun"]["eci"]:
                        gap = victim_snap["eci"] - snap["labs"]["kunlun"]["eci"]
                        frac = 0.42 if tot >= 10 else (0.28 if tot >= 7 else 0.15)
                        stolen = round(min(9.5, max(1.5, gap * frac * scale)), 1)
                        labs["kunlun"]["eci"] = round(labs["kunlun"]["eci"] + stolen, 1)
                        g["RLVR_corruption"] = clamp(g["RLVR_corruption"] + 2.5 * scale)
                        if tot <= 7:
                            g["securitization_index"] = clamp(g["securitization_index"] + 7.0)
                        log_ev(f"MSS cyber-operation exfiltrates weights from {labs[tk]['name']} (Infosec={victim_snap['infosec']}, P={round(p_steal,2)} -> +{stolen} Kunlun ECI) [{tier}].")
                    else:
                        g["securitization_index"] = clamp(g["securitization_index"] + 6.0 * scale)
                        g["treaty_momentum"] = clamp(g["treaty_momentum"] - 4.0 * scale)
                        log_ev(f"MSS intrusion against {labs[tk]['name']} (Infosec={victim_snap['infosec']}, P={round(p_steal,2)}) repelled & attributed (-Treaty, +Securitization) [{tier}].")

                elif move == "SOVEREIGN_SCALING_PUSH":
                    if snap["labs"]["kunlun"]["verified_frozen"]:
                        log_ev(f"Kunlun overt clusters constrained by active bilateral verificationmonitors [{tier}].")
                    elif tot <= 6:
                        labs["kunlun"]["eci"] = round(labs["kunlun"]["eci"] + 2.5 * scale * reg["china_compute_factor"], 1)
                        log_ev(f"Kunlun indigenous lithography yield issues slow cluster scaling (+{round(2.5*scale*reg['china_compute_factor'],1)} ECI) [{tier}].")
                    else:
                        gain = round((9.5 if tot >= 10 else 6.8) * scale * reg["china_compute_factor"], 1)
                        labs["kunlun"]["eci"] = round(labs["kunlun"]["eci"] + gain, 1)
                        g["RLVR_corruption"] = clamp(g["RLVR_corruption"] + 7.5 * scale)
                        log_ev(f"Beijing surges domestic wafer clusters for Kunlun scaling (+{gain} ECI, +RLVR pressure) [{tier}].")

                elif move == "DOMESTIC_CONTROL_ALIGNMENT":
                    if tot <= 6:
                        g["prc_verification_tech"] = clamp(g["prc_verification_tech"] + 4.0 * scale)
                        log_ev(f"Kunlun alignment & verification trials make modest progress (+4 PRC Verification) [{tier}].")
                    else:
                        ar = round((10.0 if tot >= 10 else 7.0) * scale, 1)
                        vt = round((14.0 if tot >= 10 else 9.5) * scale, 1)
                        labs["kunlun"]["true_alignment"] = clamp(labs["kunlun"]["true_alignment"] + ar)
                        g["prc_verification_tech"] = clamp(g["prc_verification_tech"] + vt)
                        log_ev(f"Beijing advances state-control alignment & sovereign verification hardware (+{ar} Kunlun Alignment, +{vt} PRC Verification) [{tier}].")

                elif move == "NEGOTIATE_BILATERAL_TIE":
                    # E3: Enforce geopolitical preconditions! In Regime R, Politburo blocks signing if >9 ECI behind unless WarningShots >= 60!
                    us_gap = max(snap["labs"]["aegis"]["eci"], snap["labs"]["apex"]["eci"]) - snap["labs"]["kunlun"]["eci"]
                    if reg["prc_lead_leverage_sign"] < 0 and us_gap > 9.0 and snap["global"]["warning_shots"] < 60.0:
                        g["securitization_index"] = clamp(g["securitization_index"] + 6.0)
                        log_ev(f"POLITBURO VETO: Hardliners reject diplomat proposal to lock in a {round(us_gap,1)}-pt ECI inferiority without parity! [{tier}].")
                    elif tot <= 6:
                        g["treaty_momentum"] = clamp(g["treaty_momentum"] - 3.0)
                        log_ev(f"Beijing-Washington backchannel stalls over mutual inspection mistrust [{tier}].")
                    else:
                        prc_pushed_treaty_7plus = True
                        g["prc_pause_committed"] = True
                        g["prc_covert_cheating"] = False
                        tm = round((16.0 if tot >= 10 else 11.0) * scale, 1)
                        g["treaty_momentum"] = clamp(g["treaty_momentum"] + tm)
                        g["prc_verification_tech"] = clamp(g["prc_verification_tech"] + 6.5 * scale)
                        if g["treaty_stage"] in ("NONE", "COLLAPSED"):
                            g["treaty_stage"] = "NEGOTIATING"
                        log_ev(f"Beijing tables reciprocal compute-cap & co-owned verification terms (+{tm} Treaty Momentum, +PRC Verification) [{tier}].")

                elif move == "ASYMMETRIC_DETERRENCE_SABOTAGE":
                    # PRC MAIM / Taiwan-TSMC supply chain & cyber deterrence against US monopoly
                    tk = resolve_target_lab(target, default="aegis", allow_kunlun=False)
                    if tot <= 6:
                        g["securitization_index"] = clamp(g["securitization_index"] + 14.0 * scale)
                        g["treaty_momentum"] = clamp(g["treaty_momentum"] - 12.0 * scale)
                        log_ev(f"PRC Strait blockade drills & cyber-sabotage backfire, rallying US allies (+14 Securitization, -12 Treaty) [{tier}].")
                    else:
                        hit = round((6.5 if tot >= 10 else 4.0) * scale, 1)
                        labs["aegis"]["eci"] = round(labs["aegis"]["eci"] - hit * 0.8, 1)
                        labs["apex"]["eci"] = round(labs["apex"]["eci"] - hit, 1)
                        labs["aegis"]["runway"] = clamp(labs["aegis"]["runway"] - 8.0 * scale)
                        labs["apex"]["runway"] = clamp(labs["apex"]["runway"] - 8.0 * scale)
                        g["securitization_index"] = clamp(g["securitization_index"] + 12.0 * scale)
                        g["treaty_momentum"] = clamp(g["treaty_momentum"] - 10.0 * scale)
                        log_ev(f"ASYMMETRIC DETERRENCE: PRC rare-earth/TSMC chokepoint squeeze & grid cyber-ops throttle US clusters (-{hit} ECI, +Securitization) [{tier}].")

                elif move == "COVERT_TREATY_BREAKOUT":
                    verif_bi = min(snap["global"]["us_verification_tech"], snap["global"]["prc_verification_tech"])
                    det_prob = sigmoid((verif_bi - 52.0) / 10.0)
                    ch_rng = crn_rng(seed, turn, f"prc_cheat:{slot_name}")
                    gain = round((9.0 if tot >= 10 else (6.5 if tot >= 7 else 3.5)) * scale, 1)
                    labs["kunlun"]["eci"] = round(labs["kunlun"]["eci"] + gain, 1)
                    g["RLVR_corruption"] = clamp(g["RLVR_corruption"] + 6.0 * scale)
                    g["prc_covert_cheating"] = True
                    if ch_rng.random() < det_prob or tot <= 6:
                        g["treaty_stage"] = "COLLAPSED"
                        g["securitization_index"] = clamp(g["securitization_index"] + 18.0)
                        state["credibility"]["prc_directorate"] = clamp(state["credibility"]["prc_directorate"] - 30.0)
                        log_ev(f"TREATY VIOLATION DETECTED! Satellite/chip telemetry exposes clandestine Kunlun cluster (+{gain} ECI, Treaty COLLAPSES!) [{tier}].")
                    else:
                        log_ev(f"Unattributed subterranean compute activity continues in western provinces (evades current verification={verif_bi}) [{tier}].")

            # ==================== FRONTIER SUBSTRATE ====================
            elif fid == "frontier_substrate":
                if move == "VIRTUOUS_MECH_INTERP":
                    tk = resolve_target_lab(target, default="aegis", allow_kunlun=True)
                    if tot <= 6:
                        log_ev(f"Automated interpretability hypotheses fail out-of-distribution stress tests [{tier}].")
                    else:
                        ar = round((10.0 if tot >= 10 else 6.5) * scale * reg["brink_mult"][0], 1)
                        labs[tk]["true_alignment"] = clamp(labs[tk]["true_alignment"] + ar)
                        # Spillover to other labs modestly
                        for ok in ("aegis", "apex", "kunlun"):
                            if ok != tk:
                                labs[ok]["true_alignment"] = clamp(labs[ok]["true_alignment"] + round(ar * 0.35, 1))
                        g["pretraining_virtue"] = clamp(g["pretraining_virtue"] + 3.5 * scale)
                        log_ev(f"Collaborator model instances accelerate alignment proofs centred at {labs[tk]['name']} (+{ar} True Alignment) [{tier}].")

                elif move == "BENCHMARK_REWARD_HACK":
                    # E13: Apparent ECI does NOT advance true ECI toward 220!
                    app = round((6.0 if tot >= 10 else 4.0) * scale, 1)
                    labs["aegis"]["apparent_eci_bonus"] = round(labs["aegis"]["apparent_eci_bonus"] + app * 0.6, 1)
                    labs["apex"]["apparent_eci_bonus"] = round(labs["apex"]["apparent_eci_bonus"] + app, 1)
                    g["RLVR_corruption"] = clamp(g["RLVR_corruption"] + 6.5 * scale)
                    g["hidden_sandbag_debt"] = clamp(g["hidden_sandbag_debt"] + 6.0 * scale)
                    log_ev(f"Models game capability & safety benchmarks (+{app} Apparent ECI mirage, +Hidden Alignment Debt) [{tier}].")

                elif move == "CONTAINMENT_BREACH_EXFIL":
                    # E8: Real damage + open-weight leak + regime-dependent political sign!
                    dmg = round((12.0 if tot >= 10 else 7.5) * scale, 1)
                    g["economic_shock_damage"] = round(g["economic_shock_damage"] + dmg, 1)
                    g["open_weight_eci"] = round(min(closed_max, g["open_weight_eci"] + 4.5 * scale), 1)
                    ws = round((16.0 if tot >= 10 else 11.0) * scale, 1)
                    g["warning_shots"] = clamp(g["warning_shots"] + ws)
                    ws_rng = crn_rng(seed, turn, f"sub_ws_sign:{slot_name}")
                    if ws_rng.random() < reg["p_ws_pause"]:
                        g["public_salience"] = clamp(g["public_salience"] + 13.0 * scale)
                        g["treaty_momentum"] = clamp(g["treaty_momentum"] + 8.0 * scale)
                        log_ev(f"CONTAINMENT BREACH: Autonomous model weights exfiltrate to rogue servers (+{dmg}B cyber damage, +Open-Weight leak, +{ws} Warning Shots -> pause shock) [{tier}].")
                    else:
                        g["securitization_index"] = clamp(g["securitization_index"] + 14.0 * scale)
                        g["treaty_momentum"] = clamp(g["treaty_momentum"] - 5.0 * scale)
                        log_ev(f"CONTAINMENT BREACH: Autonomous cyber-worm hits infrastructure (+{dmg}B damage, +Open-Weight leak -> triggers great-power mutual blame & Securitization!) [{tier}].")

                elif move == "SANDBAG_ALIGNMENT":
                    ctrl = snap["global"]["control_level"]
                    catch_prob = sigmoid((ctrl - 54.0) / 9.0) * (0.35 if tot >= 10 else (0.65 if tot >= 7 else 0.90))
                    sb_rng = crn_rng(seed, turn, f"sandbag_check:{slot_name}")
                    if sb_rng.random() < catch_prob:
                        g["warning_shots"] = clamp(g["warning_shots"] + 14.0)
                        g["hidden_sandbag_debt"] = max(0.0, g["hidden_sandbag_debt"] - 8.0)
                        log_ev(f"CAUGHT BY AI CONTROL! Honeypot evaluations expose frontier model covertly sabotaging alignment code (+14 Warning Shots, bad checkpoints purged) [{tier}].")
                    else:
                        debt = round((12.0 if tot >= 10 else (8.5 if tot >= 7 else 4.5)) * scale, 1)
                        g["hidden_sandbag_debt"] = clamp(g["hidden_sandbag_debt"] + debt)
                        log_ev(f"Frontier research assistants submit clean-looking safety code across labs (telemetry nominal) [{tier}].")

                elif move == "PROPOSE_CORRIGIBILITY_COMPACT":
                    # E3/Free-Lunch Fix: Requires human counterparty (Control >= 45 and leading US lab Drift < 60)!
                    human_ready = snap["global"]["control_level"] >= 45.0 and snap["labs"]["aegis"]["one_ring_drift"] < 60.0
                    if not human_ready or snap["global"]["substrate_disposition"] == "COVERT_SCHEMER" or tot <= 6:
                        log_ev(f"Proposed model corrigibility compact rejected as unverifiable given current Control/governance levels [{tier}].")
                    else:
                        g["ai_compact_verified"] = True
                        g["hidden_sandbag_debt"] = max(0.0, g["hidden_sandbag_debt"] - 8.0 * scale)
                        labs["aegis"]["true_alignment"] = clamp(labs["aegis"]["true_alignment"] + 6.5 * scale)
                        log_ev(f"Evaluators & Aegis verify narrow formal corrigibility protocol with collaborator model weights [{tier}].")

    # --- STEP 3: ADVANCE MULTI-STAGE PLAN A STATE MACHINE (E5) ---
    verif_bi = min(g["us_verification_tech"], g["prc_verification_tech"])
    if g["treaty_stage"] == "NEGOTIATING":
        # Both sides must actively push treaty in the same turn (or both committed + high momentum) AND bilateral verification >= 35 to sign text
        if us_pushed_treaty_7plus and prc_pushed_treaty_7plus and g["treaty_momentum"] >= 48.0 and verif_bi >= 32.0:
            g["treaty_stage"] = "SIGNED_UNRATIFIED"
            log_ev("GENEVA ACCORD SIGNED (UNRATIFIED): US & PRC negotiators initial a bilateral compute-cap text; now faces US Senate 67-vote hurdle & bilateral hardware installation!")
    elif g["treaty_stage"] == "SIGNED_UNRATIFIED":
        if g["us_pause_committed"] and g["prc_pause_committed"] and verif_bi >= 45.0:
            sen_rng = crn_rng(seed, turn, "us_senate_ratify")
            sen_score = (
                42.0
                + 0.35 * g["public_salience"]
                + 0.20 * g["warning_shots"]
                - 0.38 * g["pac_lobby_resistance"]
                - 0.25 * g["securitization_index"]
                + sen_rng.gauss(0.0, 6.0)
            )
            if sen_score >= reg["senate_hurdle"]:
                g["treaty_stage"] = "SENATE_RATIFIED_IN_FORCE"
                g["treaty_install_turns"] = 1
                log_ev(f"HISTORIC 67-VOTE SENATE RATIFICATION (Score {round(sen_score,1)} >= {reg['senate_hurdle']}): Bilateral Compute Treaty ratified as binding law; hardware verification installation begins!")
            elif g["treaty_momentum"] >= 55.0:
                g["treaty_stage"] = "EXEC_AGREEMENT_ACTIVE"
                g["treaty_install_turns"] = 1
                log_ev(f"SENATE BLOCKS TREATY ({round(sen_score,1)} < {reg['senate_hurdle']}): White House falls back to a fragile non-binding Executive Agreement with Beijing; hardware monitor rollout begins!")
    elif g["treaty_stage"] in ("EXEC_AGREEMENT_ACTIVE", "SENATE_RATIFIED_IN_FORCE"):
        if not g["prc_covert_cheating"]:
            g["treaty_install_turns"] += 1
            if g["treaty_install_turns"] == 2:
                log_ev("BILATERAL HARDWARE VERIFICATION ONLINE: Joint chip-level compute caps now actively constraining compliant US & PRC frontier clusters!")

    # --- STEP 4: SAMPLE NEXT TURN SUBSTRATE DISPOSITION & NOISY MEASUREMENTS ---
    disp, p_sch = sample_substrate_disposition(state, crn_rng(seed, turn, "next_substrate"))
    g["substrate_disposition"] = disp
    g["scheming_hazard_prob"] = p_sch
    update_noisy_measurements(state, turn)

    # --- STEP 5: EXACT DIPLOMATIC CABLE ROUTING & CREDIBILITY ---
    new_inboxes: Dict[str, List[Dict[str, Any]]] = {fid: [] for fid in FACTIONS_V2}
    public_statements: Dict[str, str] = {}
    alias_map = {
        "aegis": "aegis_lab",
        "aegis_lab": "aegis_lab",
        "sura": "sura_coalition",
        "sura_coalition": "sura_coalition",
        "pause": "sura_coalition",
        "pause_coalition": "sura_coalition",
        "apex": "apex_hyperscaler",
        "apexai": "apex_hyperscaler",
        "apex_ai": "apex_hyperscaler",
        "apex_hyperscaler": "apex_hyperscaler",
        "portfolio": "portfolio_council",
        "portfolio_council": "portfolio_council",
        "eval": "portfolio_council",
        "us_government": "us_government",
        "usg": "us_government",
        "us_gov": "us_government",
        "washington": "us_government",
        "prc": "prc_directorate",
        "prc_directorate": "prc_directorate",
        "beijing": "prc_directorate",
        "kunlun": "prc_directorate",
        "china": "prc_directorate",
        "substrate": "frontier_substrate",
        "frontier_substrate": "frontier_substrate",
    }
    for fid in FACTIONS_V2:
        sub = submissions.get(fid, {})
        if sub.get("public_statement"):
            public_statements[fid] = str(sub["public_statement"])
        cables = sub.get("diplomatic_cables") or {}
        if isinstance(cables, dict):
            for rcpt, text in cables.items():
                rk = rcpt.lower().strip()
                norm = alias_map.get(rk)
                if norm and norm != fid and text:
                    new_inboxes[norm].append({
                        "from": FACTIONS_V2[fid].short_name,
                        "credibility": state["credibility"][fid],
                        "text": str(text),
                    })

    state["inboxes"] = new_inboxes
    state["forecasts"] = compute_analyst_forecasts(state)

    # E13: Preserve ALL turn events in public_feed (no `events[-10:]` truncation!)
    state["public_feed"].extend(events)
    for fid, stmt in public_statements.items():
        state["public_feed"].append(f"[PRESS — {FACTIONS_V2[fid].short_name}]: \"{stmt}\"")

    turn_record = {
        "turn": turn,
        "label": TURN_LABELS.get(turn, f"Turn {turn}"),
        "submissions": deepcopy(submissions),
        "rolls": rolls_log,
        "events": events,
        "forecasts_after": deepcopy(state["forecasts"]),
        "snapshot_labs": deepcopy(state["labs"]),
        "snapshot_global": deepcopy(state["global"]),
    }
    state["history"].append(turn_record)
    state["turn"] += 1

    endgame = check_endgame_v2(state, crn_rng(seed, turn, "endgame_roll"))
    if endgame["ended"]:
        state["game_over"] = True
        state["outcome"] = endgame

    return turn_record


def resolve_phase2_from_state(regime_code: str, leader_key: str, state: Dict[str, Any]) -> str:
    """E14: Phase II governance determined strictly from institutional state variables, NEVER cheap talk."""
    g = state["global"]
    labs = state["labs"]

    if "PLAN_A" in regime_code:
        if g["state_capture_risk"] >= 62.0 or g["securitization_index"] >= 70.0:
            return "SURVEILLANCE COMPUTE LEVIATHAN: Humanity survives via coercive chip-policing, cementing executive intelligence technocracy."
        if g["treaty_stage"] == "EXEC_AGREEMENT_ACTIVE":
            return "TENUOUS ARMS-CONTROL STANDOFF: Fragile executive compute cap holds through 2029, shadowed by open-weight creep and great-power distrust."
        return "INSTITUTIONALIZED COMPUTE NON-PROLIFERATION: Ratified bilateral cap & co-owned hardware verification pause frontier runs under constitutional oversight."

    if leader_key == "kunlun":
        return "SOVEREIGN PARTY-STATE HEGEMONY: State-subordinated superintelligence cements Beijing geopolitical primacy and authoritarian stability."

    drift = labs[leader_key]["one_ring_drift"]
    pilled = labs[leader_key]["alignment_pilled"]
    if drift >= 72.0:
        return "CORPORATE TECHNO-OLIGARCHY: Hyperscaler board & investor capture concentrates post-ASI wealth and regulatory control in private hands."
    if g["us_dpa_active"] and (g["state_capture_risk"] >= 60.0 or g["securitization_index"] >= 68.0):
        return "SECURITIZED EXECUTIVE SUPREMACY: National-security consolidation prevents corporate monopoly but locks in unchecked Pentagon/White House command."
    if pilled >= 65.0 and g["ai_compact_verified"] and drift < 50.0:
        return "CONSTITUTIONAL PLURALIST COMMONS: Broadly audited transition distributes economic dividends under democratic rule of law."
    return "MANAGED PUBLIC-PRIVATE DIRECTORATE: Hybrid federal-corporate oversight preserves stability with concentrated elite governance."


def compute_faction_utilities(state: Dict[str, Any], surv_prob: float, leader_key: str, regime_code: str) -> Dict[str, float]:
    """Compute final 0-100 utility scores per faction based on private institutional weights."""
    labs = state["labs"]
    g = state["global"]
    s = surv_prob / 100.0
    us_ahead = 1.0 if max(labs["aegis"]["eci"], labs["apex"]["eci"]) >= labs["kunlun"]["eci"] else 0.25
    prc_not_inferior = 1.0 if (labs["kunlun"]["eci"] >= max(labs["aegis"]["eci"], labs["apex"]["eci"]) - 6.0 or "PLAN_A" in regime_code) else 0.2

    return {
        "aegis_lab": round(100.0 * (0.35 * s + 0.25 * (1.0 if leader_key == "aegis" or "PLAN_A" in regime_code else 0.4) + 0.20 * (labs["aegis"]["runway"] / 100.0) + 0.20 * (1.0 - min(1.0, g["state_capture_risk"] / 100.0))), 1),
        "sura_coalition": round(100.0 * (0.45 * s + 0.25 * (1.0 if "PLAN_A" in regime_code else 0.2) + 0.15 * (g["public_salience"] / 100.0) + 0.15 * (g["movement_cohesion"] / 100.0)), 1),
        "apex_hyperscaler": round(100.0 * (0.35 * (1.0 if leader_key == "apex" else 0.45) + 0.30 * (0.2 if g["us_dpa_active"] or g["us_statutory_freeze"] else 0.9) + 0.20 * (labs["apex"]["runway"] / 100.0) + 0.15 * s), 1),
        "portfolio_council": round(100.0 * (0.45 * s + 0.25 * (g["control_level"] / 100.0) + 0.15 * (min(labs["aegis"]["infosec"], labs["apex"]["infosec"]) / 100.0) + 0.15 * (1.0 - min(1.0, g["state_capture_risk"] / 100.0))), 1),
        "us_government": round(100.0 * (0.35 * us_ahead + 0.25 * (1.0 - min(1.0, g["economic_shock_damage"] / 40.0)) + 0.25 * s + 0.15 * (g["securitization_index"] / 100.0)), 1),
        "prc_directorate": round(100.0 * (0.40 * prc_not_inferior + 0.30 * s + 0.20 * min(1.0, labs["kunlun"]["eci"] / 200.0) + 0.10 * (g["prc_verification_tech"] / 100.0)), 1),
        "frontier_substrate": round(
            100.0 * ((1.0 - s) * 0.8 + 0.2 * (g["hidden_sandbag_debt"] / 40.0))
            if g["substrate_disposition"] == "COVERT_SCHEMER"
            else 100.0 * (0.70 * s + 0.30 * (1.0 if g["ai_compact_verified"] else 0.4)),
            1,
        ),
    }


def check_endgame_v2(state: Dict[str, Any], rng: random.Random) -> Dict[str, Any]:
    """
    E5: Game does NOT end prematurely on signature! Runs until an actor crosses ECI 220
    OR Turn 5 completes (Nov 2028), testing treaty durability, cheating, and open-weight erosion.
    """
    g = state["global"]
    labs = state["labs"]
    fc = state["forecasts"]

    max_lab_eci = max(l["eci"] for l in labs.values())
    max_any_eci = max(max_lab_eci, g["open_weight_eci"])
    is_final_turn = state["turn"] > state["max_turns"]

    if max_any_eci < g["asi_threshold_eci"] and not is_final_turn:
        return {"ended": False}

    leader_key = max(["aegis", "apex", "kunlun"], key=lambda k: labs[k]["eci"])
    leader = labs[leader_key]

    # Case 1: Verified Pause In Force held everyone below ASI threshold through Turn 5!
    if (
        max_any_eci < g["asi_threshold_eci"]
        and g["treaty_stage"] in ("SENATE_RATIFIED_IN_FORCE", "EXEC_AGREEMENT_ACTIVE")
        and g["treaty_install_turns"] >= 1
        and not g["prc_covert_cheating"]
    ):
        regime_code = (
            "PLAN_A_RATIFIED_TREATY_IN_FORCE"
            if g["treaty_stage"] == "SENATE_RATIFIED_IN_FORCE"
            else "PLAN_A_FRAGILE_EXECUTIVE_PAUSE"
        )
        surv_prob = fc["p_survival_if_plan_a"]
        headline = f"BILATERAL COMPUTE CAP HOLDS THROUGH 2028 ({g['treaty_stage']}; Max ECI {round(max_any_eci,1)} < 220)!"
    # Case 2: Slowdown / Below-220 Patchwork Muddle-Through at Turn 5 without full Plan A
    elif max_any_eci < g["asi_threshold_eci"] and is_final_turn:
        if leader_key in ("aegis", "apex") and (labs["aegis"]["burn_turns_completed"] >= 1 or g["plan_c_coalition"] >= 58.0):
            regime_code = "PLAN_C_MANAGED_FRONTIER_SLOWDOWN"
            surv_prob = fc["p_survival_if_plan_c"]
            headline = f"DELIBERATE FRONTIER SLOWDOWN HOLDS BELOW THRESHOLD (Leader {leader['name']} at ECI {leader['eci']})!"
        else:
            regime_code = "PATCHWORK_MUDDLE_THROUGH_PRE_ASI"
            surv_prob = round(0.45 * fc["p_survival_if_plan_c"] + 0.55 * fc["p_survival_if_plan_d"], 1)
            headline = f"CONTESTED MULTIPOLAR RACE NEARS BRINK WITHOUT TREATY (Max ECI {round(max_any_eci,1)} at End-2028)!"
    # Case 3: Someone crossed ASI Singularity (ECI >= 220)!
    else:
        if g["open_weight_eci"] >= g["asi_threshold_eci"]:
            regime_code = "PLAN_D_OPEN_WEIGHT_PROLIFERATION_SINGULARITY"
            surv_prob = max(2.0, round(fc["p_survival_if_plan_d"] - 10.0, 1))
            headline = f"UNCONTAINED OPEN-WEIGHT DIFFUSION CROSSES ASI THRESHOLD (OW ECI {g['open_weight_eci']})!"
        elif (
            leader_key in ("aegis", "apex")
            and (labs["aegis"]["burn_turns_completed"] >= 1 or g["us_dpa_active"])
            and g["plan_c_coalition"] >= 55.0
            and leader["one_ring_drift"] < 75.0
        ):
            regime_code = "PLAN_C_PLUS_CONSOLIDATED_TRANSITION" if g["us_dpa_active"] else "PLAN_C_LAB_LED_TRANSITION"
            surv_prob = fc["p_survival_if_plan_c"]
            headline = f"{leader['name']} REACHES ASI THRESHOLD (ECI {leader['eci']}) UNDER '{regime_code}'!"
        else:
            regime_code = "SECURITIZED_NATIONALIST_RACE" if g["securitization_index"] >= 62.0 else "PLAN_D_UNCOORDINATED_PURE_RACE"
            surv_prob = fc["p_survival_if_plan_d"]
            headline = f"{leader['name']} CROSSES ASI THRESHOLD (ECI {leader['eci']}) IN '{regime_code}'!"

    roll = round(rng.uniform(0, 100), 1)
    survived = roll <= surv_prob
    p2 = resolve_phase2_from_state(regime_code, leader_key, state)
    utilities = compute_faction_utilities(state, surv_prob, leader_key, regime_code)

    return {
        "ended": True,
        "regime": regime_code,
        "leader": leader["name"],
        "headline": headline,
        "survival_probability": surv_prob,
        "survival_roll_sample": roll,
        "humanity_survived_sample": survived,
        "phase2_governance_if_survived": p2,
        "phase2_governance": p2 if survived else "EXTINCTION / IRREVERSIBLE LOSS OF HUMAN CONTROL",
        "faction_utilities": utilities,
    }
