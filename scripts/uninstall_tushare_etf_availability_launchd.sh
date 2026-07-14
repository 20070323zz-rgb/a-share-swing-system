#!/bin/bash
set -euo pipefail

LABEL="com.dayin.a-share.tushare-etf-availability"
DEST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"

launchctl bootout "$DOMAIN" "$DEST" >/dev/null 2>&1 || true
rm -f "$DEST"
echo "Uninstalled $LABEL"
