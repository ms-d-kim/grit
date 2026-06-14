# Agentic Inference & Infrastructure — Primer + Canonical Reading List

*Compiled June 2026; foundations re-verified 2026-06-13 (Part B — all ✓). Citations to arXiv IDs
verified against live search are marked ✓; anything still ⚠ must be confirmed before it enters a
bibliography, per the project's standing no-hallucinated-citations rule.*

---

## Part A — The mental model (what you must actually understand)

**1. Inference is two phases with opposite bottlenecks.**
- **Prefill**: process the whole prompt in parallel. Compute-bound. Determines TTFT.
- **Decode**: generate one token at a time, each step reading the full KV cache. Memory-bandwidth-bound. Determines per-token latency.
- Core metrics: **TTFT** (time-to-first-token), **TPOT/ITL** (inter-token latency), **throughput** (tokens/s), and **goodput** (throughput that actually meets SLOs — the metric that matters).

**2. The KV cache is the scarce resource everything revolves around.**
- Every token's key/value tensors are cached to avoid recomputation. Cache size grows with **context length × concurrency**. When GPU memory fills, the engine evicts.
- **Paging** (PagedAttention) fixes fragmentation by storing the cache in fixed-size blocks mapped like OS virtual memory.
- **Prefix caching / RadixAttention** reuse the KV of shared prefixes (system prompts, tool defs, history) across requests. This is the lever that makes multi-turn cheap — *when it isn't evicted first*.

**3. Continuous batching** (Orca) — iteration-level scheduling that lets requests join/leave a batch every step. The single biggest throughput unlock; assume it as baseline.

**4. Disaggregation** — split prefill and decode (DistServe) or chunk prefill into decode batches (Sarathi-Serve) so each phase runs at its optimal config.

**5. The agentic shift (the whole reason your paper exists).** Chat = one prompt → one stream, cache lives one turn. Agents = a **stateful loop**: model → tool → model → tool …, where:
- context grows **monotonically** across the trajectory (not just within one response),
- the model is **re-entered** many times with a mostly-shared prefix,
- the GPU **idles** during tool calls (tool-call gaps),
- the prefill/decode balance **flips** toward decode-dominated, and KV state becomes **long-lived** rather than disposable.

