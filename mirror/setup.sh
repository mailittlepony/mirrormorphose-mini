#! /bin/sh
#
# setup.sh
# Copyright (C) 2025 stantonik <stantonik@stantonik-mba.local>
#
# Distributed under terms of the MIT license.
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Variables — customize RAM_SIZE_MB, DIR_PATH is set to parent folder of this script
RAM_SIZE_MB=512
DIR_PATH="$PARENT_DIR/mnt/ramdisk"  # For example, under parent dir in "mnt/ramdisk"

MOUNT_SCRIPT="/usr/local/bin/mount_tmpfs.sh"
SERVICE_FILE="/etc/systemd/system/mount_tmpfs.service"

echo "Parent directory of this script detected as: $PARENT_DIR"
echo "Mount directory set to: $DIR_PATH"

echo "Creating mount script at $MOUNT_SCRIPT..."

cat << EOF > "$MOUNT_SCRIPT"
#!/bin/bash

ram_size_mb=$RAM_SIZE_MB
dir_path="$DIR_PATH"

mkdir -p "\$dir_path"

mountpoint -q "\$dir_path" || mount -t tmpfs -o size="\${ram_size_mb}M" tmpfs "\$dir_path"
EOF

chmod +x "$MOUNT_SCRIPT"
echo "Mount script created and made executable."

echo "Creating systemd service at $SERVICE_FILE..."

cat << EOF > "$SERVICE_FILE"
[Unit]
Description=Mount tmpfs at boot
After=network.target

[Service]
Type=oneshot
ExecStart=$MOUNT_SCRIPT
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

echo "Systemd service created."

echo "Reloading systemd daemon, enabling and starting the service..."

SERVICE_NAME=$(basename "$SERVICE_FILE")
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"

echo "Done! Your tmpfs will be mounted at $DIR_PATH on startup with size ${RAM_SIZE_MB}M."

echo "Check status with: sudo systemctl status $SERVICE_NAME"

