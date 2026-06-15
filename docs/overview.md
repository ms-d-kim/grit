# GRIT — project overview (reference blurb)

*A self-contained one-pager: what this is, the landscape, the gap, the problem, the approach, and the
limits. For quick reference / pasting into a talk or an intro email.*

## What this project is
**GRIT** (*GPU Reuse under Interleaved Traffic*) is a **measurement-and-characterization study** of how
*agentic* LLM workloads stress an inference server —
and what that costs per unit of useful work. Not a new system, scheduler, or kernel: a rigorous,
reproducible **measurement** built only on **public benchmarks** (SWE-bench Verified, τ²-bench) and
**open infrastructure** (vLLM / SGLang). Target venue: MLSys 2027 Industry Track (stretch) / NeurIPS
Datasets & Benchmarks (floor); status: pre-pilot (design under review).

## The research landscape (what everyone is doing, mid-2026)
- **Workload characterization:** agents are decode-dominated with very high *potential* KV-cache reuse
  (Agentic AI Workload Characteristics), yet realized hit rates *collapse* in practice (Sutradhara) —
  and prior work disagrees on why. KVCache-in-the-Wild measures the realized-vs-ideal gap, but on a
  *closed* stack.
- **Mechanisms (very crowded):** dozens of systems make the cache/scheduler agent-aware — Continuum/
  CacheTTL, KVFlow, Helium, Autellix, HexAGenT, Cortex, ThunderAgent, SAGA, NVIDIA Dynamo's KV-aware
  router + agent hints, plus a 2026 wave (TokenCake, PPD, PBKV, …).
- **Cost / economics:** "Cost-of-Pass" (expected \$ per correct solution) is becoming the standard unit;
  energy is measured as Joules-per-token (TokenPowerBench).
- **Benchmarks & traces:** SWE-bench {Verified, Pro, Live}, τ²-bench, GAIA, HAL (cost-aware); a public
  *agent-only* trace corpus now exists (vLLM × Mooncake) but is not cost-labeled or mixed.

## What's missing — the opportunity
The literature splits into three disconnected camps: **serving** (optimizes throughput/goodput),
**capability** (cost-per-correct-task at the API black box), and **sustainability** (energy/token).
**Nobody ties cost-per-completed-task to serving-internal cache behavior, on open infrastructure, under
realistic mixed (chat + agent) traffic.** That intersection is empty — and it's where a serving team or
an agent builder would actually act.

## The exact problem we solve
Under realistic *mixed* traffic on a *bounded* cache:
1. how far does an agent's **realized** cache reuse fall below its **available** reuse (the **locality gap**)?
2. how much of that drop is caused by **multi-tenant interleaving** vs. the agent's own context churn?
3. what does the gap cost **per verified task the agent completes** (the **"Cost of Grit"** / locality tax)?

The mechanistic root is the **orchestrator↔engine seam**: the engine is *workflow-agnostic* — blind to
the agent loop, the coming tool pause, and cross-request prefix sharing — so the 2026 frontier is split
between *declaring* that contract via hints (Dynamo, KVFlow, …) and *inferring* it engine-side
(Continuum, GoodServe). We measure the **value of that awareness** rather than build another mechanism.

## How we solve it
Hold the model fixed; vary only serving knobs (horizon × cache policy × tenancy × KV budget) on vLLM and
SGLang; run an agent (ReAct) on the two benchmarks, alone and mixed with a chat trace. Recover **available
reuse** offline (infinite-cache replay of the recorded token stream) and **realized reuse** from engine
counters → the locality gap; account cost across all attempts (GPU-seconds / \$ / Joules) → the
cost-per-verified-task curve. Release the **mixed, cost-labeled, OpenTelemetry-format trace + harness**
(C3) — no such public artifact exists. The headline number is the **locality-tax fraction** (the share
of cost-per-task attributable to eviction), anchored on Cost-of-Pass and framed as the cost-side dual of
goodput.

## Limitations (honest)
- **Pre-data:** the harness is a scaffold; ~22 design issues gate spending GPU budget (metric definition,
  per-request cache attribution feasibility, the SWE-bench resolve-rate floor, etc.).
- **Regime-dependent:** the seam bites hardest under bounded cache + interleaving + long horizon; if good
  routing or cheap inference (TTL) recovers most reuse, the measured value of awareness is small (still a
  publishable result).
- **Narrow first cut:** one model family, one GPU class, two benchmarks → the curve is a point in a large
  space; cross-model/hardware generalization is V2.
- **Adjacency:** each individual measurement is close to published work (KVCache-in-the-Wild, SAGA,
  Cost-of-Pass); defensibility is the *bundle* (open infra + mixed traffic + interleaving isolated +
  cost-per-verified-task + the released trace), not any single number.
