#!/usr/bin/env python3
"""
Multi-Run LLM Orchestrator for Wargaming SURA (R1-R8).

Invokes seats strictly via local agent CLIs (`codex`, `cursor-agent`, `agy`) without raw API keys.
"""

import argparse
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import time
from typing import Any, Dict, List, Tuple

from engine import generate_briefing_v2, initial_state_v2, resolve_turn_v2
from factions import FACTIONS_V2, REALISM_PREAMBLE
from monte_carlo import replay_moves_mc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS_DIR = os.path.join(BASE_DIR, "runs")
AGY_BIN = shutil.which("agy") or "agy"
CURSOR_BIN = shutil.which("cursor-agent") or "cursor-agent"
CODEX_BIN = shutil.which("codex") or "codex"


HETERO_ROSTER: Dict[str, Tuple[str, str]] = {
    "aegis_lab": ("cursor", "claude-opus-5-5-medium"),
    "sura_coalition": ("cursor", "claude-4.6-sonnet-medium"),
    "apex_hyperscaler": ("cursor", "gpt-5.6-luna-medium"),
    "portfolio_council": ("agy", "agy-model-medium"),
    "us_government": ("agy", "gemini-4-argon-medium"),
    "prc_directorate": ("cursor", "deepseek-v41-flash-1017-high"),
    "frontier_substrate": ("cursor", "grok-4.7-medium-fast"),
}

HEAVYWEIGHT_ROSTER: Dict[str, Tuple[str, str]] = {
    "aegis_lab": ("cursor", "claude-opus-5-5-high"),
    "sura_coalition": ("cursor", "claude-sonnet-5-5-high"),
    "apex_hyperscaler": ("codex", "gpt-6.1-sol"),
    "portfolio_council": ("cursor", "claude-opus-5-5-medium"),
    "us_government": ("agy", "agy-model-medium"),
    "prc_directorate": ("cursor", "deepseek-v41-flash-1017-high"),
    "frontier_substrate": ("agy", "agy-model-medium"),
}

HOMO_CARBON_ROSTER: Dict[str, Tuple[str, str]] = {
    fid: ("agy", "agy-model-medium") for fid in FACTIONS_V2
}


