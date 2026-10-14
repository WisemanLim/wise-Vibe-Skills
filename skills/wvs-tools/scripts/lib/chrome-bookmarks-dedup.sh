#!/usr/bin/env bash
#
# chrome-bookmarks-dedup.sh
#   크롬(Chrome) 북마크 JSON 파일에서 중복 URL 북마크를 제거합니다.
#   별도 설치 없이 시스템에 기본 포함된 python3 만으로 동작합니다.
#   폴더 구조는 유지하며 type=url 항목만 중복 검사 대상입니다.
#   Remove duplicate URL bookmarks from a Chrome "Bookmarks" JSON file.
#   Runs with the system's built-in python3 only (no extra install).
#   Folder structure is preserved; only type=url entries are deduplicated.
#   macOS 기본 bash 3.2와 호환됩니다.
#   Compatible with macOS default bash 3.2.
#
set -u

SCRIPT_NAME="$(basename "$0")"

DRY_RUN=false
VERBOSE=false
ASSUME_YES=false

MODE="folder"          # global | folder
KEY="url"              # url | url-title
NORMALIZE=false        # normalize URLs before comparison
IGNORE_CASE=false      # case-insensitive comparison

INPUT_FILE=""
OUTPUT_FILE=""
IN_PLACE=false
BACKUP=true

OUTPUT_ENABLED=false
LOG_FILE=""

PYTHON_CMD=""

usage() {
  cat <<EOF
Usage:
  $SCRIPT_NAME [OPTIONS]

Description:
  크롬 북마크 JSON에서 중복 URL 북마크를 제거합니다. 폴더 구조는 유지하며,
  roots(bookmark_bar, other, synced 등)를 순회하면서 type=url 항목만 검사합니다.
  기본 동작: 원본을 "<input>.original.YYMMDDHHMM"으로 백업한 뒤, 원본 파일을
  직접 정리된 내용으로 교체합니다. (-o/--output 지정 시 그 파일에만 쓰고 원본은
  건드리지 않음. --in-place 는 기존과 동일하게 ".bak" 백업을 사용.)
  Remove duplicate URL bookmarks from a Chrome "Bookmarks" JSON file, preserving
  folder structure. Walks roots (bookmark_bar, other, synced, ...) and only
  inspects type=url entries. Default behavior: back up the original as
  "<input>.original.YYMMDDHHMM", then replace the original file in place with
  the cleaned result. (Use -o/--output to write to a separate file instead,
  leaving the original untouched. --in-place keeps the old ".bak" backup
  naming.)

Options:
  -i, --input FILE
      입력 북마크 파일 경로. 생략하면 OS별 크롬 기본 프로필의 "Bookmarks"를 찾습니다.
      Input bookmarks file. If omitted, the OS-specific Chrome default profile
      "Bookmarks" file is auto-detected.

  -o, --output FILE
      정리된 결과를 저장할 파일. 지정하면 원본은 수정하지 않습니다.
      생략하면 원본을 직접 정리하고, 정리 전 원본은
      "<input>.original.YYMMDDHHMM" 으로 백업합니다.
      --in-place 와 함께 쓰면 무시됩니다.
      Output file for the cleaned result. If given, the original is left
      untouched. If omitted, the original is cleaned in place and backed up
      first as "<input>.original.YYMMDDHHMM". Ignored when --in-place is used.

  -m, --mode MODE
      중복 제거 범위. 기본값: folder.
      Deduplication scope. Default: folder.
        global : 폴더와 무관하게 전체 트리에서 처음 나온 항목만 유지.
                 Keep only the first occurrence across the whole tree.
        folder : 같은 폴더 안에서만 중복 제거(다른 폴더의 같은 URL은 유지).
                 Dedup only within each folder (same URL in other folders kept).

  -k, --key KEY
      중복 판단 기준. 기본값: url.
      Duplicate key. Default: url.
        url       : URL이 같으면 중복.            Same URL => duplicate.
        url-title : URL과 제목이 모두 같을 때만 중복. Same URL AND title => duplicate.

  -N, --normalize
      비교 전 URL을 정규화합니다(끝 슬래시 제거, #프래그먼트 제거, 기본 포트 제거).
      Normalize URLs before comparison (strip trailing slash, #fragment,
      default ports).

  -I, --ignore-case
      비교 시 대소문자를 무시합니다.
      Compare keys case-insensitively.

  -p, --in-place
      새 파일을 만드는 대신 원본을 교체합니다. (--no-backup 가 아니면 .bak 백업 생성)
      안전을 위해 크롬을 먼저 종료하세요.
      Replace the original file instead of writing a new one. Creates a ".bak"
      backup unless --no-backup. Quit Chrome first for safety.

      --no-backup
      --in-place 시 백업(.bak)을 만들지 않습니다.
      Do not create a ".bak" backup when using --in-place.

  -n, --dry-run
      실제 파일을 쓰지 않고 제거될 항목 수와 통계만 출력합니다.
      Show statistics and how many entries would be removed; write nothing.

  -y, --yes
      확인을 묻지 않습니다(--in-place 와 함께 쓸 때 의미 있음).
      Do not ask for confirmation (relevant with --in-place).

  -O, --output-log [FILE]
      모든 출력을 로그 파일에도 저장합니다(터미널에도 출력).
      FILE 생략 시 "<input>_<timestamp>.log" 사용.
      Also save all output to a log file (still printed to the terminal).
      If FILE is omitted, use "<input>_<timestamp>.log".

  -v, --verbose
      상세 출력.  Verbose output.

  -h, --help
      이 도움말 표시.  Show this help.

Examples:
  # 전체 중복 제거(기본), 자동 탐지된 크롬 프로필의 원본을 직접 정리
  # (원본은 <input>.original.YYMMDDHHMM 으로 백업)
  $SCRIPT_NAME

  $SCRIPT_NAME -i ~/Bookmarks -o ~/Bookmarks.cleaned --mode global
  $SCRIPT_NAME -i ~/Bookmarks -o ~/Bookmarks.cleaned --mode folder
  $SCRIPT_NAME -i ~/Bookmarks --mode global --key url-title
  $SCRIPT_NAME -i ~/Bookmarks --normalize --ignore-case -n
  $SCRIPT_NAME -i ~/Bookmarks --in-place -y

Chrome 적용 / Applying to Chrome:
  1) 크롬 종료 / Quit Chrome
  2) 원본 백업 / Back up the original "Bookmarks"
  3) 이 스크립트로 정리 / Clean with this script
  4) 결과를 "Bookmarks" 이름으로 프로필 폴더에 복사 / Copy result as "Bookmarks"
  5) 크롬 재실행 / Restart Chrome
