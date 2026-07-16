#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.dayin.a-share.tushare-etf-availability"
TEMPLATE="$PROJECT_ROOT/launchd/$LABEL.plist.template"
DEST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"
LOCALTIME_TARGET="$(readlink /etc/localtime || true)"

if [[ "$LOCALTIME_TARGET" != *"/Asia/Shanghai" ]]; then
  echo "launchd StartCalendarInterval uses the host time zone; expected Asia/Shanghai, got: $LOCALTIME_TARGET" >&2
  exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents" "$PROJECT_ROOT/logs"
launchctl bootout "$DOMAIN" "$DEST" >/dev/null 2>&1 || true
sed "s|__PROJECT_ROOT__|$PROJECT_ROOT|g" "$TEMPLATE" > "$DEST"
plutil -lint "$DEST"
launchctl bootstrap "$DOMAIN" "$DEST"

echo "Installed $LABEL from $PROJECT_ROOT"
echo "Status: launchctl print $DOMAIN/$LABEL"
echo "Logs: $PROJECT_ROOT/logs/tushare_etf_availability.out.log"