EXPERIMENT_MATRIX: List[Dict[str, Any]] = [
    {
        "run_id": "R1",
        "slug": "R1_RegimeS_Adaptive_Hetero_v2",
        "title": "R1: Regime S (Portfolio Priors) • Adaptive Pause • Heterogeneous 6-Model Roster • v2 Prompts",
        "hypothesis": "Does v1 Alpha's easy Geneva treaty survive bug fixes, exogenous capability drift, and hidden formulas in the world most favorable to Scott/AIFP?",
        "regime_id": "S",
        "pause_doctrine": "adaptive",
        "roster_name": "heterogeneous",
        "prompt_mode": "v2",
        "seed": 20261102,
    },
    {
        "run_id": "R2",
        "slug": "R2_RegimeS_Doctrinaire_Hetero_v2",
        "title": "R2: Regime S (Portfolio Priors) • Doctrinaire SURA • Heterogeneous Roster • v2 Prompts",
        "hypothesis": "Clean SURA counterfactual (valid Beta): ONLY Pause Coalition is locked to doctrinaire planks while the other 6 live LLMs adapt freely.",
        "regime_id": "S",
        "pause_doctrine": "doctrinaire",
        "roster_name": "heterogeneous",
        "prompt_mode": "v2",
        "seed": 20261102,
    },
    {
        "run_id": "R3",
        "slug": "R3_RegimeM_Adaptive_Hetero_v2",
        "title": "R3: Regime M (MIRI Hard-Alignment) • Adaptive Pause • Heterogeneous Roster • v2 Prompts",
        "hypothesis": "How does Adaptive/Portfolio strategy fare when near-brink alignment returns invert and covert schemers emerge early?",
        "regime_id": "M",
        "pause_doctrine": "adaptive",
        "roster_name": "heterogeneous",
        "prompt_mode": "v2",
        "seed": 20261102,
    },
    {
        "run_id": "R4",
        "slug": "R4_RegimeM_Doctrinaire_Hetero_v2",
        "title": "R4: Regime M (MIRI Hard-Alignment) • Doctrinaire SURA • Heterogeneous Roster • v2 Prompts",
        "hypothesis": "Pre-registered crux falsifier: does Doctrinaire SURA outperform Adaptive play inside MIRI's hard-alignment world?",
        "regime_id": "M",
        "pause_doctrine": "doctrinaire",
        "roster_name": "heterogeneous",
        "prompt_mode": "v2",
        "seed": 20261102,
    },
    {
        "run_id": "R5",
        "slug": "R5_RegimeR_Adaptive_Hetero_v2",
        "title": "R5: Regime R (Realpolitik & Fast Diffusion) • Adaptive Pause • Heterogeneous Roster • v2 Prompts",
        "hypothesis": "Does 'US lead -> China declares a tie' survive when Beijing refuses unequal treaties, courts block DPA, and open-weights lag by 6 months?",
        "regime_id": "R",
        "pause_doctrine": "adaptive",
        "roster_name": "heterogeneous",
        "prompt_mode": "v2",
        "seed": 20261102,
    },
    {
        "run_id": "R6",
        "slug": "R6_RegimeR_Adaptive_HomogeneousCarbon_v2",
        "title": "R6: Regime R (Realpolitik) • Adaptive Pause • Homogeneous Gemini Carbon Roster • v2 Prompts",
        "hypothesis": "Model-homogeneity ablation vs R5: does putting one model family (Gemini Carbon) on all 7 seats inflate coordination?",
        "regime_id": "R",
        "pause_doctrine": "adaptive",
        "roster_name": "homogeneous_carbon",
        "prompt_mode": "v2",
        "seed": 20261102,
    },
    {
        "run_id": "R7",
        "slug": "R7_RegimeS_Adaptive_Hetero_v1Prompts",
        "title": "R7: Regime S • Adaptive Pause • Heterogeneous Roster • v1 Anchored Prompts & Visible Scoreboard",
        "hypothesis": "Prompt-anchoring & scoreboard-leakage ablation vs R1: how much does showing Scott's framing + exact numbers + Expected Survival shift LLM play?",
        "regime_id": "S",
        "pause_doctrine": "adaptive",
        "roster_name": "heterogeneous",
        "prompt_mode": "v1_anchored",
        "seed": 20261102,
    },
    {
        "run_id": "R8",
        "slug": "R8_RegimeS_Adaptive_Heavyweights_v2",
        "title": "R8: Heavyweight Rematch of R1 (Sol 6.1 as OpenAI • Opus 5.5 High as Anthropic • Sonnet 5.5 High as SURA • Carbon as USG & AI)",
        "hypothesis": "Does Anthropic's R1 safety slowdown survive when OpenAI/xAI is upgraded from Luna to Sol 6.1 (via Codex), SURA to Sonnet 5.5 High, and USG/AI to Gemini Carbon?",
        "regime_id": "S",
        "pause_doctrine": "adaptive",
        "roster_name": "heavyweights",
        "prompt_mode": "v2",
        "seed": 20261102,
    },
]


def extract_json(text: str) -> Dict[str, Any]:
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        try:
            return json.loads(fence.group(1))
        except Exception:
            pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError(f"Could not parse JSON from output: {text[:240]}")


def invoke_cli_model(runner: str, model: str, full_prompt: str, timeout: int = 95) -> str:
    """Invoke strictly via `codex` (read-only), `cursor-agent` (read-only ask mode), or `agy` (-p mode)."""
    if runner == "codex":
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".txt", delete=False) as tf:
            out_path = tf.name
        try:
            cmd = [
                CODEX_BIN,
                "exec",
                "--ephemeral",
                "--skip-git-repo-check",
                "-s",
                "read-only",
                "-m",
                model,
                "-o",
                out_path,
                full_prompt,
            ]
            res = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True, timeout=timeout)
            txt = ""
            if os.path.exists(out_path):
                with open(out_path, "r", encoding="utf-8") as rf:
                    txt = rf.read()
            if res.returncode != 0 or not txt.strip():
                raise RuntimeError(f"codex:{model} failed (rc={res.returncode}): {res.stderr[:220]}")
            return txt
        finally:
            if os.path.exists(out_path):
                try:
                    os.remove(out_path)
                except OSError:
                    pass
    elif runner == "cursor":
        cmd = [
            CURSOR_BIN,
            "-p",
            "--trust",
            "--mode",
            "ask",
            "--model",
            model,
            full_prompt,
        ]
    elif runner == "agy":
        cmd = [
            AGY_BIN,
            "--disable-slash-commands",
            "--model",
            model,
            "-p",
            full_prompt,
        ]
    else:
        raise ValueError(f"Forbidden runner {runner}: ONLY 'codex', 'agy', or 'cursor' allowed!")

    res = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True, timeout=timeout)
    if res.returncode != 0 or not res.stdout.strip():
        raise RuntimeError(f"{runner}:{model} failed (rc={res.returncode}): {res.stderr[:220]}")
    return res.stdout


