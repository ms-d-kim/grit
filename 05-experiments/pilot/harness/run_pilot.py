"""
run_pilot.py — orchestration skeleton for the pilot cell.

This is a SKELETON, not a finished harness. It defines the control flow and the seams
where each role's code plugs in. The serving-internal instrumentation is deliberately
left as an interface to co-design at the pilot-design review — do not unilaterally
implement it here.

Run flow:
    load scenarios -> build workload (tenancy) -> configure engine (cache policy)
    -> run + trace -> compute available reuse (offline) -> aggregate

Roles:
    [Vinita]  configure_engine(), the cache/eviction counters inside run_and_trace()
    [Minseok] load_scenarios(), build_workload(), compute_available_reuse(), aggregate()
"""

from __future__ import annotations
try:
    import yaml
except ModuleNotFoundError:
    raise SystemExit("run_pilot needs pyyaml — run: pip install -r requirements.txt")
from pathlib import Path
try:  # works as `python -m harness.run_pilot` (from pilot root)
    from harness.trace_schema import TaskRecord, ModelCallSpan, ToolCallSpan, Tenancy  # noqa
except ModuleNotFoundError:  # and as `python harness/run_pilot.py`
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from trace_schema import TaskRecord, ModelCallSpan, ToolCallSpan, Tenancy  # noqa


# ---------------------------------------------------------------------------
# [Minseok] workload + benchmark harness
# ---------------------------------------------------------------------------
def load_scenarios(benchmark: str, n: int) -> list[dict]:
    """Load n task instances from the public benchmark (tau2-bench / SWE-bench Verified).
    Returns scenario dicts the methodology runner can execute."""
    raise NotImplementedError("TODO[Minseok]: load tau2-bench / SWE-bench Verified subset")


def build_workload(agent_scenarios: list[dict], tenancy: str) -> list[dict]:
    """Interleave agent requests with a chat trace (Azure/BurstGPT) at the given ratio.
    'isolated' => agent only. 'mixed_0.50' => 50/50 by request count, arrival-time merged."""
    raise NotImplementedError("TODO[Minseok]: merge agent + chat arrival streams")


# ---------------------------------------------------------------------------
# [Vinita] serving engine configuration + internal instrumentation
# ---------------------------------------------------------------------------
def configure_engine(engine: str, cache_policy: str, bounded_cache_blocks: int):
    """Stand up vLLM/SGLang with the given prefix-cache/eviction policy and a *bounded*
    KV budget (so eviction actually bites). Return a handle that exposes per-call cache
    counters (hit tokens, blocks allocated/evicted, gpu_busy)."""
    raise NotImplementedError(
        "CO-DESIGN[Vinita]: engine handle + metrics endpoint wiring "
        "(prefix_cache_hit_tokens, kv_blocks_evicted, gpu_busy_ms)"
    )


def run_and_trace(engine_handle, workload: list[dict], serving_config_id: str
                  ) -> list[TaskRecord]:
    """Execute the workload, emitting ModelCallSpan/ToolCallSpan per the trace schema.
    The realized cache fields come from engine_handle's counters [Vinita]; the
    iteration/tenancy/success fields come from the harness [Minseok]."""
    raise NotImplementedError("TODO[shared]: run loop emitting trace_schema spans")


# ---------------------------------------------------------------------------
# [Minseok] offline analysis
# ---------------------------------------------------------------------------
def compute_available_reuse(records: list[TaskRecord]) -> list[TaskRecord]:
    """Replay each trajectory against an INFINITE cache (offline) to get the upper-bound
    reusable-token count, populating reusable_tokens_infinite_cache. The delta vs the
    realized hit rate is TaskRecord.locality_gap."""
    raise NotImplementedError("TODO[Minseok]: infinite-cache replay -> available reuse")


def aggregate(records: list[TaskRecord]) -> dict:
    """Roll up the headline quantities: mean locality_gap by tenancy x cache policy,
    cost_per_verified_iteration vs horizon, tool-gap distribution."""
    verified = [r for r in records if r.success]
    gaps = [r.locality_gap for r in records if r.locality_gap is not None]
    cpvi = [r.cost_per_verified_iteration for r in verified
            if r.cost_per_verified_iteration is not None]
    return {
        "n_tasks": len(records),
        "success_rate": (len(verified) / len(records)) if records else 0.0,
        "mean_locality_gap": (sum(gaps) / len(gaps)) if gaps else None,
        "mean_cost_per_verified_iteration": (sum(cpvi) / len(cpvi)) if cpvi else None,
    }


def _as_list(x):
    """matrix.yaml fields may be a scalar or a list; normalize to a list."""
    return x if isinstance(x, list) else [x]


def main(matrix_path: str = "experiments/matrix.yaml"):
    """NOTE: control-flow skeleton only. This now iterates ALL pilot axes
    (benchmark x tenancy x cache_policy x horizon x repeat) instead of the earlier
    tenancy x policy bug that (a) passed the benchmark *list* to load_scenarios and
    (b) silently dropped benchmark/horizon/repeats (pilot README issue #7). A real
    bounded-KV budget per issue #4 still must replace the -1 placeholder; the cell
    functions still raise NotImplementedError by design (co-design seams)."""
    cfg = yaml.safe_load(Path(matrix_path).read_text())
    p = cfg["pilot"]
    all_records: list[TaskRecord] = []
    for benchmark in _as_list(p["benchmark"]):
        scenarios = load_scenarios(benchmark, p["scenarios"])
        for tenancy in _as_list(p["tenancy"]):
            workload = build_workload(scenarios, tenancy)
            for policy in _as_list(p["cache_policy"]):
                for horizon in _as_list(p.get("horizon_max_iters", [16])):
                    for repeat in range(int(p.get("repeats", 1))):
                        cfg_id = f'{p["methodology"]}|{benchmark}|{tenancy}|{policy}|h{horizon}|r{repeat}'
                        engine = configure_engine(p["engine"], policy, bounded_cache_blocks=-1)  # issue #4
                        recs = run_and_trace(engine, workload, cfg_id)
                        all_records.extend(recs)
    all_records = compute_available_reuse(all_records)
    print(aggregate(all_records))


if __name__ == "__main__":
    main()
