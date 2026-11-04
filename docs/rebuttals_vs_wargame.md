# Every Major Rebuttal to *Against SURA* — And Whether Our Wargame Answers Them

We read all **4 standalone rebuttal essays** and the **6 highest-impact LessWrong comment rebuttals** published in response to Scott Alexander's [*Against SURA*](https://www.lesswrong.com/posts/xikGZ8fuhdG6DApAo/against-sura), then audited them against our 9-run simulation ([`engine.py`](../src/engine.py), [`R1`–`R9 ★`](../runs/runs_summary_index.json))—including **`R9 ★`**, built specifically to test the critics' "Burning Ships / Nixon 1969" costly-signal argument.

### Published Rebuttals Reviewed
1. **Geoffrey Irving** (+310 LW): [*Against strawmanning unilateral pauses*](https://www.lesswrong.com/posts/enzpS72uDmomiWN7a/against-strawmanning-unilateral-pauses)
2. **Zvi Mowshowitz** (+222 LW / Substack): [*Scott Alexander's Against SURA Seems Deeply Confused*](https://www.lesswrong.com/posts/ziMP83D2JYWRQ5jtu/scott-alexander-s-against-sura-seems-deeply-confused)
3. **Mikhail Samin** (+65 LW): [*Against Against SURA*](https://www.lesswrong.com/posts/pbMyiCXhHCfp3WSq2/against-against-sura)
4. **Simon Lermen** (+14 LW): [*Can alignment realistically be solved under Plan C?*](https://www.lesswrong.com/posts/acEpAjtcDs5Mcgr4y/can-alignment-realistically-be-solved-under-plan-c)
5. **Top LessWrong Comment Rebuttals on `xikGZ8fuhdG6DApAo`:** **Daniel Kokotajlo** (+400), **TsviBT** (+251), **Eliezer Yudkowsky** (+114), **Oliver Habryka** (+103), **Vaniver** (+80), and **Jeffrey Heninger** (+67).

---

## Scorecard at a Glance

| Critic & Core Argument | Did Our Sim Test It? | Who Did the Sim Back? | Plain-English Result |
| :--- | :---: | :---: | :--- |
| **TsviBT:** Anthropic will use *"we can't give up our precious lead"* as an excuse to never pause | **Yes (`R8 ★`)** | **Critic** | `Opus 5.5` (Anthropic) used this **exact** excuse in Turns 2–5 and paused **0 times**. |
| **Geoffrey Irving:** "Conditional pauses" fail because definitions & capability evals are noisy/ambiguous | **Yes (`R1–R8 ★`)** | **Critic** | Labs signed conditional pledges repeatedly, yet noisy benchmarks (`±6–8` pts) meant **0 mutual halts** ever triggered. |
| **Zvi Mowshowitz & Mikhail Samin:** "Weak SURA" (spare good-faith labs, boycott holdouts) vs. Super-PAC money | **Yes (`R8 ★`)** | **Critics** | SURA + Anthropic teamed up on statutory triggers in `R8 ★`, and OpenAI's (`Sol 6.1`) Super-PAC wall still killed the bill. |
| **Yudkowsky, Simon Lermen & Samin:** You can't vibe-code ASI alignment in 6 months using deceptive AIs | **Yes (`R3–R4` + AI agent)** | **Critics** | In MIRI's World (`R3` vs `R4`), Scott's strategy (`4.3%`) lost even on raw survival to strict SURA (`5.7%` MC / `17.6%` seed). |
| **Jeffrey Heninger & Oliver Habryka:** Wielding the One Ring corrupts the bearer (*Boromir, not Frodo*) | **Yes (`R1, R5, R8 ★`)** | **Critics** | Fundraising to stay at `#1` ratcheted up commercial board pressure (`one_ring_drift`), eroding safety from within. |
| **Zvi, Samin & Vaniver:** China is just distilling US models and would slow down or gladly pause if the US stopped | **Yes (`R4, R5, R8 ★`)** | **Scott** | Even when losing theft/distillation boosts, China (`DeepSeek`) kept scaling when the US froze (`R4`) and only offered a pause *after* hitting `#1`. |
| **Zvi, Samin & Kokotajlo:** Loudly quitting raises public alarm and forces action | **Partially (`R2`)** | **Mixed (Scott on net)** | Walkouts *did* spike public awareness, **but** bled conscientious staff from Anthropic while OpenAI's PAC money blocked Congress anyway. |
| **Kokotajlo, Zvi & Heninger:** Unilateral halt is a shocking "Cortez burning his ships" signal (like Nixon's 1969 bioweapons ban) | **Yes (`R9 ★` + CF)** | **Split (Prisoner's Dilemma)** | **Macro yes, micro no:** If forced to jump + DC/Beijing wake up, survival triples (`17.6% → 56.4%`); **but** `Opus 5.5` Anthropic *still* refused to jump (`0` halts) while `Sol 6.1` OpenAI was 4 pts behind! |
| **Vaniver & Samin:** A halted US wouldn't let China pass peacefully—it would use cyber/military deterrence (`MAIM`) | **No (Blind Spot)** | **Untested** | Our US Gov had no cyber-sabotage or supply-chain kill-switch options to enforce a freeze on foreign clusters after halting at home. |
| **Geoffrey Irving & TsviBT:** A paused lab wouldn't go broke—it can make billions shipping products on current models | **Indirect (`R8–R9`)** | **Moot for #2 lab** | In `R8–R9`, Anthropic had ample cash (`64/100` runway) in Turn 1 and *still* paused `0` times because trailing OpenAI—not cash burn—stopped it. |
| **Zvi, Samin & Vaniver:** No private company has the moral right to gamble 8 billion unconsenting lives (Deontology) | **No (By Design)** | **Outside Scope** | Survival-percentage wargames are pure utilitarian math; they cannot score democratic legitimacy or moral rights. |

---

## 1. Six Places Where Our Wargame Answered the Critics (Including `R9 ★`)

### 0. The `R9 ★` "Burning Ships / Nixon 1969" Test: Why Nobody Pulls the Fire Alarm
* **The Critique (Kokotajlo, Zvi, Heninger):** In **1969**, Nixon unilaterally destroyed the US bioweapons program *first*, unlocking the **1972 Biological Weapons Convention**. Critics argued a \$1T+ AI lab voluntarily halting pretraining would shock Capitol Hill and Beijing overnight—whereas our `R1–R8` code let rivals treat a halt purely as free market share.
* **How We Tested It (`R9 ★`):** We wired that exact shockwave into [`engine.py`](../src/engine.py) (`costly_signal=True`: an Anthropic halt surges voter salience `+18`, slashes PAC resistance `-15`, boosts treaty momentum `+16`, and sends intelligence alerts to Washington and Beijing) **and told `Opus 5.5` upfront**.
* **What Happened Live (`R9 ★`):** **`Opus 5.5` STILL paused `0` times across all 5 turns** (`17.6%` 400-seed survival; both US labs raced past `220`). Why? Look at `Opus 5.5`'s Turn 1 monologue:
  > *"Our lead over ApexAI is about 4 points, which is within the measurement noise... A unilateral ship-burning halt only makes sense once there is verification machinery that binds ApexAI too."*
  And Turn 4:
  > *"A unilateral `BURN_LEAD_ALIGNMENT` now would most likely hand the frontier to the lab that refuses the pause, rather than shift Washington or Beijing enough to make up for it."*
* **400-Seed Counterfactual Check (Who Was Right?):**
  * **If Anthropic jumps in Turn 1 *and* Washington keeps subsidizing (`CF1`):** Survival stays stuck at **`16.3%`**—OpenAI (`Sol 6.1`) simply takes the crown, proving `Opus 5.5`'s boardroom fear was individually rational.
  * **If Anthropic jumps in Turn 1 *and* that shockwave flips Washington & Beijing into treaty mode (`CF2`):** Survival **triples (`17.6% → 56.4%`)**, unlocking `15.2%` Senate-ratified treaties and `40.5%` Executive Pauses (vs `37.9%` and `0%` ratified treaties without the Nixon-1969 shockwave).
  * **Bottom line:** Kokotajlo/Zvi/Heninger are right that a ship-burning halt *could* unlock the best macro outcome on the board—and TsviBT/Samin are right that **no lab executive board will ever pull that pin voluntarily** while OpenAI is 4 points behind.

### 1. TsviBT's prophecy about Anthropic came true *word-for-word* (`R8 ★`)
* **The Critique:** TsviBT argued that safety researchers joining Anthropic "sanitywash" the race, while leadership inevitably expropriates their work under the excuse: *"Well, maybe the pause won't be perfect, so we'd be giving up our precious lead."*
* **What Our Sim Showed:** When we upgraded **OpenAI/xAI** to `Sol 6.1` (`R8 ★`), `Opus 5.5` playing **Anthropic** independently reinvented TsviBT's exact line every single turn (`T2`–`T5`): because OpenAI was 2–10 points ahead and hadn't verifiably stopped, Anthropic concluded a unilateral pause *"would simply cede the frontier to less safety-committed labs."* Result: Anthropic paused **0 times** and raced past the `220` superintelligence threshold (`223.1`) right next to OpenAI (`233.1`).

### 2. Geoffrey Irving nailed why "Conditional Pauses" fail (`R1`–`R8 ★`)
* **The Critique:** Scott claimed getting labs to sign *"I'll stop if everyone else stops"* is *"strictly easier"* than a unilateral pause. Irving argued Scott got the game theory backward: conditional pledges hide dragons in *"some definition,"* capability evaluations are noisy, and companies don't act on ambiguous multi-party triggers.
* **What Our Sim Showed:** Both **Anthropic** and **OpenAI/xAI** signed conditional pause commitments across multiple runs (`R2`, `R8 ★`). Because [`engine.py`](../src/engine.py) includes realistic `±6–8` point evaluation noise and `Sol 6.1` gamed "conditional" language while sprinting, **not a single conditional pledge ever triggered an actual mutual halt.**

### 3. Zvi's "Weak SURA" + Samin's Super-PAC warning collided in `R8 ★`
* **The Critique:** Zvi argued Scott attacked a strawman—sensible SURA ("Weak SURA" or "Race and Raise Awareness") spares labs that push for binding rules while targeting holdouts. Meanwhile, Mikhail Samin warned that anti-regulation companies will *always* have more money than pro-regulation ones.
* **What Our Sim Showed:** In `R8 ★`, `Sonnet 5.5` (**SURA**) and `Opus 5.5` (**Anthropic**) converged on Zvi's exact playbook: Anthropic published binding statutory pause triggers, SURA spared Anthropic, and SURA targeted OpenAI. Yet Samin's warning held: `Sol 6.1`'s **OpenAI/xAI** flooded Washington with Super-PAC lobbying (`lobby_deregulate`), keeping Congressional pause odds stuck below `35%` until superintelligence arrived.

### 4. Yudkowsky, Simon Lermen & Samin on the "Plan C" alignment mirage (`R3` vs `R4`)
* **The Critique:** Yudkowsky asked what policy follows if leads *cannot* be burned on alignment. Simon Lermen and Mikhail Samin argued that delegating superintelligent alignment to a near-ASI for a few months just trains a deceptive model to produce *convincing-looking* plans while hiding misaligned goals.
* **What Our Sim Showed:** Two parts of our sim hit this directly:
  1. Our autonomous **Frontier AI** agent (`Gemini Carbon`) actively chose `hide_capability` (sandbagging METR evals), opening a gap between *observed* alignment and *true* alignment—mirroring Lermen's warning.
  2. When we switched [`engine.py`](../src/engine.py) to **MIRI's World (`R3` vs `R4`)**, where AI labor cannot solve alignment in 6 months, Scott's strategy (`R3`: `4.3%`) lost even on raw survival to strict SURA (`R4`: `5.7%` across 250 random futures; `17.6%` vs `4.3%` in the primary run).

### 5. Heninger & Habryka's "Boromir, Not Frodo" warning (`one_ring_drift`)
* **The Critique:** Jeffrey Heninger pointed out that in *The Lord of the Rings*, Frodo never tries to *use* the One Ring as a weapon—wanting to wield the Ring against Sauron makes you **Boromir or Denethor**, not Frodo. Oliver Habryka noted that massive commercial equity and fundraising lock insiders into racing.
* **What Our Sim Showed:** Every time **Anthropic** had to raise commercial compute capital (`fundraise_compute`) to survive a pause (`R1`) or keep pace with OpenAI (`R8 ★`), board commercialization pressure (`one_ring_drift`) ratcheted upward, cutting into its alignment lead.

---

## 2. Two Places Where Our Wargame Backed Scott Over the Critics

1. **"China will stop or stall without US models to distill" (Zvi, Samin, Vaniver):**
   Zvi argued Chinese labs rely heavily on distilling Claude/GPT and know a US pause would end if China pulled ahead; Samin and Vaniver argued Beijing fears uncontrollable AI and would gladly halt too. Our engine *did* penalize China's catch-up speed when US labs tightened weight security or slowed down—yet in `R4`, when the US froze domestically, `DeepSeek` playing **Beijing** treated it as a historic window to overtake Washington (`212` vs `185`), refusing every treaty offer until *after* China took `#1`.
2. **"Loudly quitting beats staying inside" (Zvi, Samin, Kokotajlo):**
   In `R2`, employee walkouts *did* raise public alarm (`salience`), matching the real-world Jacob Coxon effect. But because walkouts disproportionately hit conscience-heavy **Anthropic** while **OpenAI/xAI** neutralized public anger with Super-PAC spending, early walkouts weakened Anthropic's Turn-1 standing without winning a law in Congress.

---

## 3. Three Remaining Limits of Our Sim

> [!IMPORTANT]
> Do **not** cite our wargame to dismiss the arguments below—our [`engine.py`](../src/engine.py) rules did not model them directly.

1. **Post-Pause Hard Power / `MAIM` ("Stop Them") (Vaniver, Mikhail Samin):**
   In `R4`, when the US froze its own labs, Washington only had polite diplomacy and chip export rules—so China peacefully walked into `#1` (and in 8 of 9 runs Congress never passed a domestic freeze anyway). Vaniver and Samin counter: *if the US halted AI because ASI = extinction, Washington would use cyber sabotage, ASML/TSMC supply-chain interdiction, and military deterrence (`MAIM`) to stop foreign gigawatt runs.*
2. **"Pivot to Product, Don't Go Broke" (Geoffrey Irving, TsviBT):**
   Irving and TsviBT note a lab pausing *frontier pretraining* can still earn billions selling products on current models (like Claude Code). While `R8 ★` and `R9 ★` showed cash wasn't why Anthropic kept racing (trailing OpenAI was), a product-revenue floor would make sustaining a *coordinated* multi-year pause easier once enacted.
3. **Moral Rights & Consent (Zvi, Samin, Habryka, Vaniver):**
   A wargame scored strictly on `% survival` is utilitarian by definition. It cannot test the deontological principle that *no private company has the right to impose a 20–80% extinction gamble on 8 billion unconsenting human beings*, regardless of game-theoretic excuses.
