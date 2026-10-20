#!/usr/bin/env bash
# 보고서 빌드용 Python 환경 준비 (wvs-report)
# <assets>/.venv 에 python-docx · python-pptx · matplotlib · pymupdf (+ <assets>/requirements.txt 있으면 그것도) 설치(uv 우선, 없으면 python3 -m venv + pip).
# 이후 빌드: <assets>/.venv/bin/python build.py --pdf
# 사용: setup_env.sh <assets_dir>   (출력: venv python 경로)
set -euo pipefail
A="${1:-.}"
P="$(dirname "$A")"
if [ ! -d "$P" ]; then
  echo "ERROR: output folder '$P' does not exist — decide it with: python3 <wvs-report>/scripts/out_dir.py deep|prd --root <root>" >&2
  echo "       (Miscellaneous-Data / Need-to-be-organized-into-PRD 는 이미 있을 때만 쓴다. 새로 만들지 않는다)" >&2
  exit 4
fi
mkdir -p "$A"; V="$A/.venv"
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
printf '%s\n' "$KIT_DIR" > "$A/.wvs_kit"          # 빌드 템플릿이 툴킷을 찾는 1순위 경로(에이전트·설치 위치와 무관)
PKGS=(python-docx python-pptx matplotlib pymupdf)
[ -f "$A/requirements.txt" ] && PKGS+=(-r "$A/requirements.txt")   # prune_assets.py 가 남긴 동결 버전(재작업 시 같은 환경)
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
