#!/usr/bin/env python3
"""
Strictly Blind LiveCodeBench Evaluation for Qwen 2.5 Coder 14B with CID Adapter.

Evaluates the targeted 25 problems using MLX Metal GPU in a single blind forward pass.
Zero test-time execution, zero test feedback, strict sandbox integrity.
Grades generated code against the hidden LiveCodeBench test suite.

Author: Nilesh Chakraborty / AGY Swarm Systems
"""

import os
import sys
import time
import json
import argparse
from typing import Dict, Any, List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVECODEBENCH_DIR = "/Users/nileshchakraborty/workspace/LiveCodeBench"

sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, LIVECODEBENCH_DIR)

from lcb_runner.benchmarks.code_generation import load_code_generation_dataset
from lcb_runner.evaluation.compute_code_generation_metrics import codegen_metrics
from mlx_lm import load, generate

TARGET_25_IDS = [
    "1873_A", "1873_B", "1883_B", "1883_C", "1899_A", "1899_C", "1899_D",
    "2730", "2754", "2756", "2757", "2785", "2792",
    "2810", "2811", "2817", "2819", "2824", "2827", "2828",
    "2832", "2833", "2834", "2839", "2849"
]

SYSTEM_PROMPT = """You are an elite competitive programmer and algorithmic reasoning specialist.
Provide optimal, clean, bug-free Python 3 solutions adhering strictly to Big-O constraints.
First emit a brief, dense mathematical invariant analysis inside <think> ... </think> (at most 2 sentences).
Then emit the complete, optimal Python 3 code inside a ```python ... ``` block.
For LeetCode problems, use class Solution. For competitive problems, read from sys.stdin.read().split()."""

def extract_code(text: str) -> str:
    if "<think>" in text and "</think>" in text:
        text = text.split("</think>")[-1].strip()
    if "```python" in text:
        return text.split("```python")[1].split("```")[0].strip()
    elif "```" in text:
        return text.split("```")[1].split("```")[0].strip()
    return text.strip()