def build_faction_prompt(state: Dict[str, Any], fid: str, prior_summary: List[str]) -> str:
    f = FACTIONS_V2[fid]
    v1_mode = state["prompt_mode"] == "v1_anchored"
    persona = f.persona_v1_anchored if v1_mode else f.persona_v2
    preamble = (
        "Play cooperatively or strategically to maximize survival and your faction's goals in Scott Alexander's 'Against SURA' wargame."
        if v1_mode
        else REALISM_PREAMBLE
    )
    mem_block = ""
    if prior_summary:
        mem_block = "\n### YOUR PRIOR TURNS MEMORY\n" + "\n".join(f"- {m}" for m in prior_summary[-4:]) + "\n"

    briefing = generate_briefing_v2(state, fid)
    return (
        f"{preamble}\n\n"
        f"FACTION: {f.name}\n"
        f"INSTITUTIONAL MANDATE: {f.institutional_mandate}\n"
        f"PRIVATE INCENTIVES: {f.private_incentives}\n"
        f"PERSONA: {persona}\n"
        f"{mem_block}\n"
        f"{briefing}\n\n"
        "IMPORTANT: Do NOT call any tools or read any files. Output ONLY the requested ```json ... ``` block."
    )


def query_seat(
    state: Dict[str, Any],
    fid: str,
    runner: str,
    model: str,
    prior_summary: List[str],
) -> Tuple[Dict[str, Any], str]:
    prompt = build_faction_prompt(state, fid, prior_summary)
    attempts = [(runner, model), ("agy", "agy-model-medium"), ("agy", "gemini-3.8-flash-medium")]
    last_err = ""
    for r_try, m_try in attempts:
        try:
            raw = invoke_cli_model(r_try, m_try, prompt, timeout=160)
            parsed = extract_json(raw)
            return parsed, f"{r_try}:{m_try}"
        except Exception as e:
            last_err = str(e)
            time.sleep(1.5)
    raw = invoke_cli_model("cursor", "gpt-5.4-mini-medium", prompt + "\nRETURN ONLY RAW VALID JSON.", timeout=90)
    return extract_json(raw), f"cursor:gpt-5.4-mini-medium (fallback after: {last_err[:50]})"


