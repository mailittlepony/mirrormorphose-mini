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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

SERVICE_NAME="mirrormini.service"
SERVICE_SRC="$(dirname "$0")/systemd/$SERVICE_NAME"
SERVICE_DST="/etc/systemd/system/$SERVICE_NAME"

PLATFORM="${1:-orange-pi}"
PLATFORM_DIR="$ROOT_DIR/platforms/$PLATFORM"
PLATFORM_SCRIPT="$PLATFORM_DIR/setup.sh"

PKG_FILE="$SCRIPT_DIR/packages.txt"
PLATFORM_PKG_FILE="$PLATFORM_DIR/packages.txt"

VENV_PATH="$ROOT_DIR/.venv"

# === Run the platform-specific setup
if [[ ! -x "$PLATFORM_SCRIPT" ]]; then
    echo "❌ Platform setup script not found or not executable: $PLATFORM_SCRIPT"
    exit 1
fi

echo "🚀 Running setup for platform: $PLATFORM"
"$PLATFORM_SCRIPT"

# === Install apt packages
install_packages_from_file() {
    local file="$1"

    if [[ -f "$file" ]]; then
        echo "📦 Installing packages from $file..."
        # Remove comments and blank lines, then install
        grep -vE '^\s*#|^\s*$' "$file" | xargs sudo apt install -y
    else
        echo "ℹ️  No package file found at $file, skipping."
    fi
}
echo "📦 Updating package lists..."
sudo apt update

install_packages_from_file "$PKG_FILE"
install_packages_from_file "$PLATFORM_PKG_FILE"

echo "✅ Packages installed successfully."

# === Create python venv
echo "🐍 Creating python virtual environment with required packages..."

if [ -d "$VENV_PATH" ]; then
    echo "Virtual environment already exists. Updating packages..."
else
    python3 -m venv "$VENV_PATH"
fi

source "$VENV_PATH/bin/activate"
pip install -r "$ROOT_DIR/requirements.txt"

# === Install service
echo "Adding '$SERVICE_NAME' to systemd service..."

sed "s|/path/to/your/project|$ROOT_DIR|g" "$SERVICE_SRC" > "$SERVICE_DST"

chmod 644 "$SERVICE_DST"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

echo "✅ $SERVICE_NAME installed and enabled, please reboot"
