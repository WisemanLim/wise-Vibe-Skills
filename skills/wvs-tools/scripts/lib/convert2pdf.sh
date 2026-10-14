#!/usr/bin/env bash
# convert2pdf.sh — Mermaid가 렌더링된 Markdown을 PDF로 변환 (Eden-MultiAIOS 툴체인)
# convert2pdf.sh — Mermaid-rendered Markdown → PDF (Eden-MultiAIOS toolchain)
#
# 파이프라인:
# Pipeline:
#   1. ```mermaid``` 블록 추출 → diagrams/dNN.mmd
#   1. Extract ```mermaid``` blocks → diagrams/dNN.mmd
#   2. @mermaid-js/mermaid-cli (mmdc)로 각 .mmd → .png 렌더링.
#   2. Render each .mmd → .png via @mermaid-js/mermaid-cli (mmdc).
#      블록 렌더링이 실패하면 원본 코드를 펜스 블록으로 유지하여
#      다이어그램 하나가 잘못되어도 파이프라인이 중단되지 않음.
#      If a block fails to render, the original code is kept as a fenced
#      block so the pipeline never aborts on a single bad diagram.
#   3. 이미지 참조(또는 폴백 블록)가 포함된 `<input>.rendered.md` 생성
#   3. Emit `<input>.rendered.md` with image references (or fallback blocks)
#   4. pandoc + xelatex → PDF (Noto Sans CJK KR)
#   4. pandoc + xelatex → PDF (Noto Sans CJK KR)
#   5. 선택적 --cleanup 옵션으로 중간 산출물 제거
#   5. Optional --cleanup removes intermediates
#
# 사용법:
# Usage:
#   ./convert2pdf.sh -I REPORT.md
#   ./convert2pdf.sh --input docs/spec.md --cleanup
#
# 종료 코드:
# Exit codes:
#   0 성공 · 1 사용자 오류 · 2 의존성 누락 · 3 파이프라인 실패
#   0 success · 1 user error · 2 missing dependency · 3 pipeline failure

set -euo pipefail

# ---------- defaults ----------
INPUT=""
CLEANUP=false

