#!/usr/bin/env bash
set -euo pipefail

# cd to project root (handles being launched from /scripts)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PORT="${1:-8080}"

ensure_python() {
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return
  fi

  echo "Python 3 not found."
  if command -v brew >/dev/null 2>&1; then
    echo "Attempting to install Python 3 via Homebrew..."
    brew install python
  else
    cat <<'EOF'
Homebrew not found. Please install Python 3 using one of the following and re-run:

macOS:
  - Install Homebrew:
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  - Then: brew install python

Ubuntu/Debian:
  sudo apt update && sudo apt install -y python3 python3-venv python3-pip

Fedora:
  sudo dnf install -y python3 python3-venv python3-pip

Arch:
  sudo pacman -S --noconfirm python python-virtualenv
EOF
    exit 1
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 still not found after install. Please restart your shell and try again." >&2
    exit 1
  fi
  echo "python3"
}

PYBIN="$(ensure_python)"

if [ ! -x ".venv/bin/python" ]; then
  echo "Creating virtual environment..."
  "$PYBIN" -m venv .venv
fi

. .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

export PORT="$PORT"
python -m app.main