EOF
}

log() {
  if [ "$VERBOSE" = "true" ]; then
    echo "[INFO] $*"
  fi
}

warn() {
  echo "[WARN] $*" >&2
}

err() {
  echo "[ERROR] $*" >&2
}

tolower() {
  echo "$1" | tr '[:upper:]' '[:lower:]'
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

detect_os() {
  case "$(uname -s 2>/dev/null || true)" in
    Darwin) echo "macos" ;;
    Linux) echo "linux" ;;
    *) echo "unknown" ;;
  esac
}

ensure_python() {
  if command_exists python3; then
    PYTHON_CMD="python3"
    return 0
  fi
  if command_exists python; then
    PYTHON_CMD="python"
    return 0
  fi
  err "python3 not found. Install Python 3 and retry."
  return 1
}

# Auto-detect the default Chrome "Bookmarks" file for the current OS/user.
detect_default_bookmarks() {
  local os_type candidates c
  os_type="$(detect_os)"
  candidates=()
  case "$os_type" in
    macos)
      candidates+=("$HOME/Library/Application Support/Google/Chrome/Default/Bookmarks")
      candidates+=("$HOME/Library/Application Support/Google/Chrome/Profile 1/Bookmarks")
      ;;
    linux)
      candidates+=("$HOME/.config/google-chrome/Default/Bookmarks")
      candidates+=("$HOME/.config/chromium/Default/Bookmarks")
      ;;
  esac
  for c in ${candidates[@]+"${candidates[@]}"}; do
    if [ -f "$c" ]; then
      echo "$c"
      return 0
    fi
  done
  return 1
}

