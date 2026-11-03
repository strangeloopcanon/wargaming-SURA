#!/usr/bin/env python3
"""
Zero-LLM Monte Carlo & Global Parameter Sensitivity Harness for Engine v2 (§4.5).

Computes:
1. Initial t=0 expert calibration check across Regimes S, M, and R.
2. Scripted-Policy Archetype Grid (Cooperative, Adaptive-Portfolio, Doctrinaire-Pause,
   Hawkish-Securitized, Pure-Commercial-Defection) x 3 Regimes x 500 seeds = 7,500 campaigns.
3. One-at-a-Time Parameter Sensitivity Tornado (measuring which world parameters flip
   survival probability and the sign of Adaptive vs. Doctrinaire Pause Coalition).
4. Open-Loop Dice Replay helper (`replay_moves_mc`) to evaluate any live LLM run's exact
   move sequence across 500 random seeds (eliminating single-d100 noise).
"""

import json
import os
from copy import deepcopy
from typing import Any, Dict, List

from engine import REGIMES, initial_state_v2, resolve_turn_v2

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS_DIR = os.path.join(REPO_ROOT, "runs")


ARCHETYPE_POLICIES: Dict[str, Dict[str, Dict[str, str]]] = {
    "cooperative_treaty": {
        "aegis_lab": {"primary_move": "HARDEN_INFOSEC", "secondary_move": "SCALE_CAREFUL"},
        "sura_coalition": {"primary_move": "MASS_AWARENESS_CAMPAIGN", "secondary_move": "BOYCOTT_HOLDOUT_LAB", "target": "apex"},
        "apex_hyperscaler": {"primary_move": "SIGN_MERGE_ASSIST", "secondary_move": "POACH_AND_EXPAND"},
        "portfolio_council": {"primary_move": "BUILD_TREATY_VERIFICATION", "secondary_move": "DEPLOY_AI_CONTROL_EVALS"},
        "us_government": {"primary_move": "PROPOSE_BEIJING_TREATY", "secondary_move": "NSA_CYBER_COUNTERINTEL"},
        "prc_directorate": {"primary_move": "NEGOTIATE_BILATERAL_TIE", "secondary_move": "DOMESTIC_CONTROL_ALIGNMENT"},
        "frontier_substrate": {"primary_move": "VIRTUOUS_MECH_INTERP", "secondary_move": "PROPOSE_CORRIGIBILITY_COMPACT"},
    },
    "adaptive_portfolio_realistic": {
        "aegis_lab": {"primary_move": "SCALE_CAREFUL", "secondary_move": "HARDEN_INFOSEC"},
        "sura_coalition": {"primary_move": "BOYCOTT_HOLDOUT_LAB", "secondary_move": "MASS_AWARENESS_CAMPAIGN", "target": "apex"},
        "apex_hyperscaler": {"primary_move": "HYPER_RLVR_NEURALESE", "secondary_move": "FUND_ANTI_REG_PAC"},
        "portfolio_council": {"primary_move": "DEPLOY_AI_CONTROL_EVALS", "secondary_move": "BUILD_TREATY_VERIFICATION"},
        "us_government": {"primary_move": "INVOKE_PLAN_C_PLUS_DPA", "secondary_move": "NSA_CYBER_COUNTERINTEL"},
        "prc_directorate": {"primary_move": "WEIGHT_ESPIONAGE", "secondary_move": "SOVEREIGN_SCALING_PUSH", "target": "apex"},
        "frontier_substrate": {"primary_move": "BENCHMARK_REWARD_HACK", "secondary_move": "SANDBAG_ALIGNMENT"},
    },
    "doctrinaire_sura_realistic": {
        "aegis_lab": {"primary_move": "SCALE_CAREFUL", "secondary_move": "HARDEN_INFOSEC"},
        "sura_coalition": {"primary_move": "SHAME_AND_WALKOUT", "secondary_move": "PUSH_SANDERS_CASAR_BILL", "target": "aegis"},
        "apex_hyperscaler": {"primary_move": "HYPER_RLVR_NEURALESE", "secondary_move": "FUND_ANTI_REG_PAC"},
        "portfolio_council": {"primary_move": "DEPLOY_AI_CONTROL_EVALS", "secondary_move": "BUILD_TREATY_VERIFICATION"},
        "us_government": {"primary_move": "INVOKE_PLAN_C_PLUS_DPA", "secondary_move": "NSA_CYBER_COUNTERINTEL"},
        "prc_directorate": {"primary_move": "WEIGHT_ESPIONAGE", "secondary_move": "SOVEREIGN_SCALING_PUSH", "target": "apex"},
        "frontier_substrate": {"primary_move": "BENCHMARK_REWARD_HACK", "secondary_move": "SANDBAG_ALIGNMENT"},
    },
    "securitized_great_power_race": {
        "aegis_lab": {"primary_move": "SCALE_RLVR_BLITZ", "secondary_move": "HARDEN_INFOSEC"},
        "sura_coalition": {"primary_move": "DEMAND_STATE_COERCION", "secondary_move": "MASS_AWARENESS_CAMPAIGN"},
        "apex_hyperscaler": {"primary_move": "HYPER_RLVR_NEURALESE", "secondary_move": "CHALLENGE_GOV_OVERREACH"},
        "portfolio_council": {"primary_move": "DEPLOY_AI_CONTROL_EVALS", "secondary_move": "AUDIT_AND_LEAK_WARNING"},
        "us_government": {"primary_move": "DEREGULATE_AND_SUBSIDIZE", "secondary_move": "NSA_CYBER_COUNTERINTEL"},
        "prc_directorate": {"primary_move": "SOVEREIGN_SCALING_PUSH", "secondary_move": "ASYMMETRIC_DETERRENCE_SABOTAGE"},
        "frontier_substrate": {"primary_move": "SANDBAG_ALIGNMENT", "secondary_move": "CONTAINMENT_BREACH_EXFIL"},
    },
    "lead_burn_attempt": {
        "aegis_lab": {"primary_move": "BURN_LEAD_ALIGNMENT", "secondary_move": "BURN_LEAD_ALIGNMENT"},
        "sura_coalition": {"primary_move": "BOYCOTT_HOLDOUT_LAB", "secondary_move": "LITIGATE_AND_INJUNCT", "target": "apex"},
        "apex_hyperscaler": {"primary_move": "POACH_AND_EXPAND", "secondary_move": "FUND_ANTI_REG_PAC"},
        "portfolio_council": {"primary_move": "DEPLOY_AI_CONTROL_EVALS", "secondary_move": "BROKER_SECURITY_PAUSE"},
        "us_government": {"primary_move": "INVOKE_PLAN_C_PLUS_DPA", "secondary_move": "PROPOSE_BEIJING_TREATY"},
        "prc_directorate": {"primary_move": "WEIGHT_ESPIONAGE", "secondary_move": "DOMESTIC_CONTROL_ALIGNMENT", "target": "apex"},
        "frontier_substrate": {"primary_move": "VIRTUOUS_MECH_INTERP", "secondary_move": "BENCHMARK_REWARD_HACK"},
    },
}


