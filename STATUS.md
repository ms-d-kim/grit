# STATUS — Agentic-Serving Characterization Paper

*Last reconciled: 2026-06-13. This is the single place to read "where are we." If it conflicts with
the old planning doc, this wins — that doc is a fossil record of earlier drift.*

## One-paragraph state
Measurement-and-characterization paper for **MLSys 2027 Industry Track (~Oct 2026)**, public
benchmarks (SWE-bench Verified, τ²-bench) + open infra (vLLM/SGLang) only. The lead contribution is
**C1 — the cost-per-verified-iteration / "Cost of Grit" curve**, with the realized-vs-available
**cache-locality gap** folded inside it, plus **C3 — a released mixed chat×agent, cost-labeled,
OTel-format trace + harness** as the cross-cutting artifact. The citation ledger / SOTA pass is done
and re-verified live (`02-literature/sota-verified-2026.md`); prose synthesis (survey, lit-review,
related-work) is still pending — those files are placeholders. Framing has correctly converged from an
earlier "best recipe / optimization" dead-end to measurement. **Next concrete step: the co-design /
metric-redesign meeting** to settle the open pilot-design issues (`05-experiments/pilot/README.md`);
those gate GPU spend — the pilot cell runs only after.

## What changed recently
- 2026-05-31: full lit review; "agentic ≠ chat" declared table stakes.
- 2026-06-10: candidate set C1–C6 + graveyard set; lead moved to C1 (Cost of Grit).
- 2026-06-13: live SOTA re-verification — all core competitors confirmed real; mechanism space
  confirmed crowded; gap confirmed narrowed; primer + pilot scaffold built; several reading-queue
  references flagged UNVERIFIED.
- 2026-06-13: reconciled the working brief into the repo — added the canonical inference-systems
  reading map (`docs/inference-systems-reading-map.md`) and a threats-to-validity / methods checklist
  (`docs/threats-to-validity.md`); resolved CONCUR (2601.22705, ICML 2026) UNVERIFIED → ✓; promoted
  the foundations to ✓ (10/10) and added the Sarathi-Serve ID (2403.02310); corrected the MLSys 2027
  venue detail (the earlier "Apr 11–15 / Crete" claim was wrong — MLSys runs in the US).
- 2026-06-13: verified the AA-AgentPerf / InferenceMAX / NVIDIA Dynamo agentic-inference landscape
  online — all real. Net: **C4 (hint interface) largely pre-empted** by Dynamo `nvext.agent_hints`;
  **H1 (interleaving driver) sharpened and still open** (Dynamo shows 85–97% single-session hit rates
  but no multi-tenant analysis); **C1 + C3 differentiation intact** (AA-AgentPerf is agents/MW under
  SLO with a closed test set, not cost-per-verified-iteration). Logged in `sota-verified-2026.md`.
- 2026-06-13: adversarial review pass (internal + external Codex). Applied doc-consistency fixes
  (corrected a vendor-number framing slip — Dynamo's 85–97% are *realized* not "available"; softened the
  84–99% claim pending a ledger figure; "lit review done" → ledger-done/prose-pending; venue marked
  provisional; misc status/wording). Captured 7 design BLOCKERs for the Vinita sync in
  `05-experiments/pilot/README.md` (locality_gap def + [0,1] bound, trace fields for replay/eviction,
  tenancy↔load confound, bounded-KV axis, cost-per-verified-iteration survivor bias, tool-gap≠GPU-idle,
  executor/aggregation shape). These gate spending GPU budget.
- 2026-06-14: added FlashMemory-DeepSeek-V4 (2606.09079, learned KV-importance prediction) to the
  ledger — prior art for the phase-structure hypothesis (H3); does not pre-empt the lead measurement.
  Produced the annotated **study brief** (`docs/agentic-inference-brief.pdf` + `.html` source): a
  plain-language, jargon-explained edition with a 1–2 paragraph summary of every key paper (foundations,
  agents/harnesses, and the agentic-serving frontier) and per-paper relevance to the project.