confirm_action() {
  local answer
  if [ "$ASSUME_YES" = "true" ] || [ "$DRY_RUN" = "true" ]; then
    return 0
  fi
  if [ "$IN_PLACE" = "true" ]; then
    echo "The original file will be REPLACED: $INPUT_FILE"
    echo "A backup will be created: ${INPUT_FILE}.bak"
    echo "Continue? [y/N]"
    read answer
    case "$(tolower "${answer:-n}")" in
      y|yes) return 0 ;;
      *) return 1 ;;
    esac
  fi
  if [ -z "$OUTPUT_FILE" ]; then
    echo "The original file will be REPLACED: $INPUT_FILE"
    echo "A backup will be created: ${INPUT_FILE}.original.$(date +%y%m%d%H%M)"
    echo "Continue? [y/N]"
    read answer
    case "$(tolower "${answer:-n}")" in
      y|yes) return 0 ;;
      *) return 1 ;;
    esac
  fi
  return 0
}

# The dedup engine: reads input JSON, removes duplicate url entries per the
# mode/key options, writes to output (unless dry-run), and prints a stats
# report. Pure standard-library Python so no install is needed.
run_dedup() {
  local input="$1" output="$2" mode="$3" key="$4" dry="$5"
  local normalize="$6" ignore_case="$7"

  MODE="$mode" KEY="$key" DRY="$dry" NORMALIZE="$normalize" \
  IGNORE_CASE="$ignore_case" IN_FILE="$input" OUT_FILE="$output" \
  "$PYTHON_CMD" - <<'PYEOF'
import json, os, sys
from urllib.parse import urlsplit, urlunsplit

mode        = os.environ["MODE"]
key_mode    = os.environ["KEY"]
dry         = os.environ["DRY"] == "true"
normalize   = os.environ["NORMALIZE"] == "true"
ignore_case = os.environ["IGNORE_CASE"] == "true"
in_file     = os.environ["IN_FILE"]
out_file    = os.environ["OUT_FILE"]

DEFAULT_PORTS = {"http": "80", "https": "443", "ftp": "21"}

def norm_url(u):
    if not normalize:
        return u
    try:
        p = urlsplit(u)
    except Exception:
        return u
    scheme = p.scheme.lower()
    host = p.hostname or ""
    netloc = host
    if p.username:
        cred = p.username
        if p.password:
            cred += ":" + p.password
        netloc = cred + "@" + netloc
    if p.port and DEFAULT_PORTS.get(scheme) != str(p.port):
        netloc += ":" + str(p.port)
    path = p.path.rstrip("/")
    return urlunsplit((scheme, netloc, path, p.query, ""))

def make_key(node):
    url = norm_url(node.get("url", ""))
    if key_mode == "url-title":
        k = url + "\x00" + node.get("name", "")
    else:
        k = url
    if ignore_case:
        k = k.lower()
    return k

stats = {"urls_total": 0, "folders": 0, "removed": 0}

def dedup_children(children, seen):
    """seen: shared set (global mode) or fresh per-folder set (folder mode)."""
    kept = []
    for node in children:
        ntype = node.get("type")
        if ntype == "url":
            stats["urls_total"] += 1
            k = make_key(node)
            if k in seen:
                stats["removed"] += 1
                continue
            seen.add(k)
            kept.append(node)
        elif ntype == "folder":
            stats["folders"] += 1
            child_seen = seen if mode == "global" else set()
            node["children"] = dedup_children(node.get("children", []), child_seen)
            kept.append(node)
        else:
            kept.append(node)
    return kept

try:
    with open(in_file, "r", encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    sys.stderr.write("[ERROR] Input file not found: %s\n" % in_file)
    sys.exit(2)
except (ValueError, OSError) as e:
    sys.stderr.write("[ERROR] Failed to read/parse JSON: %s\n" % e)
    sys.exit(2)

roots = data.get("roots")
if not isinstance(roots, dict):
    sys.stderr.write("[ERROR] Not a Chrome bookmarks file (missing 'roots').\n")
    sys.exit(2)

global_seen = set()
for root_name, root in roots.items():
    if not isinstance(root, dict) or "children" not in root:
        continue
    seen = global_seen if mode == "global" else set()
    root["children"] = dedup_children(root["children"], seen)

print("[STATS] mode=%s key=%s normalize=%s ignore_case=%s"
      % (mode, key_mode, normalize, ignore_case))
print("[STATS] URL bookmarks scanned : %d" % stats["urls_total"])
print("[STATS] Folders scanned       : %d" % stats["folders"])
print("[STATS] Duplicates removed     : %d" % stats["removed"])
print("[STATS] URL bookmarks kept     : %d" % (stats["urls_total"] - stats["removed"]))

if dry:
    print("[DRY-RUN] No file written.")
    sys.exit(0)

# Chrome maintains a "checksum" field; remove it so Chrome re-computes it and
# does not reject/reset the edited file.
data.pop("checksum", None)

try:
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=3)
except OSError as e:
    sys.stderr.write("[ERROR] Failed to write output: %s\n" % e)
    sys.exit(2)

print("[WRITTEN] %s" % out_file)
PYEOF
}

