#!/bin/bash
set -euo pipefail

PROJECT_ROOT="/Users/dayin/Code/a-share-swing-system"
AGENTS_DIR="$HOME/Library/LaunchAgents"
DOMAIN="gui/$(id -u)"

LABELS=(
  "com.dayin.a-share.catchup-check"
  "com.dayin.a-share.open-check"
  "com.dayin.a-share.midday-check"
  "com.dayin.a-share.afternoon-open-check"
  "com.dayin.a-share.daily-close"
  "com.dayin.a-share.weekly-review"
  "com.dayin.a-share.monthly-model-review"
)

echo "Uninstalling launchd jobs from $DOMAIN"

for label in "${LABELS[@]}"; do
  dest="$AGENTS_DIR/$label.plist"
  echo "Unloading $label"
  launchctl bootout "$DOMAIN" "$dest" >/dev/null 2>&1 || true
  if [ -f "$dest" ]; then
    rm "$dest"
    echo "Removed $dest"
  else
    echo "No installed plist found at $dest"
  fi
done

echo
echo "Project plist templates remain in $PROJECT_ROOT/launchd/"
echo "Project logs and reports were not deleted."
