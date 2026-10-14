#!/usr/bin/env bash
# docx/pptx → 같은 폴더·같은 이름의 .pdf (LibreOffice headless). wvs-report
# 파일명에 공백·'+'·'%' 가 있어도 안전하도록 임시 폴더에 복사해 변환한 뒤 되돌려 놓는다.
# 사용: docx2pdf.sh <file.docx|file.pptx> [...]
set -euo pipefail

find_soffice() {
  for c in soffice libreoffice; do command -v "$c" >/dev/null 2>&1 && { command -v "$c"; return; }; done
  for c in "/Applications/LibreOffice.app/Contents/MacOS/soffice" "/usr/lib/libreoffice/program/soffice" \
           "/opt/libreoffice/program/soffice" "/c/Program Files/LibreOffice/program/soffice.exe"; do
    [ -x "$c" ] && { echo "$c"; return; }
  done
  return 1
}

SOFFICE="$(find_soffice)" || {
  echo "ERROR: LibreOffice(soffice) not found. macOS: brew install --cask libreoffice / Debian: sudo apt-get install -y libreoffice-writer libreoffice-impress" >&2
  exit 2
}
[ $# -ge 1 ] || { echo "usage: $0 <file.docx|file.pptx> [...]" >&2; exit 1; }

for src in "$@"; do
  [ -f "$src" ] || { echo "ERROR: not found: $src" >&2; exit 1; }
  abs="$(cd "$(dirname "$src")" && pwd)/$(basename "$src")"
  ext="${abs##*.}"; stem="${abs%.*}"
  td="$(mktemp -d)"; prof="$(mktemp -d)"
  cp "$abs" "$td/in.$ext"
  "$SOFFICE" "-env:UserInstallation=file://$prof" --headless --convert-to pdf --outdir "$td" "$td/in.$ext" >/dev/null 2>&1 || true
  if [ ! -s "$td/in.pdf" ]; then
    echo "ERROR: conversion failed: $abs" >&2; rm -rf "$td" "$prof"; exit 3
  fi
  cp "$td/in.pdf" "$stem.pdf"
  rm -rf "$td" "$prof"
  echo "saved: $stem.pdf ($(du -h "$stem.pdf" | awk '{print $1}'))"
done
