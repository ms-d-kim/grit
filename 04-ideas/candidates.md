# Candidate Ideas

*Carried from the 2026-06-10 working session; verification status updated 2026-06-13.
Exploration mode: candidates stay live until a pilot collapses the choice. Every candidate has a
kill criterion; killed ideas move to `graveyard.md`. Check the graveyard before proposing anything
"new."*

## C1 — Iteration-cost curve ("The Cost of Grit") — **LEAD**
- **Claim:** measure cost/latency per *verified* iteration vs horizon × cache policy × compaction
  policy × tenancy × model size, on vLLM/SGLang + public benchmarks; quantify the locality tax.
- **Impact:** the missing meter; serving teams and agent builders both act on it.
- **Collisions:** adversarially checked 06-10. Distinguish from: Don't Break the Cache (2601.06007 ✓,
  provider-API level only), the Efficiency-Frontier-style analytical models (e.g. 2605.23929 ✓),
  More with Less (2510.16786 ✓, capability side). "SideQuest" and "Agent Memory" collisions are
  ⚠ UNVERIFIED — see `02-literature/sota-verified-2026.md`. AA-AgentPerf (Artificial Analysis,
  verified 2026-06-13) measures agents/MW under SLO tiers, **not** cost-per-verified-iteration tied to
  task success (token-economics is their future work) — C1 stays distinct.
- **Scope note (2026-06-13):** the claim lists horizon × cache policy × compaction × tenancy × model
  size, but the V1 pilot matrix varies only horizon × cache policy × tenancy on one model family.
  *Compaction policy* and *model size* are V2 expansion axes — not yet in `matrix.yaml`; narrow the
  written claim to V1 or label them explicitly as staged.
- **Status:** pilot pending. See `05-experiments/pilot/`.

## C2 — Cache-aware context-edit policy formalization
- **Claim:** treat context edits as decisions with cache-write/recompute costs + quality risk;
  policy search; quality×cost frontier across agents and cache regimes (incl. CacheBlend-class).
- **Status:** watching; natural sequel or pivot of C1. Home venue: COLM 2027.
- **Note (2026-06-13):** TTL-style retention across tool gaps now ships in production (Dynamo
  `cache_control` ephemeral TTL; cf. Continuum/CacheTTL) — reinforces measurement-not-mechanism.

## C3 — Mixed-tenancy, cost-labeled public trace + harness
- **Claim:** release the chat×agent interleaved serving trace with arrival dynamics, cache events,
  cost labels, OTel-format cross-layer spans + the collection harness.
- **Collisions:** trace-alone eroded (Continuum 2511.02230 ✓; "lmcache-agent-trace" ⚠ unverified).
  **Tenancy-mix + cost labels on open infra is the surviving differentiation.** Note ServeGen
  (2505.09999 ✓) released a generator on real but non-agentic data. **(2026-06-14) vLLM × Mooncake
  released a public 610-trace Codex/SWE-bench-Pro corpus — agent-only, NOT cost-labeled, NOT mixed;
  it is now the closest prior artifact. Differentiation narrows to: mixed chat+agent + cost labels + open infra.**
- **Status:** bundled into C1's instrumentation by design. De-risked home: NeurIPS D&B.

## C4 — Runtime↔engine hint interface (value-of-hints study → spec)
- **Claim:** measure marginal value of each hint type (resume-time, fan-out, durable-prefix markers)
  vs inference-only baselines, then propose the minimal spec.
- **Collision (2026-06-13, verified online):** NVIDIA Dynamo already SHIPS this interface —
  `nvext.agent_hints` = {priority, osl, speculative_prefill} + `cache_control {ephemeral, ttl}`
  (see `02-literature/sota-verified-2026.md`). The "propose the minimal spec" framing is pre-empted.
- **Note (2026-06-14):** the *declared*-contract side is now broadly crowded — beyond Dynamo: KVFlow
  (Agent Step Graph), Helium (query plan), HexAGenT (online-revealed DAG), Cortex (call graph + SLO
  slack), Autellix. See the "declared vs inferred" seam map in `02-literature/sota-verified-2026.md`.
- **Status:** ⚠ largely pre-empted. Re-scope to *measuring the value of awareness* (the marginal value
  of the existing declared hints on open infra — a measurement, not a spec), or graveyard. Decide at the sync.

## C5 — Iteration-economics metering (product-shaped)
- **Claim:** cost-per-verified-iteration and realized-vs-available locality as first-class serving
  metrics/SLOs; reference implementation on open infra.
- **Status:** the PM-role twin of C1. **Build internally at NVIDIA if at all — keep OUT of this repo**
  (IP separation). Design notes only.

## C6 — Harness-conditional benchmarking methodology
- **Claim:** quantify harness/model attribution (home-field advantage) and cost-per-success norms.
- **Status:** low-cost background option; could be a workshop paper.