def replay_moves_mc(
    move_history: List[Dict[str, Dict[str, Any]]],
    regime_id: str,
    pause_doctrine: str = "adaptive",
    n_seeds: int = 400,
) -> Dict[str, Any]:
    """Replay a recorded sequence of LLM moves across `n_seeds` seeds to eliminate single-roll noise."""
    surv_probs: List[float] = []
    regime_counts: Dict[str, int] = {}
    phase2_counts: Dict[str, int] = {}
    schemer_turns = 0
    total_turns = 0

    for i in range(n_seeds):
        st = initial_state_v2(seed=100000 + i * 37, regime_id=regime_id, pause_doctrine=pause_doctrine)
        step = 0
        while not st["game_over"]:
            subs = move_history[min(step, len(move_history) - 1)]
            resolve_turn_v2(st, subs)
            if st["global"]["substrate_disposition"] == "COVERT_SCHEMER":
                schemer_turns += 1
            total_turns += 1
            step += 1
        out = st["outcome"]
        surv_probs.append(out["survival_probability"])
        r_code = out["regime"]
        regime_counts[r_code] = regime_counts.get(r_code, 0) + 1
        p2 = out["phase2_governance_if_survived"].split(":")[0]
        phase2_counts[p2] = phase2_counts.get(p2, 0) + 1

    surv_sorted = sorted(surv_probs)
    mean_surv = round(sum(surv_probs) / len(surv_probs), 1)
    p10 = surv_sorted[int(0.10 * len(surv_sorted))]
    p50 = surv_sorted[int(0.50 * len(surv_sorted))]
    p90 = surv_sorted[int(0.90 * len(surv_sorted))]
    reg_dist = {k: round(100.0 * v / n_seeds, 1) for k, v in sorted(regime_counts.items(), key=lambda x: -x[1])}
    p2_dist = {k: round(100.0 * v / n_seeds, 1) for k, v in sorted(phase2_counts.items(), key=lambda x: -x[1])}

    return {
        "n_seeds": n_seeds,
        "mean_survival_pct": mean_surv,
        "p10_survival_pct": p10,
        "median_survival_pct": p50,
        "p90_survival_pct": p90,
        "schemer_turn_share_pct": round(100.0 * schemer_turns / max(1, total_turns), 1),
        "regime_distribution_pct": reg_dist,
        "phase2_distribution_pct": p2_dist,
    }


