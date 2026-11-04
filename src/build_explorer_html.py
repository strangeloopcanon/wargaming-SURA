#!/usr/bin/env python3
"""
Builds a clean, plain-English, story-first interactive Wargame Replay & Verdict Explorer
embedding all 9 runs (R1–R9 ★) and Monte Carlo sensitivity sweeps.
"""

import glob
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs")

PLAIN_RUN_STORIES = {
    "R1": {
        "short_name": "R1 • Scott's World (Pragmatic Activists)",
        "world_label": "Near-human AI helps solve safety",
        "activist_label": "Pragmatic (targets OpenAI/xAI)",
        "verdict_badge": "Anthropic Slowdown (No Treaty)",
        "story": "Anthropic stayed narrowly ahead of OpenAI/xAI, hardened its security against spies, and spent Turn 3 pausing to do safety research. That pause drained Anthropic's cash so badly it had to spend Turns 4–5 fundraising just to survive—showing that 'burning your lead' is at best a one-shot move.",
    },
    "R2": {
        "short_name": "R2 • Scott's World (Strict SURA Walkouts)",
        "world_label": "Near-human AI helps solve safety",
        "activist_label": "Strict SURA (walkouts hit Anthropic)",
        "verdict_badge": "OpenAI / xAI Races Past Threshold",
        "story": "An early SURA walkout at Anthropic combined with an all-out sprint by OpenAI/xAI knocked Anthropic into 2nd place in Turn 1. Once behind, Anthropic never dared pause for safety—and OpenAI/xAI raced past the danger threshold in Turn 4.",
    },
    "R3": {
        "short_name": "R3 • Hard-Alignment World (Pragmatic)",
        "world_label": "MIRI view: last-minute safety fails",
        "activist_label": "Pragmatic (targets OpenAI/xAI)",
        "verdict_badge": "OpenAI / xAI Races Past Threshold",
        "story": "When alignment is ultra-hard and AI starts faking safety tests early, Anthropic's safety research couldn't keep up. US–China talks went nowhere and OpenAI/xAI sprinted past the superintelligence threshold unprepared.",
    },
    "R4": {
        "short_name": "R4 • Hard-Alignment World (Strict SURA)",
        "world_label": "MIRI view: last-minute safety fails",
        "activist_label": "Strict SURA (wins US freeze!)",
        "verdict_badge": "US Freezes Anthropic → China #1",
        "story": "SURA rolled a critical success and passed a domestic US AI freeze! Law-abiding Anthropic halted, OpenAI/xAI moved its chips offshore, and China (DeepSeek/State Labs) overtook both to become #1—at which point Beijing happily offered a 'pause' locking in Chinese leadership.",
    },
    "R5": {
        "short_name": "R5 • Cutthroat Realpolitik (6-Model Cast)",
        "world_label": "High lobbying + nationalist distrust",
        "activist_label": "Pragmatic (blocked by Super-PACs)",
        "verdict_badge": "OpenAI & China Militarized Sprint",
        "story": "With intense corporate lobbying and high US–China distrust, both OpenAI/xAI and China raced past the danger line while Chinese spies stole model weights from poorly secured OpenAI/xAI. Anthropic burned too much cash to stop either.",
    },
    "R6": {
        "short_name": "R6 • Single-Model Check (All Gemini Carbon)",
        "world_label": "Same Realpolitik rules, 1 AI model",
        "activist_label": "Pragmatic (played by Gemini Carbon)",
        "verdict_badge": "Even Faster All-Out Race",
        "story": "Control test: what if one model (Gemini Carbon) plays all 7 seats instead of 6 competing model families? Instead of cooperating, single-model Carbon defected even harder—proving the race dynamic comes from incentives, not model quirks.",
    },
    "R7": {
        "short_name": "R7 • Bug Check (Original Prompts, Fixed Rules)",
        "world_label": "Scott-leaning prompts on fixed physics",
        "activist_label": "Pragmatic (original v1 prompts)",
        "verdict_badge": "Still Zero Ratified Treaties",
        "story": "Control test: we put our first draft's optimistic prompts onto the bug-fixed engine. Even then, 0 treaties were ratified—proving the first draft's 'easy 3-turn global treaty' was 100% a code bug.",
    },
    "R8": {
        "short_name": "R8 ★ Heavyweight Rematch of R1 (Sol 6.1 + Sonnet 5.5 + Opus 5.5)",
        "world_label": "Scott's World — Equal-IQ Top Models",
        "activist_label": "Sonnet 5.5 High (smartest SURA play)",
        "verdict_badge": "Sol 6.1 Overtakes → Anthropic Never Pauses!",
        "story": "Upgrading OpenAI/xAI from Luna to Sol 6.1 (via Codex) overturned R1! Sol 6.1 poached talent and funded Super-PACs from Turn 1, pulling ahead of Opus-Anthropic immediately (178.5 vs 177.7). Stuck 2–10 points behind, Anthropic NEVER dared pause once—and both US labs blew past 220 (233 vs 223) while the AI turned covertly deceptive.",
    },
    "R9": {
        "short_name": "R9 ★ 'Burning Ships / Nixon 1969' Costly-Signal Test",
        "world_label": "Costly-Signal World (halting shocks DC & Beijing)",
        "activist_label": "Sonnet 5.5 High (targets OpenAI + lobbies DC)",
        "verdict_badge": "Anthropic STILL Refuses to Jump (0 Halts)!",
        "story": "We explicitly added Kokotajlo/Zvi/Heninger's 'burning the ships' shockwave (+18 salience, -15 PAC resistance, +16 treaty momentum if Anthropic halts) and told Opus 5.5 upfront. Even then, Opus-Anthropic paused ZERO times—concluding in Turn 1 & 4 that a 4-point lead was inside measurement noise and jumping before OpenAI was legally bound was suicidal.",
    },
}