parse_args() {
  while [ $# -gt 0 ]; do
    case "$1" in
      -i|--input)
        [ $# -lt 2 ] && { err "Missing value for $1"; exit 1; }
        INPUT_FILE="$2"; shift 2 ;;
      --input=*) INPUT_FILE="${1#*=}"; shift ;;
      -o|--output)
        [ $# -lt 2 ] && { err "Missing value for $1"; exit 1; }
        OUTPUT_FILE="$2"; shift 2 ;;
      --output=*) OUTPUT_FILE="${1#*=}"; shift ;;
      -m|--mode)
        [ $# -lt 2 ] && { err "Missing value for $1"; exit 1; }
        MODE="$2"; shift 2 ;;
      --mode=*) MODE="${1#*=}"; shift ;;
      -k|--key)
        [ $# -lt 2 ] && { err "Missing value for $1"; exit 1; }
        KEY="$2"; shift 2 ;;
      --key=*) KEY="${1#*=}"; shift ;;
      -N|--normalize) NORMALIZE=true; shift ;;
      -I|--ignore-case) IGNORE_CASE=true; shift ;;
      -p|--in-place) IN_PLACE=true; shift ;;
      --no-backup) BACKUP=false; shift ;;
      -n|--dry-run) DRY_RUN=true; shift ;;
      -y|--yes) ASSUME_YES=true; shift ;;
      -O|--output-log)
        OUTPUT_ENABLED=true
        if [ $# -ge 2 ]; then
          case "$2" in
            -*) shift ;;
            *) LOG_FILE="$2"; shift 2 ;;
          esac
        else
          shift
        fi ;;
      --output-log=*) OUTPUT_ENABLED=true; LOG_FILE="${1#*=}"; shift ;;
      -v|--verbose) VERBOSE=true; shift ;;
      -h|--help) usage; exit 0 ;;
      --) shift; [ $# -gt 0 ] && { INPUT_FILE="$1"; shift; } ;;
      -*) err "Unknown option: $1"; usage; exit 1 ;;
      *)
        if [ -z "$INPUT_FILE" ]; then
          INPUT_FILE="$1"
        else
          err "Unexpected argument: $1"; exit 1
        fi
        shift ;;
    esac
  done
}

validate() {
  case "$MODE" in
    global|folder) ;;
    *) err "Invalid --mode: $MODE (expected: global | folder)"; exit 1 ;;
  esac
  case "$KEY" in
    url|url-title) ;;
    *) err "Invalid --key: $KEY (expected: url | url-title)"; exit 1 ;;
  esac
}

resolve_log() {
  [ "$OUTPUT_ENABLED" = "true" ] || return 0
  if [ -z "$LOG_FILE" ]; then
    local base
    base="$(basename "${INPUT_FILE:-bookmarks}")"
    base="${base// /_}"
    LOG_FILE="${base}_$(date +%Y%m%d-%H%M%S).log"
  fi
}

