#!/bin/bash
set -euo pipefail

REPO="invisi101/firefox-settings"
RELEASE_TAG="v1.0"
ZIP_NAME="ff-profile.zip"
ZIP_PATH="$(dirname "$0")/$ZIP_NAME"

if [[ ! -f "$ZIP_PATH" ]]; then
    echo "Error: $ZIP_PATH not found"
    echo "Update the zip file first, then re-run this script."
    exit 1
fi

echo "Uploading $ZIP_NAME to $REPO release $RELEASE_TAG..."
gh release upload "$RELEASE_TAG" "$ZIP_PATH" --repo "$REPO" --clobber

echo "Done."
