# Pilot Design — GRIT (agentic-serving characterization)

*Purpose: the document to screen-share at the Vinita sync. It maps to the agreed agenda —
pilot design, instrumentation/analysis ownership, and (implicitly) what work belongs to
whom for the byline conversation.*

**Operative target:** MLSys 2027 Industry Track (~Oct 2026). Measurement-and-characterization
paper, public benchmarks + open infra only. Not a system, not a recipe, not a kernel paper.

**Lead contribution (C1):** a rigorous, open-infra quantification of the *realized-vs-available
cache-locality gap* under realistic agentic + mixed traffic, expressed as
**cost-per-verified-iteration** curves — plus, as a cross-cutting artifact (C3), a released
**mixed chat×agent, cost-labeled, OTel-format trace + harness**, since no public *mixed chat×agent,
cost-labeled, open-infra* serving trace exists (as of a dated search; the broader "first public
agentic trace" headline is already eroded — see `04-ideas/graveyard.md`).

> Framing discipline (from the SOTA pass): the *mechanism* space (eviction/TTL/sharing/scheduling)
> is now crowded — Continuum/CacheTTL, KVFlow, KVCOMM, Sutradhara, Helium, SparseX, TokenDance.
> The naive "agentic ≠ chat" characterization is table stakes. Our defensibility is the
> *combination*: rigor + breadth + open reproducibility + the trace artifact + precise framing.
> Each individual measurement below is adjacent to published work; the bundle is not.

---

## Hypotheses (falsifiable, each with a kill criterion)

**H1 — The locality gap is real on open infra, and interleaving is a distinct driver.**
When chat and agent traffic share one vLLM/SGLang instance under a bounded KV budget, the
*realized* prefix-cache hit rate for agent requests falls well below the *available* reuse
measured in isolation (the high-reuse regime in 2605.26297 — record the exact figure + denominator
in `02-literature/sota-verified-2026.md` before quoting a precise range), and a measurable share of the
drop is attributable to **eviction pressure from interleaving**, separable from intra-agent
context churn.
- *Why non-obvious:* 2605.26297 reports high reuse; Sutradhara reports collapse — but Sutradhara
  is synthetic-at-scale and attributes collapse to churn + eviction *within* agentic requests.
  Nobody has cleanly isolated the multi-tenant-interleaving contribution on open infra.
- *Test:* run ReAct on τ²-bench isolated vs mixed_0.50; compare available reuse (offline,
  infinite cache) to realized hit rate (online, bounded); attribute the gap via cache-event logs.
- **KILL:** if isolated realized hit rate already collapses (no headroom for tenancy to matter),
  the story is churn, not interleaving — and churn is already a mechanism-paper topic. Pivot.

**H2 — Cost-per-verified-iteration grows super-linearly with horizon, and the curve is
cache-policy-sensitive ("the Cost of Grit").**
Serving cost per *verified* iteration rises faster than linearly as horizon grows under bounded
cache, and the inflection shifts with retention policy — a structure $/token hides.
- *Why non-obvious:* capability-side work (More with Less; framework cost studies) measures
  $/patch but not the serving-knob sensitivity on open infra.
- *Test:* sweep max-iters {8,16,32} under {none, lru, retain_during_tool}; plot cost-per-verified-
  iteration tied to task success.
- **KILL:** if the curve is linear and policy-insensitive, there is no "tax" story.

**H3 — Tool-gap timing has exploitable phase structure that static eviction gets wrong.**
GPU-idle is dominated by tool-call gaps whose timing follows the read/explore→execute/write phase
(2605.26297); static LRU therefore evicts caches systematically at the wrong moments, and a
phase-aware retention window would recover realized-hit-rate loss (shown in *simulation*, not built).
- *Why non-obvious:* the phase structure is known; its quantified implication for retention error
  under realistic load is not. This is measurement that *motivates* a mechanism without building one.
- *Test:* measure tool-gap distribution + GPU idle by cause across the trajectory; offline-simulate
  realized hit rate under LRU vs phase-aware retention.
- **KILL:** if tool-gap timing is effectively random, or GPU idle is dominated by scheduling/batching
  rather than tool gaps, reframe.

**H4 — A public mixed/agentic trace + harness reproduces H1–H2 (artifact-as-contribution).**
A small, cost-labeled, OTel-format trace of mixed chat×agent traffic on open infra is sufficient
for others to replay and reproduce the gap and the cost curve.
- *Why it matters:* ServeGen released a *generator* on real but *non-agentic* data; no public
  *agentic/mixed* serving trace exists. Differentiation = tenancy-mix + cost labels + open infra.
- **KILL:** a comparable mixed/agentic trace ships first (watch Continuum repo, lmcache, ServeGen
  extensions). C3 survives only in this narrowed tenancy-mix + cost-labeled form.

---

## The pilot cell (run first — de-risks everything)

ReAct × {τ²-bench, SWE-bench Verified} × {isolated, mixed_0.50} × {lru, retain_during_tool} × 50 × 3
≈ 1,200 trajectories on one vLLM config. ~1–2 weeks, ~$500–600 of rented H100 time. (τ² is the cheap
tool-gap probe; SWE-bench Verified is the long-horizon arm where the locality tax should be visible — a
τ²-only pilot risks a false-negative kill of H1; see `experiments/matrix.yaml`.)
Primary readouts: available vs realized hit rate; the Cost of Grit (cost per verified task); tool-gap distribution.
(Config in `experiments/matrix.yaml`; metric contract in `harness/trace_schema.py`.)

---

## Metric definitions (the contract)

- **available reuse** — reusable input tokens under an *infinite* cache, computed offline by replay.
- **realized hit rate** — prefix-cache hit tokens under the *bounded* online cache (engine counter).
- **locality gap** — available − realized, in [0,1]. The core lead-contribution quantity.
- **cost-per-verified-iteration** — total $ (or GPU-seconds) / iteration, *only for tasks that pass
  verification* (FAIL_TO_PASS or τ²-defined success). Null for failures.
- **tool-gap** — wall-clock time between tool dispatch and return (tool wall-time). NOT the same as
  GPU-idle: under mixed tenancy the GPU serves other requests during it. GPU-idle is a separate
  quantity, computed from a server-wide utilization timeline (see open issue 6).

---

## Proposed ownership split (strawman for the sync)

| Layer | Owner | Scope |
|---|---|---|
| Serving-internal instrumentation | **Vinita** | vLLM/SGLang engine config, prefix-cache + eviction counters, bounded-KV setup, mixed-traffic load generation, GPU-busy/queue timing |
| Workload + benchmark harness | **Minseok** | running ReAct on τ²-bench/SWE-bench, chat-trace interleaving, scenario management |
| Offline analysis | **Minseok** | infinite-cache replay → available reuse, cost-per-verified-iteration, phase labeling, stats |
| Trace schema / OTel spans | **shared** | `trace_schema.py` is the seam — co-own it |
| Framing, lit, writing | **Minseok** (lead) | — |

The instrumentation layer is the credibility-critical part and is squarely Vinita's. That is the
honest basis for the author-order conversation — decide a *proposed* order before the meeting.

---

## Open questions to resolve at the sync

1. **Alignment first:** does Vinita agree C1 (measurement) is the lead, not a recipe/optimization
   paper? Everything below is premature if not.
2. **Bandwidth:** realistic hrs/week each. (~10 hrs/wk × ~5–6 wks per person is the binding constraint.)
3. **Compute funding:** Stanford credits / NVIDIA credits / personal?
4. **Author order:** given the instrumentation weighting, what ordering are we proposing?
5. **What I have NOT pre-built:** the engine instrumentation, on purpose — it's a co-design item.

---

## Open design issues to resolve at the sync (from 2026-06-13 adversarial review)

Settle these **before** spending GPU budget — they affect whether H1–H3 are even identifiable. Note
the single pilot cell (fixed horizon, no cache-budget axis) is an **H1-feasibility test only**: H2
needs the horizon sweep, H3 needs a server-wide utilization timeline + offline simulation, and H4
needs the independently-replayable artifact — give each its own protocol.

1. **`locality_gap` definition + bounds.** The contract above says `available − realized` on a common
   denominator; the code (`trace_schema.py`) normalizes by reusable tokens and can return values
   outside [0,1] (it returns −0.4 for realized>reusable). Pick ONE definition (recommend: both rates
   over *total eligible input tokens*), make code + docstring match, and validate `0 ≤ realized ≤ available ≤ 1`.
2. **Trace schema can't yet compute available reuse or attribute eviction.** It records token *counts*
   but not prompt token-IDs / block hashes, global request ordering + timestamps, tokenizer revision,
   cache keys, eviction victims, or tenant provenance — so the infinite-cache replay (and "did chat
   evict agent blocks?") is not computable. Add these (Vinita owns the serving-internal fields). Same
   gap makes the "OTel-format" label aspirational: add real trace/span/parent IDs + timestamps or drop the claim.
3. **Tenancy vs offered-load confound.** `isolated` vs `mixed_0.50` changes *composition* AND total
   load/concurrency at once. Hold the agent trajectories fixed and add chat as a *rate-matched*
   background (control total token-arrival rate + concurrency) so the gap is attributable to interleaving.
4. **Bounded-KV budget is unset** (`bounded_cache_blocks=-1`; no matrix axis). Add a positive
   block/byte budget as a first-class axis; ideally sweep ≥2 pressure regimes.
5. **Cost-per-verified-iteration has horizon-dependent survivor bias** — nulling cost on failures drops
   the expensive long-horizon failures, exactly where "Cost of Grit" lives. Report cost-per-verified-*task*
   including failed-attempt cost + a success/censoring curve, over all attempts (not just successes).
6. **"Tool-gap" ≠ GPU-idle.** `tool_gap_ms` is tool wall-time; under mixed tenancy the GPU serves other
   requests during it. H3 needs an engine-wide utilization timeline to compute idle-by-cause.
7. **Executor/aggregation don't match the design.** `run_pilot.main` loops only tenancy×policy (drops
   repeats + horizon → 4 cells, not 600); `aggregate` returns one global mean, not grouped/paired
   estimates with CIs. Fix the cell runner + grouped, token-weighted, paired stats.
8. **Mixed-tenant cost attribution + attempt structure are undefined.** `total_cost_usd` is one number
   per task with no rule for allocating shared GPU / CPU-tool / idle / background-chat cost, and no way
   to represent multiple *failed attempts* before a success — which cost-per-verified-*task* requires.
   Add an attempt/retry record + a server-accounting window; pre-register the attribution rule + a
   sensitivity analysis.
9. **No experimental-hygiene controls.** No cache warmup/flush, process isolation, teardown, or
   cell-order randomization; cells run in fixed order and engine handles are never closed, so
   carryover/order effects confound results. Add warmup/flush protocols, fresh isolated processes per
   cell, randomized/blocked order, and lifecycle logging.

10. **The chat baseline has no content — the mixed arm is un-constructable as named.** Azure / BurstGPT
    are *token-count-only* traces (no prompt text), but prefix-cache eviction is a function of actual
    token-ID prefixes. Synthesize chat *content* (e.g. ShareGPT / LMSYS-Chat-1M) shaped to the
    Azure/BurstGPT *arrival dynamics*; pre-register, and add a PII-scrub step for the synthesized content.
11. **The infinite-cache replay must use the *identical* recorded token stream.** The online trajectory
    is itself shaped by the bounded-cache run (latencies, timeouts, sampling drift), so "available −
    realized" on the online stream conflates *evicted tokens* with *trajectory divergence*. Record the
    trajectory once and replay the SAME token stream under infinite vs. bounded cache; pre-register.
12. **"Success-rate invariance" must be MEASURED, not assumed** (see `docs/metric-design.md`). Run
    greedy + fixed seeds, cache-on; measure the per-task success delta across policies (paired test) and
    report it as a noise floor; the `none` arm is numerically non-comparable.
13. **No LICENSE / artifact licensing, no example fixture, no pinning.** The headline artifact (C3) is
    unlicensed — add `LICENSE` (Apache-2.0, code) + `LICENSE-data` (CC-BY-4.0, trace) + a committed tiny
    `example_trace.jsonl` + a validator; pin engine SHA / tokenizer revision / benchmark commit /
    per-repeat seeds (none currently exist).

**Sharpened 2026-06-14 (judge panel):** #3 also needs **KV-footprint-matching** (not just rate-matching)
+ **eviction-victim tenant tagging** — equal token-arrival rate does not equalize KV footprint, so the
gap can't be attributed to interleaving without knowing *whose* blocks were evicted. #7 needs a
**pre-registered effect size + power/MDE**: the 3 repeats share the same 50 tasks (effective n ≈ 50
paired, heavy-tailed), so bootstrap over *tasks*, not repeats; the headline locality-tax *fraction* needs
a delta-method / bootstrap CI.

*(Source: internal pass 2026-06-13 (items 1–7) + external Codex pass 2026-06-14 (items 8–9) + adversarial
judge-panel pass 2026-06-14 (items 10–13 + the #3/#7 sharpening + the success-invariance correction +
two falsely-dismissed real competitors: Agent Memory 2606.06448, ThunderAgent 2602.13692). The
headline-metric denominator [cost-per-verified-*task*, group-level] is a sync decision — see `docs/metric-design.md`.)*

### Net-new from the 2026-06-14 judge re-review (pass 2)
14. **(BLOCKER) SWE-bench Verified resolve-rate floor.** A bare ReAct loop on Qwen2.5-Coder-32B may
    resolve only single-digit % of SWE-bench Verified — at 50 scenarios the verified-task *denominator*
    could be ~2–5/cell, nulling the headline metric independent of bias. Add a **minimum-verified-task
    floor** to the kill criteria; measure the resolve rate (or use a stronger scaffold) before scaling.
15. **(BLOCKER) Per-request cache attribution may be infeasible on stock engines.** vLLM/SGLang expose
    prefix-hit + eviction mostly as *server-wide* aggregates under continuous batching; H1 needs
    *per-request, per-tenant* attribution ("did chat evict THIS agent's blocks"), which may require an
    engine patch — materially changing the instrumentation scope. Run a feasibility spike before the sync.
16. **vLLM vs SGLang are not directly comparable.** LRU paged caching vs RadixAttention tree eviction →
    "realized hit / blocks evicted" mean different things and the policy knobs map differently. Treat
    engine as a *stratification* variable with engine-specific metric definitions; never pool for the headline.
17. **Trace-redistribution legality (gates C3; distinct from #13).** Confirm τ²-bench permits
    redistributing *derived trajectories*; SWE-bench instances embed third-party repo code (not uniformly
    MIT) and the trace embeds Qwen *model outputs* — scope released content to permissive repos or store
    token-ID hashes/offsets, and confirm the model license permits releasing generated tokens.
18. **Multi-week run drift.** If model/tokenizer/engine are re-pulled or upgraded mid-collection, the
    "identical recorded token stream" (#11) and prefix-block hashes silently break. Freeze pinned local
    artifacts + log a content hash per cell *before* run start; abort on drift.
19. **The "settle issues before GPU spend" gate is partly circular.** #4 (which KV budget bites),
    #11/#12 (stream/success invariance), and #14 (resolve rate) can only be answered by a micro-run.
    Split the list into *settle-on-paper* vs *needs-a-micro-pilot*; make the first GPU spend an explicit
    instrumentation + floor-rate spike, not the full 1,200-trajectory cell.