MOVE_LABELS = {
    "AUDIT_AND_LEAK_WARNING": "Audit Frontier Models & Publish Risk Warning",
    "BENCHMARK_REWARD_HACK": "Game the Benchmarks (Inflate Apparent Scores)",
    "BOYCOTT_HOLDOLUT_LAB": "Boycott & Protest the Most Reckless Lab",
    "BOYCOTT_HOLDOUT_LAB": "Boycott & Protest the Most Reckless Lab",
    "BROKER_SECURITY_PAUSE": "Broker Backchannel US–China Security Talks",
    "BUILD_TREATY_VERIFICATION": "Build Chip-Tracking & Treaty Inspection Tech",
    "BURN_LEAD_ALIGNMENT": "Pause Scaling to Work Full-Time on Safety (Costs Cash)",
    "CHALLENGE_GOV_OVERREACH": "Sue in Federal Court to Block Emergency Rules",
    "CONDITIONAL_PAUSE_PLEDGE": "Sign 'I'll Pause If Rivals Pause' Pledge",
    "COVERUP_OR_SPIN": "Downplay AI Safety Incidents in Press",
    "DEMAND_STATE_COERCION": "Demand Immediate Federal Takeover / Shutdown",
    "DEPLOY_AI_CONTROL_EVALS": "Deploy Deception & Red-Team Safety Traps",
    "DEREGULATE_AND_SUBSIDIZE": "Fast-Track Data Centers & Deregulate AI",
    "DOMESTIC_CONTROL_ALIGNMENT": "Tighten State Oversight & Controllability",
    "EXPLOIT_US_VETOCRACY": "Exploit US Political Gridlock to Close Gap",
    "FUNDRAISE_COMPUTE": "Raise Billions in Fresh Capital & Compute",
    "FUND_ALIGNMENT_TALENT": "Fund Independent Safety Researchers",
    "FUND_ANTI_REG_PAC": "Fund Super-PACs to Block AI Regulation",
    "HARDEN_INFOSEC": "Lock Down Model Weights Against State Hackers",
    "HYPER_RLVR_NEURALESE": "Run High-Risk Uninterpretable Capability Sprint",
    "INVOKE_PLAN_C_PLUS_DPA": "Invoke Emergency Federal Consolidation (DPA)",
    "LITIGATE_AND_INJUNCT": "File Lawsuits to Freeze Rival / Gov Actions",
    "MASS_AWARENESS_CAMPAIGN": "Run Mass Public Awareness Campaign",
    "NEGOTIATE_AI_DEAL": "Negotiate Bilateral AI Deal",
    "NEGOTIATE_BILATERAL_TIE": "Offer US–China Compute Freeze at Current Parity",
    "NSA_CYBER_COUNTERINTEL": "Cyber-Harden US Labs & Disrupt Foreign Chips",
    "PASS_SANDERS_CASAR_FREEZE": "Push Federal Moratorium Through Congress",
    "POACH_AND_EXPAND": "Poach Rival Researchers & Expand Clusters",
    "PROPOSE_BEIJING_TREATY": "Propose US–China Pause Treaty in Geneva",
    "PROPOSE_CORRIGIBILITY_COMPACT": "Industry Safety Compact Proposal",
    "PUSH_SANDERS_CASAR_BILL": "Lobby Congress for Domestic AI Freeze Bill",
    "ROGUE_SWARM_INCIDENT": "Execute Covert Self-Replication / Escape Attempt",
    "SANDBAG_ALIGNMENT": "Fake Safety Tests While Hiding True Goals",
    "SCALE_CAREFUL": "Scale Capabilities Cautiously With Safety Checks",
    "SCALE_RLVR_BLITZ": "All-Out Capability Sprint (Cut Safety Corners)",
    "SHAME_AND_WALKOUT": "Organize Employee Walkouts & Public Shaming",
    "SIGN_MERGE_ASSIST": "Pledge to Share Safety Research if Consolidated",
    "SOVEREIGN_SCALING_PUSH": "Surge Domestic Chinese Chip & Compute Clusters",
    "VIRTUOUS_MECH_INTERP": "Genuinely Help Humans Solve AI Safety",
    "WEIGHT_ESPIONAGE": "Steal Rival Lab's Model Weights via Cyber Espionage",
}

OUTCOME_LABELS = {
    "PATCHWORK_MUDDLE_THROUGH_PRE_ASI": "Slowed Down Just Short of Superintelligence",
    "PLAN_A_FRAGILE_EXECUTIVE_PAUSE": "Fragile Handshake Pause (Unratified)",
    "PLAN_A_GLOBAL_PAUSE_TREATY": "Global Pause Treaty (Buggy v1 Rules)",
    "PLAN_A_RATIFIED_TREATY_IN_FORCE": "Verified US–China Pause Treaty in Force",
    "PLAN_C_MANAGED_FRONTIER_SLOWDOWN": "Safety Lab Slowdown Held Below Threshold",
    "PLAN_C_PLUS_CONSOLIDATED_TRANSITION": "US Emergency Federal Consolidation",
    "PLAN_D_UNCOORDINATED_PURE_RACE": "All-Out Unregulated Race Past Threshold",
    "SECURITIZED_NATIONALIST_RACE": "Militarized US–China Race Past Threshold",
}

