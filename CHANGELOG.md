# CHANGELOG / Decision & Rollback Log

*Human-readable history of substantive changes, keyed to git commits, so any change can be rolled back.
Newest first. Git is the source of truth; this file maps commits → what/why → how to undo. Append a row
here whenever you make a substantive change.*

## How to roll back
- **Inspect a commit:** `git show <hash>`
- **Undo one commit, keep history:** `git revert <hash>`  (safe; makes a new inverse commit)
- **Restore one file to a past state:** `git checkout <hash> -- <path>`
- **Hard reset to a known-good commit (destructive):** `git reset --hard <hash>` then `git push --force-with-lease`
- **Compare:** `git diff <oldhash> <newhash> -- <path>`

## Key reversible decisions (what reverting each era undoes)
- **Metric = cost per verified _task_** (not per-iteration): `docs/metric-design.md` (commit `76be0cb`, extended in the landscape-refresh + judge-panel commits). Revert those to return to the per-iteration framing.
- **Pilot is two-armed** (τ²-bench **+ SWE-bench Verified**): `matrix.yaml` in the landscape-refresh commit (`a58f1a3`). Revert that hunk to return to the τ²-only 600-trajectory pilot.
- **Seam framed as a regime-dependent cost lever** (not a fundamental gap): landscape-refresh commit. 
- **C3 novelty narrowed** to *mixed + cost-labeled + open-infra* (after vLLM×Mooncake): graveyard/candidates/README in `a58f1a3`.
- **README tagline / problem / contributions / methodology rewrite + Mermaid flowchart:** `dab2c27`, `707a7bf`.

## Log

### 2026-06-14 — Ecosystem figure restyled to NeurIPS/ICLR look
Replaced the "AI-generated" palette (ivory background, ~8 hue accents, rounded frosted cards) in `docs/ecosystem-map.html` with a **systems-paper figure aesthetic**: pure-white canvas, **titled group boxes** (PERSONAS · CLIENTS · OPEN SERVING ENGINES · VENDOR · THIS WORK), grayscale white-fill nodes with thin black borders, Helvetica labels + a Times figure caption/key, and **directed arrowheads** trimmed to box borders. Color is now **functional and two-tone only** — red = the orchestrator↔engine seam / interleaving (the problem), blue = this work / its outputs (the contribution); everything else black/gray. Verified via headless-Chrome render.

### 2026-06-14 — Academic redesign of the ecosystem figure + wrong-layer-tools note
- Rebuilt `docs/ecosystem-map.html` from the rounded/"AI-generated" look into an **academic "Figure 1" style**: left-to-right tiered dataflow with serif column headers, rectangular nodes (category tag + title + description), **labeled edges** (the seam, mixed-traffic interleaving, the measurement arrow, pre-emption, anchoring), an edge-type **key**, and a figure **caption**. Added nodes for the *chat co-tenant* (the interleaving driver) and the *Cost-of-Pass anchor*. Verified the layout via headless-Chrome render; fixed an auto-fit bug that clipped the measurement band.
- Extended `docs/observability-and-power.md` with **"wrong-layer tools"**: GPU profilers (Nsight Compute/Systems) and reuse predictors (Tencent FlashMemory `2606.09079`) **cannot** source per-tenant eviction attribution — profilers live at the hardware/kernel layer (no notion of request/tenant/KV-block); the predictor is an intra-request *mechanism*, not cross-tenant observability, and adopting it would make us a mechanism paper. Attribution stays an engine block-manager fact.