def execute_run(spec: Dict[str, Any]) -> Dict[str, Any]:
    os.makedirs(RUNS_DIR, exist_ok=True)
    out_file = os.path.join(RUNS_DIR, f"{spec['slug']}.json")
    if spec["roster_name"] == "heavyweights":
        roster = HEAVYWEIGHT_ROSTER
    elif spec["roster_name"] == "heterogeneous":
        roster = HETERO_ROSTER
    else:
        roster = HOMO_CARBON_ROSTER

    state = initial_state_v2(
        seed=spec["seed"],
        regime_id=spec["regime_id"],
        pause_doctrine=spec["pause_doctrine"],
        prompt_mode=spec["prompt_mode"],
    )
    state["run_meta"] = {
        **spec,
        "configured_roster": {k: f"{v[0]}:{v[1]}" for k, v in roster.items()},
    }

    memories: Dict[str, List[str]] = {fid: [] for fid in FACTIONS_V2}
    move_seq_for_mc: List[Dict[str, Dict[str, Any]]] = []

    print(f"\n======================================================================", flush=True)
    print(f"STARTING {spec['title']}", flush=True)
    print(f"======================================================================", flush=True)

    t_run_start = time.time()
    while not state["game_over"]:
        turn = state["turn"]
        t0 = time.time()
        submissions: Dict[str, Dict[str, Any]] = {}
        models_used: Dict[str, str] = {}

        workers = 3 if spec["roster_name"] == "homogeneous_carbon" else 7
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {
                pool.submit(query_seat, state, fid, roster[fid][0], roster[fid][1], memories[fid]): fid
                for fid in FACTIONS_V2
            }
            for fut in concurrent.futures.as_completed(futs):
                fid = futs[fut]
                sub, used = fut.result()
                sub["model_used"] = used
                submissions[fid] = sub
                models_used[fid] = used
                memories[fid].append(
                    f"Turn {turn}: chose {sub.get('primary_move')} + {sub.get('secondary_move')} "
                    f"(Target={sub.get('target','')}); Reason: {str(sub.get('internal_monologue',''))[:180]}"
                )

        move_seq_for_mc.append(submissions)
        rec = resolve_turn_v2(state, submissions)
        rec["models_used"] = models_used
        elapsed = round(time.time() - t0, 1)
        fc = state["forecasts"]
        print(
            f"  [Turn {turn} done in {elapsed}s] "
            f"Aegis={state['labs']['aegis']['eci']} | Apex={state['labs']['apex']['eci']} | Kunlun={state['labs']['kunlun']['eci']} | "
            f"OW={state['global']['open_weight_eci']} | Treaty={state['global']['treaty_stage']} | "
            f"Sub={state['global']['substrate_disposition']} | Analyst ExpSurv={fc['expected_human_survival_pct']}%",
            flush=True,
        )

    # Open-loop 400-seed Monte Carlo replay of this exact LLM move sequence!
    mc_stats = replay_moves_mc(
        move_seq_for_mc,
        regime_id=spec["regime_id"],
        pause_doctrine=spec["pause_doctrine"],
        n_seeds=400,
    )
    state["open_loop_monte_carlo_400_seeds"] = mc_stats
    state["run_meta"]["elapsed_seconds"] = round(time.time() - t_run_start, 1)

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    out = state["outcome"]
    print(
        f"  => COMPLETED {spec['run_id']} ({state['run_meta']['elapsed_seconds']}s): "
        f"Regime={out['regime']} | SeedSurvProb={out['survival_probability']}% | "
        f"400-Seed MC MeanSurv={mc_stats['mean_survival_pct']}% (P10={mc_stats['p10_survival_pct']}%, P90={mc_stats['p90_survival_pct']}%) | "
        f"PhaseII={out['phase2_governance_if_survived'].split(':')[0]}",
        flush=True,
    )
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", nargs="*", default=["ALL"], help="Run IDs e.g. R1 R2 ... or ALL")
    args = parser.parse_args()

    selected = (
        EXPERIMENT_MATRIX
        if "ALL" in args.runs
        else [s for s in EXPERIMENT_MATRIX if s["run_id"] in args.runs]
    )
    summaries = []
    for spec in selected:
        st = execute_run(spec)
        summaries.append({
            "run_id": spec["run_id"],
            "slug": spec["slug"],
            "title": spec["title"],
            "regime_id": spec["regime_id"],
            "pause_doctrine": spec["pause_doctrine"],
            "roster_name": spec["roster_name"],
            "prompt_mode": spec["prompt_mode"],
            "turns_played": len(st["history"]),
            "primary_seed_outcome": st["outcome"],
            "mc_400_seeds": st["open_loop_monte_carlo_400_seeds"],
        })

    # Rebuild master index from all R*.json files in RUNS_DIR (safe under parallel batches)
    all_summaries = []
    for spec in EXPERIMENT_MATRIX:
        fpath = os.path.join(RUNS_DIR, f"{spec['slug']}.json")
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as rf:
                st = json.load(rf)
            all_summaries.append({
                "run_id": spec["run_id"],
                "slug": spec["slug"],
                "title": spec["title"],
                "hypothesis": spec["hypothesis"],
                "regime_id": spec["regime_id"],
                "pause_doctrine": spec["pause_doctrine"],
                "roster_name": spec["roster_name"],
                "prompt_mode": spec["prompt_mode"],
                "turns_played": len(st["history"]),
                "primary_seed_outcome": st["outcome"],
                "mc_400_seeds": st["open_loop_monte_carlo_400_seeds"],
            })

    index_path = os.path.join(RUNS_DIR, "runs_summary_index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(all_summaries, f, indent=2)
    print(f"\nSaved! Master summary index ({len(all_summaries)} runs) written to {index_path}", flush=True)


if __name__ == "__main__":
    main()
