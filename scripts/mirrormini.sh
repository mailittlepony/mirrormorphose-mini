#! /bin/bash
#
# mirrormini.sh
# Copyright (C) 2025 stantonik <stantonik@stantonik-mba.local>
#
# Distributed under terms of the GPLv3 license.
#

set -e

# Go to project root
cd "$(dirname "$0")/../"

# Configuration
RAM_SIZE_MB=512
RAMDISK_PATH="$(pwd)/ramdisk"

echo "🔧 Mounting ramdisk of ${RAM_SIZE_MB}MB at $RAMDISK_PATH..."
mkdir -p "$RAMDISK_PATH"

# Mount tmpfs if not already mounted
if ! mountpoint -q "$RAMDISK_PATH"; then
    mount -t tmpfs -o size="${RAM_SIZE_MB}M" tmpfs "$RAMDISK_PATH"
    echo "✅ tmpfs mounted at $RAMDISK_PATH with size ${RAM_SIZE_MB}MB"
fi

# Set permissions
USER=$(pwd | cut -d '/' -f 3)
chown -R "$USER:$USER" "$RAMDISK_PATH"

# Activate virtual environment and run the app
echo "🚀 Starting application..."
.venv/bin/python3 run.py