run() {
  trap 'echo; echo "[ABORTED] interrupted by user"; exit 130' INT TERM

  echo "[START] $(date +%Y-%m-%d' '%H:%M:%S) mode=$MODE key=$KEY dry_run=$DRY_RUN in_place=$IN_PLACE"

  ensure_python || exit 1
  log "Using python: $PYTHON_CMD"

  # Resolve input.
  if [ -z "$INPUT_FILE" ]; then
    if INPUT_FILE="$(detect_default_bookmarks)"; then
      log "Auto-detected bookmarks: $INPUT_FILE"
    else
      err "No --input given and no default Chrome Bookmarks file found."
      exit 1
    fi
  fi
  if [ ! -f "$INPUT_FILE" ]; then
    err "Input file does not exist: $INPUT_FILE"
    exit 1
  fi

  # Resolve output target. Default (no -o, no --in-place) also replaces the
  # original in place, backed up as "<input>.original.YYMMDDHHMM".
  local target_output default_inplace=false backup_ts=""
  if [ "$IN_PLACE" = "true" ]; then
    target_output="$INPUT_FILE"
  elif [ -n "$OUTPUT_FILE" ]; then
    target_output="$OUTPUT_FILE"
  else
    target_output="$INPUT_FILE"
    default_inplace=true
    backup_ts="$(date +%y%m%d%H%M)"
  fi

  echo "Configuration"
  echo "  python             : $PYTHON_CMD"
  echo "  Input              : $INPUT_FILE"
  if [ "$DRY_RUN" = "true" ]; then
    echo "  Output             : (dry-run, none)"
  else
    echo "  Output             : $target_output"
  fi
  echo "  Mode               : $MODE"
  echo "  Key                : $KEY"
  echo "  Normalize URLs     : $NORMALIZE"
  echo "  Ignore case        : $IGNORE_CASE"
  echo "  In-place           : $IN_PLACE"
  [ "$IN_PLACE" = "true" ] && echo "  Backup (.bak)      : $BACKUP"
  if [ "$default_inplace" = "true" ] && [ "$DRY_RUN" != "true" ]; then
    echo "  Backup (.original) : ${INPUT_FILE}.original.${backup_ts}"
  fi
  echo

  if ! confirm_action; then
    warn "Cancelled by user."
    exit 1
  fi

  if [ "$DRY_RUN" = "true" ]; then
    run_dedup "$INPUT_FILE" "$target_output" "$MODE" "$KEY" "true" \
      "$NORMALIZE" "$IGNORE_CASE"
    echo "[END] $(date +%Y-%m-%d' '%H:%M:%S)"
    return 0
  fi

  # In-place: dedup to a temp file first, then back up and swap. This keeps the
  # original intact if the dedup step fails.
  if [ "$IN_PLACE" = "true" ]; then
    local tmp
    tmp="$(mktemp "${TMPDIR:-/tmp}/bm-dedup.XXXXXX")" || { err "mktemp failed"; exit 1; }
    if ! run_dedup "$INPUT_FILE" "$tmp" "$MODE" "$KEY" "false" \
         "$NORMALIZE" "$IGNORE_CASE"; then
      rm -f "$tmp"
      err "Dedup failed; original left untouched."
      exit 1
    fi
    if [ "$BACKUP" = "true" ]; then
      if cp -p "$INPUT_FILE" "${INPUT_FILE}.bak"; then
        echo "[BACKUP] ${INPUT_FILE}.bak"
      else
        rm -f "$tmp"
        err "Backup failed; original left untouched."
        exit 1
      fi
    fi
    if mv "$tmp" "$INPUT_FILE"; then
      echo "[REPLACED] $INPUT_FILE"
    else
      err "Failed to replace original."
      exit 1
    fi
  elif [ "$default_inplace" = "true" ]; then
    local tmp
    tmp="$(mktemp "${TMPDIR:-/tmp}/bm-dedup.XXXXXX")" || { err "mktemp failed"; exit 1; }
    if ! run_dedup "$INPUT_FILE" "$tmp" "$MODE" "$KEY" "false" \
         "$NORMALIZE" "$IGNORE_CASE"; then
      rm -f "$tmp"
      err "Dedup failed; original left untouched."
      exit 1
    fi
    if cp -p "$INPUT_FILE" "${INPUT_FILE}.original.${backup_ts}"; then
      echo "[BACKUP] ${INPUT_FILE}.original.${backup_ts}"
    else
      rm -f "$tmp"
      err "Backup failed; original left untouched."
      exit 1
    fi
    if mv "$tmp" "$INPUT_FILE"; then
      echo "[REPLACED] $INPUT_FILE"
    else
      err "Failed to replace original."
      exit 1
    fi
  else
    if ! run_dedup "$INPUT_FILE" "$target_output" "$MODE" "$KEY" "false" \
         "$NORMALIZE" "$IGNORE_CASE"; then
      err "Dedup failed."
      exit 1
    fi
  fi

  echo "[END] $(date +%Y-%m-%d' '%H:%M:%S)"
}

main() {
  parse_args "$@"
  validate
  resolve_log

  if [ "$OUTPUT_ENABLED" = "true" ]; then
    if ! : > "$LOG_FILE" 2>/dev/null; then
      err "Cannot create log file: $LOG_FILE"
      exit 1
    fi
    set -o pipefail
    log "Writing output to: $LOG_FILE"
    run 2>&1 | { trap '' INT TERM; exec tee -a "$LOG_FILE"; }
    exit ${PIPESTATUS[0]}
  fi

  run
}

main "$@"
