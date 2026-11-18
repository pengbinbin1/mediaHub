#!/bin/bash
# 通过本地代理下载 Inno Setup，失败自动重试
set -u
URL="https://github.com/jrsoftware/issrc/releases/download/is-6_7_4/innosetup-6.7.4.exe"
OUT="tools/downloads/innosetup-6.7.4.exe"
PROXY="http://127.0.0.1:7897"

for i in 1 2 3 4 5; do
  echo "=== attempt $i (proxy) ==="
  curl -L -x "$PROXY" -o "$OUT.tmp" "$URL" --connect-timeout 20 --max-time 600 -sS
  if [ -s "$OUT.tmp" ]; then
    mv "$OUT.tmp" "$OUT"
    echo "DOWNLOAD-OK"
    ls -la "$OUT"
    exit 0
  fi
  sleep 5
done
echo "DOWNLOAD-FAILED"
exit 1