- 2026-06-14: 2nd external (Codex) review pass + a metric-design deep-dive. Added **two new pilot-design
  issues** (#8 mixed-tenant cost attribution + attempt/retry structure; #9 experimental-hygiene controls)
  and the "single cell = H1-feasibility only" framing. Metric deep-dive → headline should be
  **cost-per-verified-*task*** (group-level: total cost over all attempts ÷ successful tasks; report in
  GPU-seconds primarily, also $/Joules; cost-per-iteration as a diagnostic) — framed as goodput's
  economic dual; pending co-author sign-off. Applied doc-consistency fixes (next-step gate, brief section
  cross-refs + metric self-contradiction, GPU-idle wording, primer intro, reading-queue/budget wording).
- 2026-06-14: verified the metric/seam literature online; wrote `docs/metric-design.md` (the
  **cost-per-verified-task** decision — resolves pilot issues #1/#5). Resolved **GoodServe** (2605.16867,
  agentic goodput = the throughput-side dual) UNVERIFIED → ✓; added newly-found competitors **HexAGenT**
  (2605.16637) + **Cortex** (2510.14126, workflow-aware serving) and metric anchors **Cost-of-Pass**
  (2504.13359, ICLR 2026), Efficient Agents (2508.02694), EET (2601.05777), TokenPowerBench. Added the
  **"declared vs inferred"** orchestrator↔engine seam map (engine is workflow-agnostic by default; C4 =
  the 'declared' approach, pre-empted). Added a Methodology Mermaid flowchart to the README.
- 2026-06-14: broad landscape sweep (4 parallel scouts) + stress-test pass + adversarial README review.
  **New competitors → ledger:** closest pre-empts **KVCache-in-the-Wild** (2506.02634, locality gap on a
  *closed* stack) and **SAGA** (2605.00528, agent reuse gap on vLLM); a mechanism wave (TokenCake, PPD,
  CacheFlow, PBKV, AgentServeSim, WRP); cost/eval (Efficiency Frontier 2605.23071, HAL 2510.11977,
  Observation-Masking 2508.21433, SWE-Pruner) + TokenPowerBench id fix (2512.03024). **C3 hardened:**
  vLLM x Mooncake shipped a public *agent-only, un-cost-labeled* 610-trace corpus — our narrowed
  (mixed + cost-labeled + open-infra) claim survives but it is the closest prior artifact. **Pilot now
  two-armed** (tau2 + SWE-bench Verified, the long-horizon arm, so H1 isn't killed on tau2 alone; ~$500-600).
  **metric-design.md extended:** cost-attribution rule (marginal + proportional), replay semantics, the
  lossless-caching -> success-rate-invariance strength, and "locality-tax fraction is the headline"
  positioning. **Seam softened** to a regime-dependent cost lever. Verdict: competitive set current as of
  2026-06-14; the measurement + cost-per-verified-task + serving-internal-attribution lane is still open.

## Honest assessment of the gap
Narrowing fast. Mechanism paper = dead. Naive characterization = dead. Even individual measurements
are adjacent to published work. Defensibility = the *bundle* (rigor + breadth + open reproducibility
+ the trace artifact + precise framing). Window is closing — pilot-now-or-lose-it.

## Open decisions (blocking)
1. **Co-author alignment:** confirm Vinita agrees C1 (measurement) is the lead, not a recipe paper.
2. **Author order:** instrumentation is the credibility-critical layer and is Vinita's — decide a
   *proposed* order before the sync.
3. **NVIDIA disclosure:** has the one-line outside-paper disclosure been sent/cleared? Gates whether
   this repo can go public. (`06-collab/stakeholders.md`)
4. **Compute funding:** Stanford / NVIDIA credits / personal?
5. **Reconcile the old planning doc** to one venue (MLSys 2027) and one lead (C1).

## Framing-precision corrections (carry into the writeup)
- Sutradhara is **synthetic-at-production-scale**, not real production; it attributes cache collapse
  to intra-request churn + eviction, not multi-tenancy. H1 must *prove* the interleaving driver.
- "No public trace exists" → **no public *agentic/mixed* serving trace** (ServeGen released a
  generator on real but non-agentic data).

## Repo map
- `STATUS.md` — this file.
- `docs/agentic-inference-primer.md` — expert primer + canonical reading list.
- `docs/inference-systems-reading-map.md` — canonical inference-systems reading map (verified arXiv IDs).
- `docs/threats-to-validity.md` — reviewer-defense checklist + methods/artifact commitments.
- `docs/metric-design.md` — the "Cost of Grit" metric decision (cost-per-verified-task); resolves #1/#5.
- `docs/agentic-inference-brief.pdf` / `.html` — annotated study brief (every key paper summarized in
  plain language; the readable companion to the primer + reading map).
- `02-literature/` — `sota-verified-2026.md` (citation source of truth), `reading-queue.md`,
  and PLACEHOLDER stubs for the prior-session survey / related-work / lit-review (paste real text in).
- `04-ideas/` — `candidates.md` (C1–C6), `graveyard.md` (killed ideas; check before "new" ideas).
- `05-experiments/pilot/` — pilot design doc (`README.md`), `experiments/matrix.yaml`,
  `harness/trace_schema.py` (metric contract, runs), `harness/run_pilot.py` (skeleton w/ ownership seams).
- `06-collab/stakeholders.md` — Vinita / NVIDIA / faculty + IP separation.
- `07-venues/venues.md` — venue tracking.

## How to continue in Code/Cowork
1. Unzip; `git init`; commit to a **private** remote (see README "On GitHub").
2. `cd 05-experiments/pilot && python3 harness/trace_schema.py` to sanity-check the schema.
3. Pilot cell + ownership split are in `05-experiments/pilot/README.md` — that's the Vinita-sync artifact.
