#!/bin/bash
set -euo pipefail

PROJECT_ROOT="/Users/dayin/Documents/量化学习/a-share-swing-system"
LAUNCHD_DIR="$PROJECT_ROOT/launchd"
AGENTS_DIR="$HOME/Library/LaunchAgents"
DOMAIN="gui/$(id -u)"

LABELS=(
  "com.dayin.a-share.open-check"
  "com.dayin.a-share.daily-close"
  "com.dayin.a-share.weekly-review"
)

mkdir -p "$AGENTS_DIR"
mkdir -p "$PROJECT_ROOT/logs"

echo "Installing launchd jobs into $AGENTS_DIR"

for label in "${LABELS[@]}"; do
  src="$LAUNCHD_DIR/$label.plist"
  dest="$AGENTS_DIR/$label.plist"
  if [ ! -f "$src" ]; then
    echo "missing plist: $src" >&2
    exit 1
  fi

  echo "Installing $label"
  launchctl bootout "$DOMAIN" "$dest" >/dev/null 2>&1 || true
  cp "$src" "$dest"
  launchctl bootstrap "$DOMAIN" "$dest"
done

echo
echo "Installed jobs:"
for label in "${LABELS[@]}"; do
  echo "- $label"
done

echo
echo "View jobs:"
for label in "${LABELS[@]}"; do
  echo "launchctl print $DOMAIN/$label"
done

echo
echo "Manual trigger:"
for label in "${LABELS[@]}"; do
  echo "launchctl kickstart -k $DOMAIN/$label"
done

echo
echo "View logs:"
echo "tail -n 80 $PROJECT_ROOT/logs/open_check.log"
echo "tail -n 80 $PROJECT_ROOT/logs/daily_close.log"
echo "tail -n 80 $PROJECT_ROOT/logs/weekly_review.log"
echo "tail -n 80 $PROJECT_ROOT/logs/launchd_open_check.err.log"
echo "tail -n 80 $PROJECT_ROOT/logs/launchd_daily_close.err.log"
echo "tail -n 80 $PROJECT_ROOT/logs/launchd_weekly_review.err.log"

echo
echo "These jobs only run local scripts for reports and simulated records. They do not connect to broker APIs or place real orders."
