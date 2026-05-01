#!/bin/bash
set -euo pipefail

REPO="invisi101/firefox-settings"
RELEASE_TAG="v1.0"
ZIP_NAME="ff-profile.zip"

# Check dependencies
for cmd in zip unzip; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Error: '$cmd' is not installed. Install it and re-run this script."
        exit 1
    fi
done

# Check Firefox is not running
if pgrep -x "firefox|firefox-bin|firefox-esr" &>/dev/null; then
    echo "Error: Firefox is currently running. Close it first, then re-run this script."
    exit 1
fi

# Find all possible Firefox profile directories
find_profile_dirs() {
    local dirs=()
    local search_paths=(
        "$HOME/.mozilla/firefox"
        "$HOME/.config/mozilla/firefox"
        "$HOME/.var/app/org.mozilla.firefox/.mozilla/firefox"
        "$HOME/snap/firefox/common/.mozilla/firefox"
        "$HOME/Library/Application Support/Firefox/Profiles"
    )

    for base in "${search_paths[@]}"; do
        [[ -d "$base" ]] || continue

        for profile in "$base"/*.default-release "$base"/*.default-release-[0-9]*; do
            [[ -d "$profile" ]] && dirs+=("$profile|Firefox")
        done
        for profile in "$base"/*.default-esr "$base"/*.default-esr-[0-9]*; do
            [[ -d "$profile" ]] && dirs+=("$profile|Firefox ESR")
        done
        for profile in "$base"/*.dev-edition-default "$base"/*.dev-edition-default-[0-9]*; do
            [[ -d "$profile" ]] && dirs+=("$profile|Firefox Developer Edition")
        done
    done

    [[ ${#dirs[@]} -gt 0 ]] && printf '%s\n' "${dirs[@]}"
}

# Download the zip
download_zip() {
    local dest="$1"
    if command -v gh &>/dev/null; then
        gh release download "$RELEASE_TAG" --repo "$REPO" --pattern "$ZIP_NAME" --dir "$dest" --clobber
    elif command -v curl &>/dev/null; then
        curl -sL "https://github.com/$REPO/releases/download/$RELEASE_TAG/$ZIP_NAME" -o "$dest/$ZIP_NAME"
    else
        echo "Error: need either gh or curl installed"
        exit 1
    fi
}

# Main
echo "Before continuing, make sure you have opened and closed the version"
echo "of Firefox you want to set up, so that a profile directory is created."
echo ""
read -rp "Press Enter to continue..."

profiles=()
while IFS= read -r line; do
    [[ -n "$line" ]] && profiles+=("$line")
done < <(find_profile_dirs)

if [[ ${#profiles[@]} -eq 0 ]]; then
    echo "No Firefox profiles found."
    echo "Launch Firefox at least once to create a profile, then re-run this script."
    exit 1
fi

echo "Found Firefox installations:"
echo ""
for i in "${!profiles[@]}"; do
    path="${profiles[$i]%%|*}"
    edition="${profiles[$i]##*|}"
    echo "  $((i + 1))) $edition"
    echo "     $path"
    echo ""
done

read -rp "Select a profile to install settings to (1-${#profiles[@]}): " choice

if ! [[ "$choice" =~ ^[0-9]+$ ]] || (( choice < 1 || choice > ${#profiles[@]} )); then
    echo "Invalid selection."
    exit 1
fi

selected="${profiles[$((choice - 1))]}"
target="${selected%%|*}"
edition="${selected##*|}"

echo ""
echo "This will overwrite settings in:"
echo "  $target"
read -rp "Continue? (y/n): " confirm
[[ "$confirm" == "y" ]] || exit 0

# Backup existing profile
backup="${target}.backup.$(date +%Y%m%d-%H%M%S).zip"
echo "Backing up current profile to:"
echo "  $backup"
(cd "$target" && zip -rq "$backup" .)

# Download and extract
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

echo "Downloading profile..."
download_zip "$tmpdir"

echo "Extracting to profile..."
unzip -o "$tmpdir/$ZIP_NAME" -d "$target" > /dev/null

# Remove compatibility.ini so Firefox regenerates it with the correct version
# on next launch rather than rejecting the profile due to a version mismatch
rm -f "$target/compatibility.ini"

# Offer arkenfox hardening
echo ""
read -rp "Apply arkenfox privacy hardening? (y/n): " arkenfox
if [[ "$arkenfox" == "y" ]]; then
    echo "Fetching latest arkenfox user.js..."
    arkenfox_url="https://raw.githubusercontent.com/arkenfox/user.js/master"
    curl -sL "$arkenfox_url/user.js" -o "$target/user.js"
    curl -sL "$arkenfox_url/updater.sh" -o "$target/updater.sh"
    chmod +x "$target/updater.sh"

    # Copy user-overrides.js from this repo
    script_dir="$(cd "$(dirname "$0")" && pwd)"
    if [[ -f "$script_dir/user-overrides.js" ]]; then
        cp "$script_dir/user-overrides.js" "$target/user-overrides.js"
        echo "Installed arkenfox user.js + user-overrides.js + updater.sh"
    else
        echo "Installed arkenfox user.js + updater.sh (no user-overrides.js found)"
    fi
fi

echo "Done. Restart $edition to apply settings."