# ---------- arg parsing ----------
usage() {
  cat <<'USAGE'
사용법: convert2pdf.sh -I <input.md> [-C|--cleanup]
Usage: convert2pdf.sh -I <input.md> [-C|--cleanup]

  -I, --input <FILE>   변환할 Markdown 파일. PDF는 동일한 디렉터리에
                       동일한 기본 이름으로 저장됨.
  -I, --input <FILE>   Markdown file to convert. PDF is written to the same
                       directory with the same base name.
  -C, --cleanup        PDF 생성 후 생성된 `diagrams/` 폴더와 중간
                       산출물 `<input>.rendered.md`를 제거.
  -C, --cleanup        Remove the generated `diagrams/` folder and the
                       intermediate `<input>.rendered.md` after the PDF is
                       produced.
  -h, --help           이 메시지를 표시.
  -h, --help           Show this message.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -I|--input)
      [[ $# -ge 2 ]] || { echo "ERROR: $1 requires a value" >&2; usage; exit 1; }
      INPUT="$2"; shift 2 ;;
    -C|--cleanup)
      CLEANUP=true; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "ERROR: unknown argument: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "${INPUT}" ]]; then
  echo "ERROR: --input is required." >&2
  usage
  exit 1
fi
if [[ ! -f "${INPUT}" ]]; then
  echo "ERROR: input file not found: ${INPUT}" >&2
  exit 1
fi

# Normalise paths.
INPUT_ABS="$(cd "$(dirname "${INPUT}")" && pwd)/$(basename "${INPUT}")"
WORK_DIR="$(dirname "${INPUT_ABS}")"
STEM="$(basename "${INPUT_ABS}" .md)"
RENDERED_MD="${WORK_DIR}/${STEM}.rendered.md"
OUTPUT_PDF="${WORK_DIR}/${STEM}.pdf"
DIAGRAMS_DIR="${WORK_DIR}/diagrams"

# ---------- dependency probes ----------
# xelatex may live outside the default PATH on macOS TeX installs.
if ! command -v xelatex >/dev/null 2>&1; then
  for candidate in /Library/TeX/texbin /usr/local/texlive/*/bin/*; do
    [[ -x "${candidate}/xelatex" ]] && export PATH="${candidate}:${PATH}"
  done
fi

require() {
  local name="$1"; local hint="$2"
  if ! command -v "${name}" >/dev/null 2>&1; then
    echo "ERROR: required tool '${name}' is missing. ${hint}" >&2
    exit 2
  fi
}

require pandoc  "Install with 'brew install pandoc'."
require xelatex "Install with 'brew install --cask basictex' then 'sudo tlmgr install collection-xetex collection-fontsrecommended'."
require mmdc    "Install with 'npm i -g @mermaid-js/mermaid-cli'."
require python3 "macOS ships python3 by default. Check 'xcode-select --install'."

# Noto CJK KR font check (warn only; pandoc will fail clearly otherwise).
if command -v fc-list >/dev/null 2>&1; then
  if ! fc-list | grep -qi "Noto Sans CJK KR"; then
    echo "WARN: Noto Sans CJK KR not detected. 'brew install --cask font-noto-sans-cjk' recommended." >&2
  fi
fi

# ---------- 1+2. extract + render mermaid blocks (single python pass) ----------
mkdir -p "${DIAGRAMS_DIR}"
export DIAGRAMS_DIR  # consumed by the embedded Python below

python3 - "${INPUT_ABS}" "${RENDERED_MD}" "${DIAGRAMS_DIR}" <<'PY'
import os, pathlib, re, subprocess, sys

src_path, dst_path, diag_dir = map(pathlib.Path, sys.argv[1:4])
src = src_path.read_text(encoding="utf-8")
diag_dir.mkdir(parents=True, exist_ok=True)

count = {"ok": 0, "fail": 0}

def repl(m):
    code = m.group(1)
    n = count["ok"] + count["fail"] + 1
    mmd = diag_dir / f"d{n:02d}.mmd"
    mmd.write_text(code, encoding="utf-8")
    png = mmd.with_suffix(".png")
    try:
        subprocess.run(
            ["mmdc", "-i", str(mmd), "-o", str(png), "-b", "white", "-w", "1600"],
            check=True, capture_output=True, text=True,
        )
        count["ok"] += 1
        rel = png.relative_to(dst_path.parent)
        return f"\n![diagram {n}]({rel})\n"
    except subprocess.CalledProcessError as exc:
        count["fail"] += 1
        err_tail = (exc.stderr or "").strip().splitlines()[-1:] or ["mmdc failed"]
        print(f"  WARN: diagram {n} render failed ({err_tail[0]}); embedding source.", file=sys.stderr)
        # Re-emit as a fenced code block so pandoc renders the original text.
        return "\n```text\n" + code.rstrip() + "\n```\n"

new = re.sub(r"```mermaid\n(.*?)```", repl, src, flags=re.S)
dst_path.write_text(new, encoding="utf-8")
print(f"  rendered ok={count['ok']} failed={count['fail']} into {diag_dir}")
PY

# ---------- 3. pandoc → PDF ----------
echo "pandoc → ${OUTPUT_PDF}"
# pandoc's default `Shaded` env requires framed.sty; basictex ships listings.sty
# instead. Switch to --listings when framed is missing so code blocks still
# render without needing an extra `tlmgr install framed`.
PANDOC_FLAGS=(
  --pdf-engine=xelatex
  -V mainfont="Noto Sans CJK KR"
  -V monofont="Noto Sans Mono CJK KR"
  -V geometry:margin=20mm
  -V linkcolor=blue
  --resource-path="${WORK_DIR}"
)
if command -v kpsewhich >/dev/null 2>&1 && ! kpsewhich framed.sty >/dev/null 2>&1; then
  if kpsewhich listings.sty >/dev/null 2>&1; then
    PANDOC_FLAGS+=(--listings)
  else
    echo "WARN: neither framed.sty nor listings.sty found." >&2
    echo "      Install with: sudo tlmgr install framed listings" >&2
  fi
fi

pandoc "${RENDERED_MD}" -o "${OUTPUT_PDF}" "${PANDOC_FLAGS[@]}" \
  || { echo "ERROR: pandoc failed." >&2; exit 3; }

if [[ ! -s "${OUTPUT_PDF}" ]]; then
  echo "ERROR: PDF was not produced." >&2
  exit 3
fi

echo "✓ PDF: ${OUTPUT_PDF} ($(du -h "${OUTPUT_PDF}" | awk '{print $1}'))"

# ---------- 4. cleanup ----------
if [[ "${CLEANUP}" == true ]]; then
  echo "cleanup → removing ${RENDERED_MD} and ${DIAGRAMS_DIR}"
  rm -f "${RENDERED_MD}"
  rm -rf "${DIAGRAMS_DIR}"
fi

exit 0
