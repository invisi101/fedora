#!/bin/bash
# Fixed for Fedora: ClamAV freshclam runs as 'clamupdate', not 'clamav'.

echo "Updating ClamAV virus definitions..."
sudo -u clamupdate freshclam

echo ""
echo "Select a folder to scan..."
FOLDER=$(zenity --file-selection --directory --title="Select a folder to scan with ClamAV")

if [ -z "$FOLDER" ]; then
    echo "No folder selected. Exiting."
    exit 1
fi

echo ""
echo "Scanning: $FOLDER"
echo "========================================="
clamscan -r --infected "$FOLDER"
