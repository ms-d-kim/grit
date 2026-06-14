# SOTA — Verified Literature Ledger

*Verification pass: 2026-06-13 (live search). This is the source of truth for citations.
Status: ✓ = verified this session (ID + authors + finding); ⚠ = NOT verified this session,
treat as suspect until checked; ✗ = ID in prior notes appears wrong.*

> Standing rule for this project: prior sessions hallucinated arXiv references. Nothing goes
> into a bibliography or a claim without a ✓ here.
>
> Scope: this ledger is authoritative for the *agentic-serving* competitive set + anything entering a
> claim. The canonical inference-systems foundations are verified in the companion
> [`../docs/inference-systems-reading-map.md`](../docs/inference-systems-reading-map.md) — treat the
> two together as the source of truth.

## Closest prior work (the competitive frontier)

| Paper | arXiv | Authors / Affil | One-line finding | Status |
|---|---|---|---|---|
| Agentic AI Workload Characteristics | 2605.26297 | Yuan, Nayak, Kundu, Talati — UIUC / Gimlet / Intel | Agentic serving is decode-dominated with high KV reuse; read/explore→execute/write tool phases | ✓ |
| Sutradhara (orchestrator-engine co-design) | 2601.12967 | Biswas, Goel, Mohan, Khare, Parayil, Ramjee, Bansal — MSR / M365 | Tool calls 30–85% of time-to-first-token (TTFT); KV hit rates collapse despite reuse | ✓ |
| ServeGen (workload char + generator) | 2505.09999 | Xiang et al. — Alibaba / PKU (NSDI'26) | Real prod characterization (billions req, 12 models, 4mo) + open-source generator | ✓ |
| CPU-Centric Perspective on Agentic AI | 2511.00739 | Georgia Tech / Intel | Host-CPU tool processing dominates latency on heterogeneous CPU–GPU | ✓ |
| Compiling Agentic Workflows into LLM Weights | 2605.22502 | Dennis, Patil, Shabahang, Guo — Univ. Melbourne | "Subterranean agent": near-frontier quality at ~1/100 cost (the internalize bet) | ✓ |

### Critical nuances (do not get these wrong)
- **Sutradhara is SYNTHETIC requests at production scale**, not real production traffic. And it
  attributes cache collapse to intra-request context churn + eviction — **not** specifically to
  multi-tenant interleaving. Our "contradiction with 2605.26297" framing partly resolves without
  invoking tenancy; H1 must *prove* the interleaving contribution, not assume it.
- **ServeGen releases a generator on real but NON-agentic data.** So "no public trace exists" must
  be stated precisely as **no public agentic/mixed serving trace**.

## Cache / scheduling mechanisms for agents (this space is CROWDED → mechanism paper is dead)

| Paper | arXiv | Note | Status |
|---|---|---|---|
| Continuum / CacheTTL | 2511.02230 | Li et al., Berkeley/Sky — KV TTL retention across tool gaps; LRU breaks for agentic interleaving | ✓ |
| KVFlow | 2507.07400 | Pan et al., UCSD/AWS — workflow-aware eviction (Agent Step Graph) | ✓ |
| KVCOMM | 2510.12872 | training-free KV reuse across multi-agent, cache-offset alignment, ~70% reuse | ✓ |
| Helium | 2603.16104 | Wadlom et al., NUS — agentic workflows as query plans, LLM-as-operators | ✓ |
| Autellix | 2502.13965 | Luo et al., Berkeley — serving engine for "agents as general programs" | ✓ |
| SparseX | 2606.01751 | segment-level KV sharing for interleaved serving (June 2026) | ✓ |
| TokenDance | 2604.03143 | multi-agent collective KV cache sharing | ✓ |
| ScaleSim | 2601.21473 | multi-agent simulation, invocation-distance memory mgmt | ✓ |
| Aragog | 2511.20975 | JIT model routing for agentic workflows | ✓ |
| AWO (meta-tools) | 2601.22037 | compile recurring behaviors into deterministic meta-tools | ✓ |
| CONCUR | 2601.22705 | ICML 2026 — congestion-based concurrency control for agentic batch inference | ✓ |
| HexAGenT | 2605.16637 | workflow- & heterogeneity-aware scheduling; request as an online-revealed DAG (verified 2026-06-14) | ✓ |
| Cortex | 2510.14126 | workflow-aware resource pooling/scheduling from a compiled call graph + per-request SLO slack; notes platforms are "workflow-agnostic" (verified 2026-06-14) | ✓ |

> **Adjacent (not agent-specific):** *FlashMemory-DeepSeek-V4 / Lookahead Sparse Attention* (arXiv
> 2606.09079 ✓, Tencent et al.) — a learned Neural Memory Indexer predicts *query-critical* KV chunks
> and keeps only those (~13.5% footprint). This is **intra-request, ultra-long-context** KV
> sparsification (importance prediction), NOT multi-tenant interleaving or tool-gap survival — so it
> does **not** pre-empt C1, but it is prior art for **H3**'s "phase-aware retention" (a learned version
> of the same idea) and reinforces the crowded mechanism space. Caveats: DeepSeek-V4-architecture-coupled
> (not a drop-in vLLM/SGLang policy for the Qwen pilot); preliminary, project suspended — treat figures
> as unsettled.