**6. The orchestrator/engine seam.** The orchestrator (LangGraph, CrewAI, OpenAI Agents SDK) and the serving engine (vLLM, SGLang) are decoupled black boxes. Neither sees the other's state — the engine is **workflow-agnostic** (Cortex's word), blind to the agent loop, the coming tool pause, and cross-request prefix sharing — so globally optimal cache/scheduling is impossible. "Break the abstraction barrier" is the recurring 2026 theme, and the frontier splits into **declaring** the contract (hints/plans/DAGs: Dynamo `agent_hints`, KVFlow, Helium, HexAGenT, Cortex, Autellix, Sutradhara) vs **inferring** it engine-side (Continuum/CacheTTL TTL heuristic, GoodServe prompt-inference). Nobody has standardized it or measured the *value of awareness* on open infra — that's our wedge.
*Severity is regime-dependent*, though: RadixAttention already shares prefixes by content and good
routing alone hits 85–97%, so the seam bites mainly under bounded cache + interleaving + long horizon —
treat it as an unquantified cost lever in that regime, not a fundamental gap. (See the "declared vs
inferred" note in `../02-literature/sota-verified-2026.md`.)

**7. Two competing paradigms in the ecosystem.**
- **Externalize** — keep the model frozen, optimize the scaffold/prompt/skill document (SkillOpt, ALIGN).
- **Internalize** — compile a recurring procedural workflow *into model weights*, getting near-frontier quality at ~1/100 the cost (Dennis et al.).
- These bound your scope: both dominate for **procedural** tasks, so your paper targets the **non-compilable** workload — open-ended, long-horizon, novel-per-run — which is exactly where neither wins and serving cost is unavoidable.

**8. Eval hygiene (where most agent papers are sloppy, and where you can be credible).**
- **Harness attribution / home-field advantage**: a model's benchmark score depends heavily on its scaffold. Attribute effects to model vs harness vs serving, or your numbers mean nothing.
- **Cost-per-success, not accuracy alone**: report $/verified-task, not $/token or raw pass rate.
- **Contamination**: prefer contamination-resistant / held-out benchmarks (SWE-bench Pro, SWE-EVO).

---

## Part B — Canonical foundations (read these first)

**Serving systems** *(all ✓ verified 2026-06-13 per the working brief)*
- **PagedAttention / vLLM** — Kwon et al., SOSP 2023, arXiv 2309.06180 ✓. The paging model for KV cache; the de-facto open serving baseline.
- **Orca** — Yu et al., OSDI 2022 ✓ (no arXiv). Continuous (iteration-level) batching.
- **SGLang / RadixAttention** — Zheng et al., arXiv 2312.07104 ✓. Prefix-sharing via a radix tree; the most relevant cache story to your hypotheses.
- **DistServe** — Zhong et al., OSDI 2024, arXiv 2401.09670 ✓. Prefill/decode disaggregation for goodput.
- **Sarathi-Serve** — Agrawal et al., OSDI 2024, arXiv 2403.02310 ✓. Chunked prefill; throughput-latency tradeoff.
- **FlashAttention** — Dao et al., arXiv 2205.14135 ✓. IO-aware exact attention.
- **Speculative decoding** — Leviathan et al., arXiv 2211.17192 ✓. (Note: a *serving-engine* feature, not an orchestrator one.)

> The broader inference-systems canon (disaggregation, attention kernels, KV-cache compression,
> parallelism, quantization, speculative decoding) is mapped and verified in
> [`inference-systems-reading-map.md`](inference-systems-reading-map.md).

**Agent patterns** *(all ✓ verified 2026-06-13)*
- **ReAct** — Yao et al., arXiv 2210.03629 ✓. Reason+act interleaving; the default loop.
- **Reflexion** — Shinn et al., arXiv 2303.11366 ✓. Self-critique memory.
- **Toolformer** — Schick et al., arXiv 2302.04761 ✓. Learned tool invocation.
- **ReWOO / Plan-and-Execute** — Xu et al., arXiv 2305.18323 ✓. Decouple planning from execution.
- **Tree of Thoughts** — Yao et al., arXiv 2305.10601 ✓. Search over reasoning branches.

**Protocols**
- **MCP (Model Context Protocol)** — Anthropic, late 2024 ✓ (context). The emerging tool-interface standard.
- **A2A (Agent-to-Agent)** — 2025 ⚠ verify. Cross-agent discovery/delegation.

---

## Part C — The agentic-serving frontier (verified June 2026)

This is your live competitive set. All IDs below were confirmed against search.

**Workload characterization (closest prior art)**
- **Agentic AI Workload Characteristics** — Yuan, Nayak, Kundu, Talati (UIUC / Gimlet Labs / Intel), arXiv **2605.26297** ✓. Traces ReAct agents across 5 benchmarks; finds agentic serving is **decode-dominated with very high KV reuse**, plus a temporal **read/explore → execute/write** tool-use structure. *This is the "high available reuse" pole of your contradiction.*
- **Sutradhara** — Biswas, Goel, Mohan, Khare, Parayil, Ramjee, Bansal (Microsoft Research / M365), arXiv **2601.12967** ✓. **Synthetic requests at production scale** (not real production traffic — important). Finds tool calls = 30–85% of first-token latency and **KV hit rates collapse despite reuse**; proposes orchestrator-engine co-design. *This is the "realized collapse" pole — but attributes collapse to intra-request churn + eviction, not specifically multi-tenancy.*
- **ServeGen** — Xiang et al. (Alibaba / Peking Univ.), arXiv **2505.09999** ✓, NSDI'26, open-source. Real production characterization (billions of requests, 12 models, 4 months) + a **workload generator** — but covers language/multimodal/reasoning, **not agentic tool-loops**. Releases a generator, not a raw trace.
- **A CPU-Centric Perspective on Agentic AI** — Georgia Tech / Intel, arXiv **2511.00739** ✓. Host-CPU tool processing can reach ~90% of latency; CPU dynamic energy up to ~44%.

**Cache / scheduling mechanisms for agents (this space is now CROWDED)**
- **Continuum / CacheTTL** — Hanchen Li et al. (Berkeley / Sky), arXiv **2511.02230** ✓. KV time-to-live retention across short tool-call pauses; renamed CacheTTL across versions.
- **KVFlow** — Pan et al. (UCSD / AWS), arXiv **2507.07400** ✓. Workflow-aware eviction via an "Agent Step Graph" (LRU anticipates wrong).
- **KVCOMM** — arXiv **2510.12872** ✓. Training-free KV reuse across multi-agent with cache-offset alignment; ~70% reuse.
- **Helium** — Wadlom et al. (NUS), arXiv **2603.16104** ✓. Treats agentic workflows as **query plans**, LLM calls as first-class operators; cross-call cache-aware scheduling.
- **Autellix** — Luo et al. (Berkeley), arXiv **2502.13965** ✓. Serving engine for "LLM agents as general programs."
- Adjacent/newer to watch: **SparseX** (2606.01751, interleaved KV sharing) ✓, **TokenDance** (2604.03143, multi-agent collective KV sharing) ✓, **ScaleSim** (2601.21473, multi-agent simulation memory) ✓, **Aragog** (2511.20975, JIT model routing for agentic workflows) ✓, **AWO** (2601.22037, meta-tool compilation) ✓.

**Measurement / cost (the angle adjacent to yours)**
- **Don't Break the Cache: Prompt Caching for Long-Horizon Agentic Tasks** — Lumer et al. (PwC US), arXiv **2601.06007** ✓. Quantifies prompt-caching cost/latency savings across OpenAI/Anthropic/Google on DeepResearch Bench. *Occupies the "quantify caching for agents" space — but at the provider-API black-box level, not open-infra serving internals.*
- **More with Less: Turn-Control Strategies for Efficient Coding Agents** — arXiv **2510.16786** ✓. Cost-per-patch (~$5.85 avg, ~$7.80 for a correct patch; 41–58 median turns). *Cost-per-iteration from the capability side, not serving side.*
- **Toward Reliable Design of LLM-Enabled Agentic Workflows: Latency-Reliability-Cost Tradeoffs** — arXiv **2605.23929** ✓. Models the tradeoff analytically.

**The "internalize" boundary**
- **Compiling Agentic Workflows into LLM Weights** — Dennis et al. (Univ. of Melbourne), arXiv **2605.22502** ✓. "Subterranean agent," near-frontier quality at ~1/100 cost. The reason to scope to non-compilable workloads.

---

## Part D — Benchmarks you'll actually use or cite

- **SWE-bench / SWE-bench Verified** — real GitHub issues; the de-facto coding-agent benchmark.
- **SWE-bench Pro** — contamination-resistant, long-horizon, held-out set. Prefer for currency.
- **SWE-EVO** — arXiv 2512.18470 ✓; software-evolution tasks (multi-PR, ~21 files); proposes a partial-progress "Fix Rate."
- **τ-bench / τ²-bench** — Sierra; tool-agent-user interaction (your stated benchmark).
- **WebArena, GAIA** — web / general-assistant agents.
- **BFCL** — Berkeley Function-Calling Leaderboard.
- **Chat baselines for comparison**: Azure LLM Inference Trace 2024, BurstGPT.

---

## Part E — Things people get wrong (your edges)

1. **$/token hides $/verified-task.** A cheaper-per-token run that needs 3× the iterations is more expensive. Always anchor cost to verified outcomes.
2. **"Available" reuse ≠ "realized" reuse.** 2605.26297 measures what's *reusable*; production sees what's *retained after eviction*. The gap is your candidate finding — but prove the mechanism, don't assert it.
3. **Don't treat Sutradhara as real production data** — it's synthetic-at-production-scale. State this precisely; it actually strengthens the case for a public agentic trace.
4. **Attribute latency correctly** — model capability vs harness behavior vs serving infra are confounded in raw benchmark numbers. Separating them is half your methodological contribution.
5. **Don't cite vendor headline figures** (e.g., SWE-bench Pro marketing numbers, model-launch blog claims) as research evidence. Use the paper + your own measurement.
