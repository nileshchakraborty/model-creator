#!/usr/bin/env python3
"""
Model Weight Fusion Runner: Qwen 2.5 Coder 14B + CID Adapter.

Fuses trained Compact Invariant Distillation (CID) LoRA weights into the base
quantized model on Apple Silicon M4 Max using MLX.
Produces a self-contained, standalone model ready for zero-overhead deployment.

Author: Nilesh Chakraborty / AGY Swarm Systems
"""

import os
import sys
import time
import subprocess
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_MODEL = "mlx-community/Qwen2.5-Coder-14B-Instruct-4bit"
ADAPTER_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJECT_ROOT, "adapters/qwen_cid_v2_lora")
SAVE_PATH = os.path.join(PROJECT_ROOT, "models/qwen2.5_coder_14b_cid_fused")
VENV_PYTHON = "/Users/nileshchakraborty/workspace/.venv-qwen-systems/bin/python3"

def get_swap_used_mb() -> float:
    try:
        out = subprocess.check_output(["sysctl", "-n", "vm.swapusage"], text=True).strip()
        if "used =" in out:
            val = out.split("used =")[1].split("M")[0].strip()
            return float(val)
    except Exception:
        pass
    return 0.0

def main():
    print("=" * 80)
    print("🔧 FUSING CID LORA ADAPTER INTO BASE QUANTIZED WEIGHTS")
    print("=" * 80)
    print(f"Base Model:     {BASE_MODEL}")
    print(f"Adapter Path:   {ADAPTER_PATH}")
    print(f"Fused Output:   {SAVE_PATH}")
    
    init_swap = get_swap_used_mb()
    print(f"Pre-flight Swap: {init_swap:.2f} MB")
    
    os.makedirs(SAVE_PATH, exist_ok=True)
    
    cmd = [
        VENV_PYTHON, "-m", "mlx_lm.fuse",
        "--model", BASE_MODEL,
        "--adapter-path", ADAPTER_PATH,
        "--save-path", SAVE_PATH
    ]
    
    print("\nExecuting MLX weight fusion on Apple Silicon Metal GPU...")
    print(" ".join(cmd), flush=True)
    
    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    total_time = time.time() - t0
    
    print("\nCommand stdout:")
    print(proc.stdout)
    if proc.stderr:
        print("\nCommand stderr:")
        print(proc.stderr)
        
    if proc.returncode != 0:
        print(f"❌ Fusion failed with return code {proc.returncode}")
        sys.exit(proc.returncode)
        
    final_swap = get_swap_used_mb()
    swap_churn = final_swap - init_swap
    
    print("=" * 80)
    print("✅ FUSION COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print(f"Fusion Duration: {total_time:.2f} seconds")
    print(f"Final Swap Used: {final_swap:.2f} MB")
    print(f"Swap Churn:      {swap_churn:+.2f} MB ({'✅ 0 CHURN' if abs(swap_churn) < 50 else '⚠️ CHURN DETECTED'})")
    print(f"Fused Model:     {SAVE_PATH}")
    
    # Verify fused model by loading and generating 1 test sequence
    print("\n🔬 Verifying fused standalone model in Unified Memory...")
    from mlx_lm import load, generate
    t_load = time.time()
    model, tokenizer = load(SAVE_PATH)
    print(f"Standalone fused model loaded in {time.time() - t_load:.2f}s.")
    
    test_prompt = "def xor_sum(arr: list[int]) -> int:\n"
    t_gen = time.time()
    response = generate(model, tokenizer, prompt=test_prompt, max_tokens=25, verbose=False)
    print(f"Test generation completed in {time.time() - t_gen:.2f}s.")
    print(f"Output snippet:\n{response}")
    print("=" * 80)

if __name__ == "__main__":
    main()