def main():
    parser = argparse.ArgumentParser(description="Evaluate CID LoRA on LiveCodeBench 25 Problems")
    parser.add_argument("--model-path", default="mlx-community/Qwen2.5-Coder-14B-Instruct-4bit")
    parser.add_argument("--adapter-path", default=os.path.join(PROJECT_ROOT, "adapters/qwen_cid_v2_lora"))
    parser.add_argument("--output-file", default=os.path.join(PROJECT_ROOT, "tests/lcb_benchmark_cid_v2_25p.json"))
    parser.add_argument("--cache-file", default=os.path.join(PROJECT_ROOT, "tests/cached_cid_v2_generations.json"))
    args = parser.parse_args()

    print("=" * 80)
    print("🔬 STRICTLY BLIND EVALUATION: QWEN 2.5 CODER 14B (CID ADAPTER)")
    print("=" * 80)
    print(f"Base Model:   {args.model_path}")
    print(f"Adapter Path: {args.adapter_path}")
    print(f"Target Count: {len(TARGET_25_IDS)} failure set problems")
    print(f"Output File:  {args.output_file}")
    
    # 1. Load LiveCodeBench Dataset
    dataset = load_code_generation_dataset()
    problem_map = {p.question_id: p for p in dataset}
    eval_problems = [problem_map[pid] for pid in TARGET_25_IDS if pid in problem_map]
    print(f"Loaded {len(eval_problems)} matching LiveCodeBench problems.")

    cached_generations = {}
    if os.path.exists(args.cache_file):
        try:
            with open(args.cache_file, "r") as f:
                cached_generations = json.load(f)
            print(f"Loaded {len(cached_generations)} cached generations from {args.cache_file}")
        except Exception:
            cached_generations = {}

    needs_generation = any(prob.question_id not in cached_generations for prob in eval_problems)
    model = None
    tokenizer = None

    if needs_generation:
        print("\nLoading MLX model and CID LoRA adapter into Unified Memory...")
        t0 = time.time()
        adapter_to_load = args.adapter_path if args.adapter_path and os.path.exists(args.adapter_path) else None
        model, tokenizer = load(args.model_path, adapter_path=adapter_to_load)
        print(f"Model and adapter loaded in {time.time() - t0:.2f}s.")

    # 3. Strictly Blind Single-Pass Forward Generation
    results = dict(cached_generations)
    samples_for_metrics = []

    print("\nStarting blind generation (zero execution, zero test feedback)...")
    for idx, prob in enumerate(eval_problems, 1):
        pid = prob.question_id
        diff = prob.difficulty.value if hasattr(prob.difficulty, "value") else str(prob.difficulty)
        print(f"\n[{idx}/{len(eval_problems)}] Problem {pid} ({diff}) - {prob.question_title[:40]}...", flush=True)

        if pid in results:
            code = results[pid]["extracted_code"]
            gen_time = results[pid].get("generation_time_sec", 0.0)
            print(f"   Using cached solution ({len(code.splitlines())} lines, {gen_time:.2f}s).", flush=True)
        else:
            if prob.starter_code and prob.starter_code.strip():
                prompt_text = (
                    f"PROBLEM SPECIFICATION:\n{prob.question_content}\n\n"
                    f"STARTER CODE TEMPLATE:\n```python\n{prob.starter_code}\n```\n"
                    f"Output a brief <think> ... </think> invariant (at most 2 sentences), then complete Python code inside ```python ```."
                )
            else:
                prompt_text = (
                    f"PROBLEM SPECIFICATION:\n{prob.question_content}\n\n"
                    f"CRITICAL INSTRUCTIONS FOR EXECUTION:\n"
                    f"1. Read all input from standard input using fast I/O: import sys; input_data = sys.stdin.read().split()\n"
                    f"2. Print final results directly to standard output.\n"
                    f"3. Strictly adhere to optimal Big-O bounds.\n"
                    f"4. Do NOT use class Solution for this problem.\n\n"
                    f"Output a brief <think> ... </think> invariant (at most 2 sentences), then complete Python code inside ```python ```."
                )

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt_text}
            ]
            
            formatted_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            
            t_gen_start = time.time()
            raw_response = generate(
                model,
                tokenizer,
                prompt=formatted_prompt,
                max_tokens=2048,
                verbose=False
            )
            gen_time = time.time() - t_gen_start
            code = extract_code(raw_response)
            
            print(f"   Generated {len(code.splitlines())} lines in {gen_time:.2f}s.")
            results[pid] = {
                "question_id": pid,
                "question_title": prob.question_title,
                "difficulty": diff,
                "raw_response": raw_response,
                "extracted_code": code,
                "generation_time_sec": gen_time
            }
            with open(args.cache_file, "w") as f:
                json.dump(results, f, indent=2)

        samples_for_metrics.append([results[pid]["extracted_code"]])

    # 4. Strictly Isolated Hidden Sandbox Grading
    print("\n" + "=" * 80)
    print("🧪 EXECUTING LIVECODEBENCH HIDDEN TEST SANDBOX GRADING")
    print("=" * 80)
    
    eval_samples = [prob.get_evaluation_sample() for prob in eval_problems]
    t_eval_start = time.time()
    metrics, graded_results, _ = codegen_metrics(
        eval_samples,
        samples_for_metrics,
        k_list=[1],
        num_process_evaluate=4,
        timeout=12
    )
    eval_duration = time.time() - t_eval_start
    print(f"Grading completed in {eval_duration:.2f}s.")

    # 5. Compile Scorecard
    detailed_problems = []
    passed_count = 0

    print("\n" + "=" * 80)
    print(f"{'ID':<8} {'Title':<30} {'Diff':<8} {'Status':<8} {'Cases'}")
    print("-" * 80)

    for idx, prob in enumerate(eval_problems):
        pid = prob.question_id
        diff = prob.difficulty.value if hasattr(prob.difficulty, "value") else str(prob.difficulty)
        res_list = graded_results.get(idx, [])
        all_passed = bool(res_list and all(x > 0 for x in res_list[0]) and len(res_list[0]) > 0) if res_list else False
        passed_cases = sum(1 for x in res_list[0] if x > 0) if res_list else 0
        total_cases = len(res_list[0]) if res_list else 0

        if all_passed:
            passed_count += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"

        print(f"{pid:<8} {prob.question_title[:28]:<30} {diff:<8} {status:<8} {passed_cases}/{total_cases}")

        detailed_problems.append({
            "question_id": pid,
            "question_title": prob.question_title,
            "difficulty": diff,
            "passed": all_passed,
            "passed_cases": passed_cases,
            "total_cases": total_cases,
            "latency_sec": results[pid]["generation_time_sec"],
            "code": results[pid]["extracted_code"]
        })

    pass_at_1 = float(metrics.get("pass@1", 0.0))
    print("=" * 80)
    print(f"🏆 FINAL VERIFIED CID SCORE: {passed_count}/{len(eval_problems)} ({pass_at_1 * 100:.1f}%)")
    print("=" * 80)

    benchmark_record = {
        "benchmark": "LiveCodeBench (Strictly Blind CID LoRA)",
        "model": args.model_path,
        "adapter": args.adapter_path,
        "problem_count": len(eval_problems),
        "overall_pass_at_1": pass_at_1,
        "passed_count": passed_count,
        "metrics": metrics,
        "problems": detailed_problems
    }
    
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    with open(args.output_file, "w") as f:
        json.dump(benchmark_record, f, indent=2)
    print(f"\nSaved verified CID benchmark record to {args.output_file}")

if __name__ == "__main__":
    main()
