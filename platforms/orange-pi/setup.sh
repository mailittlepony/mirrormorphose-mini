#! /bin/bash
#
# setup.sh
# Copyright (C) 2025 stantonik <stantonik@stantonik-mba.local>
#
# Distributed under terms of the GPLv3 license.
#

# Edit config.txt
CONFIG_FILE="/boot/config.txt"
GPU_MEM=256
CAM_OVERLAY="ov13855"

echo_cmd() {
    # print command to terminal with '+'
    printf '+'
    for arg in "$@"; do
        printf ' %q' "$arg"
    done
    echo

    # run the command
    "$@"
}

# Helper to append text to file with logging
append_to_file() {
    echo "+ echo $1 >> $2"
    echo "$1" >> "$2"
}

# Backup original file
cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"
echo "🗂️  Backup created at ${CONFIG_FILE}.bak"

# === Disable Headless Mode ===
echo "🔧 Disable headless mode"
echo_cmd sed --follow-symlinks -i '/^[[:blank:]]*max_framebuffers=/c\#max_framebuffers=2' "$CONFIG_FILE"
echo_cmd sed --follow-symlinks -i '/^[[:blank:]]*hdmi_ignore_hotplug=/c\#hdmi_ignore_hotplug=0' "$CONFIG_FILE"
echo_cmd sed --follow-symlinks -i '/^[[:blank:]]*enable_tvout=/c\#enable_tvout=0' "$CONFIG_FILE"

# === RPi OpenGL driver (vc4-kms-v3d) ===
echo "🔧 Activate RPi driver (vc4-kms-v3d)"
echo_cmd sed --follow-symlinks -Ei '/^[[:blank:]]*dtoverlay=vc4-f?kms-v3d/d' "$CONFIG_FILE"
append_to_file "dtoverlay=vc4-kms-v3d,noaudio" "$CONFIG_FILE"

# === GPU Memory Split ===
echo "🔧 Change GPU memory to $GPU_MEM"
if grep -q '^gpu_mem_256=' "$CONFIG_FILE"; then
    echo_cmd sed --follow-symlinks -i "s/^gpu_mem_256=.*/gpu_mem_256=$GPU_MEM/" "$CONFIG_FILE"
else
    append_to_file "gpu_mem_256=$GPU_MEM" "$CONFIG_FILE"
fi
if grep -q '^gpu_mem_512=' "$CONFIG_FILE"; then
    echo_cmd sed --follow-symlinks -i "s/^gpu_mem_512=.*/gpu_mem_512=$GPU_MEM/" "$CONFIG_FILE"
else
    append_to_file "gpu_mem_512=$GPU_MEM" "$CONFIG_FILE"
fi
if grep -q '^gpu_mem_1024=' "$CONFIG_FILE"; then
    echo_cmd sed --follow-symlinks -i "s/^gpu_mem_1024=.*/gpu_mem_1024=$GPU_MEM/" "$CONFIG_FILE"
else
    append_to_file "gpu_mem_1024=$GPU_MEM" "$CONFIG_FILE"
fi

# === Enable RPi codec and camera ===
echo "🔧 Enable RPi codec and camera"
echo_cmd rm -f /etc/modprobe.d/dietpi-disable_vcsm.conf
echo_cmd rm -f /etc/modprobe.d/dietpi-disable_rpi_codec.conf
echo_cmd rm -f /etc/modprobe.d/dietpi-disable_rpi_camera.conf

if grep -q '^#start_x=' "$CONFIG_FILE"; then
    echo_cmd sed --follow-symlinks -i 's/^#start_x=.*/start_x=1/' "$CONFIG_FILE"
elif grep -q '^start_x=' "$CONFIG_FILE"; then
    echo_cmd sed --follow-symlinks -i 's/^start_x=.*/start_x=1/' "$CONFIG_FILE"
else
    append_to_file "start_x=1" "$CONFIG_FILE"
fi

if ! grep -q "^dtoverlay=$CAM_OVERLAY" "$CONFIG_FILE"; then
    append_to_file "dtoverlay=$CAM_OVERLAY" "$CONFIG_FILE"
fi

# === HDMI config ===
echo "🔧 Setting up custom HDMI for the screen"
read -r -d '' HDMI_SETTINGS <<EOF
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_timings=1080 0 48 6 25 1920 0 8 2 4 0 0 0 59 0 134490000 0
framebuffer_width=1080
framebuffer_height=1920
EOF

while IFS= read -r HDMI_LINE; do
    # Skip empty lines or comments in the list
    [[ -z "$HDMI_LINE" || "$HDMI_LINE" == \#* ]] && continue

    KEY=$(echo "$HDMI_LINE" | cut -d= -f1)

    if grep -Eq "^[[:space:]]*#?[[:space:]]*$KEY=" "$CONFIG_FILE"; then
        echo_cmd sed --follow-symlinks -i -E "s|^[[:space:]]*#?[[:space:]]*$KEY=.*|$HDMI_LINE|" "$CONFIG_FILE"
    else
        append_to_file "$HDMI_LINE" "$CONFIG_FILE"
    fi
done <<< "$HDMI_SETTINGS"

echo "✅ Hardware settings updated successfully. Please reboot."

