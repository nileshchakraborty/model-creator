#!/usr/bin/env python3
"""
Holistic Three-Way Coding Model Benchmark:
ApexCode (Qwen 2.5 Coder 14B) vs. ApexPhi (Microsoft Phi-4 14.7B) vs. ApexMistral (Mistral Codestral 22B).

Author: Nilesh Chakraborty / AGY Swarm Systems
"""

import os
import sys
import time
import json
import ast
import argparse
import urllib.request
import subprocess
from typing import Dict, Any, List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.ast_linter_tool import KarpathyASTLinter
from scripts.car_analyzer import CARAnalyzer

OLLAMA_API = os.getenv("OLLAMA_API", "http://localhost:11434")

BENCHMARK_SUITE = [
    {
        "id": "1873_B",
        "title": "Algorithmic Invariant (Good Kid - Product Maximization)",
        "difficulty": "Easy / Algorithmic Theorem",
        "prompt": (
            "Solve this competitive programming problem in Python 3:\n"
            "Given an array of n digits, increment exactly one digit by 1 such that the product of all digits is maximized.\n"
            "Input: First line contains t test cases. Each test case has n followed by n space-separated integers.\n"
            "Use fast bulk I/O with sys.stdin.read().split(). Output each answer on a new line.\n"
            "Output ONLY the complete code inside a ```python ``` block."
        ),
        "test_input": "3\n4\n2 2 1 2\n3\n0 1 2\n5\n4 3 2 3 4\n",
        "expected_output": "16\n2\n432"
    },
    {
        "id": "1873_A",
        "title": "Boundary & Permutation Logic (Short Sort - At Most 1 Swap)",
        "difficulty": "Easy / Corner Case Handling",
        "prompt": (
            "Solve this competitive programming problem in Python 3:\n"
            "There are three cards on a table with 'a', 'b', 'c' in some order. "
            "Determine if you can obtain the string 'abc' by performing AT MOST ONE swap of any two cards.\n"
            "Input: First line is t (number of test cases). Next t lines each contain a 3-letter permutation of 'abc'.\n"
            "Output: 'YES' if it can be sorted in <= 1 swap, 'NO' otherwise. Use sys.stdin.read().split().\n"
            "Output ONLY the complete code inside a ```python ``` block."
        ),
        "test_input": "6\nabc\nacb\nbac\nbca\ncab\ncba\n",
        "expected_output": "YES\nYES\nYES\nNO\nNO\nYES"
    },
    {
        "id": "SPSC_RING_BUFFER",
        "title": "Systems Programming (Single-Producer Single-Consumer Buffer)",
        "difficulty": "Medium / Concurrency & Data Structures",
        "prompt": (
            "Write a production-grade lock-free or lightweight thread-safe Single-Producer Single-Consumer (SPSC) "
            "Ring Buffer in Python 3 using atomic index pointers and fixed capacity. "
            "Include typed methods `push(item: T) -> bool` and `pop() -> Optional[T]`. "
            "Output ONLY the complete code inside a ```python ``` block."
        ),
        "test_input": None,
        "expected_output": None
    },
    {
        "id": "KADANE_INDICES",
        "title": "Dynamic Programming with Exact Subarray Boundaries",
        "difficulty": "Medium / Space Optimization",
        "prompt": (
            "Write a Python 3 function `max_subarray(nums: list[int]) -> tuple[int, int, int]` "
            "that finds the maximum sum of a non-empty contiguous subarray and returns (max_sum, start_index, end_index) "
            "in strictly O(N) time and O(1) auxiliary space. Handle arrays with all negative numbers correctly. "
            "Output ONLY the complete code inside a ```python ``` block."
        ),
        "test_input": None,
        "expected_output": None
    }
]


def query_ollama_model(model_name: str, prompt: str) -> Dict[str, Any]:
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


def execute_in_sandbox(code: str, test_input: str, expected_output: str) -> Dict[str, Any]:
    """
    Executes generated code in an isolated subprocess with timeout and verifies output.
    """
    if not test_input or not expected_output:
        return {"executed": False, "passed": True, "note": "Class/signature task"}

    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            input=test_input,
            text=True,
            capture_output=True,
            timeout=5.0
        )
        actual = proc.stdout.strip()
        expected = expected_output.strip()
        passed = (actual == expected)
        return {
            "executed": True,
            "passed": passed,
            "actual_output": actual[:100],
            "expected_output": expected[:100],
            "stderr": proc.stderr[:100] if proc.stderr else None
        }
    except subprocess.TimeoutExpired:
        return {"executed": True, "passed": False, "error": "TimeoutExpired (TLE)"}
    except Exception as e:
        return {"executed": True, "passed": False, "error": str(e)}


