#! /bin/bash
#
# setup.sh
# Copyright (C) 2025 stantonik <stantonik@stantonik-mba.local>
#
# Distributed under terms of the GPLv3 license.
#

# Edit config.txt
CONFIG_FILE="/boot/config.txt"

# Backup original file
cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"
echo "🗂️  Backup created at ${CONFIG_FILE}.bak"

# ========== Screen config (HDMI) ==========
read -r -d '' HDMI_SETTINGS <<EOF
hdmi_group=2
hdmi_mode=82
hdmi_drive=2
EOF

echo "🔍 Removing existing HDMI settings:"
grep '^hdmi_' "$CONFIG_FILE"
sed -i '/^hdmi_/d' "$CONFIG_FILE"

echo "➕ Adding HDMI settings:"
echo "$HDMI_SETTINGS"
echo "$HDMI_SETTINGS" >> "$CONFIG_FILE"

# ========== Camera config ==========
if ! grep -q '^dtoverlay=ov13855' "$CONFIG_FILE"; then
    echo "➕ Adding camera overlay: dtoverlay=ov13855"
    echo "dtoverlay=ov13855" >> "$CONFIG_FILE"
else
    echo "✅ Camera overlay already present: dtoverlay=ov13855"
fi

# ========== GPU config ==========
echo "🔍 Removing existing GPU memory settings:"
grep '^gpu_mem=' "$CONFIG_FILE"
sed -i '/^gpu_mem=/d' "$CONFIG_FILE"

echo "➕ Adding GPU memory setting: gpu_mem=1024"
echo "gpu_mem=1024" >> "$CONFIG_FILE"

echo "✅ '$CONFIG_FILE' successfully updated!"

# Edit cmdline.txt
CMDLINE_FILE="/boot/cmdline.txt"

# Backup first
cp "$CMDLINE_FILE" "${CMDLINE_FILE}.bak"
echo "🗂️  Backup created at ${CMDLINE_FILE}.bak"

# Read original line
ORIGINAL_CMDLINE=$(cat "$CMDLINE_FILE")

# Clean it:
# - Remove console=... entries
# - Remove splash, loglevel=..., fbcon=..., etc.
# - Keep root=, rootwait, and other essential flags
CLEANED_CMDLINE=$(echo "$ORIGINAL_CMDLINE" | \
    sed -E 's/console=[^ ]+//g' | \
    sed -E 's/loglevel=[^ ]+//g' | \
    sed -E 's/splash//g' | \
    sed -E 's/fbcon=[^ ]+//g' | \
    sed -E 's/\s+/ /g' | \
    sed -E 's/^\s+|\s+$//g')

# Add quiet mode and hide cursor
CLEANED_CMDLINE="${CLEANED_CMDLINE} quiet vt.global_cursor_default=0"

# Update the file
echo "$CLEANED_CMDLINE" > "$CMDLINE_FILE"

echo "✅ '$CMDLINE_FILE' cleaned!"

