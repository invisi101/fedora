#!/bin/bash
# Commit and push all git repos listed in ~/.config/mygitrepos
# Usage:
#   pushmygit                  — auto-commits with "Update <repo name>"
#   pushmygit "your message"   — commits with your custom message

REPO_LIST="$HOME/.config/mygitrepos"
CUSTOM_MSG="$1"

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
        name=$(basename "$repo")
        echo "=== $name ==="
        changes=$(git -C "$repo" status --porcelain 2>/dev/null)
        branch=$(git -C "$repo" rev-parse --abbrev-ref HEAD 2>/dev/null)
        if [ -n "$changes" ]; then
            msg="${CUSTOM_MSG:-Update $name}"
            echo "Committing: $msg"
            git -C "$repo" add -A
            git -C "$repo" commit -m "$msg"
            git -C "$repo" push
        else
            ahead=$(git -C "$repo" rev-list --count "origin/$branch..HEAD" 2>/dev/null)
            if [ "$ahead" -gt 0 ] 2>/dev/null; then
                echo "Pushing $ahead unpushed commit(s)..."
                git -C "$repo" push
            else
                echo "Already up to date"
            fi
        fi
        echo
    else
        echo "=== $(basename "$repo") === SKIPPED (not a git repo)"
        echo
    fi
done < "$REPO_LIST"
