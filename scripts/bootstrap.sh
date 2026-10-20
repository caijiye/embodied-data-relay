#!/usr/bin/env bash
set -euo pipefail

# Bootstrap on Ubuntu 22.04/24.04.
# For other platforms, install Python 3.11/3.12, FFmpeg, and uv manually.

sudo apt-get update
sudo apt-get install -y ffmpeg python3.12-venv curl

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

uv venv --python 3.12
uv pip install -e ".[dev]"
uv run pytest -q

echo "OK. Next:"
echo "  uv run python scripts/synth_recorder.py --out data/incoming --sessions 2 --episodes 7 --cameras 2 --frames 30"
echo "  uv run python -m edr.cli pipeline --config config.yaml"
echo "  uv run python -m edr.cli serve --config config.yaml"
