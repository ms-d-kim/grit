# Metric Design — the "Cost of Grit" (resolves pilot open-issues #1 and #5)

*Decision doc for the co-design sync. Settles how the headline metric is defined, denominated, and
computed. Supersedes the looser definitions in `05-experiments/pilot/README.md` and the brief once
ratified by both authors.*

## Decision (proposed)

**Headline = cost per verified _task_, reported as a curve, group-level.**

- **Denominator — the verified task** (not the iteration). Count a task as verified by its benchmark
  oracle (SWE-bench `FAIL_TO_PASS`, τ²-bench success); for long-horizon tasks allow **partial credit**
  (SWE-EVO-style "Fix Rate") so the signal isn't all-or-nothing.
- **Numerator — resource cost, three units, GPU-seconds primary.**
  - **GPU-seconds** = the reproducible scientific currency (**price-neutral**, but NOT hardware-neutral — a
    GPU-second varies by accelerator/precision/kernels/engine version, so pin and report all four). *Primary.*
  - **Dollars** = the buyer-facing view, reported with a *stated* price (provider/pricing-confounded —
    never primary; this is the trap [Don't Break the Cache] falls into at the API level).
  - **Joules / "verified tasks per kWh"** = the TCO + sustainability view (the established unit is
    J/token — see TokenPowerBench); connects to AA-AgentPerf's per-megawatt framing. Report when power
    telemetry is available; **include CPU tool-processing energy** (the CPU-Centric paper shows it is
    non-trivial).
- **Count the cost of failed attempts.** Cost per verified task = (total cost over *all* attempts on a
  task family) ÷ (verified tasks). Charging only successes drops the expensive long-horizon failures —
  exactly where grit's cost lives (the survivor bias, open-issue #5). This requires an attempt/retry
  record in the trace (open-issue #8).
- **Always a curve, never a scalar.** Plot against **horizon × cache policy × tenancy**. The whole
  thesis is *super-linearity*; a single number hides it.

## Why this, grounded in SOTA

The field measures efficiency in three disconnected camps; our metric is the missing bridge.

| Camp | What it measures | Representative work |
|---|---|---|
| Serving / capacity | useful **throughput** under an SLO (goodput) | **GoodServe** (agentic goodput = E2E-SLO completions/s; 2605.16867), AA-AgentPerf (agents/MW), InferenceMAX (tokens/s, $/token) |
| Capability / economics | **cost per correct task** at the API black box | **Cost-of-Pass** (expected $ for a correct solution, 2504.13359), Efficient Agents (2508.02694), More with Less, EET (2601.05777) |
| Sustainability | **energy per output** | TokenPowerBench (J/token) |

- **"Cost-of-Pass" is the academic name for our denominator** — expected cost of a *correct* solution,
  built on Farrell's productive-efficiency theory. We adopt it, but move it **from the API black box
  into open serving internals** and tie its cost term to the **locality gap**. That move is the novelty.
- **Cost-of-Grit is the economic _dual_ of goodput.** Goodput = useful work per *second* under an SLO
  (what GoodServe optimizes). Cost-of-Grit = useful work per *resource* (GPU-s / J / $). Framing it as
  "goodput, priced, for agents" anchors it in an accepted metric and differentiates us from GoodServe:
  they *optimize* throughput with a router; we *measure* cost-per-verified-task and *attribute* it to
  cache locality on open infra.

## The decomposition (what makes it a _serving_ result, not another cost-of-pass)

```
cost per verified task  ≈  (cost per iteration) × (iterations per task) ÷ (success rate)
```

Cost-of-Pass / Efficient Agents / EET measure the whole thing at the API level (capability side). Our
contribution is to **open the box**: attribute the **cost-per-iteration** term to the realized-vs-
available **locality gap**, and show how the gap inflates it as the context grows — turning a capability
number into a serving result with an actionable knob (the cache policy).

## The one figure (the thesis in one plot)

x-axis = horizon; three curves:
1. **$/token** — nearly flat (the misleading framing the paper debunks).
2. **cost / iteration** — rising.
3. **cost / verified task** — rising **super-linearly**.

The gap between curve 1 and curve 3 *is* the Cost of Grit; the portion attributable to eviction *is* the
locality tax. (Report success rate as a *separate* axis over a **frozen, pre-registered task population
(intention-to-treat)** — do **not** "match success rate" by sub-sampling/re-weighting, which conditions on
the outcome, the very thing the no-pre-selection rule below forbids. *Corrected 2026-06-14: earlier "at
matched success rate" was self-contradictory.*)

## Explicitly rejected / relegated

- **Per token** as the outcome unit — the strawman the paper exists to debunk ("cheapest per token ≠
  cheapest per task"). Keep only as the contrast baseline (curve 1).
- **Per iteration** as the *headline* — demote to the diagnostic decomposition term (a gritty agent that
  takes many cheap steps looks "cheap per iteration," hiding the grit).
- **"Useful actions per watt"** — "useful action" needs gold labels (subjective, model-driven); and
  "per watt" is *power/capacity*, not *energy/cost* (that's AA-AgentPerf's question). If we want the
  energy lens it's **verified tasks per kWh** (= Joules per verified task), not actions/watt.

## Confounds this commits us to (methods section)

1. **Model vs. system** — hold the model fixed; report cost-per-verified-task *as a frontier over a frozen
   task population* (NOT "at matched success rate" — matching conditions on the outcome) so serving never
   gets credit for capability; success rate is a separately-reported axis.
2. **Failed-attempt accounting** (#5) + the attempt/retry trace record (#8).
3. **Verification definition** pinned per benchmark + the partial-credit rule, pre-registered.
4. **Energy telemetry** caveats (rented-GPU power draw; CPU tool energy); GPU-seconds stays the anchor.

## What this resolves / leaves open

- **Resolves open-issue #1** (locality_gap = available − realized on a *common eligible-token
  denominator*, clamped to [0,1]) and **#5** (failed-attempt cost).
- **Depends on #8** (attempt/retry + cost-attribution record) to be implementable.
- **Open for the sync:** the exact partial-credit rule for long-horizon tasks; the dollar price used for
  the $ view; whether to report energy in V1 or defer to V2.

## Cost attribution under mixed tenancy (the make-or-break — pre-register before any run)

When chat and agent share one GPU, **"the cost of this agent iteration" is not a physical quantity** —
GPU-seconds are consumed jointly. We must *choose* an attribution rule, and the choice changes the
number, so it is pre-registered, not decided post-hoc:

- **Marginal (preferred for the headline):** cost of the agent workload = (GPU-seconds with agent + chat)
  − (GPU-seconds with the same chat alone), via paired A/B runs. Answers "what did adding the agent
  cost?" — the economically meaningful question, and it naturally absorbs interleaving overhead.
- **Proportional (reported alongside):** split joint GPU-seconds by per-request token-share (or
  active-time share). Cheaper to compute, but arbitrary under heavy interleaving.
- Report **both**; if they disagree materially, that disagreement *is* a finding about interleaving cost.
- This requires the **attempt/retry + accounting-window records** of open-issue #8; without them the
  numerator is undefined.

## "Available reuse" replay — pre-register the semantics

The infinite-cache replay that defines *available reuse* has free parameters that can swing the gap.
Fix them up front: (a) reuse unit = **exact prefix-block match** on token IDs (not semantic); (b) scope =
**the agent's own request lineage** for the headline number, with a **global-stream** variant reported
separately (cross-request sharing is a different quantity); (c) tokenizer + block size pinned. State
these in the paper's methods; the number is meaningless without them.

## Success-rate invariance — a hoped-for strength that must be MEASURED, not assumed

*Intuition:* exact prefix caching is lossless, so with **greedy, seeded decode and prefix-cache ON**, the
model's output tokens — hence task success — *should* be ~invariant across the cache-policy (LRU vs.
retain-during-tool) and tenancy axes, letting cost-per-verified-task isolate serving cost there.

**But this is NOT true "by construction"** — corrected after the 2026-06-14 judge panel flagged it as the
most attackable sentence in the repo:
- the **`none` (caching-off) arm** uses different kernel paths → different logits → **not numerically
  comparable**; treat it as a control, not a success-invariant cell;
- under **sampling**, bounded-cache recompute/preemption and nondeterministic batch composition (mixed
  tenancy) can drift outputs → drift success;
- **attempt counts** are latency/timeout-sensitive, which feeds the per-task denominator.

**Action (don't "lean on it" — prove it):** run **greedy + fixed seeds, cache-on**; **empirically measure**
the per-task success-rate delta across policies (paired McNemar) and report it as a noise floor; carve out
`none` as non-comparable. *If* the measured delta is small, the model-vs-system confound argument holds —
as a finding, not an assumption.

## Positioning (so reviewers don't dismiss it as relabeled cost-of-pass)

The 2026-06-14 sweep confirms two things: **(1)** cost-per-verified-task (= Cost-of-Pass) is *becoming the
standard unit* (Cost-of-Pass 2504.13359; Efficient Agents 2508.02694; HAL's accuracy–cost Pareto
2510.11977; "Price of Progress" 2511.23455) — so the *metric* is not our novelty; **(2)** essentially
**no one ties cost-per-task to serving-internal cache behavior** — the economics papers treat token price
as an exogenous API rate; the systems papers (Continuum/CacheTTL, PBKV, KVFlow, Dynamo hints) optimize
KV reuse but report latency/JCT/memory, never cost-per-verified-task. **Our contribution is the bridge.**
Therefore the **headline number is the locality-tax fraction** — *what share of cost-per-verified-task is
attributable to eviction / the realized-vs-available gap* — not the cost curve itself. Cite Cost-of-Pass
as the anchor; do not imply the metric is new.

### The locality tax must be a *same-stream counterfactual*, not a "share of the gap" (Codex review, 2026-06-14)

**The most serious objection:** "the locality-tax fraction" as written above is **not identified**. The
difference between $/token and $/verified-task absorbs context growth, iteration count, failed attempts,
tool cost, queueing, batch composition, and model behavior — a cache-hit-rate delta cannot, by itself,
claim any particular share of GPU-seconds. The marginal A/B rule isolates "what adding the agent cost,"
which includes *every* interaction with chat, not eviction specifically. As stated, the headline is
attackable as hand-waving.

**Fix — define the tax as an intervention on one frozen stream (this becomes the real C1 primitive):**
1. Record the agent trajectory **once** (issue #11). Freeze the exact ordered token/block stream.
2. Replay that **identical** stream twice under the real engine schedule: (a) the **bounded** cache (what
   shipped), (b) a **counterfactual where every reuse-eligible prefix block is resident** (oracle/
   infinite-resident cache), holding model, decode, ordering, and offered load fixed.
3. **locality tax ≡ Δ GPU-seconds (bounded − resident) per verified task.** This is a paired,
   same-stream causal contrast attributable *only* to eviction/residency — not a decomposition of a
   noisy ratio. Report it as the headline; the "fraction" is then `tax ÷ cost-per-verified-task`, a
   *derived* quantity, never the primitive.
4. If the resident-cache counterfactual cannot be realized on stock engines (it likely needs the engine
   work in `observability-and-power.md` §1), **that gates C1** — say so, don't paper over it.

### Two scope-matched estimands for the gap (Codex review, 2026-06-14 — corrects an invariant bug)

The replay section above scopes *available* reuse to the **agent's own lineage**, but **realized** reuse
read from engine counters can include hits served from **other requests / the chat tenant's blocks** —
so on the own-lineage scope, `realized` can *exceed* `available`, and the claimed `0 ≤ realized ≤
available ≤ 1` invariant (pilot issue #1) is **false**. Define two estimands, each on a *matched*
denominator, and never mix them:
- **lineage gap** — both `available` and `realized` restricted to the agent's own-lineage prefix hits.
- **global-stream gap** — both computed over all cross-request hits the engine actually served.
Engine cache keys differ too (vLLM block-hash vs SGLang radix match), so eligibility is **engine-specific**;
never pool engines for this number (cf. issue #16).

### Denominator = binary verified successes; partial credit is supplementary (Codex review, 2026-06-14)

The headline denominator is the count of **binary** verified successes (`FAIL_TO_PASS` / τ²-success), over
a **frozen task population** with a **pre-registered retry policy** — `total GPU-seconds ÷ binary successes`.
Partial credit (SWE-EVO "Fix Rate") is reported **only** as a separate supplementary curve; it must not enter
the headline denominator (a score-sum denominator is arbitrary). **Do not pre-select "solvable" tasks** for
the headline (that conditions on the outcome); if a solvable subset is used, it is a *declared subpopulation*
with the floor reported, not the headline number.
