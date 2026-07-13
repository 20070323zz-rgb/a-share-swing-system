#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="量化研究控制台"
DIST_DIR="$PROJECT_ROOT/dist"
ASSET_DIR="$PROJECT_ROOT/assets"
APP_DIR="$DIST_DIR/$APP_NAME.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
ICONSET_DIR="$DIST_DIR/app_icon.iconset"
SVG_FILE="$ASSET_DIR/app_icon.svg"
PNG_FILE="$ASSET_DIR/app_icon.png"
ICNS_FILE="$RESOURCES_DIR/app_icon.icns"
PY_BIN="$PROJECT_ROOT/.venv/bin/python"
if [ ! -x "$PY_BIN" ]; then
  PY_BIN="$(command -v python3 || true)"
fi

mkdir -p "$DIST_DIR" "$ASSET_DIR" "$MACOS_DIR" "$RESOURCES_DIR"

if [ ! -s "$SVG_FILE" ]; then
  echo "ERROR 缺少 $SVG_FILE"
  exit 1
fi

if command -v qlmanage >/dev/null 2>&1; then
  qlmanage -t -s 1024 -o "$ASSET_DIR" "$SVG_FILE" >/dev/null 2>&1 || true
  if [ -s "$ASSET_DIR/app_icon.svg.png" ]; then
    mv "$ASSET_DIR/app_icon.svg.png" "$PNG_FILE"
  fi
fi

if [ ! -s "$PNG_FILE" ]; then
  export PROJECT_ROOT
  if [ -z "$PY_BIN" ]; then
    echo "CAUTION 未找到 Python，跳过 PNG 生成；仍保留 SVG 图标。"
  else
    "$PY_BIN" - <<'PY'
from pathlib import Path
import os
import struct
import zlib

root = Path(os.environ["PROJECT_ROOT"])
out = root / "assets" / "app_icon.png"
size = 1024

def rgba(x, y):
    cx = (x - size / 2) / (size / 2)
    cy = (y - size / 2) / (size / 2)
    dist = min(1.0, (cx * cx + cy * cy) ** 0.5)
    r = int(246 - 28 * dist)
    g = int(251 - 38 * dist)
    b = int(255 - 18 * dist)
    a = 255
    return r, g, b, a

rows = []
for y in range(size):
    row = bytearray([0])
    for x in range(size):
        row.extend(rgba(x, y))
    rows.append(bytes(row))
raw = b"".join(rows)

def chunk(kind, data):
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
png += chunk(b"IDAT", zlib.compress(raw, 9))
png += chunk(b"IEND", b"")
out.write_bytes(png)
PY
  fi
fi

rm -rf "$ICONSET_DIR"
mkdir -p "$ICONSET_DIR"
if command -v sips >/dev/null 2>&1 && [ -s "$PNG_FILE" ]; then
  sips -z 16 16 "$PNG_FILE" --out "$ICONSET_DIR/icon_16x16.png" >/dev/null
  sips -z 32 32 "$PNG_FILE" --out "$ICONSET_DIR/icon_16x16@2x.png" >/dev/null
  sips -z 32 32 "$PNG_FILE" --out "$ICONSET_DIR/icon_32x32.png" >/dev/null
  sips -z 64 64 "$PNG_FILE" --out "$ICONSET_DIR/icon_32x32@2x.png" >/dev/null
  sips -z 128 128 "$PNG_FILE" --out "$ICONSET_DIR/icon_128x128.png" >/dev/null
  sips -z 256 256 "$PNG_FILE" --out "$ICONSET_DIR/icon_128x128@2x.png" >/dev/null
  sips -z 256 256 "$PNG_FILE" --out "$ICONSET_DIR/icon_256x256.png" >/dev/null
  sips -z 512 512 "$PNG_FILE" --out "$ICONSET_DIR/icon_256x256@2x.png" >/dev/null
  sips -z 512 512 "$PNG_FILE" --out "$ICONSET_DIR/icon_512x512.png" >/dev/null
  cp "$PNG_FILE" "$ICONSET_DIR/icon_512x512@2x.png"
fi

if command -v iconutil >/dev/null 2>&1 && [ -d "$ICONSET_DIR" ]; then
  iconutil -c icns "$ICONSET_DIR" -o "$ICNS_FILE" >/dev/null 2>&1 || true
fi

cat > "$CONTENTS_DIR/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key>
  <string>量化研究控制台</string>
  <key>CFBundleDisplayName</key>
  <string>量化研究控制台</string>
  <key>CFBundleIdentifier</key>
  <string>local.dayin.a-share-swing-system</string>
  <key>CFBundleVersion</key>
  <string>0.2.0-local</string>
  <key>CFBundleShortVersionString</key>
  <string>0.2.0-local</string>
  <key>CFBundleExecutable</key>
  <string>launch</string>
  <key>LSArchitecturePriority</key>
  <array>
    <string>arm64</string>
    <string>x86_64</string>
  </array>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>LSMinimumSystemVersion</key>
  <string>10.15</string>
  <key>NSHighResolutionCapable</key>
  <true/>
  <key>CFBundleIconFile</key>
  <string>app_icon</string>
</dict>
</plist>
PLIST

cat > "$MACOS_DIR/launch" <<'LAUNCH'
#!/bin/bash
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
unset __PYVENV_LAUNCHER__
unset PYTHONHOME
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
cd "$PROJECT_ROOT" || exit 1
if /usr/bin/arch -arm64 /usr/bin/true >/dev/null 2>&1; then
  exec /usr/bin/arch -arm64 /bin/bash "$PROJECT_ROOT/scripts/run_app.sh"
fi
exec /bin/bash "$PROJECT_ROOT/scripts/run_app.sh"
LAUNCH

chmod +x "$MACOS_DIR/launch"
chmod +x "$PROJECT_ROOT/scripts/run_app.sh"
chmod +x "$PROJECT_ROOT/打开量化研究控制台.command" 2>/dev/null || true
chmod +x "$PROJECT_ROOT/A-Share Swing App.command" 2>/dev/null || true

if [ -s "$ICNS_FILE" ]; then
  ICON_STATUS="active"
else
  ICON_STATUS="fallback_png_svg"
fi

echo "OK app bundle: $APP_DIR"
echo "OK icon svg: $SVG_FILE"
echo "OK icon png: $PNG_FILE"
echo "OK icon status: $ICON_STATUS"
echo "提示：可以把 dist/$APP_NAME.app 拖到桌面或 Dock。"
