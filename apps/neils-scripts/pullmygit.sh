#!/bin/bash
# Pull all git repos listed in ~/.config/mygitrepos
# Add repo paths (one per line) to ~/.config/mygitrepos to manage them

REPO_LIST="$HOME/.config/mygitrepos"

if [ ! -f "$REPO_LIST" ]; then
    echo "No repo list found at $REPO_LIST"
    echo "Create it with one repo path per line, e.g.:"
    echo "  ~/dev/DD-imager"
    exit 1
fi

while IFS= read -r repo || [ -n "$repo" ]; do
    repo="${repo/#\~/$HOME}"
    [ -z "$repo" ] && continue
    [[ "$repo" == \#* ]] && continue
    if [ -d "$repo/.git" ]; then
        echo "=== $(basename "$repo") ==="
        git -C "$repo" pull
        echo
    else
        echo "=== $(basename "$repo") === SKIPPED (not a git repo)"
        echo
    fi
done < "$REPO_LIST"
