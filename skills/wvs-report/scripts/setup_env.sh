#!/usr/bin/env bash
# 보고서 빌드용 Python 환경 준비 (wvs-report)
# <assets>/.venv 에 python-docx · python-pptx · matplotlib · pymupdf 설치(uv 우선, 없으면 python3 -m venv + pip).
# 이후 빌드: <assets>/.venv/bin/python build.py --pdf
# 사용: setup_env.sh <assets_dir>   (출력: venv python 경로)
set -euo pipefail
A="${1:-.}"; mkdir -p "$A"; V="$A/.venv"
PKGS=(python-docx python-pptx matplotlib pymupdf)
if [ ! -x "$V/bin/python" ]; then
  if command -v uv >/dev/null 2>&1; then uv venv -q "$V"; else python3 -m venv "$V"; fi
fi
if command -v uv >/dev/null 2>&1; then
  uv pip install -q --python "$V/bin/python" "${PKGS[@]}"
else
  "$V/bin/python" -m pip install -q --upgrade pip >/dev/null
  "$V/bin/python" -m pip install -q "${PKGS[@]}"
fi
"$V/bin/python" -c "import docx, pptx, matplotlib, pymupdf" && echo "$V/bin/python"
