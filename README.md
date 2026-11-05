# 🛠️ Model-Creator
### Universal LLM Auto-Profiler, Hardware Sizing Advisor & 1-Command Deployment Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9+-brightgreen.svg)](pyproject.toml)
[![Hardware: Mac | Intel | AMD | ARM](https://img.shields.io/badge/Hardware-Metal%20%7C%20Vulkan%20%7C%20CUDA%20%7C%20CPU-orange.svg)](#-hardware-acceleration--bandwidth-matrix)

**Model-Creator** is a standalone, hardware-adaptive toolchain designed to build, quantize, optimize, serve, condition, and benchmark **any model family** (Qwen, Llama, DeepSeek, Mistral, Gemma, Phi) on **any machine**.

Instead of assuming fixed memory sizes, `model-creator` dynamically analyzes your host's physical RAM, GPU VRAM, and memory bus bandwidth. It calculates the exact optimal parameter tier (1.5B, 3B, 7B, 14B, 32B, 70B) and quantization scheme (`IQ3_M`, `Q4_K_M`, `Q5_K_M`, `Q8_0`), generates flash-attention presets, pairs speculative draft models, and produces 1-click launchers for `llama-server` and `ollama`.

---

## ⚡ 1-Minute Quick Start

### 1. Auto-Profile Your System
Detect your CPU, physical RAM, GPU VRAM, and optimal model sizing:

```bash
python3 scripts/hardware_model_profiler.py
```

### 2. Create a Tailored Model in 1 Command
Create a customized, ready-to-deploy LLM stack tailored to your auto-detected hardware (or custom limits):

```bash
# Auto-detect local system and create Qwen 2.5 Coder
python3 scripts/create_custom_model.py \
  --base-model "Qwen/Qwen2.5-Coder-7B-Instruct" \
  --name "my-local-code-llm"

# Or tailor to custom limits (e.g., 4GB VRAM GPU, 16GB RAM)
python3 scripts/create_custom_model.py \
  --base-model "Qwen/Qwen2.5-Coder-7B-Instruct" \
  --name "apex-vulkan-4gb" \
  --vram-gb 4.0 \
  --ram-gb 16.0
```

This outputs:
- `Modelfile.<name>`: Engineered system prompt, thinking tokens, and format constraints.
- `presets.<name>.ini`: Fast flash-attention, `q8_0` KV cache, and thread pinning.
- `download_<name>.sh`: Automated GGUF downloader from Hugging Face Hub.
- `start_<name>.sh`: 1-click launcher for `llama-server` or `ollama`.

---

## 🎛️ Hardware Acceleration & Bandwidth Matrix

Generation throughput is fundamentally bounded by memory bandwidth:
$$\text{Max Generation Tokens/sec} \approx \frac{\text{Memory Bandwidth (GB/s)}}{\text{Model Footprint (GB)}}$$

| System Architecture | Memory Bus | Bandwidth | Optimal Model Size | Quantization | Headroom Left |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Apple Silicon (36–64 GB)** | Unified LPDDR5 | 300–400 GB/s | **14B to 32B** | **Q5_K_M** (9.8–22 GB) | 20+ GB |
| **Apple Silicon (16–24 GB)** | Unified LPDDR5 | 150–200 GB/s | **7B** | **Q5_K_M** (5.2 GB) | 10+ GB |
| **Discrete GPU (8–16 GB VRAM)**| Dedicated GDDR6 | 288–448 GB/s | **7B to 14B** | **Q5_K_M** / **Q4_K_M** | 2–4 GB |
| **Discrete GPU (4 GB GDDR6)** | Dedicated GDDR6 | 192 GB/s | **7B** | **IQ3_M** (3.57 GB) | 0.4 GB |
| **Intel/AMD DDR4 RAM (CPU)** | Dual-channel DDR4 | 25–40 GB/s | **1.5B to 3B** | **Q4_K_M** (1.1–2.1 GB) | 14+ GB |
| **Linux ARM64 (Graviton/SBC)**| DDR4 / LPDDR4x | 20–50 GB/s | **1.5B to 3B** | **Q4_K_M** (1.1–2.1 GB) | 10+ GB |

---

## 🧠 Research-Backed Test-Time Compute (TTC) Pipeline

### 1. Karpathy Software 3.0 External AST Linter (`scripts/ast_linter_tool.py`)
Deterministic Python AST analysis catching competitive programming anti-patterns without benchmark leakage:
- Catches repeated `sys.stdin.read()` inside loops (preventing EOF bugs).
- Enforces integer division `//` in index expressions.
- Flags hardcoded index multiplications (`a[0] * a[1] * a[2]...`).
- Generates single-shot tool repair prompts to correct defects in a single follow-up forward pass.

### 2. DiffCodeGen Behavioral Clustering Engine (`scripts/diff_codegen_cluster.py`)
Implements *arXiv:2605.20473*:
- Samples $K$ diverse candidates at temperature $T=0.3-0.5$.
- Runs candidates against synthetic, problem-agnostic boundary arrays (`"1\n1"`, `"2\n1 2"`, `"3\n1 2 3"`).
- Computes behavioral execution agreement matrix and selects the consensus medoid candidate.

### 3. Air-Gapped Benchmarking (`scripts/test_livecodebench_eval.py`)
Evaluates models against LiveCodeBench or HumanEval using a pre-warmed, memory-capped Docker container (`--network none`, `--memory 512m`, `--cpus 2.0`).

---

## 🤖 Antigravity & Agent Customizations Included

This repository comes pre-packaged with first-class agent customizations:

- **Autonomous Agent**: [`.agents/agents/universal-model-builder.md`](.agents/agents/universal-model-builder.md)
  Can be invoked by any AI coding assistant to autonomously profile hardware, quantize models, deploy servers, run benchmarks, and publish releases.
- **Engineering Skill**: [`.agents/skills/universal-model-builder/SKILL.md`](.agents/skills/universal-model-builder/SKILL.md)
  Step-by-step operational runbook and hardware presets.
- **Turnkey Session Replication Prompt**: [`REPLICATION_TRANSCRIPT.md`](REPLICATION_TRANSCRIPT.md)
  Ready to copy and paste into any fresh session.
- **System Architecture Blueprint**: [`BLUEPRINT.md`](BLUEPRINT.md)
  Complete mathematical and technical documentation.

---

## 📂 Repository Structure

```text
model-creator/
├── .agents/
│   ├── agents/
│   │   └── universal-model-builder.md       # Autonomous agent specification
│   └── skills/
│       └── universal-model-builder/
│           ├── SKILL.md                     # Skill instructions & runbook
│           ├── examples/presets.ini         # Multi-hardware presets template
│           └── references/hardware_matrix.md# Memory bandwidth & hardware reference
├── scripts/
│   ├── hardware_model_profiler.py          # Dynamic hardware & memory profiler
│   ├── create_custom_model.py               # 1-command custom model creator
│   ├── ast_linter_tool.py                   # Karpathy Software 3.0 AST linter
│   ├── diff_codegen_cluster.py              # DiffCodeGen behavioral clustering
│   ├── clean_decoding_pipeline.py           # Unified decoding with tool self-repair
│   └── test_livecodebench_eval.py           # Air-gapped benchmark harness
├── BLUEPRINT.md                             # Deep architectural specification
├── REPLICATION_TRANSCRIPT.md                # Turnkey session replication transcript
├── pyproject.toml                           # Package metadata and CLI entrypoints
├── LICENSE                                  # MIT License
└── README.md
```

---

## 📜 License
MIT License. Created by [Nilesh Chakraborty](https://github.com/nileshchakraborty).
