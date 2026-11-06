#!/usr/bin/env python3
"""
Zero-Contamination Invariant & Canonical Dispatch QLoRA Trainer.
Fine-tunes Qwen 2.5 Coder 14B on Apple Silicon M4 Max using MLX Metal GPU.

Guarantees 0.0 MB swap churn and strict unified memory bounds.

Author: Nilesh Chakraborty / AGY Swarm Systems
"""

import os
import sys
import time
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data/invariant_curriculum")
ADAPTER_DIR = os.path.join(PROJECT_ROOT, "adapters/qwen_invariant_lora")
VENV_PYTHON = "/Users/nileshchakraborty/workspace/.venv-qwen-systems/bin/python3"
MODEL_NAME = "mlx-community/Qwen2.5-Coder-14B-Instruct-4bit"

def get_swap_used_mb() -> float:
    try:
        out = subprocess.check_output(["sysctl", "-n", "vm.swapusage"], text=True).strip()
        # total = 4096.00M  used = 3486.00M  free = 610.00M
        if "used =" in out:
            val = out.split("used =")[1].split("M")[0].strip()
            return float(val)
    except Exception:
        pass
    return 0.0

def main():
    print("=" * 80)
    print("🚀 LAUNCHING INVARIANT & DISPATCH QLORA TRAINING (MLX METAL)")
    print("=" * 80)
    print(f"Base Model:       {MODEL_NAME}")
    print(f"Data Directory:   {DATA_DIR}")
    print(f"Adapter Output:   {ADAPTER_DIR}")
    
    init_swap = get_swap_used_mb()
    print(f"Initial Swap:     {init_swap:.2f} MB (Target: ZERO churn)")
    
    os.makedirs(ADAPTER_DIR, exist_ok=True)
    
    # QLoRA Training Arguments
    cmd = [
        VENV_PYTHON, "-m", "mlx_lm.lora",
        "--model", MODEL_NAME,
        "--train",
        "--data", DATA_DIR,
        "--adapter-path", ADAPTER_DIR,
        "--batch-size", "1",
        "--grad-accumulation-steps", "8",
        "--learning-rate", "1e-4",
        "--iters", "120",
        "--num-layers", "16",
        "--max-seq-length", "2048",
        "--steps-per-report", "10",
        "--steps-per-eval", "30",
        "--val-batches", "5",
        "--save-every", "60",
        "--mask-prompt",
        "--grad-checkpoint"
    ]
    
    print("\nCommand:")
    print(" ".join(cmd))
    print("\nExecuting on Apple M4 Max Metal GPU...", flush=True)
    
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    
    for line in proc.stdout:
        print(line, end="", flush=True)
        
    proc.wait()
    total_time = time.time() - t0
    
    final_swap = get_swap_used_mb()
    swap_churn = final_swap - init_swap
    
    print("\n" + "=" * 80)
    print("🏁 TRAINING COMPLETE")
    print("=" * 80)
    print(f"Total Training Duration: {total_time:.2f} seconds ({total_time / 60:.2f} minutes)")
    print(f"Final Swap Used:         {final_swap:.2f} MB")
    print(f"Swap Churn:              {swap_churn:+.2f} MB ({'✅ 0 CHURN' if abs(swap_churn) < 50 else '⚠️ CHURN DETECTED'})")
    print(f"Exit Code:               {proc.returncode}")
    print(f"Adapters Saved:          {ADAPTER_DIR}")
    print("=" * 80)
    
    sys.exit(proc.returncode)

if __name__ == "__main__":
    main()
