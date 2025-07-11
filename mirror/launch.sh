#!/bin/bash
# mirrormini startup script

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$PROJECT_ROOT"

source "$PROJECT_ROOT/venv/bin/activate"
python main.py
