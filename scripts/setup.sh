#! /bin/bash
#
# setup.sh
# Copyright (C) 2025 stantonik <stantonik@stantonik-mba.local>
#
# Distributed under terms of the GPLv3 license.
#

# Run this script immediately after cloning the repository.
# It prepares the system by installing dependencies, setting up a Python virtual environment, and configuring the service to run via systemd.

set -e

SERVICE_NAME="mirrormini.service"
SERVICE_SRC="$(dirname "$0")/systemd/$SERVICE_NAME"
SERVICE_DST="/etc/systemd/system/$SERVICE_NAME"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

VENV_PATH="$ROOT_DIR/.venv"
echo "Creating python virtual environment with required packages..."

if [ -d "$VENV_PATH" ]; then
    echo "Virtual environment already exists. Updating packages..."
else
    echo "Creating Python virtual environment in .venv..."
    python3 -m venv "$VENV_PATH"
fi

source "$VENV_PATH/bin/activate"
pip install -r "$ROOT_DIR/requirements.txt"

echo "Adding '$SERVICE_NAME' to systemd service..."

sed "s|/path/to/your/project|$PROJECT_PATH|g" "$SERVICE_SRC" > "$SERVICE_DST"

chmod 644 "$SERVICE_DST"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

echo "✅ $SERVICE_NAME installed and enabled, please reboot"