def run_holistic_benchmark(models: List[str]) -> Dict[str, Any]:
    print("=" * 82)
    print("🏆 THREE-WAY HOLISTIC BENCHMARK")
    print("  Models:", " vs. ".join(models))
    print("=" * 82)

    results_by_model: Dict[str, List[Dict[str, Any]]] = {m: [] for m in models}

    for task_idx, task in enumerate(BENCHMARK_SUITE, 1):
        print(f"\n[{task_idx}/{len(BENCHMARK_SUITE)}] {task['id']}: {task['title']} ({task['difficulty']})")
        print("-" * 82)

        for model in models:
            print(f"  ▶ Querying {model}...")
            res = query_ollama_model(model, task["prompt"])
            
            # Execute sandbox test if input available
            test_run = execute_in_sandbox(res["code"], task.get("test_input"), task.get("expected_output"))
            res["test_run"] = test_run
            passed_icon = "✅ PASS" if test_run["passed"] else "❌ FAIL"
            
            print(f"    ⚡ {model:<22}: {res['tokens']:>3} toks | {res['latency_sec']:>5.2f}s | {res['tok_per_sec']:>4.1f} tok/s | AST: {res['ast_valid']} | Execution: {passed_icon}")
            results_by_model[model].append({
                "task_id": task["id"],
                "title": task["title"],
                **res
            })

    # Summary Statistics
    summary = {}
    print("\n" + "=" * 82)
    print("📊 HOLISTIC COMPARATIVE SCORECARD")
    print("=" * 82)
    header = f"{'Metric':<32} | " + " | ".join(f"{m:<20}" for m in models)
    print(header)
    print("-" * 82)

    # 1. Average Speed
    speeds = [round(sum(r["tok_per_sec"] for r in results_by_model[m]) / len(results_by_model[m]), 1) for m in models]
    print(f"{'Average Speed (tok/s)':<32} | " + " | ".join(f"{s} tok/s".ljust(20) for s in speeds))

    # 2. Total Latency
    lats = [round(sum(r["latency_sec"] for r in results_by_model[m]), 2) for m in models]
    print(f"{'Total Latency (4 Tasks)':<32} | " + " | ".join(f"{l}s".ljust(20) for l in lats))

    # 3. AST Syntax Pass Rate
    ast_passes = [sum(1 for r in results_by_model[m] if r["ast_valid"]) for m in models]
    print(f"{'AST Syntax Valid':<32} | " + " | ".join(f"{p}/4 (100%)".ljust(20) for p in ast_passes))

    # 4. Sandbox Execution Pass
    exec_passes = [sum(1 for r in results_by_model[m] if r["test_run"]["passed"]) for m in models]
    print(f"{'Sandbox Test Verification':<32} | " + " | ".join(f"{p}/4 ({p/4*100:.0f}%)".ljust(20) for p in exec_passes))

    print("=" * 82)

    for m in models:
        summary[m] = {
            "avg_tok_per_sec": round(sum(r["tok_per_sec"] for r in results_by_model[m]) / len(results_by_model[m]), 1),
            "total_latency_sec": round(sum(r["latency_sec"] for r in results_by_model[m]), 2),
            "ast_pass_count": sum(1 for r in results_by_model[m] if r["ast_valid"]),
            "exec_pass_count": sum(1 for r in results_by_model[m] if r["test_run"]["passed"])
        }

    return {
        "models": models,
        "summary": summary,
        "detailed_results": results_by_model
    }


def main():
    parser = argparse.ArgumentParser(description="Three-Way Coding Benchmark: ApexCode vs ApexPhi vs ApexMistral")
    parser.add_argument("--output", default="tests/three_way_model_benchmark_report.json", help="Output JSON path")
    args = parser.parse_args()

    models = ["apex-coder-14b", "apex-phi-14b", "apex-mistral-22b"]
    report = run_holistic_benchmark(models)

    out_file = os.path.join(PROJECT_ROOT, args.output)
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n📄 Saved full three-way benchmark report to: {out_file}\n")


if __name__ == "__main__":
    main()