### 2026-06-14 — Observability/power doc + interactive ecosystem map
Added `docs/observability-and-power.md` — makes the two BLOCKER issues concrete: (§1) the cache *is* visible per-request off-the-shelf today (vLLM `prefix_cache_hits/queries` + `num_cached_tokens`, SchedulerStats evictions, SGLang/LMCache metrics); the only gap is per-tenant eviction attribution, solved by request-tagging → optional small block-manager hook → footprint-matched proxy, de-risked by a 1-day spike before GPU spend; (§2) **replay is a *different, easier* problem** than instrumentation — it needs only what our harness logs (the recorded request/block stream), not engine internals, so `available − realized = locality gap`; (§3) statistical soundness = denominator floor (#14) + pre-registered MDE/power bootstrapped over tasks (#7) + measured success-invariance (#12). Added `docs/ecosystem-map.html` — self-contained, dependency-free interactive ecosystem map (drag-pan, scroll-zoom, hover-detail, click-to-focus). Rollback: delete the two files + their README pointers.

### 2026-06-14 — Removed IP/disclosure framing; added one-page overview
Per direction, **purged the NVIDIA-disclosure / IP- & employer-publication-review framing** entirely (`stakeholders.md`, `STATUS.md` open-decisions + repo map, `threats-to-validity.md` #7, reading-map #10, `candidates.md` C5, and the CHANGELOG). The open-infra / public-benchmark scope is retained but reframed as a **reproducibility** choice, not an IP one. Added `docs/overview.md` (one-page reference: what / landscape / gap / problem / approach / limitations).

### 2026-06-14 — Added product/ecosystem map (companion lens)
Created `docs/ecosystem-and-product-map.md` — the product/business view (ecosystem relational graph + mindmap, personas, user journeys, pain→opportunity map). Explicitly a *companion* to the measurement paper, not part of its scientific claims; supports the product / internship customer-discovery lens. Rollback: delete the file + its README layout pointer.

### 2026-06-14 — Judge re-review (pass 2) + contradiction fixes
A second judge panel (re-convened fresh — the subagent-continue channel was unavailable) re-read the *corrected* repo, verified the pass-1 fixes landed (Agent Memory/ThunderAgent now ✓, success-invariance corrected, CHANGELOG accurate), and caught what pass 1 + my fixes missed:
- **Fixed 3 internal contradictions:** issue-count (README still said "nine" in 2 line-wrapped spots — numeral now dropped to avoid churn); trajectory count (pilot README still said 600/<$300 single-arm — now 1,200/two-arm); **Tambe** (ledger called him "our faculty contact" but `stakeholders.md` says he passed on the project — reconciled: he is now *adjacent prior art* via Agent Memory 2606.06448; flagged in `stakeholders.md`).
- **Recorded net-new pilot issues #14–#19** (`05-experiments/pilot/README.md`): SWE-bench resolve-rate floor (BLOCKER — denominator may not exist), per-request cache-attribution feasibility on stock engines (BLOCKER — may need an engine patch), vLLM↔SGLang non-comparability, trace-redistribution legality, multi-week run drift, circular "settle-before-spend" gate.
- **Chair verdict:** accept-with-work; the #1 risk is that *no data exists and everything below the schema is `NotImplementedError`*, blocked on the unscheduled co-author sync. Venue: **NeurIPS D&B floor for C3, MLSys stretch for C1, dated arXiv for priority.**

### 2026-06-14 — Adversarial judge-panel review (this entry; corrections committed alongside)
Four parallel "judge" subagents (methodology · literature · contributions/novelty · dataset/artifact) reviewed the repo top-to-bottom; convergent verdict + prioritized critiques recorded in the chat transcript. **Corrections applied this pass (all reversible via the commit that carries them):**
- **Fixed two false citation verdicts** (integrity — the core discipline): **Agent Memory `2606.06448`** (Omri/Tambe, Stanford — real characterization competitor) was wrongly marked ✗; **ThunderAgent `2602.13692`** (real program-aware system) was in the "maybe-hallucinated" bucket. Both flipped to ✓ and added (`sota-verified-2026.md`, `reading-queue.md`).
- **Corrected the success-rate-invariance overclaim** in `docs/metric-design.md` (it is NOT true "by construction"; must be measured — greedy+seeded, cache-on, `none` non-comparable).
- **Narrowed the stale "no public agentic/mixed trace" phrasing** in `STATUS.md` to the four-part form.
- **Added pilot-design issues #10–#13** (`05-experiments/pilot/README.md`): content-free chat baseline; replay-identical-stream; success-invariance-must-be-measured; LICENSE/fixture/pinning. Sharpened #3 (KV-footprint matching + eviction-victim tenant tagging) and #7 (effect size / power / bootstrap-over-tasks).
- **Deferred to co-author decision (NOT changed):** retitle to measured scope; reconsider venue (MLSys Industry Track → likely NeurIPS D&B); de-emphasize the "Cost of Grit" brand vs. "locality tax"; add a LICENSE; add RAG-serving + multi-agent-serving coverage; write the related-work prose (3 files still placeholders).

### 2026-06-14 — Landscape refresh + stress-test edits — `a58f1a3`
4-scout web sweep. Added competitors (KVCache-in-the-Wild 2506.02634, SAGA 2605.00528, TokenCake/PPD/CacheFlow/PBKV/AgentServeSim/WRP, Efficiency Frontier, HAL, Observation-Masking, SWE-Pruner; TokenPowerBench id 2512.03024). C3 hardened vs. the vLLM×Mooncake public trace. Two-armed pilot. metric-design extended (attribution rule, replay semantics, positioning). Seam softened.

### 2026-06-14 — Academic Mermaid flowchart — `707a7bf`
Role-color-coded methodology diagram + legend in the README.

### 2026-06-14 — README sharpen + adversarial honesty fixes — `dab2c27`
Tagline/problem/contributions/methodology rewrite; reframed intent-vs-built overclaims to "planned, open issue #N".

### 2026-06-14 — metric-design.md + GoodServe + seam map — `76be0cb`
Cost-per-verified-task decision doc; resolved GoodServe; added HexAGenT/Cortex; "declared vs inferred" seam map.

### 2026-06-14 — 2nd Codex review reconciliation — `d8ed255`
+2 pilot issues (#8 cost attribution, #9 hygiene controls); doc-consistency fixes.

### 2026-06-14 — Annotated study brief (PDF + HTML) — `6cfde05`
Plain-language paper-by-paper brief (`docs/agentic-inference-brief.*`).

### 2026-06-14 — FlashMemory-DeepSeek-V4 added — `161249c`
Verified 2606.09079 into the ledger (prior art for H3).

### 2026-06-13 — README rewrite — `de9ac6e` · Landscape reconcile (AA-AgentPerf/Dynamo) — `9dc6249` · Working brief reconciled — `3424109` · README cleanup — `72110f6` · Initial scaffold — `ec57a70`
Project bootstrapped, brief reconciled into the repo, AA-AgentPerf/Dynamo industry landscape verified, CONCUR resolved, foundations promoted to ✓, MLSys venue detail corrected.
