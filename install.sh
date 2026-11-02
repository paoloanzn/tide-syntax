#!/bin/sh
# Install (or update) Tide syntax highlighting for Vim and Neovim.
#
#   curl -fsSL https://raw.githubusercontent.com/paoloanzn/tide-syntax/main/install.sh | sh
#
# Clones the repository once and links its vim/ folder into the native package
# directory of each editor found (Vim, Neovim). Re-run it to update.
set -eu

REPO="https://github.com/paoloanzn/tide-syntax.git"
SRC="${XDG_DATA_HOME:-$HOME/.local/share}/tide-syntax"

command -v git >/dev/null 2>&1 || { echo "tide-syntax: git is required" >&2; exit 1; }

if [ -d "$SRC/.git" ]; then
    git -C "$SRC" pull --quiet --ff-only
else
    git clone --quiet --depth 1 "$REPO" "$SRC"
fi

link() {
    mkdir -p "$1"
    ln -sfn "$SRC/vim" "$1/tide"
    echo "tide-syntax: installed for $2 ($1/tide)"
}

found=
if command -v vim >/dev/null 2>&1 || [ -d "$HOME/.vim" ]; then
    link "$HOME/.vim/pack/tide/start" "Vim"; found=1
fi
if command -v nvim >/dev/null 2>&1; then
    link "${XDG_DATA_HOME:-$HOME/.local/share}/nvim/site/pack/tide/start" "Neovim"; found=1
fi
[ -n "$found" ] || { echo "tide-syntax: neither vim nor nvim found on PATH" >&2; exit 1; }
