#!/bin/bash
set -euo pipefail
ZIP_PATH="${1:-}"
if [ -z "$ZIP_PATH" ]; then
  echo "Usage: $0 /path/to/drive-download-....zip"
  exit 1
fi
if [ ! -f "$ZIP_PATH" ]; then
  echo "ZIP not found: $ZIP_PATH"
  exit 1
fi
mkdir -p data/inputs
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
unzip -q "$ZIP_PATH" -d "$TMP_DIR"
# Copy the extracted prompt/reference folders into the project input area.
# This deliberately preserves the supplied filenames and folder structure.
if [ -d "$TMP_DIR"/* ]; then
  cp -R "$TMP_DIR"/* data/inputs/
else
  echo "No files found in ZIP."
  exit 1
fi
echo "Imported reference inputs into data/inputs"
find data/inputs -maxdepth 2 -type f | sed -n '1,80p'