### The orchestrator↔engine seam: declared vs. inferred (verified 2026-06-14)

By default the orchestrator (LangGraph/CrewAI) and the engine (vLLM/SGLang) are decoupled: the engine
sees a flat stream of independent requests and is **workflow-agnostic** (Cortex's word) — blind to the
agent loop, the coming tool pause, and cross-request prefix sharing. The 2026 frontier is a race to
break this seam, and it splits into two families:
- **Declared** (the agent *tells* the engine its structure/intent): Dynamo `nvext.agent_hints`,
  KVFlow (Agent Step Graph), Helium (query plan), HexAGenT (online-revealed DAG), Cortex (compiled
  call graph + SLO slack), Autellix (agents-as-programs), Sutradhara (explicit orchestrator-engine co-design).
- **Inferred** (the engine *guesses*, no signal): Continuum/CacheTTL (TTL heuristic — the agent will be
  back), GoodServe (infers task type from the prompt at the router).
- **Cross-request/agent KV awareness** (a sub-form): KVCOMM, SparseX, TokenDance share/dedupe KV across
  interleaved or cooperating agents.

**Our wedge:** nobody has *standardized* the contract, and nobody has *measured* — on open infra, under
realistic mixed traffic — how much reuse is actually lost when it is absent vs. present. That quantified
**"value of awareness"** is the gap. (The hint interface, C4, is the *declared* approach — now pre-empted
by Dynamo; see `04-ideas/candidates.md`.)

**Severity caveat (don't overclaim the seam).** RadixAttention already shares prefixes *by content*
without any signal, and Dynamo hits 85–97% with good routing alone — so the seam bites hardest
specifically under **bounded cache + multi-tenant interleaving + long horizon** (our scope) and may be
minor when well-provisioned / single-tenant. We frame it as an **unquantified cost lever in that
regime**, not a fundamental architecture gap. Risk: if cheap inference (TTL) or "just add cache" recovers
most of the reuse, the measured value of awareness is small — which is itself a publishable result.

## Measurement / cost (the angle adjacent to ours)

| Paper | arXiv | Note | Status |
|---|---|---|---|
| Don't Break the Cache (prompt caching for agents) | 2601.06007 | Lumer et al., PwC — quantifies prompt-caching cost across providers; **provider-API level, not open-infra internals** | ✓ |
| More with Less (turn-control for coding agents) | 2510.16786 | cost-per-patch (~$5.85 avg, ~$7.80 correct), 41–58 median turns — capability side, not serving | ✓ |
| Latency-Reliability-Cost tradeoffs in agentic workflows | 2605.23929 | analytical tradeoff model | ✓ |
| SWE-EVO (long-horizon SE benchmark) | 2512.18470 | multi-PR tasks, "Fix Rate" partial-progress metric | ✓ |
| **Cost-of-Pass** (economic eval framework) | 2504.13359 | ICLR 2026 — expected $ for a *correct* solution (Farrell efficiency); the **academic anchor for our cost-per-verified-task**; we move it from the API black box into open-infra internals | ✓ |
| Efficient Agents | 2508.02694 | efficiency–effectiveness tradeoff; 28.4% cost-of-pass improvement on GAIA (capability side) | ✓ |
| EET (early termination for SE agents) | 2601.05777 | experience-driven early stopping; −32% avg cost, ≤0.2% resolution loss — the "when to stop gritting" lever | ✓ |
| TokenPowerBench (energy) | AAAI | benchmarks **J/token** power draw of LLM inference — the energy numerator for the cost-of-grit | ✓ |
| **GoodServe** (agentic goodput) | 2605.16867 | SJTU/CUHK-SZ — agentic **goodput** = E2E-SLO completions/s over heterogeneous resources; router-layer, *infers* task type (no hints); no cost-to-success, no released trace. The **throughput-side dual** of our cost-per-verified-task — see `../docs/metric-design.md` | ✓ |

## Industry / vendor benchmarks & systems (verified real online 2026-06-13)

*Real and source-checked — but vendor blogs / a commercial benchmark, NOT peer-reviewed. Use for
landscape & motivation; do NOT quote their numbers as research evidence (no-vendor-headline rule).*

| Source | Where | What it is / relevance | Status |
|---|---|---|---|
| AA-AgentPerf (Artificial Analysis) | artificialanalysis.ai/articles/aa-agentperf | "First agentic-AI hardware benchmark": concurrent **agents per megawatt** (lead metric) under model-specific SLO tiers (P25 output speed, P95 TTFT) on **real coding-agent trajectories** (≤200 turns; input ~27K mean, ≤131K), multi-vendor HW. **Test set CLOSED/held-out.** Cost-per-success / token-economics = *future work.* | ✓ real |
| SemiAnalysis InferenceMAX / InferenceX | inferencex.semianalysis.com | Open, continuous inference benchmark — cost-per-token / throughput / TCO. The "InferenceX" referenced as prior work. **Not agentic** (general serving). | ✓ real |
| NVIDIA Dynamo — agentic inference | developer.nvidia.com/blog/full-stack-optimizations-for-agentic-inference-with-nvidia-dynamo | **KV-aware router** (global KV-block index, overlap-score placement) + **agentic hints** `nvext.agent_hints` = {priority, osl, speculative_prefill} + `cache_control {ephemeral, ttl}`. Reports 85–97% Claude-Code cache hit (**realized, under their routing — not infinite-cache "available"**), 11.7× read/write. **No multi-tenant interleaving / realized-vs-available analysis; no released traces.** | ✓ real |
| NVIDIA NemoClaw / OpenShell | nvidia.com/nemoclaw | Autonomous-agent blueprints (Nemotron) + sandboxed runtime (OpenShell/OpenClaw). Context for the "stack extends upward" framing; not serving characterization. | ✓ real |

### Relevance to our contributions (important)
- **C4 (runtime↔engine hint interface) is largely PRE-EMPTED.** Dynamo already ships the hint spec C4
  would propose (`nvext.agent_hints`: priority / osl / speculative_prefill / cache_control TTL).
  Re-scope C4 to *measuring the marginal value of these existing hints on open infra*, or graveyard it.
- **H1 (interleaving as a distinct driver) is SHARPENED and still open.** Dynamo's 85–97% are
  *realized* hit rates measured under its OWN KV-aware routing in single-session/managed settings —
  NOT infinite-cache *available* reuse, and with no multi-tenant interleaving / bounded-cache analysis.
  Use them as motivation only (even good production routing leaves the interleaving question open);
  do NOT equate them with our "available" pole or compare them numerically with our locality metric.
- **C1 stays distinct.** AA-AgentPerf = agents/MW under SLO, not **cost-per-verified-iteration** tied
  to success (they list token-economics as future work).
- **C3 / H4 (no public agentic/mixed trace) STRENGTHENED.** AA-AgentPerf's test set is closed; Dynamo
  releases no traces. The public-trace gap stays open.

## 2026-06-14 landscape refresh (web sweep — new entrants & pre-empt risks)

*All IDs found via live search this pass. Two are the closest pre-empts yet; the rest deepen the
"mechanism space is crowded" verdict. Re-read SAGA + KVCache-in-the-Wild before drafting.*

**Closest pre-empts (read first):**
- **KVCache Cache in the Wild** — 2506.02634 (SJTU/Alibaba, USENIX ATC'25) — production-trace
  characterization of KV reuse incl. *ideal-hit-ratio-vs-cache-size* (≈ realized-vs-available locality)
  on real single/multi-turn mixed traffic. ✓ **Pre-empts the characterization half** — but closed stack,
  no agent tool-gap isolation, no cost-per-task. Our wedge = open infra + agent + cost-per-verified-task.
- **SAGA — Workflow-Atomic Scheduling** — 2605.00528 — program-level scheduling on **vLLM**; Agent
  Execution Graphs predict cross-tool-call KV reuse to within 1.31× of Bélády. ✓ Near-competitor
  (open-infra, quantifies the reuse gap on agent traffic) — but agent-only, no mixed traffic, no cost-per-task.

**Mechanism wave (reinforces: mechanism paper = dead):** TokenCake 2510.18586 · RelayCaching 2603.13289 ·
PrefillShare 2602.12029 · PPD (not-all-prefills-equal) 2603.13358 · CacheFlow 2604.25080 · Halo 2509.02121 ·
PBKV (predict agent invocation) 2605.06472 · AgentServeSim (simulator) 2606.09613 · Agent.xpu (edge)
2506.24045 · WRP / vLLM-Semantic-Router vision 2603.21354 (names our chat-vs-agent axis).

**Public agentic trace now EXISTS (C3 watch):** **vLLM × Mooncake** (vLLM blog, May 2026) open-sourced a
**610-trace Codex/SWE-bench-Pro corpus** (HF; ~33 turns median, ~80–180K ctx, 94%+ reusable prefixes),
reporting cache hit 1.7%→92.2% via a distributed KV pool. **Agent-only, NOT cost-labeled, NOT mixed** → our
narrowed claim (mixed chat+agent **+ cost-labeled** open-infra trace) survives, but this is the closest
prior artifact — cite + differentiate. Dynamo v1.2–1.3 is adding an "Agent Trajectory Interchange Format"
+ agentic trace-replay in-tree — watch.

**Cost/eval + harness confounds (new):** Efficiency Frontier 2605.23071 (amortized-reuse cost) · "Price of
Progress" 2511.23455 · HAL accuracy-cost Pareto 2510.11977 · Observation-Masking / Complexity Trap
2508.21433 (masking halves cost — a confound) · SWE-Pruner 2601.16746 · TokenPowerBench **2512.03024**
(AAAI; J/token — corrects the earlier id-less entry).

**Benchmarks (current set):** SWE-bench Verified · **SWE-bench Pro 2509.16941** · SWE-bench-Live · SWE-EVO
2512.18470 · AppWorld 2407.18901 · τ²-bench · GAIA · BFCL v4. (Pilot now runs τ² **+ SWE-bench Verified** —
the long-horizon arm where the gap is visible; see `../05-experiments/pilot/experiments/matrix.yaml`.)

## Foundations (verified 2026-06-13 per the working brief)

PagedAttention/vLLM 2309.06180 ✓ · Orca (OSDI'22, no arXiv) ✓ · SGLang/RadixAttention 2312.07104 ✓ ·
DistServe 2401.09670 ✓ · Sarathi-Serve 2403.02310 ✓ · FlashAttention 2205.14135 ✓ · ReAct 2210.03629 ✓ ·
Reflexion 2303.11366 ✓ · Toolformer 2302.04761 ✓ · ReWOO 2305.18323 ✓ · ToT 2305.10601 ✓ · MCP (standard) ✓

The broader inference-systems canon (Splitwise, Mooncake, AlpaServe, FlashInfer, MQA/GQA, StreamingLLM,
H2O, KIVI, Prompt Cache, Megatron/GPipe/ZeRO/Ring, quantization, speculative decoding) is mapped and
verified in [`../docs/inference-systems-reading-map.md`](../docs/inference-systems-reading-map.md).

## ⚠ UNVERIFIED references carried over from June-10 notes — CHECK BEFORE USE

These appear in `04-ideas/candidates.md` and `02-literature/reading-queue.md` but were NOT
confirmed this session. Some may be internal codenames, renamed, or hallucinated:
- **SideQuest (2602.22603)** — not verified.
- **Agent Memory (2606.06448)** — ✗ likely wrong ID. A real paper "Agent Memory Below the Prompt"
  may exist at **2603.04428** — ⚠ NOT verified this session; confirm before use.
- **AutoLab** (and its "+0.43" harness-ablation figure) — not verified; do not quote the figure.
- **Inside the Scaffold**, **Self-Harness**, **lmcache-agent-trace**, **ThunderAgent**,
  **Agentix@NSDI** — not verified this session.
- **GoodServe** — ✓ RESOLVED 2026-06-14: real (arXiv 2605.16867, SJTU/CUHK-SZ); agentic goodput over
  heterogeneous resources; promoted to the measurement/cost table above.
- **CONCUR** — ✓ RESOLVED 2026-06-13: real (arXiv 2601.22705, ICML 2026); promoted to the mechanisms
  table above.

## Verdict (2026-06-13)

The field has converged on the orchestrator/engine seam + cache-under-agents as *the* problem
(MSR, Berkeley/Sky, Alibaba, UCSD, NUS, Intel all active). We are aligned and sensibly scoped, but
the gap has **narrowed sharply**: mechanism papers are dead, naive characterization is table stakes,
and even the measurement pieces are individually adjacent to published work. What survives is the
*intersection* — open-infra quantification of the realized-vs-available locality gap under realistic
mixed traffic, as cost-per-verified-iteration, released with a public agentic trace + harness. The
window is closing; defensibility is the bundle + open reproducibility, not any single number.
