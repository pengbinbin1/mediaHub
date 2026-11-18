#!/bin/bash
# 自动重试安装依赖：最多 4 次，前 3 次清华镜像，最后 1 次官方源
cd "$(dirname "$0")/.."
for i in 1 2 3 4; do
  if [ "$i" -le 3 ]; then IDX="https://pypi.tuna.tsinghua.edu.cn/simple"; else IDX="https://pypi.org/simple"; fi
  echo "=== attempt $i ($IDX) ==="
  .venv/Scripts/python.exe -m pip install --no-cache-dir -i "$IDX" --timeout 60 --retries 5 \
    -r requirements.txt pyinstaller imageio imageio-ffmpeg numpy 2>&1 | tail -2
  if .venv/Scripts/python.exe -c "import PySide6, fitz, docx, PIL, PyInstaller" 2>/dev/null; then
    echo "ALL_DEPS_OK"
    exit 0
  fi
  sleep 10
done
echo "ALL_DEPS_FAILED"
exit 1
