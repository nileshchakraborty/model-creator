#!/usr/bin/env python3
"""
Phase 2 Targeted Alignment Training Runner for Qwen 2.5 Coder 14B.

Resumes from Phase 1 Systems LoRA adapter and fine-tunes on targeted gap remediations:
- Binary search on monotonic stacks (fixing 2839)
- Exact modulo 3 parity game theoretical invariants (fixing 1899_A)
- Exact string pair combinatorics (fixing 2850)
- Palindrome with k deletions (fixing 1883_B)
- Composite divisibility for k=4 (fixing 1883_C)
- Alternating parity Kadane (fixing 1899_C)

Author: Nilesh Chakraborty / AGY Swarm Systems
"""

import os
import sys
import time
import subprocess

def get_macos_memory_info():
    try:
        memsize_out = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True).strip()
        total_ram_gb = int(memsize_out) / (1024**3)
        vm_stat = subprocess.check_output(["vm_stat"], text=True)
        stats = {}
        for line in vm_stat.split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                v = v.strip().rstrip('.')
                if v.isdigit():
                    stats[k.strip()] = int(v)
        page_size = 16384
        free_pages = stats.get("Pages free", 0) + stats.get("Pages speculative", 0)
        avail_ram_gb = (free_pages * page_size) / (1024**3)
        swap_out = subprocess.check_output(["sysctl", "-n", "vm.swapusage"], text=True).strip()
        used_mb = 0.0
        if "used =" in swap_out:
            part = swap_out.split("used =")[1].split("M")[0].strip()
            used_mb = float(part)
        swap_used_gb = used_mb / 1024.0
        return {"ram_total_gb": total_ram_gb, "ram_avail_gb": avail_ram_gb, "swap_used_gb": swap_used_gb}
    except Exception:
        return {"ram_total_gb": 36.0, "ram_avail_gb": 20.0, "swap_used_gb": 0.0}

def main():
    print("=" * 80)
    print("🚀 LAUNCHING PHASE 2 TARGETED ALIGNMENT TRAINING (MLX METAL GPU)")
    print("=" * 80)
    
    init_mem = get_macos_memory_info()
    print(f"Pre-flight RAM Available: {init_mem['ram_avail_gb']:.2f} GB / {init_mem['ram_total_gb']:.2f} GB")
    print(f"Pre-flight Swap Used:     {init_mem['swap_used_gb']:.2f} GB")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data/systems_phase2")
    base_adapter = os.path.join(project_root, "adapters/qwen_systems_lora/adapters.safetensors")
    target_adapter_dir = os.path.join(project_root, "adapters/qwen_systems_phase2")
    os.makedirs(target_adapter_dir, exist_ok=True)
    
    python_bin = "/Users/nileshchakraborty/workspace/.venv-qwen-systems/bin/python3"
    model_name = "mlx-community/Qwen2.5-Coder-14B-Instruct-4bit"
    
    iters = 40
    batch_size = 1
    grad_accum = 4
    learning_rate = "5e-5"
    num_layers = 16
    max_seq_len = 2048
    steps_per_report = 5
    steps_per_eval = 20
    save_every = 20
    
    cmd = [
        python_bin, "-m", "mlx_lm.lora",
        "--model", model_name,
        "--train",
        "--data", data_dir,
        "--resume-adapter-file", base_adapter,
        "--adapter-path", target_adapter_dir,
        "--batch-size", str(batch_size),
        "--grad-accumulation-steps", str(grad_accum),
        "--learning-rate", learning_rate,
        "--iters", str(iters),
        "--num-layers", str(num_layers),
        "--max-seq-length", str(max_seq_len),
        "--steps-per-report", str(steps_per_report),
        "--steps-per-eval", str(steps_per_eval),
        "--save-every", str(save_every),
        "--mask-prompt",
        "--grad-checkpoint"
    ]
    
    print("\nPhase 2 Command:")
    print(" ".join(cmd))
    print("\nStarting execution on Metal GPU...")
    start_time = time.time()
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    for line in iter(process.stdout.readline, ''):
        print(line, end='', flush=True)
        
    process.stdout.close()
    return_code = process.wait()
    
    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"Phase 2 completed in {elapsed:.2f} seconds ({elapsed / 60:.2f} minutes). Return code: {return_code}")
    
    final_mem = get_macos_memory_info()
    swap_delta = final_mem['swap_used_gb'] - init_mem['swap_used_gb']
    print(f"Post-flight RAM Available: {final_mem['ram_avail_gb']:.2f} GB")
    print(f"Post-flight Swap Used:     {final_mem['swap_used_gb']:.2f} GB (Delta: {swap_delta:+.2f} GB)")
    
    if return_code == 0:
        print("✅ Phase 2 training succeeded! Adapters saved to:", target_adapter_dir)
    else:
        print(f"❌ Phase 2 failed with return code {return_code}")
        sys.exit(return_code)

if __name__ == "__main__":
    main()
