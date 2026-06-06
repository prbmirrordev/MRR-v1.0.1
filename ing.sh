#!/bin/bash
# MRR English Installer
# Usage: chmod +x ing.sh && ./ing.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
USER_NAME="${SUDO_USER:-$(whoami)}"
USER_HOME="$(eval echo "~$USER_NAME")"

echo "MRR English mode installer"

target_files=("$USER_HOME/.bashrc" "$USER_HOME/.zshrc" "$USER_HOME/.profile")
updated=false

for rc in "${target_files[@]}"; do
    if [ -f "$rc" ]; then
        if grep -q "MRR_LANG" "$rc" 2>/dev/null; then
            echo "MRR_LANG already present in $rc"
        else
            printf "\n# MRR Language English mode\nexport MRR_LANG=\"en\"\n" >> "$rc"
            echo "Updated $rc"
            updated=true
        fi
    fi
 done

if [ "$updated" = false ]; then
    echo "No shell rc file found. Adding to $USER_HOME/.bashrc"
    printf "\n# MRR Language English mode\nexport MRR_LANG=\"en\"\n" >> "$USER_HOME/.bashrc"
fi

echo "English mode enabled for MRR. Restart your terminal to apply changes."
