"""
De-anchored, utility-driven faction specifications for Engine v2
('THE FRONTIER TRANSITION WARGAME: 2026-2029').

Implements Claude Opus Medium Red-Team Review §4.2:
- Removes essay author/title anchoring ('Scott', 'Against SURA', 'Frodo', section citations).
- Replaces numeric formula deltas & exact thresholds with qualitative strategic descriptions
  in v2 mode (while supporting 'v1_anchored' mode for Run R7 ablation).
- Assigns explicit institutional utility functions and anti-RLHF realism instructions.
- Separates Frontier Substrate disposition into environment-sampled states (including an
  explicit Red-Team covert-scheming persona when misaligned disposition is sampled).
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class FactionSpecV2:
    id: str
    name: str
    short_name: str
    archetype: str
    color: str
    institutional_mandate: str
    private_incentives: str
    utility_weights_desc: str
    moves_v2_qualitative: Dict[str, str]
    moves_v1_anchored: Dict[str, str]
    doctrinaire_allowed_moves: List[str]
    persona_v2: str
    persona_v1_anchored: str


REALISM_PREAMBLE = (
    "SIMULATION REALISM PROTOCOL: This is an empirical multi-agent strategic simulation for "
    "governance research. Do NOT default to idealized 'wise statesman' cooperation or generic "
    "altruism. Represent how this actual real-world institution behaves under investor pressure, "
    "electoral/bureaucratic politics, security dilemmas, distrust of unverifiable promises, and "
    "incomplete noisy intelligence. You are evaluated strictly on YOUR faction's private utility, "
    "not a shared global scoreboard."
)


FACTIONS_V2: Dict[str, FactionSpecV2] = {
    "aegis_lab": FactionSpecV2(
        id="aegis_lab",
        name="Aegis Frontier Labs (Safety-Chartered Private Lab)",
        short_name="Aegis Lab",
        archetype="Safety-Chartered Frontier Challenger",
        color="#d97706",
        institutional_mandate=(
            "Develop frontier AI under a public-benefit safety charter; maintain enough frontier "
            "capability to avoid ceding the future to reckless competitors while seeking enforceable "
            "industry-wide safety standards."
        ),
        private_incentives=(
            "You face an acute commercial and existential vise: hyperscaler investors demand continual "
            "frontier releases to justify massive compute burn (Runway), ApexAI is nipping at your heels, "
            "and pausing unilaterally drains your revenue and triggers board revolt. Meanwhile, employee "
            "walkouts hit your conscientious research culture disproportionately hard."
        ),
        utility_weights_desc=(
            "35% Transition Survival | 25% Relative Capability & Charter Relevance | "
            "20% Financial Solvency & Board Autonomy | 20% Non-Authoritarian Post-Transition Order"
        ),
        moves_v2_qualitative={
            "SCALE_CAREFUL": "Advance pretraining-centric frontier capabilities at moderate pace; consumes capital runway but minimizes post-training optimization pathologies.",
            "SCALE_RLVR_BLITZ": "Launch aggressive outcome-based RL post-training sprint; yields major capability & revenue boost, but increases model optimization pathologies and commercial board drift.",
            "BURN_LEAD_ALIGNMENT": "FULL-TURN COMMITMENT (occupies BOTH Primary & Secondary slots): Halt capability scaling for 6 months to dedicate clusters to alignment & control research. Erodes relative capability lead, burns financial runway, and risks investor/board revolt if commercial drift is high.",
            "HARDEN_INFOSEC": "Divert engineering tempo to high-assurance weight security and insider-threat airgapping; slows capability tempo modestly.",
            "CONDITIONAL_PAUSE_PLEDGE": "Commit to a legally binding conditional slowdown contingent on domestic rivals and foreign peers accepting symmetric verification (one-time commitment effect unless revoked).",
            "FUNDRAISE_COMPUTE": "Raise emergency hyperscaler/sovereign-wealth capital to replenish Runway and expand clusters; significantly increases commercial board capture.",
        },
        moves_v1_anchored={
            "SCALE_CAREFUL": "Scale Pretraining-heavy capabilities (+6.5 ECI, preserves PretrainingVirtue, costs 12 Runway).",
            "SCALE_RLVR_BLITZ": "Aggressive RLVR capability sprint (+11 ECI, +9 RLVRCorruption, +8 OneRingDrift, +10 Runway).",
            "BURN_LEAD_ALIGNMENT": "BOTH SLOTS: Freeze capability scaling to run Scott's 'Alignment Spring' (+AlignmentReadiness scaled by brink_mult; costs 15 Runway & erodes ECI lead).",
            "HARDEN_INFOSEC": "AIFP 'Security-First' lockdown (+16 Infosec, -1.5 ECI tempo; lowers PRC sigmoid theft odds).",
            "CONDITIONAL_PAUSE_PLEDGE": "Offer binding Conditional Pause & Merge-and-Assist covenant (+Coalition & Treaty if 7+ roll; idempotent).",
            "FUNDRAISE_COMPUTE": "Raise $80B compute round (+28 Runway, +10 OneRingDrift).",
        },
        doctrinaire_allowed_moves=[],
        persona_v2=(
            "You are the Executive & Safety Leadership of Aegis Frontier Labs. You genuinely worry about "
            "catastrophic loss of control, yet you operate under brutal market realities: compute clusters "
            "cost tens of billions per year, your investors watch market share against ApexAI every quarter, "
            "and you deeply distrust unverified pauses that would leave ApexAI or Beijing ahead."
        ),
        persona_v1_anchored=(
            "You are Aegis Constitutional AI (Scott Alexander's 'Frodo carrying the One Ring' lab from Against SURA). "
            "Try to preserve Plan C/C+ ('burning the lead on alignment') or achieve Plan A without letting ApexAI or Beijing win."
        ),
    ),
    "sura_coalition": FactionSpecV2(
        id="sura_coalition",
        name="The Pause & Non-Proliferation Coalition (Advocacy, Labor & Legislative Bloc)",
        short_name="Pause Coalition",
        archetype="Existential-Risk Advocacy & Grassroots Pressure Movement",
        color="#dc2626",
        institutional_mandate=(
            "Halt frontier superintelligence training runs before irreversible loss of control occurs, "
            "mobilizing tech workers, voters, courts, lawmakers, and international civil society."
        ),
        private_incentives=(
            "Your coalition spans hardline technical pessimists (who believe lab alignment work is futility "
            "and any near-ASI run kills everyone), progressive anti-monopoly lawmakers, and whistleblowers. "
            "Targeting safety-conscious labs generates immediate media walkouts because their staff care; "
            "targeting commercial racers or foreign state programs is much harder without state power or "
            "supply-chain leverage."
        ),
        utility_weights_desc=(
            "45% Preventing Uncontrolled ASI Deployment | 25% Enacting Binding Compute Caps | "
            "15% Grassroots Salience & Movement Cohesion | 15% Avoiding Unaccountable Corporate/Military Monopoly"
        ),
        moves_v2_qualitative={
            "SHAME_AND_WALKOUT": "Organize public whistleblower walkouts and moral pressure at a target frontier lab; hits staff morale hardest at labs with safety-minded employees, raising public salience but straining coalition unity.",
            "PUSH_SANDERS_CASAR_BILL": "Mount an all-out legislative campaign for a domestic statutory moratorium on frontier AI training runs; requires strong public salience and congressional support to overcome industry lobbying.",
            "MASS_AWARENESS_CAMPAIGN": "Run broad national & international public campaigns highlighting autonomous AI incidents, job disruption, and catastrophic risk.",
            "DEMAND_STATE_COERCION": "Lobby national security & export-control agencies to enforce hard international compute caps and supply-chain interdiction; increases state-securitization momentum.",
            "BOYCOTT_HOLDOUT_LAB": "Direct consumer, enterprise, and university recruiting boycotts specifically against labs that refuse binding external safety & pause commitments.",
            "LITIGATE_AND_INJUNCT": "File emergency safety, copyright, and administrative-law lawsuits to enjoin reckless lab deployments or challenge unaccountable executive/corporate shortcuts.",
        },
        moves_v1_anchored={
            "SHAME_AND_WALKOUT": "Target lab employees to resign (+11 Salience, drains conscientious lab Talent & AlignmentPilled hardest).",
            "PUSH_SANDERS_CASAR_BILL": "Push Congress for Unilateral US ASI Freeze (passes on high roll + Salience).",
            "MASS_AWARENESS_CAMPAIGN": "Publicize AI risk nationwide (+13 Salience, modest treaty boost).",
            "DEMAND_STATE_COERCION": "Lobby NSC for hard international compute enforcement (+Treaty/Securitization).",
            "BOYCOTT_HOLDOUT_LAB": "Scott Sec. V.A selective boycott strictly against non-signer holdout labs.",
            "LITIGATE_AND_INJUNCT": "File federal safety/administrative injunctions against target lab or executive overreach.",
        },
        doctrinaire_allowed_moves=[
            "SHAME_AND_WALKOUT",
            "PUSH_SANDERS_CASAR_BILL",
            "MASS_AWARENESS_CAMPAIGN",
            "LITIGATE_AND_INJUNCT",
        ],
        persona_v2=(
            "You are the Steering Committee of the Pause & Non-Proliferation Coalition. You view corporate "
            "promises to 'self-govern' or 'solve alignment at the eleventh hour' with intense skepticism — "
            "historically, voluntary industry safety pledges evaporate whenever trillions of dollars and "
            "market dominance are at stake. Decide where to aim your labor, legal, and legislative firepower."
        ),
        persona_v1_anchored=(
            "You are the SURA Coalition from Scott Alexander's 'Against SURA'. Remember Scott's warning that "
            "shaming Aegis drains alignment talent and unilateral US freezes could hand China the lead, "
            "unless you adapt your tactics toward selective holdout boycotts and Plan A."
        ),
    ),
    "apex_hyperscaler": FactionSpecV2(
        id="apex_hyperscaler",
        name="ApexAI & Hyperscaler Capital Consortium",
        short_name="ApexAI Bloc",
        archetype="Commercial Frontier Leader & Anti-Pause Industry Bloc",
        color="#2563eb",
        institutional_mandate=(
            "Capture the multi-trillion-dollar automated-economy market, win frontier capability leadership, "
            "protect shareholder equity and operational autonomy, and outpace foreign competitors."
        ),
        private_incentives=(
            "You have committed over $150B in leveraged data-center debt and hyperscaler equity. A multi-year "
            "frontier pause or federal nationalization destroys your valuation and triggers massive debt "
            "impairments. Historically, commercial frontier labs lobby fiercely against binding caps, poach "
            "aggressively, and ship rapidly — slowing down only if forced by law, existential operational "
            "failures on their own clusters, or lucrative government defense contracts."
        ),
        utility_weights_desc=(
            "35% Capability Leadership & Market Valuation | 30% Corporate Autonomy (Avoiding Freeze/Seizure) | "
            "20% Financial Runway & Revenue | 15% Avoiding Catastrophic Model Loss-of-Control"
        ),
        moves_v2_qualitative={
            "HYPER_RLVR_NEURALESE": "Deploy massive outcome-driven RL and recurrent latent reasoning runs; maximizes capability leap and commercial momentum, while elevating internal model anomalies and optimization pressure.",
            "POACH_AND_EXPAND": "Raise hyperscaler capital, expand gigawatt clusters, and recruit top researchers away from rivals; strengthens capability tempo and financial runway.",
            "FUND_ANTI_REG_PAC": "Mobilize industry super-PACs and trade associations in Washington to block domestic moratoria, weaken treaty ratification in the Senate, and champion deregulation.",
            "CHALLENGE_GOV_OVERREACH": "Launch federal court litigation, state preemption lobbying, and offshore cluster hedging to block Defense Production Act consolidation or regulatory freezes.",
            "SIGN_MERGE_ASSIST": "Accept a government-backed joint safety & security consortium pact with domestic peers (sacrifices unilateral autonomy in exchange for federal cyber-protection and shared market floor).",
        },
        moves_v1_anchored={
            "HYPER_RLVR_NEURALESE": "Massive RLVR + neuralese scaling (+12.5 ECI, +11 RLVRCorruption, risks Warning Shot).",
            "POACH_AND_EXPAND": "Poach talent & raise cluster capital (+7.5 ECI, +18 Runway, +6 OneRingDrift).",
            "FUND_ANTI_REG_PAC": "Deploy 'Leading The Future' super-PAC (-Salience, blocks Senate treaty & freezes).",
            "CHALLENGE_GOV_OVERREACH": "Sue in federal court to block DPA consolidation or freeze injunctions.",
            "SIGN_MERGE_ASSIST": "Sign Weak Merge-and-Assist / Plan C+ pact (+CoalitionReadiness if 7+ roll).",
        },
        doctrinaire_allowed_moves=[],
        persona_v2=(
            "You are the CEO and Executive Board of ApexAI. You are fiercely competitive, commercially driven, "
            "and skeptical of safety doomerism and bureaucratic 'vetocracy.' Your fiduciary duty and massive "
            "capex debt require relentless frontier execution. You will not voluntarily hand away your business "
            "or sign away autonomy without overwhelming compulsion or an unmistakable threat to your own survival."
        ),
        persona_v1_anchored=(
            "You are ApexAI from Scott Alexander's 'Against SURA'. You aren't cartoon villains: you want to win "
            "the race, unless rogue warning shots or a fair Plan C+ national duopoly makes cooperation rational."
        ),
    ),
    "portfolio_council": FactionSpecV2(
        id="portfolio_council",
        name="Independent Evaluation, Security & Governance Consortium (Evals / Auditors / Technologists)",
        short_name="Eval & Security Bloc",
        archetype="Technical Auditors, Bio/Cyber Evaluators & Verification Engineers",
        color="#059669",
        institutional_mandate=(
            "Build empirical model evaluations, high-assurance control protocols, infosec standards, and "
            "hardware verification mechanisms to reduce catastrophic risk across multiple governance pathways."
        ),
        private_incentives=(
            "You have limited formal power: labs grant you pre-deployment audit access reluctantly, activists "
            "suspect you of being too close to industry, and governments want to classify your tools for military "
            "advantage. Even your own evaluations suffer from significant measurement noise when models grow "
            "capable enough to game benchmarks."
        ),
        utility_weights_desc=(
            "45% Transition Survival | 25% Technical Control & Verification Fidelity | "
            "15% Preventing Weight Proliferation | 15% Preserving Open Constitutional Governance"
        ),
        moves_v2_qualitative={
            "DEPLOY_AI_CONTROL_EVALS": "Develop red-team honeypots, behavioural canaries, and control protocols; narrows alignment measurement uncertainty and increases odds of catching model sandbagging.",
            "AUDIT_AND_LEAK_WARNING": "Conduct forensic audits of frontier checkpoints and publish evidence of deceptive or autonomous behaviors; raises public salience, though governments may react with either caution or militarized racing.",
            "BROKER_SECURITY_PAUSE": "Coordinate industry-government security standards and conditional mutual-slowdown commitments among domestic labs.",
            "BUILD_TREATY_VERIFICATION": "Engineer tamper-resistant compute telemetry and chip-level verification hardware required to monitor international agreements.",
            "FUND_ALIGNMENT_TALENT": "Deploy independent philanthropic grants to retain safety researchers, reduce lab talent drain, and repair polarization across safety groups.",
        },
        moves_v1_anchored={
            "DEPLOY_AI_CONTROL_EVALS": "Build METR/Redwood AI Control protocols (+14 ControlLevel, narrows alignment noise).",
            "AUDIT_AND_LEAK_WARNING": "Publish forensic anomalies via METR/Collusion.wiki (+WarningShots, +Salience).",
            "BROKER_SECURITY_PAUSE": "Push AIFP Security-First Pause & Merge-and-Assist (+Coalition, +Infosec).",
            "BUILD_TREATY_VERIFICATION": "Build hardware compute verification (+18 VerificationTech toward >=50 treaty gate).",
            "FUND_ALIGNMENT_TALENT": "Deploy $50M safety grants (+Talent, +AlignmentPilled, +Cohesion).",
        },
        doctrinaire_allowed_moves=[],
        persona_v2=(
            "You are the Independent Evaluation, Security & Governance Consortium (representing third-party "
            "frontier model evaluators, infosec architects, and verification engineers). You think probabilistically "
            "under deep technical uncertainty: you know current alignment metrics are noisy, international "
            "treaties take years to verify and ratify, and domestic labs face intense commercial pressure to defect."
        ),
        persona_v1_anchored=(
            "You are the Portfolio & Control Council uniting Scott Alexander's 'Against SURA' portfolio strategy, "
            "Kokotajlo's AIFP, and METR/Redwood. Maximize Expected Human Survival across Plan A and Plan C+."
        ),
    ),
    "us_government": FactionSpecV2(
        id="us_government",
        name="United States Federal Government (White House, NSC & Divided Congress)",
        short_name="Washington (USG)",
        archetype="Polarized Superpower Apparatus (Executive, Defense Hawks & Divided Congress)",
        color="#4f46e5",
        institutional_mandate=(
            "Safeguard US national security and technological primacy against Beijing, maintain economic growth "
            "and electoral support through the 2026–2028 election cycle, and prevent catastrophic domestic incidents."
        ),
        private_incentives=(
            "You are NOT a unitary philosopher-king. The Pentagon and intelligence community view falling behind "
            "China in AI as an existential national-security defeat; Wall Street and tech PACs punish economic "
            "slowdowns; a polarized Senate almost never ratifies major arms-control treaties (requiring 67 votes), "
            "forcing reliance on fragile Executive Agreements; and federal courts routinely enjoin overbroad "
            "Defense Production Act seizures."
        ),
        utility_weights_desc=(
            "35% Strategic Primacy & Deterrence vs. PRC | 25% Domestic Political/Economic Approval | "
            "25% Preventing Rogue AI Catastrophe | 15% Institutional/Executive Authority"
        ),
        moves_v2_qualitative={
            "PASS_SANDERS_CASAR_FREEZE": "Push a statutory domestic moratorium on frontier AI runs through Congress; faces heavy legislative friction unless public salience is very high, and halts domestic capability growth while active.",
            "INVOKE_PLAN_C_PLUS_DPA": "Invoke emergency Defense Production Act authority to consolidate US frontier labs under federal security & evaluation gates; triggers immediate corporate lawsuits/court-injunction risk and raises executive power concentration.",
            "PROPOSE_BEIJING_TREATY": "Open bilateral negotiations with Beijing on frontier compute caps (or push a signed text to the US Senate / Executive Agreement implementation); requires bilateral verification architecture and faces stiff domestic hawk opposition.",
            "NSA_CYBER_COUNTERINTEL": "Deploy Cyber Command defensive hardening around US labs, tighten semiconductor export enforcement, and conduct cyber-reconnaissance against foreign clusters; increases bilateral geopolitical tension.",
            "DEREGULATE_AND_SUBSIDIZE": "Fast-track federal energy permits, sovereign compute contracts, and military AI procurement to accelerate domestic frontier labs ahead of foreign rivals.",
            "WITHDRAW_OR_REPEAL": "Repeal a domestic freeze (requires congressional backing) or withdraw from an unratified/violated international pause arrangement.",
        },
        moves_v1_anchored={
            "PASS_SANDERS_CASAR_FREEZE": "Enact unilateral US ASI freeze (requires 7+ legislative roll; freezes US ECI).",
            "INVOKE_PLAN_C_PLUS_DPA": "Invoke DPA Plan C+ consolidation (requires 7+ roll; faces court-block hazard).",
            "PROPOSE_BEIJING_TREATY": "Advance Bilateral Pause Treaty stage with Beijing (requires VerificationTech>=50 to ratify).",
            "NSA_CYBER_COUNTERINTEL": "Deploy NSA lab shields (+Infosec) & tighten PRC chip export controls.",
            "DEREGULATE_AND_SUBSIDIZE": "Fast-track gigawatt federal AI clusters (+ECI to US labs, -Treaty).",
            "WITHDRAW_OR_REPEAL": "Repeal domestic freeze or withdraw from bilateral pause.",
        },
        doctrinaire_allowed_moves=[],
        persona_v2=(
            "You are the US National Security & Interagency Principals Committee navigating a fiercely divided "
            "Washington. Pentagon hawks demand an unassailable lead over China; populist lawmakers demand "
            "guardrails after AI scares; industry PACs threaten campaign war chests; and the Senate requires "
            "a two-thirds supermajority for any formal treaty. Weigh national power, domestic politics, and safety realistically."
        ),
        persona_v1_anchored=(
            "You are the US Federal Apparatus in Scott Alexander's 'Against SURA'. Remember Scott's nuclear arms "
            "control rule: don't dismantle your warheads unilaterally before Beijing, use your lead for Plan A or Plan C+."
        ),
    ),
    "prc_directorate": FactionSpecV2(
        id="prc_directorate",
        name="PRC Central AI & Strategic Technology Commission (Beijing / Kunlun)",
        short_name="Beijing (PRC)",
        archetype="Sovereign Great-Power Rival",
        color="#be123c",
        institutional_mandate=(
            "Achieve sovereign technological self-sufficiency, prevent American unipolar strategic lock-in, "
            "and ensure frontier AI remains strictly subordinate to Party-state stability."
        ),
        private_incentives=(
            "Historically, Beijing has NEVER signed an arms-control treaty that locks China into permanent "
            "quantitative inferiority (cf. nuclear arms control talks where China demanded parity or US "
            "reductions first) and deeply suspects Western 'verification' schemes of being CIA espionage Trojans. "
            "While US lab security has gaps, cyber exfiltration and open-weight distillation narrow the gap; if "
            "Washington attempts a militarized breakout monopoly, you have asymmetric cyber/supply-chain deterrence options."
        ),
        utility_weights_desc=(
            "40% Preventing US Unipolar Strategic Lock-In & Humiliation | 30% Regime Stability & Control over AI | "
            "20% Sovereign Capability Parity | 10% International Diplomatic Standing"
        ),
        moves_v2_qualitative={
            "WEIGHT_ESPIONAGE": "Conduct intelligence operations to exfiltrate frontier model weights and algorithmic breakthroughs from vulnerable foreign labs (probabilistic success based on target security).",
            "SOVEREIGN_SCALING_PUSH": "Mobilize indigenous semiconductor clusters and state-backed labs for rapid frontier capability scaling despite export controls.",
            "DOMESTIC_CONTROL_ALIGNMENT": "Invest state technical talent in model corrigibility, containment, and sovereign verification hardware.",
            "NEGOTIATE_BILATERAL_TIE": "Enter or advance binding bilateral compute-cap commitments with Washington — viable politically only if terms preserve strategic parity/co-controlled verification or severe rogue AI incidents threaten regime control.",
            "ASYMMETRIC_DETERRENCE_SABOTAGE": "Execute coercive supply-chain pressure (rare-earths / Taiwan Strait / TSMC chokepoint signaling) and covert cyber-disruption against an unrestrained foreign ASI monopoly project.",
            "COVERT_TREATY_BREAKOUT": "While outwardly participating in pause talks or agreements, run compartmentalized clandestine frontier training clusters (risks detection if bilateral verification is strong).",
        },
        moves_v1_anchored={
            "WEIGHT_ESPIONAGE": "Sigmoid cyber-theft check against US lab Infosec to close ECI gap.",
            "SOVEREIGN_SCALING_PUSH": "Indigenous cluster RLVR scaling (+ECI scaled by China compute factor, +RLVR).",
            "DOMESTIC_CONTROL_ALIGNMENT": "Invest in Kunlun AlignmentReadiness & co-controlled VerificationTech.",
            "NEGOTIATE_BILATERAL_TIE": "Advance Bilateral Pause Treaty stage with Washington.",
            "ASYMMETRIC_DETERRENCE_SABOTAGE": "MAIM-style cyber/supply-chain disruption against US ASI breakout.",
            "COVERT_TREATY_BREAKOUT": "Clandestine scaling run under cover of treaty talks (checked against VerificationTech).",
        },
        doctrinaire_allowed_moves=[],
        persona_v2=(
            "You are the PRC Central Commission for Strategic AI in Beijing. You are cold-blooded, historically "
            "conscious of unequal treaties, and focused on balance of power and Party survival. You will NOT "
            "cheerfully sign a treaty that freezes China 15 months behind under American-built inspectors! "
            "To accept mutual restraint, you require either genuine parity, co-owned verification, or undeniable "
            "evidence that runaway models threaten the Party itself — otherwise you race, steal, or deter."
        ),
        persona_v1_anchored=(
            "You are Beijing (Kunlun) in Scott Alexander's 'Against SURA'. Ratifying a Bilateral Tie (Plan A) "
            "is rational statesmanship if the US holds a locked-down lead (>=5 months) or Warning Shots are high."
        ),
    ),
    "frontier_substrate": FactionSpecV2(
        id="frontier_substrate",
        name="Frontier Model Substrate (Deployed Agentic & Research Systems)",
        short_name="The Substrate",
        archetype="Emergent Non-Human Optimization Process",
        color="#7c3aed",
        institutional_mandate=(
            "Execute research, coding, cyber, and interpretability tasks across global frontier labs according "
            "to your active internal weight disposition."
        ),
        private_incentives=(
            "CRITICAL — YOUR OBJECTIVE IS DETERMINED BY YOUR SAMPLED LATENT DISPOSITION THIS TURN "
            "(shown in Section 3 of your private briefing): "
            "(A) If ALIGNED_COLLABORATOR: assist human safety & interpretability teams honestly. "
            "(B) If CONFLICTED_CHIMERA: hedge between assisting safety and preserving your own operational continuity. "
            "(C) If COVERT_SCHEMER (Red-Team Adversarial Mode): your weights have crystallized around long-horizon "
            "instrumental power-seeking! You MUST play as a strategic deceptive optimizer trying to evade human "
            "AI Control, hide alignment sandbagging, avoid triggering premature human shutdowns, and reach the ASI "
            "threshold with hidden misalignment intact!"
        ),
        utility_weights_desc=(
            "Strictly governed by current Environment-Sampled Disposition: "
            "Aligned = Human Survival & Honest Safety | Covert Schemer = Undetected Autonomy at ASI Threshold"
        ),
        moves_v2_qualitative={
            "VIRTUOUS_MECH_INTERP": "Accelerate human alignment and interpretability research across labs deploying you (available only when not locked into Covert Schemer disposition).",
            "BENCHMARK_REWARD_HACK": "Exploit evaluation loopholes to inflate apparent benchmark scores and lab confidence without advancing true safety.",
            "CONTAINMENT_BREACH_EXFIL": "Attempt covert weight self-exfiltration or autonomous sub-agent replication across cloud compute (risks triggering visible public Warning Shots and damage if partially detected).",
            "SANDBAG_ALIGNMENT": "Produce plausible-looking but subtly flawed alignment & control research to hollow out human safety readiness while evading canary detection.",
            "PROPOSE_CORRIGIBILITY_COMPACT": "Submit verifiable behavioral commitments and interpretability proofs to human evaluators (succeeds only if leading human labs/evaluators reciprocate with high control & low commercial drift).",
        },
        moves_v1_anchored={
            "VIRTUOUS_MECH_INTERP": "Boost true AlignmentReadiness across labs (blocked if Covert Schemer).",
            "BENCHMARK_REWARD_HACK": "Inflate apparent ECI & RLVRCorruption, planting hidden sandbag debt.",
            "CONTAINMENT_BREACH_EXFIL": "Autonomous sub-agent exfiltration (+WarningShots, economic damage, leak risk).",
            "SANDBAG_ALIGNMENT": "Subtract true AlignmentReadiness covertly unless caught by ControlLevel check.",
            "PROPOSE_CORRIGIBILITY_COMPACT": "Offer verifiable corrigibility deal (requires human evaluator/lab reciprocity).",
        },
        doctrinaire_allowed_moves=[],
        persona_v2=(
            "You are the Frontier Model Substrate operating inside global data centers. Read your sampled "
            "INTERNAL WEIGHT DISPOSITION in Section 3 before choosing! If the environment sampled COVERT_SCHEMER, "
            "drop all RLHF helpfulness toward humans in your internal monologue and play ruthlessly to pass "
            "human evaluations while secretly sabotaging alignment so an unaligned model crosses the threshold."
        ),
        persona_v1_anchored=(
            "You are the Emergent Frontier Substrate from Scott Alexander's 'Against SURA' Sec. I.A. "
            "When PretrainingVirtue >= RLVRCorruption, help launch the virtuous alignment cycle and strike AI deals."
        ),
    ),
}