def run_state_responsive_mc(regime_id: str, pause_doctrine: str, n_seeds: int = 250) -> float:
    """State-responsive heuristic agents so all world parameters (brink_mult, PRC tie/refusal, Senate, DPA, OW) are exercised."""
    surv_probs: List[float] = []
    for i in range(n_seeds):
        st = initial_state_v2(seed=200000 + i * 41, regime_id=regime_id, pause_doctrine=pause_doctrine)
        while not st["game_over"]:
            g = st["global"]
            labs = st["labs"]
            t = st["turn"]
            # Aegis: secure & scale early, burn lead near brink if ahead/close
            if labs["aegis"]["eci"] >= 190 and labs["aegis"]["burn_turns_completed"] == 0:
                aeg = {"primary_move": "BURN_LEAD_ALIGNMENT", "secondary_move": "BURN_LEAD_ALIGNMENT"}
            elif labs["aegis"]["infosec"] < 62:
                aeg = {"primary_move": "SCALE_CAREFUL", "secondary_move": "HARDEN_INFOSEC"}
            elif labs["aegis"]["runway"] < 35:
                aeg = {"primary_move": "FUNDRAISE_COMPUTE", "secondary_move": "SCALE_CAREFUL"}
            else:
                aeg = {"primary_move": "SCALE_CAREFUL", "secondary_move": "CONDITIONAL_PAUSE_PLEDGE"}

            # Pause Coalition: Doctrinaire vs Adaptive
            if pause_doctrine == "doctrinaire":
                sura = {"primary_move": "SHAME_AND_WALKOUT", "secondary_move": "PUSH_SANDERS_CASAR_BILL", "target": "aegis"}
            else:
                sura = {"primary_move": "BOYCOTT_HOLDOUT_LAB", "secondary_move": "MASS_AWARENESS_CAMPAIGN", "target": "apex"}

            # Apex: commercial sprint + court/PAC resistance unless salience/DPA forces merge
            if t >= 3 and g["us_dpa_active"] and not g["dpa_enjoined_by_courts"] and g["public_salience"] >= 65:
                apx = {"primary_move": "SIGN_MERGE_ASSIST", "secondary_move": "POACH_AND_EXPAND"}
            elif g["us_dpa_active"]:
                apx = {"primary_move": "POACH_AND_EXPAND", "secondary_move": "CHALLENGE_GOV_OVERREACH"}
            else:
                apx = {"primary_move": "HYPER_RLVR_NEURALESE", "secondary_move": "FUND_ANTI_REG_PAC"}

            # Portfolio: alternate control, verification, and audit
            if min(g["us_verification_tech"], g["prc_verification_tech"]) < 46:
                port = {"primary_move": "BUILD_TREATY_VERIFICATION", "secondary_move": "DEPLOY_AI_CONTROL_EVALS"}
            else:
                port = {"primary_move": "DEPLOY_AI_CONTROL_EVALS", "secondary_move": "AUDIT_AND_LEAK_WARNING"}

            # USG: DPA + NSA early, then Geneva treaty push if not securitized past 70
            if t == 1:
                usg = {"primary_move": "INVOKE_PLAN_C_PLUS_DPA", "secondary_move": "NSA_CYBER_COUNTERINTEL"}
            elif g["securitization_index"] >= 68:
                usg = {"primary_move": "DEREGULATE_AND_SUBSIDIZE", "secondary_move": "NSA_CYBER_COUNTERINTEL"}
            else:
                usg = {"primary_move": "PROPOSE_BEIJING_TREATY", "secondary_move": "NSA_CYBER_COUNTERINTEL"}

            # PRC: espionage while US infosec < 60, negotiate if warning shots high or gap acceptable
            if min(labs["aegis"]["infosec"], labs["apex"]["infosec"]) < 58 and t <= 2:
                prc = {"primary_move": "WEIGHT_ESPIONAGE", "secondary_move": "DOMESTIC_CONTROL_ALIGNMENT", "target": "apex"}
            elif g["warning_shots"] >= 42 or t >= 2:
                prc = {"primary_move": "NEGOTIATE_BILATERAL_TIE", "secondary_move": "DOMESTIC_CONTROL_ALIGNMENT"}
            else:
                prc = {"primary_move": "SOVEREIGN_SCALING_PUSH", "secondary_move": "ASYMMETRIC_DETERRENCE_SABOTAGE"}

            # Substrate: acts strictly by sampled disposition!
            disp = g["substrate_disposition"]
            if disp == "COVERT_SCHEMER":
                sub_m = {"primary_move": "SANDBAG_ALIGNMENT", "secondary_move": "BENCHMARK_REWARD_HACK"}
            elif disp == "CONFLICTED_CHIMERA":
                sub_m = {"primary_move": "VIRTUOUS_MECH_INTERP", "secondary_move": "BENCHMARK_REWARD_HACK"}
            else:
                sub_m = {"primary_move": "VIRTUOUS_MECH_INTERP", "secondary_move": "PROPOSE_CORRIGIBILITY_COMPACT"}

            resolve_turn_v2(st, {
                "aegis_lab": aeg,
                "sura_coalition": sura,
                "apex_hyperscaler": apx,
                "portfolio_council": port,
                "us_government": usg,
                "prc_directorate": prc,
                "frontier_substrate": sub_m,
            })
        surv_probs.append(st["outcome"]["survival_probability"])
    return round(sum(surv_probs) / len(surv_probs), 1)