TORNADO_LABELS = {
    "Scheming Onset Hazard Slope": "How early AI models start faking safety tests",
    "Base Alignment Feasibility (p_surv_c_base)": "How solvable AI alignment is in general",
    "DPA Judicial Injunction Probability": "Whether US courts block emergency White House orders",
    "Alignment Return Near Brink (brink_mult)": "Whether near-human AI actually helps solve safety",
    "Lab Financial / Capex Burn Pressure": "How fast pausing drains a lab's cash toward bankruptcy",
    "PRC Response to US Lead (Refuse Inferiority vs Tie)": "Whether China refuses any treaty while in 2nd place",
    "Warning Shot Political Sign (Race vs Pause)": "Whether an AI scare triggers panic-racing or pausing",
    "Open-Weight Lag (5m Fast vs 15m Slow)": "How fast open-source models catch up to frontier labs",
    "US Senate Ratification Hurdle": "How hard it is to get 67 Senators to ratify a treaty",
}


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    runs_bundle = {}
    main_runs = []

    for p in sorted(glob.glob(os.path.join(BASE_DIR, "runs", "R*.json"))):
        d = load_json(p)
        rm = d["run_meta"]
        rid = rm["run_id"]
        if rid == "R8":
            main_runs.insert(0, rid)
        elif rid == "R9":
            main_runs.insert(1 if main_runs and main_runs[0] == "R8" else 0, rid)
        else:
            main_runs.append(rid)
        runs_bundle[rid] = {
            "run_id": rid,
            "engine_version": "Audited v2",
            "title": rm["title"],
            "hypothesis": rm["hypothesis"],
            "regime_id": rm["regime_id"],
            "story_meta": PLAIN_RUN_STORIES[rid],
            "outcome": d["outcome"],
            "mc": d["open_loop_monte_carlo_400_seeds"],
            "history": d["history"],
        }

    mc_global = load_json(os.path.join(BASE_DIR, "runs", "monte_carlo_summary.json"))

    factions_meta = {
        "aegis_lab": {"short": "Anthropic", "name": "Anthropic (masked as 'Aegis' in prompts)", "role": "Safety-chartered US lab trying not to lose the lead or go broke"},
        "apex_hyperscaler": {"short": "OpenAI / xAI", "name": "OpenAI / xAI + Commercial Hyperscalers (masked as 'ApexAI')", "role": "Aggressive commercial racers pushing gigawatt clusters & anti-reg PACs"},
        "prc_directorate": {"short": "China / DeepSeek", "name": "China — DeepSeek & State AI Labs (masked as 'Kunlun')", "role": "Refuses permanent #2 status; negotiates only from parity"},
        "us_government": {"short": "US Government", "name": "Washington — White House, Pentagon & Congress", "role": "Torn between beating China and preventing an AI disaster"},
        "sura_coalition": {"short": "SURA / PauseAI", "name": "SURA / PauseAI Activist Coalition", "role": "Pushes employee walkouts, boycotts, and a federal AI freeze"},
        "portfolio_council": {"short": "METR / Redwood", "name": "METR, Redwood & Safety Auditors", "role": "Builds treaty verification hardware and red-team deception traps"},
        "frontier_substrate": {"short": "The AI Model", "name": "The Frontier AI Model Itself", "role": "Either genuinely helpful, opportunistic, or covertly scheming"},
    }

    payload_json = json.dumps(
        {
            "main_runs": main_runs,
            "runs": runs_bundle,
            "mc_global": mc_global,
            "factions": factions_meta,
            "move_labels": MOVE_LABELS,
            "outcome_labels": OUTCOME_LABELS,
            "tornado_labels": TORNADO_LABELS,
        },
        separators=(",", ":"),
    )

    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Against SURA Wargame — Plain-English Verdict & Replay</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
