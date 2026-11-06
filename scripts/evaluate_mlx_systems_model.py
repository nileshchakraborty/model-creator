#!/usr/bin/env python3
"""
Strictly Blind LiveCodeBench Evaluation for Qwen 2.5 Coder 14B with Systems LoRA Adapter.

Runs unassisted inference on the 19 failure problems using MLX Metal GPU.
Evaluates using the official LiveCodeBench execution sandbox with ZERO hints or human assistance.

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
APEX_DIR = "/Users/nileshchakraborty/workspace/apex-code-36gb"

sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, LIVECODEBENCH_DIR)
sys.path.insert(0, APEX_DIR)

from lcb_runner.benchmarks.code_generation import load_code_generation_dataset
from lcb_runner.evaluation.compute_code_generation_metrics import codegen_metrics
from mlx_lm import load, generate

TARGET_19_IDS = [
    "1873_B", "1873_D", "1883_B", "1883_C", "1899_A", "1899_C",
    "2754", "2777", "2784", "2808", "2817", "2827",
    "2832", "2833", "2837", "2839", "2849", "2850", "2854"
]

SYSTEM_PROMPT = """You are an elite competitive programmer and systems architect.
Provide optimal, clean, bug-free Python 3 solutions adhering strictly to Big-O constraints.
Always wrap code inside ```python ... ``` blocks and read input via sys.stdin.read().split()."""

def extract_code(text: str) -> str:
    if "<think>" in text and "</think>" in text:
        text = text.split("</think>")[-1].strip()
    if "```python" in text:
        return text.split("```python")[1].split("```")[0].strip()
    elif "```" in text:
        return text.split("```")[1].split("```")[0].strip()
    return text.strip()

def main():
    parser = argparse.ArgumentParser(description="Evaluate Qwen Systems LoRA on LiveCodeBench 19 Failure Set")
    parser.add_argument("--model-path", default="mlx-community/Qwen2.5-Coder-14B-Instruct-4bit")
    parser.add_argument("--adapter-path", default=os.path.join(PROJECT_ROOT, "adapters/qwen_systems_lora"))
    parser.add_argument("--output-file", default=os.path.join(PROJECT_ROOT, "tests/qwen_systems_lora_blind_benchmark.json"))
    parser.add_argument("--cache-file", default=os.path.join(PROJECT_ROOT, "tests/cached_qwen_systems_generations.json"))
    args = parser.parse_args()

    print("=" * 80)
    print("🔬 STRICTLY BLIND EVALUATION: QWEN 2.5 CODER 14B (SYSTEMS ADAPTER)")
    print("=" * 80)
    print(f"Base Model:   {args.model_path}")
    print(f"Adapter Path: {args.adapter_path}")
    print(f"Target IDs:   {len(TARGET_19_IDS)} problems")
    
    # 1. Load LiveCodeBench Dataset
    dataset = load_code_generation_dataset()
    problem_map = {p.question_id: p for p in dataset}
    eval_problems = [problem_map[pid] for pid in TARGET_19_IDS if pid in problem_map]
    print(f"Loaded {len(eval_problems)} matching LiveCodeBench problems.")

    cached_generations = {}
    if os.path.exists(args.cache_file):
        try:
            with open(args.cache_file, "r") as f:
                cached_generations = json.load(f)
            print(f"Loaded {len(cached_generations)} cached generations from {args.cache_file}")
        except Exception:
            cached_generations = {}

    # 2. Load Model + Adapter if we need to generate anything
    needs_generation = any(prob.question_id not in cached_generations for prob in eval_problems)
    model = None
    tokenizer = None

    if needs_generation:
        print("\nLoading MLX model into Unified Memory...")
        t0 = time.time()
        model, tokenizer = load(args.model_path, adapter_path=args.adapter_path)
        print(f"Model and adapter loaded in {time.time() - t0:.2f}s.")

    # 3. Strictly Blind Generation
    results = {}
    samples_for_metrics = []

    for idx, prob in enumerate(eval_problems, 1):
        pid = prob.question_id
        diff = prob.difficulty.value if hasattr(prob.difficulty, "value") else str(prob.difficulty)
        print(f"\n[{idx}/{len(eval_problems)}] Problem {pid} ({diff}) - {prob.question_title[:40]}...", flush=True)

        if pid in cached_generations:
            code = cached_generations[pid]["extracted_code"]
            raw_response = cached_generations[pid]["raw_response"]
            gen_time = cached_generations[pid].get("generation_time_sec", 0.0)
            print(f"   Using cached solution ({len(code.split('\n'))} lines).", flush=True)
        else:
            if prob.starter_code and prob.starter_code.strip():
                prompt_text = f"PROBLEM SPECIFICATION:\n{prob.question_content}\n\nSTARTER CODE TEMPLATE:\n```python\n{prob.starter_code}\n```\nOutput ONLY the complete, correct Python 3 code inside a ```python ``` block."
            else:
                prompt_text = f"PROBLEM SPECIFICATION:\n{prob.question_content}\n\nCRITICAL INSTRUCTIONS FOR EXECUTION:\n1. Wrap the entire solution inside ```python ... ``` fences.\n2. Read all input from standard input using fast I/O:\n   import sys\n   input_data = sys.stdin.read().split()\n3. Print final results directly to standard output.\n4. Strictly adhere to optimal Big-O bounds.\n\nOutput ONLY the complete, correct Python 3 code inside a ```python ``` block."

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
                max_tokens=1536,
                verbose=False
            )
            gen_time = time.time() - t_gen_start
            code = extract_code(raw_response)
            code_lines = len(code.split('\n'))
            print(f"   Generated {code_lines} lines of code in {gen_time:.2f}s.", flush=True)

            cached_generations[pid] = {
                "question_id": pid,
                "title": prob.question_title,
                "difficulty": diff,
                "raw_response": raw_response,
                "extracted_code": code,
                "generation_time_sec": gen_time
            }
            # Save cache incrementally
            with open(args.cache_file, "w") as f:
                json.dump(cached_generations, f, indent=2)

        results[pid] = {
            "question_id": pid,
            "title": prob.question_title,
            "difficulty": diff,
            "raw_response": raw_response,
            "extracted_code": code,
            "generation_time_sec": gen_time
        }
        samples_for_metrics.append([code])

    # 4. Official Sandbox Execution & Metrics
    print("\n" + "=" * 80)
    print("⚡ EXECUTING CANDIDATES IN OFFICIAL LIVECODEBENCH SANDBOX...")
    print("=" * 80, flush=True)
    
    # CRITICAL: get_evaluation_sample() converts the problem into the dictionary format expected by the sandbox
    evaluation_samples = [p.get_evaluation_sample() for p in eval_problems]

    eval_t0 = time.time()
    metrics, graded, _ = codegen_metrics(
        evaluation_samples,
        samples_for_metrics,
        k_list=[1],
        num_process_evaluate=4,
        timeout=10
    )
    eval_duration = time.time() - eval_t0

    # 5. Collate Results
    passed_count = 0
    passed_ids = []
    failed_ids = []

    for idx, prob in enumerate(eval_problems):
        pid = prob.question_id
        res_list = graded.get(idx, [])
        all_passed = bool(res_list and all(x > 0 for x in res_list[0]) and len(res_list[0]) > 0) if res_list else False
        passed_cases = sum(1 for x in res_list[0] if x > 0) if res_list else 0
        total_cases = len(res_list[0]) if res_list else 0
        
        results[pid]["passed"] = all_passed
        results[pid]["passed_cases"] = passed_cases
        results[pid]["total_cases"] = total_cases
        
        status_str = "✅ PASS" if all_passed else "❌ FAIL"
        print(f"[{pid}] {prob.question_title[:30]}: {status_str} ({passed_cases}/{total_cases} tests passed)", flush=True)
        
        if all_passed:
            passed_count += 1
            passed_ids.append(pid)
        else:
            failed_ids.append(pid)

    pass_rate = (passed_count / len(eval_problems)) * 100.0
    print("\n" + "=" * 80)
    print(f"🏆 BENCHMARK RESULTS (AUTHENTIC BLIND EVALUATION)")
    print(f"Passed:    {passed_count} / {len(eval_problems)} ({pass_rate:.1f}%)")
    print(f"Pass IDs:  {passed_ids}")
    print(f"Fail IDs:  {failed_ids}")
    print("=" * 80, flush=True)

    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_path": args.model_path,
        "adapter_path": args.adapter_path,
        "total_problems": len(eval_problems),
        "passed_count": passed_count,
        "pass_rate_pct": pass_rate,
        "passed_ids": passed_ids,
        "failed_ids": failed_ids,
        "eval_duration_sec": eval_duration,
        "problems": results
    }

    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    with open(args.output_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Detailed benchmark report saved to: {args.output_file}", flush=True)

if __name__ == "__main__":
    main()