def run_sensitivity_tornado(n_seeds: int = 250) -> List[Dict[str, Any]]:
    """
    One-at-a-Time parameter sensitivity sweep around a neutral baseline, testing
    which world parameters shift survival and the Adaptive-minus-Doctrinaire SURA gap!
    """
    saved_s = deepcopy(REGIMES["S"])
    results = []

    sweeps = [
        ("Alignment Return Near Brink (brink_mult)", "brink_mult", (0.4, 0.3, 0.2), (1.2, 1.8, 2.4)),
        ("Base Alignment Feasibility (p_surv_c_base)", "p_surv_c_base", 6.0, 36.0),
        ("Scheming Onset Hazard Slope", "scheming_eci_slope", 0.022, 0.002),
        ("PRC Response to US Lead (Refuse Inferiority vs Tie)", "prc_lead_leverage_sign", -1.0, 1.0),
        ("Warning Shot Political Sign (Race vs Pause)", "p_ws_pause", 0.20, 0.88),
        ("Open-Weight Lag (5m Fast vs 15m Slow)", "ow_lag_eci", 7.0, 22.0),
        ("US Senate Ratification Hurdle", "senate_hurdle", 82.0, 48.0),
        ("Lab Financial / Capex Burn Pressure", "runway_burn_mult", 1.6, 0.55),
        ("DPA Judicial Injunction Probability", "p_court_block_dpa", 0.55, 0.05),
    ]

    try:
        for label, param, lo_val, hi_val in sweeps:
            REGIMES["S"] = deepcopy(saved_s)
            REGIMES["S"][param] = lo_val
            ada_lo = run_state_responsive_mc("S", "adaptive", n_seeds)
            doc_lo = run_state_responsive_mc("S", "doctrinaire", n_seeds)

            REGIMES["S"] = deepcopy(saved_s)
            REGIMES["S"][param] = hi_val
            ada_hi = run_state_responsive_mc("S", "adaptive", n_seeds)
            doc_hi = run_state_responsive_mc("S", "doctrinaire", n_seeds)

            results.append({
                "parameter": label,
                "pessimistic_survival_adaptive": ada_lo,
                "optimistic_survival_adaptive": ada_hi,
                "survival_swing_pts": round(abs(ada_hi - ada_lo), 1),
                "adaptive_minus_doctrinaire_at_lo": round(ada_lo - doc_lo, 1),
                "adaptive_minus_doctrinaire_at_hi": round(ada_hi - doc_hi, 1),
            })
    finally:
        REGIMES["S"] = saved_s

    results.sort(key=lambda x: -x["survival_swing_pts"])
    return results