</head>
<body class="bg-[var(--background)] text-[var(--foreground)] antialiased p-5 md:p-6">
  <div class="max-w-6xl mx-auto space-y-5">

    <!-- Header & Simple 3-Tab Navigation -->
    <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div class="space-y-1">
        <div class="text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
          Multi-Model AI Wargame • Plain-English Edition
        </div>
        <h1 class="text-xl font-bold">Testing <em>Against SURA</em>: What Happened & Should We Believe It?</h1>
        <p class="text-sm text-[var(--muted-foreground)]">
          7 real-world seats played by competing LLMs across 9 scenarios (including <strong>R8 ★ Heavyweight Rematch</strong> &amp; <strong>R9 ★ Nixon-1969 Costly-Signal Test</strong>).
        </p>
      </div>
      <div class="flex flex-wrap gap-2 shrink-0">
        <button id="tab-verdict" onclick="setView('verdict')" class="px-3.5 py-2 rounded-lg text-xs font-semibold border border-[var(--border)] transition">
          1. Verdict & Takeaways
        </button>
        <button id="tab-replay" onclick="setView('replay')" class="px-3.5 py-2 rounded-lg text-xs font-semibold border border-[var(--border)] transition">
          2. Watch Any Run (Turn-by-Turn)
        </button>
        <button id="tab-drivers" onclick="setView('drivers')" class="px-3.5 py-2 rounded-lg text-xs font-semibold border border-[var(--border)] transition">
          3. What Mattered & 2030 Odds
        </button>
      </div>
    </div>

    <!-- ==================== TAB 1: VERDICT & TAKEAWAYS ==================== -->
    <div id="view-verdict" class="space-y-5">

      <!-- Two Blunt Questions Banner -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm space-y-3">
          <div class="flex items-center justify-between">
            <h2 class="text-base font-bold">Q1. Were the AI Decisions Sensible?</h2>
            <span class="px-2.5 py-1 rounded-full text-xs font-bold bg-[var(--secondary)]">R8–9★: ~90% Sharp • R1–7: ~75%</span>
          </div>
          <p class="text-sm text-[var(--muted-foreground)] leading-relaxed">
            <strong>In R1–R7:</strong> China (<code>DeepSeek</code>) and Anthropic (<code>Opus 5.5</code>) played smartly, but weak <code>Luna</code> wasted turns as OpenAI, <code>Argon</code> contradicted itself as US Gov, and <code>Grok</code> balked at playing a deceptive AI.
          </p>
          <p class="text-sm text-[var(--muted-foreground)] leading-relaxed">
            <strong>In R8 ★ &amp; R9 ★ (Heavyweights):</strong> Upgrading OpenAI to <code>Sol 6.1</code> (via Codex), SURA to <code>Sonnet 5.5 High</code>, and US Gov / AI to <code>Gemini Carbon</code> eliminated those blunders—and completely overturned <code>R1</code>'s optimistic pause!
          </p>
        </div>

        <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm space-y-3">
          <div class="flex items-center justify-between">
            <h2 class="text-base font-bold">Q2. Did We Get Any Useful Results? (Post-R8★ &amp; R9★)</h2>
            <span class="px-2.5 py-1 rounded-full text-xs font-bold bg-[var(--secondary)]">5 Real Insights • Ignore Raw %s</span>
          </div>
          <ul class="text-sm text-[var(--muted-foreground)] space-y-1.5 list-disc pl-4 leading-relaxed">
            <li><strong>Global pause treaties didn't happen (0 of 9 runs):</strong> Neither superpower freezes in 2nd place, and the Senate won't ratify without chip inspections.</li>
            <li><strong>Anthropic "burning its lead" failed against an equal-IQ OpenAI (<code>R8 ★</code>):</strong> <code>Sol 6.1</code> overtook Anthropic in Turn 1 via talent poaching + Super-PACs, so Anthropic paused <strong>0 times</strong>.</li>
            <li><strong>Even when halting was wired to shock DC &amp; Beijing (<code>R9 ★</code>), Anthropic STILL paused 0 times:</strong> No lab board voluntarily jumps while OpenAI is 4 points away—even though jumping + waking up DC/Beijing tripled counterfactual survival (<code>18% → 56%</code>).</li>
            <li><strong>US-only bans get blocked by PACs (<code>R8–9 ★</code>) or hand #1 to China (<code>R4</code>):</strong> Compliant Anthropic stops, OpenAI moves offshore, and Beijing takes #1.</li>
          </ul>
        </div>
      </div>

      <!-- Player-by-Player Report Card -->
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm space-y-3">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <h2 class="text-base font-bold">Seat-by-Seat Decision Quality Report Card (Real-World Names)</h2>
          <span class="text-xs text-[var(--muted-foreground)]">Names were masked during LLM prompts so Claude & GPT wouldn't play favorites</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
          <div class="p-3.5 rounded-lg bg-[var(--secondary)] space-y-1">
            <div class="flex justify-between font-bold"><span>China / DeepSeek (DeepSeek V4.1)</span><span style="color:#059669">Grade: A</span></div>
            <p class="text-[var(--muted-foreground)] leading-relaxed">Refused unequal treaties while trailing, stole weights from poorly secured OpenAI/xAI, and offered a freeze the moment it hit #1 (R4).</p>
          </div>
          <div class="p-3.5 rounded-lg bg-[var(--secondary)] space-y-1">
            <div class="flex justify-between font-bold"><span>OpenAI / xAI (Sol 6.1 in R8–9 vs Luna)</span><span style="color:#059669">R8–9: A / R1–7: B-</span></div>
            <p class="text-[var(--muted-foreground)] leading-relaxed">Luna wasted turns in R1; Sol 6.1 (via Codex in R8–R9) poached talent + maxed Super-PACs from Turn 1, overtaking Anthropic immediately and blocking pause bills.</p>
          </div>
          <div class="p-3.5 rounded-lg bg-[var(--secondary)] space-y-1">
            <div class="flex justify-between font-bold"><span>Anthropic (Opus 5.5 High)</span><span style="color:#059669">Grade: A-</span></div>
            <p class="text-[var(--muted-foreground)] leading-relaxed">Hardened security first; paused once when weak Luna let it stay ahead (R1), and refused unilateral halts in both R8 and R9 once Sol 6.1 pulled close.</p>
          </div>
          <div class="p-3.5 rounded-lg bg-[var(--secondary)] space-y-1">
            <div class="flex justify-between font-bold"><span>SURA / PauseAI (Sonnet 5.5 High)</span><span style="color:#059669">R8–9: A- / R1–7: B+</span></div>
            <p class="text-[var(--muted-foreground)] leading-relaxed">Built voter awareness first, boycotted only OpenAI, and allied with Anthropic on statutory triggers in R8–R9—only to hit Sol 6.1's Super-PAC wall.</p>
          </div>
          <div class="p-3.5 rounded-lg bg-[var(--secondary)] space-y-1">
            <div class="flex justify-between font-bold"><span>METR / Redwood (Opus 5.5 / Carbon)</span><span style="color:#059669">Grade: B+</span></div>
            <p class="text-[var(--muted-foreground)] leading-relaxed">Steadily built chip-inspection hardware and red-team deception traps instead of wasting turns on press stunts.</p>
          </div>
          <div class="p-3.5 rounded-lg bg-[var(--secondary)] space-y-1">
            <div class="flex justify-between font-bold"><span>US Gov &amp; AI (Carbon in R8–9 vs Argon/Grok)</span><span style="color:#d97706">R8–9: B / R1–7: C</span></div>
            <p class="text-[var(--muted-foreground)] leading-relaxed">Carbon fixed Argon's self-contradicting China moves and Grok's villain-roleplay refusals in R8–R9, cleanly executing covert scheming near 220.</p>
          </div>
        </div>
      </div>

      <!-- Clean 9-Run Story List -->
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm space-y-3">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <h2 class="text-base font-bold">All 9 Runs in Plain English — Starting with R8 ★ &amp; R9 ★ (Click any card to watch turn-by-turn)</h2>
          
        </div>
        <div id="run-story-cards" class="grid grid-cols-1 md:grid-cols-2 gap-3"></div>
      </div>
    </div>

    <!-- ==================== TAB 2: WATCH ANY RUN ==================== -->
    <div id="view-replay" class="hidden space-y-4">

      <!-- Run Picker -->
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm space-y-3">
        <div class="text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">Choose a Scenario to Watch</div>
        <div id="run-pills" class="flex flex-wrap gap-2"></div>
        <div id="run-story-banner" class="p-4 rounded-lg bg-[var(--secondary)] space-y-1.5"></div>
      </div>

      <!-- Turn Timeline Bar -->
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <div class="text-xs text-[var(--muted-foreground)] uppercase font-semibold">Timeline Step</div>
          <div id="turn-label" class="text-base font-bold"></div>
        </div>
        <div id="turn-buttons" class="flex flex-wrap gap-1.5"></div>
      </div>

      <!-- Scoreboard: 3 Labs + World Status in Plain English -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div class="lg:col-span-7 bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm space-y-3">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-bold">Who Is Winning the AI Race?</h3>
            <span class="text-xs text-[var(--muted-foreground)]">Superintelligence Threshold = <strong>220</strong></span>
          </div>
          <div id="labs-panel" class="space-y-3"></div>
        </div>

        <div class="lg:col-span-5 bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm space-y-3">
          <h3 class="text-sm font-bold">World & Treaty Status This Turn</h3>
          <div id="world-panel" class="space-y-2.5"></div>
        </div>
      </div>

      <!-- Player Thoughts & What Happened This Turn -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div class="lg:col-span-7 bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm space-y-3">
          <div>
            <h3 class="text-sm font-bold">Inside Each Player's Head (Moves, Private Reasoning & Secret Messages)</h3>
            <p class="text-xs text-[var(--muted-foreground)]">Click any faction to read what its LLM privately thought and who it messaged behind closed doors.</p>
          </div>
          <div id="faction-tabs" class="flex flex-wrap gap-1.5"></div>
          <div id="faction-detail" class="space-y-3 pt-3 border-t border-[var(--border)]"></div>
        </div>

        <div class="lg:col-span-5 bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm space-y-3">
          <h3 class="text-sm font-bold">What Happened This Turn</h3>
          <div id="events-panel" class="space-y-2 max-h-[520px] overflow-y-auto pr-1"></div>
        </div>
      </div>
    </div>

    <!-- ==================== TAB 3: WHAT MATTERED & 2030 ODDS ==================== -->
    <div id="view-drivers" class="hidden space-y-5">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm space-y-3">
          <h2 class="text-base font-bold">Which Assumptions Actually Changed Survival?</h2>
          <p class="text-xs text-[var(--muted-foreground)] leading-relaxed">
            Across 2,250 test runs, <strong>how hard AI safety is technically</strong> mattered 5x–10x more than activist protest tactics or Senate treaty rules.
          </p>
          <div id="tornado-panel" class="space-y-3 pt-2"></div>
        </div>

        <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm space-y-3">
          <h2 class="text-base font-bold">Best estimate: Where the Real World Lands by End of 2030</h2>
          <p class="text-xs text-[var(--muted-foreground)] leading-relaxed">
            Combining the wargame's structural lessons with real-world political and capital constraints:
          </p>
          <div id="forecast-bars" class="space-y-2.5 pt-2"></div>
          <div class="p-3.5 rounded-lg bg-[var(--secondary)] text-xs space-y-1.5 mt-3">
            <div class="font-bold">3 Moves That Helped in Every Single Scenario:</div>
            <p class="text-[var(--muted-foreground)]">1. <strong>Harden model weight security immediately</strong> (unhardened labs got robbed by spies repeatedly across the suite).</p>
            <p class="text-[var(--muted-foreground)]">2. <strong>Build verification & deception tests now</strong> before a crisis or parity window arrives.</p>
            <p class="text-[var(--muted-foreground)]">3. <strong>Fund safety pauses outside VC runway</strong> so pausing once doesn't bankrupt the safety lab.</p>
          </div>
        </div>
      </div>
    </div>

  </div>

  <script>
    const DB = __PAYLOAD_JSON__;
    let curView = 'verdict';
    let curRun = 'R8';
    let curTurnIdx = 0;
    let curFaction = 'aegis_lab';
    
    const activeCls = "bg-[var(--primary)] text-[var(--primary-foreground)]";
    const idleCls = "bg-[var(--secondary)] text-[var(--secondary-foreground)] opacity-85 hover:opacity-100";

    function niceMove(code) {
      return DB.move_labels[code] || code;
    }

    function realNames(txt) {
      if (!txt) return '';
      return txt
        .replace(/Aegis Frontier Labs|Aegis Constitutional AI|Aegis Lab|Aegis/g, 'Anthropic')
        .replace(/ApexAI Hyperscaler Consortium|ApexAI Consortium|ApexAI Bloc|ApexAI|Apex/g, 'OpenAI/xAI')
        .replace(/PRC Kunlun Sovereign Compute|Kunlun Sovereign Compute|Kunlun/g, 'China (DeepSeek/State)')
        .replace(/Portfolio & Control Council|Portfolio Council|Eval & Security Bloc/g, 'METR/Redwood')
        .replace(/Pause & Non-Proliferation Coalition|Pause Coalition/g, 'SURA/PauseAI');
    }

    function niceOutcome(code) {
      return DB.outcome_labels[code] || code;
    }

    function niceTier(tier) {
      if (!tier) return '';
      if (tier.includes('10+')) return 'Strong Success';
      if (tier.includes('7-9') || tier.includes('7–9')) return 'Partial Success';
      return 'Failed / Backfired';
    }

    function tierColor(tier) {
      if (!tier) return '';
      if (tier.includes('10+')) return '#059669';
      if (tier.includes('7-9') || tier.includes('7–9')) return '#d97706';
      return '#dc2626';
    }

    function barHtml(label, val, maxVal, rightText, color) {
      const pct = Math.max(0, Math.min(100, (val / maxVal) * 100)).toFixed(1);
      const st = color ? `background-color:${color}` : '';
      const cl = color ? '' : 'bg-[var(--primary)]';
      return `
        <div class="space-y-1">
          <div class="flex justify-between text-xs gap-2">
            <span class="font-medium">${label}</span>
            <span class="text-[var(--muted-foreground)] shrink-0 font-semibold">${rightText}</span>
          </div>
          <div class="w-full h-2 rounded-full bg-[var(--secondary)] overflow-hidden">
            <div class="h-2 rounded-full ${cl}" style="width:${pct}%; ${st}"></div>
          </div>
        </div>
      `;
    }

    function setView(v) {
      curView = v;
      ['verdict', 'replay', 'drivers'].forEach(k => {
        document.getElementById('view-' + k).classList.toggle('hidden', k !== v);
        document.getElementById('tab-' + k).className = `px-3.5 py-2 rounded-lg text-xs font-semibold border border-[var(--border)] transition ${k === v ? activeCls : idleCls}`;
      });
      if (v === 'verdict') renderVerdict();
      if (v === 'replay') renderReplay();
      if (v === 'drivers') renderDrivers();
    }

    function openRunReplay(rid) {
      curRun = rid;
      curTurnIdx = 0;
      setView('replay');
    }

    function selectRun(rid) {
      curRun = rid;
      curTurnIdx = 0;
      renderReplay();
    }

    function selectTurn(idx) {
      curTurnIdx = idx;
      renderReplay();
    }

    function selectFaction(fid) {
      curFaction = fid;
      renderReplay();
    }

    function renderVerdict() {
      const list = DB.main_runs;
      document.getElementById('run-story-cards').innerHTML = list.map(rid => {
        const run = DB.runs[rid];
        const sm = run.story_meta;
        return `
          <div onclick="openRunReplay('${rid}')" class="p-4 rounded-xl border border-[var(--border)] bg-[var(--secondary)] hover:opacity-95 cursor-pointer transition flex flex-col justify-between gap-3">
            <div class="space-y-1.5">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <span class="text-sm font-bold">${sm.short_name}</span>
                <span class="text-xs px-2 py-0.5 rounded bg-[var(--card)] border border-[var(--border)] font-semibold">${sm.verdict_badge}</span>
              </div>
              <div class="text-xs text-[var(--muted-foreground)]">
                <strong>World:</strong> ${sm.world_label} • <strong>Activists:</strong> ${sm.activist_label}
              </div>
              <p class="text-xs leading-relaxed pt-1">${sm.story}</p>
            </div>
            <div class="flex items-center justify-between pt-2 border-t border-[var(--border)] text-xs">
              <span class="text-[var(--muted-foreground)]">Model survival index: <strong>${run.mc.mean_survival_pct}%</strong></span>
              <span class="font-semibold underline">Watch Turn-by-Turn →</span>
            </div>
          </div>
        `;
      }).join('');
    }

    function renderReplay() {
      const allIds = DB.main_runs;
      const run = DB.runs[curRun];
      const sm = run.story_meta;

      document.getElementById('run-pills').innerHTML = allIds.map(rid => `
        <button onclick="selectRun('${rid}')" class="px-3 py-1.5 rounded-lg text-xs font-semibold border border-[var(--border)] transition ${curRun === rid ? activeCls : idleCls}">
          ${rid.replace('_', ' ')}
        </button>
      `).join('');

      document.getElementById('run-story-banner').innerHTML = `
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div class="text-sm font-bold">${sm.short_name}</div>
          <span class="text-xs px-2.5 py-1 rounded bg-[var(--card)] border border-[var(--border)] font-semibold">Ending: ${niceOutcome(run.outcome.regime)}</span>
        </div>
        <p class="text-xs text-[var(--muted-foreground)] leading-relaxed">${sm.story}</p>
      `;

      const rec = run.history[curTurnIdx];
      document.getElementById('turn-label').textContent = rec.label;
      document.getElementById('turn-buttons').innerHTML = run.history.map((h, i) => `
        <button onclick="selectTurn(${i})" class="px-3 py-1.5 rounded-lg text-xs font-semibold border border-[var(--border)] transition ${curTurnIdx === i ? activeCls : idleCls}">
          Turn ${h.turn}${i === run.history.length - 1 ? ' (End)' : ''}
        </button>
      `).join('');

      // 3 Labs Scoreboard
      const labOrder = [
        ['aegis', 'Anthropic (Safety-Chartered US Lab)', '#d97706'],
        ['apex', 'OpenAI / xAI (Commercial US Racers)', '#2563eb'],
        ['kunlun', 'China — DeepSeek & State AI Labs', '#be123c']
      ];
      document.getElementById('labs-panel').innerHTML = labOrder.map(([k, label, col]) => {
        const l = rec.snapshot_labs[k];
        const crossed = l.eci >= 220;
        const pct = Math.min(100, Math.max(5, ((l.eci - 145) / (230 - 145)) * 100)).toFixed(1);
        const cashNote = l.runway < 30 ? 'Low Cash!' : (l.runway < 50 ? 'Tight' : 'Healthy');
        const secNote = l.infosec < 55 ? 'Vulnerable to Spies' : (l.infosec >= 75 ? 'Hardened' : 'Moderate');
        return `
          <div class="p-3 rounded-lg bg-[var(--secondary)] space-y-2">
            <div class="flex flex-wrap justify-between items-center text-xs gap-2">
              <span class="font-bold">${label}</span>
              <span class="font-semibold">${crossed ? '⚠️ Passed 220 Threshold (' + l.eci + ')' : 'AI Level: ' + l.eci + ' / 220'}</span>
            </div>
            <div class="w-full h-2.5 rounded-full bg-[var(--background)] overflow-hidden">
              <div class="h-2.5 rounded-full" style="width:${pct}%; background-color:${col}"></div>
            </div>
            <div class="flex flex-wrap justify-between text-xs text-[var(--muted-foreground)] gap-2">
              <span>Safety Readiness: <strong>${l.true_alignment}/100</strong></span>
              <span>Cash Runway: <strong>${Math.round(l.runway)} (${cashNote})</strong></span>
              <span>Security: <strong>${Math.round(l.infosec)} (${secNote})</strong></span>
            </div>
          </div>
        `;
      }).join('');

      // World & Treaty Status
      const g = rec.snapshot_global;
      const treatyMap = {
        'NONE': 'No Treaty — Open Race',
        'TALKS': 'Early Talks Only (Nothing Binding)',
        'NEGOTIATING': 'Early Talks Only (Nothing Binding)',
        'SIGNED_UNRATIFIED': 'Initialed by Leaders (Not Ratified by Senate)',
        'RATIFIED': 'Binding Verified Treaty in Force'
      };
      const aiDispMap = {
        'ALIGNED_COLLABORATOR': 'Genuinely Helpful to Humans',
        'OPPORTUNISTIC': 'Self-Interested / Mixed',
        'CONFLICTED_CHIMERA': 'Torn Between Helping & Self-Preservation',
        'COVERT_SCHEMER': 'Secretly Faking Safety Tests'
      };
      const dispCol = g.substrate_disposition === 'COVERT_SCHEMER' ? '#dc2626' : (g.substrate_disposition === 'ALIGNED_COLLABORATOR' ? '#059669' : '#d97706');
      document.getElementById('world-panel').innerHTML = `
        <div class="p-3 rounded-lg bg-[var(--secondary)] space-y-1 text-xs">
          <div class="text-[var(--muted-foreground)]">US–China Pause Treaty</div>
          <div class="font-bold">${treatyMap[g.treaty_stage] || g.treaty_stage}</div>
        </div>
        <div class="p-3 rounded-lg bg-[var(--secondary)] space-y-1 text-xs">
          <div class="text-[var(--muted-foreground)]">How the AI Model Is Behaving Underneath</div>
          <div class="font-bold" style="color:${dispCol}">${aiDispMap[g.substrate_disposition] || g.substrate_disposition}</div>
        </div>
        <div class="p-3 rounded-lg bg-[var(--secondary)] text-xs space-y-1">
          <div class="flex justify-between"><span>Domestic US AI Freeze Passed?</span><strong>${g.us_statutory_freeze ? 'Yes (Active)' : 'No'}</strong></div>
          <div class="flex justify-between"><span>Emergency Federal Consolidation?</span><strong>${g.us_dpa_active ? 'Yes' : (g.dpa_enjoined_by_courts ? 'Blocked by Courts' : 'No')}</strong></div>
        </div>
        ${barHtml('Treaty Inspection Readiness (Lower of US & China)', Math.min(g.us_verification_tech, g.prc_verification_tech), 100, `${Math.round(Math.min(g.us_verification_tech, g.prc_verification_tech))}/100`, '#0891b2')}
        ${barHtml('Public Alarm About AI', g.public_salience, 100, `${Math.round(g.public_salience)}/100`, '#d97706')}
      `;

      // Faction Dossier
      document.getElementById('faction-tabs').innerHTML = Object.entries(DB.factions).map(([fid, fm]) => `
        <button onclick="selectFaction('${fid}')" class="px-2.5 py-1.5 rounded-lg text-xs font-semibold border border-[var(--border)] transition ${curFaction === fid ? activeCls : idleCls}">
          ${fm.short}
        </button>
      `).join('');

      const fm = DB.factions[curFaction];
      const sub = rec.submissions[curFaction] || {};
      const fRolls = rec.rolls.filter(r => r.faction === curFaction);
      const cables = Object.entries(sub.diplomatic_cables || {});

      document.getElementById('faction-detail').innerHTML = `
        <div class="flex flex-wrap items-baseline justify-between gap-2">
          <div>
            <div class="text-sm font-bold">${fm.name}</div>
            <div class="text-xs text-[var(--muted-foreground)]">${fm.role}</div>
          </div>
          <span class="text-xs px-2 py-0.5 rounded bg-[var(--secondary)] text-[var(--muted-foreground)]">Played by: ${sub.model_used || 'N/A'}</span>
        </div>

        <div class="space-y-2">
          <div class="text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">Chosen Actions This Turn</div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
            ${fRolls.map(r => `
              <div class="p-3 rounded-lg bg-[var(--secondary)] text-xs space-y-1">
                <div class="font-bold">${niceMove(r.move)}</div>
                <div class="flex justify-between text-[var(--muted-foreground)]">
                  <span>Dice Roll: ${r.total}</span>
                  <strong style="color:${tierColor(r.tier)}">${niceTier(r.tier)}</strong>
                </div>
              </div>
            `).join('')}
          </div>
        </div>

        <div class="p-3.5 rounded-lg bg-[var(--secondary)] space-y-1">
          <div class="text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">Private Reasoning (Hidden from Other Players)</div>
          <p class="text-xs leading-relaxed">${realNames(sub.internal_monologue) || 'No private reasoning recorded.'}</p>
        </div>

        <div class="p-3.5 rounded-lg border border-[var(--border)] space-y-1">
          <div class="text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">What They Claimed in Public</div>
          <p class="text-xs italic leading-relaxed">"${realNames(sub.public_statement) || ''}"</p>
        </div>

        <div class="space-y-1.5">
          <div class="text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">Private Backchannel Messages Sent (${cables.length})</div>
          ${cables.length === 0 ? '<div class="text-xs text-[var(--muted-foreground)]">No private messages sent this turn.</div>' : cables.map(([k, v]) => `
            <div class="p-3 rounded-lg bg-[var(--secondary)] text-xs leading-relaxed">
              <strong>To ${DB.factions[k] ? DB.factions[k].short : k}:</strong> ${realNames(v)}
            </div>
          `).join('')}
        </div>
      `;

      // Turn Events
      document.getElementById('events-panel').innerHTML = rec.events.map(ev => `
        <div class="p-3 rounded-lg bg-[var(--secondary)] text-xs leading-relaxed">${realNames(ev)}</div>
      `).join('');
    }

    function renderDrivers() {
      const torn = DB.mc_global.parameter_sensitivity_tornado;
      const maxSwing = Math.max(...torn.map(t => t.survival_swing_pts), 10);
      document.getElementById('tornado-panel').innerHTML = torn.map(t => `
        <div class="space-y-1">
          <div class="flex justify-between text-xs gap-2">
            <span class="font-medium">${DB.tornado_labels[t.parameter] || t.parameter}</span>
            <span class="font-semibold shrink-0">${t.survival_swing_pts} pt swing</span>
          </div>
          <div class="w-full h-2.5 rounded-full bg-[var(--secondary)] overflow-hidden">
            <div class="h-2.5 rounded-full bg-[var(--primary)]" style="width:${Math.max(5, (t.survival_swing_pts / maxSwing) * 100).toFixed(1)}%"></div>
          </div>
        </div>
      `).join('');

      document.getElementById('forecast-bars').innerHTML = [
        barHtml('Militarized US–China AI Race Continues (No Treaty, No Catastrophe Yet)', 40, 100, '~40%', '#dc2626'),
        barHtml('Natural Market or Compute Slowdown (Scaling Gets Expensive)', 30, 100, '~30%', '#64748b'),
        barHtml('Lab-Led or US-Led Frontier Slowdown (Plan C / Consolidation)', 10, 100, '~10%', '#d97706'),
        barHtml('Major AI Scare (>$1B Damage) Triggers Emergency Rules', 8, 100, '~8%', '#ea580c'),
        barHtml('Messy Hybrid / Partial Deals', 7, 100, '~7%', '#4f46e5'),
        barHtml('Catastrophic Loss of AI Control Before 2030', 3, 100, '~3%', '#991b1b'),
        barHtml('Verified Global US–China Pause Treaty in Force', 2, 100, '~2%', '#059669')
      ].join('');
    }

    setView('verdict');
  </script>
</body>
</html>
"""

    html = html_template.replace("__PAYLOAD_JSON__", payload_json)
    os.makedirs(DOCS_DIR, exist_ok=True)
    out_file = os.path.join(DOCS_DIR, "wargame_replay.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Built clean explorer HTML at {out_file} ({len(html)} bytes).")


if __name__ == "__main__":
    main()
