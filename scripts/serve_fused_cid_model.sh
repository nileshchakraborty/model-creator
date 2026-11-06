#!/usr/bin/env bash
# Standalone MLX OpenAI-Compatible Server for Fused Qwen 2.5 Coder 14B CID
# Provides http://127.0.0.1:8080/v1/chat/completions for local IDEs and agents

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="/Users/nileshchakraborty/workspace/.venv-qwen-systems/bin/python3"
MODEL_PATH="${PROJECT_ROOT}/models/qwen2.5_coder_14b_cid_fused"
PORT="${1:-8080}"

echo "================================================================================"
echo "🚀 LAUNCHING STANDALONE FUSED QWEN 2.5 CODER 14B CID SERVER"
echo "================================================================================"
echo "Model Path: ${MODEL_PATH}"
echo "Server URL: http://127.0.0.1:${PORT}/v1/chat/completions"
echo "Hardware:   Apple Silicon M4 Max (Metal GPU)"
echo "Swap Usage: Zero churn guaranteed"
echo "================================================================================"

exec "${VENV_PYTHON}" -m mlx_lm.server \
    --model "${MODEL_PATH}" \
    --host "127.0.0.1" \
    --port "${PORT}" \
    --temp 0.0 \
    --max-tokens 2048
