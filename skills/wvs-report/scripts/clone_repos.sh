#!/usr/bin/env bash
# 매핑표(TSV: 분류<TAB>도구<TAB>owner/repo)대로 <root>/<분류>/<도구>/ 에 shallow clone (wvs-report)
# 이미 있으면 건너뛴다(재실행 안전). 결과: <assets>/research/sizes.tsv (분류/도구<TAB>크기)
# 사용: clone_repos.sh <map.tsv> <project_root> [parallel=6]
set -euo pipefail
MAP="$1"; ROOT="$2"; PAR="${3:-6}"
[ -f "$MAP" ] || { echo "usage: $0 <map.tsv> <project_root> [parallel]" >&2; exit 1; }
mkdir -p "$ROOT"
export ROOT
grep -v '^#' "$MAP" | awk -F'\t' 'NF>=3 {print $1"\t"$2"\t"$3}' | while IFS=$'\t' read -r cat name repo; do
  printf '%s\0%s\0%s\0' "$cat" "$name" "$repo"
done | xargs -0 -n 3 -P "$PAR" bash -c '
  cat="$0"; name="$1"; repo="$2"; dst="$ROOT/$cat/$name"
  if [ -d "$dst/.git" ]; then echo "skip  $cat/$name"; exit 0; fi
  mkdir -p "$ROOT/$cat"
  if git clone -q --depth 1 --single-branch "https://github.com/$repo.git" "$dst" 2>/dev/null; then
    echo "ok    $cat/$name ← $repo"
  else
    echo "FAIL  $cat/$name ← $repo" >&2
  fi'
ASSETS="${WVS_ASSETS:-$ROOT/_assets}"; mkdir -p "$ASSETS/research"
: > "$ASSETS/research/sizes.tsv"
grep -v '^#' "$MAP" | awk -F'\t' 'NF>=3 {print $1"\t"$2}' | while IFS=$'\t' read -r cat name; do
  [ -d "$ROOT/$cat/$name" ] && printf '%s/%s\t%s\n' "$cat" "$name" "$(du -sh "$ROOT/$cat/$name" 2>/dev/null | awk '{print $1}')" >> "$ASSETS/research/sizes.tsv"
done
echo "sizes → $ASSETS/research/sizes.tsv"