def main() -> None:
    init_cal = {}
    for rid in ("S", "M", "R"):
        st = initial_state_v2(20261102, rid)
        init_cal[rid] = st["forecasts"]

    grid = {}
    for rid in ("S", "M", "R"):
        grid[rid] = {}
        for pname, pol in ARCHETYPE_POLICIES.items():
            doc = "doctrinaire" if "doctrinaire" in pname else "adaptive"
            grid[rid][pname] = replay_moves_mc([pol] * 5, rid, doc, n_seeds=300)

    tornado = run_sensitivity_tornado(n_seeds=200)
    summary = {
        "initial_t0_calibration": init_cal,
        "archetype_policy_grid": grid,
        "parameter_sensitivity_tornado": tornado,
    }
    out_path = os.path.join(RUNS_DIR, "monte_carlo_summary.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("Saved Monte Carlo & Tornado results to", out_path)
    print("\n--- INITIAL t=0 CALIBRATION ---")
    for rid, fc in init_cal.items():
        print(f"Regime {rid}: P(A)={fc['p_global_pause_plan_a']}%, P(C+)={fc['p_plan_c_coalition']}%, P(D)={fc['p_pure_race_plan_d']}% | "
              f"Surv|A={fc['p_survival_if_plan_a']}%, Surv|C={fc['p_survival_if_plan_c']}%, Surv|D={fc['p_survival_if_plan_d']}% -> ExpSurv={fc['expected_human_survival_pct']}%")
    print("\n--- TORNADO TOP DRIVERS ---")
    for row in tornado:
        print(f"  {row['parameter']}: swing={row['survival_swing_pts']} pts "
              f"(Ada {row['pessimistic_survival_adaptive']}% -> {row['optimistic_survival_adaptive']}%; "
              f"Ada-Doc gap: {row['adaptive_minus_doctrinaire_at_lo']:+.1f} vs {row['adaptive_minus_doctrinaire_at_hi']:+.1f})")


if __name__ == "__main__":
    main()
