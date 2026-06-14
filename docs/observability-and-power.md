# Observability & statistical power — how the two blockers actually get solved

*Makes the two BLOCKER pilot issues concrete: #15 (can we even see the cache per request?), #2/#11
(can we recompute the ideal?), #14 (is the denominator big enough?), #7 (is the effect bigger than the
noise?). If the answers here hold, the study is measurable AND a real contribution. If they don't, we
learn that for ~1 day of spike work instead of ~$600 of GPU.*

## 1. The instrumentation question — can we see the cache? (issue #15)

**What we need:** per-request **realized** reuse (the numerator) + per-tenant **eviction attribution**
("did chat evict *this* agent's blocks") — on open engines, ideally with no patch.

**What's exposed off-the-shelf, mid-2026:**
- **vLLM** ships `vllm:prefix_cache_queries` and `vllm:prefix_cache_hits` Prometheus counters
  (token-level: *queries* = prompt tokens seen, *hits* = tokens already cached), per-request
  `num_cached_tokens` in the response usage, eviction events via `SchedulerStats`, and `LLM.get_metrics()`.
  ([vLLM metrics docs](https://docs.vllm.ai/en/latest/design/metrics/), [counters issue](https://github.com/llm-d/llm-d-inference-sim/issues/356))
- **SGLang / RadixAttention** exposes a cache hit-rate metric.
- **LMCache** re-exposes cache metrics through the [vLLM `/metrics` endpoint](https://docs.lmcache.ai/production/observability/vllm_endpoint.html); Mooncake / llm-d add KV-pool stats.
- **Standardization is mid-flight, not done:** OTel genai semantic-conventions
  [issue #87](https://github.com/open-telemetry/semantic-conventions-genai/issues/87) proposes
  `gen_ai.server.kv_cache.{hit_rate, evictions_total, usage_ratio}` — not stable yet, so we can't assume it.

**Verdict:** the **numerator is gettable today** (per-request cached-token count, no patch). Aggregate
evictions are gettable. The one genuinely missing piece is **per-tenant eviction *attribution***.

**How we get attribution, in preference order:**
1. **Tag requests by tenant; read per-request `num_cached_tokens`.** Gives realized reuse per tenant with
   zero engine changes. (Do this regardless.)
2. **Correlate `SchedulerStats` eviction events to block→request ownership.** If the event stream carries
   block ids, no patch needed. If not, a *small* block-manager hook (Vinita's layer) logs
   `(evicted_block, owning_request, tenant)` — a few lines, not a new system.
3. **Footprint-matched proxy (issue #3).** If neither, run agent-only vs. agent+chat with a *matched* KV
   footprint; the **delta** in realized reuse is the interleaving tax even without naming the victim block.

**First action — the instrumentation spike (1 day, 1 config, before any GPU spend):** confirm which of
1/2/3 the stock engines actually give us. This is the cheapest possible de-risk of issue #15.

## 2. The replay question — is it the *same* problem? (issue #2/#11)

**No — and it's the easier half.** The two are different axes:

| | online instrumentation (§1) | offline replay |
|---|---|---|
| computes | **realized** reuse (what actually got reused) | **available** reuse (the ideal, infinite cache) |
| depends on | the **engine** reporting its internals | **our harness** recording the request stream |
| hardest piece | per-tenant eviction attribution | nothing — it's our own log |

Replay = simulate an infinite cache over the **recorded ordered (request, prefix-block) stream** and count
how many blocks *could* have been reused. That needs only that `trace_schema` records, per request: the
token/block sequence (or block hashes) + arrival order + agent lineage. **All of that is in our control** —
it does not require seeing inside the engine.

So the uncertainty you flagged is real but **localized to §1**. Replay is gated by *what we choose to log*,
not by engine observability. The two overlap only at "log enough." And:

> **locality gap = available (replay) − realized (instrumentation).**

Concretely: even in the worst case where eviction attribution needs a patch (§1 step 2), replay still works,
because it never touches the engine. That's why replay is the tractable half.

## 3. Statistical soundness — enough to be a real contribution (issues #14, #7, #12)

Three independent things have to hold; each has a pre-registered guard:

- **Denominator floor (#14, BLOCKER).** The metric is cost-per-**verified**-task, so we need enough tasks the
  agent actually solves. A bare ReAct scaffold resolves maybe ~20–30% of SWE-bench Verified → at 50 tasks
  that's ~10–15 successes per cell, too few for a stable mean. **Fixes:** use a stronger published scaffold;
  pre-select a solvable subset; make τ²-bench (higher success rate) the *primary* curve and SWE-bench the
  *stress* arm; report successes-per-arm; widen N if the floor is too low. **Pre-register a minimum
  successes-per-cell** before spending.
- **Pre-registered MDE + power (#7).** Decide the smallest **locality-tax fraction** worth detecting (e.g.
  10%), pick N (tasks × seeds) to detect it at ~80% power, and **bootstrap confidence intervals over tasks**
  (tasks are the unit of randomness, not trajectories). The matrix —
  `{τ²-bench, SWE-bench Verified} × {isolated, mixed} × {LRU, retain-during-tool} × 50 tasks × 3 seeds
  ≈ 1,200 trajectories` — is *sized* for this; the power calc on pilot data confirms or adjusts it.
- **Success-invariance measured, not assumed (#12).** Cost-per-task only compares across arms if the *set* of
  solved tasks is roughly stable. Greedy decode + fixed seeds, cache-on; the `none` arm is non-comparable by
  design; **measure** the drift, don't assume it away.

**Net:** the contribution is valuable iff *(numerator visible — §1)* AND *(denominator big enough — floor)*
AND *(effect bigger than noise — MDE)*. The spike (§1) plus a power calc on pilot data settle all three
**before** the full spend — which is exactly issue #19's "settle before you spend" gate, made concrete.
