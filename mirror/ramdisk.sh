#! /bin/sh
#
# ramdisk.sh
# Copyright (C) 2025 stantonik <stantonik@stantonik-mba.local>
#
# Distributed under terms of the GPLv3 license.
#

OS_TYPE="$(uname)"

action="$1"
dir_path="$2"
ram_size_mb=256

if [[ $# -ne 2 || ( "$action" != "mount" && "$action" != "unmount" ) ]]; then
    echo "Usage: $0 <mount|unmount> <path>"
    exit 1
fi

parent_dir="$(dirname "$dir_path")"

if [[ "$OS_TYPE" == "Darwin" ]]; then
    echo "Darwin detected"
elif [[ "$OS_TYPE" == "Linux" ]]; then
    echo "Linux detected"
else
    echo "$OS_TYPE is unsuported"
    exit 1
fi

function mount_ram_disk() {
    # Check if directory already exists
    if [[ -e "$dir_path" ]]; then
        echo "Error: Target directory '$dir_path' already exists."
        exit 1
    fi

    # Check if parent directory exists and is a directory
    if [[ ! -d "$parent_dir" ]]; then
        echo "Error: Parent directory '$parent_dir' does not exist or is not a directory."
        exit 1
    fi
    if [[ "$OS_TYPE" == "Darwin" ]]; then
        echo "Mounting a ram disk at /Volumes/ramdisk..."
        diskutil erasevolume HFS+ 'ramdisk' $(hdiutil attach -nobrowse -nomount ram://$((ram_size_mb * 2048)))
        if [[ $? -ne 0 ]]; then
            echo "Failed to mount ram disk at /Volumes/ramdisk"
            exit 1
        fi
        echo "Ram disk succesfully mounted at /Volumes/ramdisk"
        ln -s "/Volumes/ramdisk" "$dir_path"
        echo "Symlink created at $dir_path -> /Volumes/ramdisk"
    elif [[ "$OS_TYPE" == "Linux" ]]; then
        echo "Mounting a ram disk at $dir_path"
        mkdir -p "$dir_path"
        sudo mount -t tmpfs -o size="${ram_size_mb}M" tmpfs "$dir_path"
        if mountpoint -q "$dir_path"; then
            echo "Ram disk successfully mounted at $dir_path"
        else
            echo "Failed to mount ram disk at $dir_path"
            exit 1
        fi
    fi
}

function unmount_ram_disk() {
    if [[ "$OS_TYPE" == "Darwin" ]]; then
        echo "Unmounting ram disk at /Volumes/ramdisk..."

        # Unmount and detach the device
        device=$(diskutil info /Volumes/ramdisk 2>/dev/null | grep 'Device Identifier' | sed 's/.*: *//')

        if [[ -n "$device" ]]; then
            echo "Trying to detach /dev/$device ..."
            diskutil unmountDisk "/Volumes/ramdisk"
            if [[ $? -ne 0 ]]; then
                echo "Failed to unmount /Volumes/ramdisk"
                exit 1
            fi

            hdiutil detach "/dev/$device"
            if [[ $? -ne 0 ]]; then
                echo "Failed to detach /dev/$device — device might be busy."
                exit 1
            fi
        else
            echo "No device found for /Volumes/ramdisk"
        fi

        echo "Ram disk unmounted and device detached."

        # Remove the symlink if it exists
        if [[ -L "$dir_path" ]]; then
            rm "$dir_path"
            echo "Symlink $dir_path removed."
        fi

    elif [[ "$OS_TYPE" == "Linux" ]]; then
        echo "Unmounting ram disk at $dir_path"

        if mountpoint -q "$dir_path"; then
            sudo umount "$dir_path"
            if [[ $? -eq 0 ]]; then
                echo "Ram disk unmounted from $dir_path"
                rmdir "$dir_path"  # Remove the mount point directory if empty
            else
                echo "Failed to unmount $dir_path"
                exit 1
            fi
        else
            echo "No ram disk mounted at $dir_path"
            exit 1
        fi

    else
        echo "Unsupported OS: $OS_TYPE"
        exit 1
    fi
}

case "$action" in
    mount)
        mount_ram_disk
        ;;
    unmount)
        unmount_ram_disk
        ;;
    *)
        echo "Usage: $0 <mount|unmount> <path>"
        exit 1
        ;;
esac 
