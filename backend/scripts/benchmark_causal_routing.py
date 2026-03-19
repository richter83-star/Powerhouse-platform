"""
Causal Routing Benchmark: 50-task comparison.

Runs 50 tasks through NeuralAgentSelector with and without causal_context,
then compares which agent was selected each time to validate that high-confidence
causal recommendations meaningfully shift routing decisions.

Usage:
    cd backend && python scripts/benchmark_causal_routing.py

Output:
    - Per-task selection table
    - Aggregate routing-change rate
    - Domain-match accuracy (did the causal hint steer toward the right domain?)
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import json
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from core.learning.neural_agent_selector import NeuralAgentSelector
from core.reasoning.causal_agent_router import (
    CausalAgentRouter,
    CausalInterventionRecommendation,
    DOMAIN_KEYWORDS,
)

# ---------------------------------------------------------------------------
# Benchmark configuration
# ---------------------------------------------------------------------------

NUM_TASKS = 50
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# Simulated agents covering different domains
AGENT_POOL: Dict[str, Dict] = {
    "reasoning_agent":        {"success_rate": 0.78, "avg_latency_ms": 1100.0, "total_runs": 30},
    "analysis_agent":         {"success_rate": 0.82, "avg_latency_ms": 950.0,  "total_runs": 45},
    "generation_agent":       {"success_rate": 0.75, "avg_latency_ms": 800.0,  "total_runs": 60},
    "planning_orchestrator":  {"success_rate": 0.70, "avg_latency_ms": 1400.0, "total_runs": 20},
    "parameter_optimizer":    {"success_rate": 0.68, "avg_latency_ms": 700.0,  "total_runs": 15},
    "evaluator_agent":        {"success_rate": 0.80, "avg_latency_ms": 1050.0, "total_runs": 35},
}

# Task templates paired with a "ground truth" causal domain
TASK_TEMPLATES: List[Tuple[str, str]] = [
    ("Perform causal inference on the dataset",            "reasoning"),
    ("Generate a creative marketing copy",                  "generation"),
    ("Analyse user engagement metrics",                     "analysis"),
    ("Plan a 6-week product roadmap",                       "planning"),
    ("Tune the model temperature for better output",        "parameter_tuning"),
    ("Evaluate the quality of LLM responses",              "analysis"),
    ("Reason through this logical argument",               "reasoning"),
    ("Synthesise a summary of the research paper",         "generation"),
    ("Create a strategic deployment plan",                 "planning"),
    ("Calibrate the top_p parameter",                      "parameter_tuning"),
]

# Causal variables associated with each domain
DOMAIN_VARIABLES: Dict[str, str] = {
    "reasoning":       "logic_path",
    "generation":      "output_creativity",
    "analysis":        "data_quality",
    "planning":        "strategy_horizon",
    "parameter_tuning": "temperature",
}


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkTask:
    task_id: int
    task: str
    gt_domain: str
    causal_variable: str
    causal_confidence: float

    selected_baseline: Optional[str] = None     # Without causal context
    selected_causal: Optional[str] = None       # With causal context
    routing_changed: bool = False
    domain_matched_baseline: bool = False       # Baseline picked a domain-matching agent
    domain_matched_causal: bool = False         # Causal routing picked a domain-matching agent


def _domain_matches(agent_name: str, domain: str) -> bool:
    keywords = DOMAIN_KEYWORDS.get(domain, [])
    return any(kw in agent_name.lower() for kw in keywords)


def run_benchmark() -> List[BenchmarkTask]:
    selector = NeuralAgentSelector(num_agents=len(AGENT_POOL))
    router = CausalAgentRouter(causal_reasoner=None, agent_selector=selector)

    results: List[BenchmarkTask] = []

    for i in range(NUM_TASKS):
        template_idx = i % len(TASK_TEMPLATES)
        task_text, gt_domain = TASK_TEMPLATES[template_idx]
        # Vary task slightly so all 50 aren't identical
        task_text = f"[Task {i+1}] {task_text}"

        causal_var   = DOMAIN_VARIABLES[gt_domain]
        confidence   = round(random.uniform(0.75, 0.98), 2)  # always high-confidence

        bt = BenchmarkTask(
            task_id=i + 1,
            task=task_text,
            gt_domain=gt_domain,
            causal_variable=causal_var,
            causal_confidence=confidence,
        )

        # --- Baseline: no causal context ---
        baseline_scores = selector.predict_agent_scores(
            task=task_text,
            agent_histories=AGENT_POOL,
        )
        bt.selected_baseline = baseline_scores[0][0] if baseline_scores else None
        bt.domain_matched_baseline = _domain_matches(bt.selected_baseline or "", gt_domain)

        # --- Causal routing ---
        causal_rec = CausalInterventionRecommendation(
            variable=causal_var,
            intervention_value=1.0,
            predicted_effect=0.8,
            confidence=confidence,
            domain=gt_domain,
        )
        bt.selected_causal = router.select_agent(
            task=task_text,
            causal_context={causal_var: causal_rec},
            agent_histories=AGENT_POOL,
        )
        bt.domain_matched_causal = _domain_matches(bt.selected_causal or "", gt_domain)
        bt.routing_changed = bt.selected_baseline != bt.selected_causal

        results.append(bt)

    return results


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_report(results: List[BenchmarkTask]) -> None:
    RESET  = "\033[0m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"

    print(f"\n{BOLD}{'='*90}{RESET}")
    print(f"{BOLD}  Causal Routing Benchmark – {len(results)} tasks{RESET}")
    print(f"{BOLD}{'='*90}{RESET}")

    header = (
        f"{'#':>3}  {'Domain':<18} {'Baseline Agent':<26} {'Causal Agent':<26} "
        f"{'Changed':>8} {'Domain✓':>8}"
    )
    print(f"\n{CYAN}{header}{RESET}")
    print("-" * 90)

    for r in results:
        changed_flag = f"{GREEN}YES{RESET}" if r.routing_changed else "   "
        domain_flag  = (
            f"{GREEN}✓ causal{RESET}"
            if r.domain_matched_causal and not r.domain_matched_baseline
            else (f"{YELLOW}both{RESET}" if r.domain_matched_causal and r.domain_matched_baseline
                  else ("none"))
        )
        print(
            f"{r.task_id:>3}.  {r.gt_domain:<18} "
            f"{(r.selected_baseline or 'N/A'):<26} "
            f"{(r.selected_causal   or 'N/A'):<26} "
            f"{changed_flag:>8}  {domain_flag}"
        )

    # Aggregate stats
    total = len(results)
    changed       = sum(1 for r in results if r.routing_changed)
    dm_baseline   = sum(1 for r in results if r.domain_matched_baseline)
    dm_causal     = sum(1 for r in results if r.domain_matched_causal)
    causal_better = sum(
        1 for r in results
        if r.domain_matched_causal and not r.domain_matched_baseline
    )

    print(f"\n{BOLD}{'='*90}{RESET}")
    print(f"{BOLD}Aggregate Results{RESET}")
    print(f"  Tasks run                  : {total}")
    print(f"  Routing changed            : {changed:>3} / {total}  "
          f"({100*changed/total:.1f}%)")
    print(f"  Domain match – baseline    : {dm_baseline:>3} / {total}  "
          f"({100*dm_baseline/total:.1f}%)")
    print(f"  Domain match – causal      : {dm_causal:>3} / {total}  "
          f"({100*dm_causal/total:.1f}%)")
    print(f"  Causal improved matching   : {causal_better:>3} / {total}  "
          f"({100*causal_better/total:.1f}%)")
    print(f"{BOLD}{'='*90}{RESET}\n")

    # Write JSON results for CI consumption
    out_path = backend_dir / "benchmark_results.json"
    summary = {
        "num_tasks": total,
        "routing_changed": changed,
        "routing_changed_pct": round(100 * changed / total, 1),
        "domain_match_baseline": dm_baseline,
        "domain_match_causal": dm_causal,
        "domain_match_baseline_pct": round(100 * dm_baseline / total, 1),
        "domain_match_causal_pct": round(100 * dm_causal / total, 1),
        "causal_improved_matches": causal_better,
        "causal_improved_pct": round(100 * causal_better / total, 1),
        "tasks": [
            {
                "id": r.task_id,
                "domain": r.gt_domain,
                "confidence": r.causal_confidence,
                "baseline": r.selected_baseline,
                "causal": r.selected_causal,
                "routing_changed": r.routing_changed,
                "domain_matched_baseline": r.domain_matched_baseline,
                "domain_matched_causal": r.domain_matched_causal,
            }
            for r in results
        ],
    }
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Full results written to: {out_path}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Running causal routing benchmark …")
    results = run_benchmark()
    print_report(results)
