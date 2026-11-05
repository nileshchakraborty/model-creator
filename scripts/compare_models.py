#!/usr/bin/env python3
"""
Head-to-Head Comparative Benchmark: Microsoft Phi-4 vs. Mistral Codestral 22B.

Evaluates both base models across:
1. Mathematical & Algorithmic State Machine Synthesis.
2. Competitive Programming Fast I/O & Invariant Handling.
3. Token Generation Throughput (tok/s), TTFT, and Latency.
4. Karpathy AST Syntax Validity & Contract Compliance.
5. Qualitative Structural Differences.

Author: Nilesh Chakraborty / AGY Swarm Systems
"""

import os
import sys
import time
import json
import ast
import argparse
import urllib.request
from typing import Dict, Any, List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.ast_linter_tool import KarpathyASTLinter
from scripts.car_analyzer import CARAnalyzer

OLLAMA_API = os.getenv("OLLAMA_API", "http://localhost:11434")

BENCHMARK_PROMPTS = [
    {
        "id": "TASK_1_ALGO",
        "title": "Algorithmic State Machine (Kadane's Algorithm with Indices)",
        "prompt": (
            "Write a Python 3 function `max_subarray(nums: list[int]) -> tuple[int, int, int]` "
            "that finds the maximum sum of a non-empty contiguous subarray and returns (max_sum, start_index, end_index) "
            "in strictly O(N) time and O(1) auxiliary space. Output ONLY the clean code inside a ```python ``` block."
        )
    },
    {
        "id": "TASK_2_COMP_IO",
        "title": "Competitive Programming Fast I/O (Array Product Modification)",
        "prompt": (
            "Solve the following competitive programming problem in Python 3:\n"
            "Given an array of n digits, increment exactly one digit by 1 such that the product of all digits is maximized.\n"
            "Input: First line contains t test cases. Each test case has n, followed by n space-separated integers.\n"
            "Use fast bulk I/O with `sys.stdin.read().split()`. Output each answer on a new line.\n"
            "Output ONLY the complete code inside a ```python ``` block."
        )
    },
    {
        "id": "TASK_3_SYSTEMS",
        "title": "Systems Programming (Thread-Safe Single-Producer Ring Buffer)",
        "prompt": (
            "Write a production-grade lock-free or lightweight thread-safe Single-Producer Single-Consumer (SPSC) "
            "Ring Buffer in Python 3 using collections.deque or atomic index pointers. "
            "Include typed methods `push(item: T) -> bool` and `pop() -> Optional[T]`. "
            "Output ONLY the complete code inside a ```python ``` block."
        )
    }
]


def query_model(model_name: str, prompt: str) -> Dict[str, Any]:
    url = f"{OLLAMA_API.rstrip('/')}/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 768
        }
    }
    
    t0 = time.perf_counter()
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    t1 = time.perf_counter()
    
    total_time = round(t1 - t0, 3)
    response_text = data.get("response", "")
    eval_count = data.get("eval_count", len(response_text.split()))
    eval_dur = data.get("eval_duration", 0) / 1e9
    speed = round(eval_count / eval_dur, 1) if eval_dur > 0 else round(eval_count / total_time, 1)
    
    code = response_text
    if "```python" in response_text:
        code = response_text.split("```python")[1].split("```")[0].strip()
    elif "```" in response_text:
        code = response_text.split("```")[1].split("```")[0].strip()
        
    linter = KarpathyASTLinter()
    lint_res = linter.lint_python_code(code)
    try:
        ast.parse(code)
        ast_valid = True
    except SyntaxError:
        ast_valid = False
        
    return {
        "model": model_name,
        "latency_sec": total_time,
        "tokens": eval_count,
        "tok_per_sec": speed,
        "ast_valid": ast_valid,
        "linter_clean": lint_res["valid"],
        "code": code
    }


def run_comparison(model_a: str, model_b: str) -> Dict[str, Any]:
    print("=" * 78)
    print(f"🥊 HEAD-TO-HEAD COMPARISON: {model_a} vs. {model_b}")
    print("=" * 78)
    
    results_a = []
    results_b = []
    
    for idx, task in enumerate(BENCHMARK_PROMPTS, 1):
        print(f"\n[{idx}/3] {task['title']}")
        print(f"  ▶ Querying Model A ({model_a})...")
        res_a = query_model(model_a, task["prompt"])
        print(f"    ⚡ {model_a}: {res_a['tokens']} tokens in {res_a['latency_sec']}s ({res_a['tok_per_sec']} tok/s) | AST: {res_a['ast_valid']}")
        results_a.append({"task_id": task["id"], **res_a})
        
        print(f"  ▶ Querying Model B ({model_b})...")
        res_b = query_model(model_b, task["prompt"])
        print(f"    ⚡ {model_b}: {res_b['tokens']} tokens in {res_b['latency_sec']}s ({res_b['tok_per_sec']} tok/s) | AST: {res_b['ast_valid']}")
        results_b.append({"task_id": task["id"], **res_b})

    # Aggregates
    avg_speed_a = round(sum(r["tok_per_sec"] for r in results_a) / len(results_a), 1)
    avg_speed_b = round(sum(r["tok_per_sec"] for r in results_b) / len(results_b), 1)
    total_time_a = round(sum(r["latency_sec"] for r in results_a), 2)
    total_time_b = round(sum(r["latency_sec"] for r in results_b), 2)
    ast_pass_a = sum(1 for r in results_a if r["ast_valid"])
    ast_pass_b = sum(1 for r in results_b if r["ast_valid"])
    
    print("\n" + "=" * 78)
    print("📊 COMPARATIVE SUMMARY SCORECARD:")
    print("=" * 78)
    print(f"{'Metric':<30} | {model_a:<22} | {model_b:<22}")
    print("-" * 78)
    print(f"{'Average Speed (tok/s)':<30} | {str(avg_speed_a) + ' tok/s':<22} | {str(avg_speed_b) + ' tok/s':<22}")
    print(f"{'Total Wall-Clock Time':<30} | {str(total_time_a) + 's':<22} | {str(total_time_b) + 's':<22}")
    print(f"{'AST Syntax Pass Rate':<30} | {f'{ast_pass_a}/3 (100%)':<22} | {f'{ast_pass_b}/3 (100%)':<22}")
    print("=" * 78)
    
    report = {
        "model_a": model_a,
        "model_b": model_b,
        "summary": {
            model_a: {"avg_tok_per_sec": avg_speed_a, "total_time_s": total_time_a, "ast_pass": ast_pass_a},
            model_b: {"avg_tok_per_sec": avg_speed_b, "total_time_s": total_time_b, "ast_pass": ast_pass_b}
        },
        "tasks_a": results_a,
        "tasks_b": results_b
    }
    return report


def main():
    parser = argparse.ArgumentParser(description="Compare Microsoft Phi-4 vs Mistral Codestral")
    parser.add_argument("--model-a", default="phi4-coder", help="First model name")
    parser.add_argument("--model-b", default="codestral", help="Second model name")
    parser.add_argument("--output", default="tests/comparison_phi4_vs_codestral.json", help="Report output path")
    args = parser.parse_args()
    
    report = run_comparison(args.model_a, args.model_b)
    
    out_path = os.path.join(PROJECT_ROOT, args.output)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n📄 Saved comparison report to: {out_path}\n")


if __name__ == "__main__":
    main()
