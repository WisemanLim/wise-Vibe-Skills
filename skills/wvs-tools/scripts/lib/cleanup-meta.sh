#!/usr/bin/env bash

set -u

SCRIPT_NAME="$(basename "$0")"

DRY_RUN=false
VERBOSE=false
TEMPORARY=true
ASSUME_YES=false

OUTPUT_ENABLED=false
OUTPUT_FILE=""

TARGET_DIR="."

DIR_PATTERNS=()
FILE_PATTERNS=()
EXCLUDE_PATTERNS=()

MATCHED_FILE_COUNT=0
MATCHED_DIR_COUNT=0
DELETED_FILE_COUNT=0
DELETED_DIR_COUNT=0
FAILED_DELETE_COUNT=0

usage() {
  cat <<'EOF'
Usage:
  cleanup-meta.sh [OPTIONS] [TARGET_DIR]

설명:
  사용자가 지정한 파일/디렉터리 및 OS별 임시 파일/디렉터리를 검색하고 삭제합니다.
  macOS 기본 bash 3.2와 호환됩니다.
Description:
  Search and delete user-specified files/directories and OS-specific temporary files/directories.
  Compatible with macOS default bash 3.2.

인자:
Arguments:
  TARGET_DIR
      검색을 시작할 루트 디렉터리입니다. 기본값: .
      Root directory to search. Default: .

옵션:
Options:
  -D, --directory PATTERN
      삭제할 디렉터리 이름 패턴입니다. 여러 번 지정할 수 있습니다.
      Directory name pattern to delete. Can be repeated.
      Example: -D '@tmp' -D '@eaDir' -D '*yunpantmp*'

  -F, --file PATTERN
      삭제할 파일 이름 패턴입니다. 여러 번 지정할 수 있습니다.
      File name pattern to delete. Can be repeated.
      Example: -F '.DS_Store' -F '*yunpantmp*'

  -E, --exclude PATTERN
      검색/삭제에서 제외할 경로 패턴입니다. 여러 번 지정할 수 있습니다.
      Exclude path pattern from search/deletion. Can be repeated.
      매칭은 전체 경로에 적용됩니다.
      Match is applied to the full path.
      Example: -E '*/node_modules/*' -E '*/.git/*'

  -T, --temporary [BOOL]
      OS별 대표 임시 파일/디렉터리 정리를 활성화합니다.
      Enable OS-specific representative temporary file/directory cleanup.
      기본값: 활성화.
      Default: enabled.
      BOOL을 생략하면 true로 처리됩니다.
      If BOOL is omitted, it is treated as true.
      '-T false' 또는 '--temporary=false'만 비활성화합니다.
      Only '-T false' or '--temporary=false' disables it.

  -O, --output [FILE]
      출력은 항상 로그 파일에 저장됩니다(터미널에도 출력됨).
      Output is ALWAYS saved to a log file (also printed to the terminal).
      이 옵션은 로그 파일 이름을 변경할 때만 사용하세요.
      Use this option only to override the log file name.
      FILE이 주어지면 그대로 사용합니다(예: -O a.log -> a.log).
      If FILE is given, use it (e.g. -O a.log -> a.log).
      FILE이 생략되면(또는 -O 미사용 시) 공백을 '_'로 바꾼 "<target-dir-name>_<timestamp>.log"를 사용합니다.
      If FILE is omitted (or -O not used), use "<target-dir-name>_<timestamp>.log"
      with spaces replaced by '_' (e.g. Samsung_P3_Portable_Media_20260531-150330.log).

  -n, --dry-run
      매칭된 항목만 표시하고 삭제하지 않습니다.
      Show matches only, do not delete.

  -y, --yes
      확인을 묻지 않습니다.
      Do not ask for confirmation.

  -v, --verbose
      상세 출력.
      Verbose output.

  -h, --help
      이 도움말을 표시합니다.
      Show this help.

예시:
Examples:
  cleanup-meta.sh -D '@tmp' -D '@eaDir' -F '.DS_Store' -F '*yunpantmp*'
  cleanup-meta.sh -E '*/.git/*' -E '*/node_modules/*' -D '@tmp' /data/share
  cleanup-meta.sh -T false -D '*yunpantmp*' -F '.DS_Store'
  cleanup-meta.sh --temporary=false --exclude '*/System Volume Information/*' /mnt/usb
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

is_true() {
  case "$(tolower "${1:-true}")" in
    1|true|yes|y|on) return 0 ;;
    *) return 1 ;;
  esac
}

is_false() {
  case "$(tolower "${1:-false}")" in
    0|false|no|n|off) return 0 ;;
    *) return 1 ;;
  esac
}

detect_os() {
  local uname_s
  uname_s="$(uname -s 2>/dev/null || true)"
  case "$uname_s" in
    Darwin) echo "macos" ;;
    Linux) echo "linux" ;;
    MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
    *)
      if [ "${OS:-}" = "Windows_NT" ] || [ -n "${WINDIR:-}" ]; then
        echo "windows"
      else
        echo "unknown"
      fi
      ;;
  esac
}

append_unique() {
  local value="$1"
  shift
  eval "set -- \"\${$1[@]}\""
  local existing
  for existing in "$@"; do
    [ "$existing" = "$value" ] && return 0
  done
  eval "$1+=(\"\$value\")"
}

add_dir_pattern() {
  local existing
  for existing in ${DIR_PATTERNS[@]+"${DIR_PATTERNS[@]}"}; do
    [ "$existing" = "$1" ] && return 0
  done
  DIR_PATTERNS+=("$1")
}

add_file_pattern() {
  local existing
  for existing in ${FILE_PATTERNS[@]+"${FILE_PATTERNS[@]}"}; do
    [ "$existing" = "$1" ] && return 0
  done
  FILE_PATTERNS+=("$1")
}

add_exclude_pattern() {
  local existing
  for existing in ${EXCLUDE_PATTERNS[@]+"${EXCLUDE_PATTERNS[@]}"}; do
    [ "$existing" = "$1" ] && return 0
  done
  EXCLUDE_PATTERNS+=("$1")
}

add_default_temporary_patterns() {
  local os="$1"

  case "$os" in
    macos)
      add_file_pattern ".DS_Store"
      add_file_pattern ".AppleDouble"
      add_file_pattern "._*"
      add_file_pattern ".LSOverride"
      # add_file_pattern "Icon"$'\r'
      add_file_pattern ".apdisk"

      add_dir_pattern ".DS_Store"
      add_dir_pattern ".AppleDouble"
      add_dir_pattern ".Trashes"
      add_dir_pattern ".fseventsd"
      add_dir_pattern "@eaDir"
      add_dir_pattern "@tmp"
      ;;
    linux)
      add_file_pattern "*~"
      add_file_pattern ".~*"
      add_file_pattern ".nfs*"
      add_file_pattern "*.swp"
      add_file_pattern "*.swo"
      add_file_pattern "*.tmp"
      add_file_pattern "*.temp"

      add_dir_pattern ".cache"
      add_dir_pattern "@eaDir"
      add_dir_pattern "@tmp"
      ;;
    windows)
      add_file_pattern "Thumbs.db"
      add_file_pattern "Desktop.ini"
      add_file_pattern "*.tmp"
      add_file_pattern "*.temp"
      add_file_pattern "~*"

      add_dir_pattern "@eaDir"
      add_dir_pattern "@tmp"
      ;;
    *)
      add_file_pattern "*.tmp"
      add_file_pattern "*.temp"
      add_file_pattern "*~"

      add_dir_pattern "@eaDir"
      add_dir_pattern "@tmp"
      ;;
  esac
}

path_excluded() {
  local path="$1"
  local pattern
  [ "${#EXCLUDE_PATTERNS[@]}" -eq 0 ] && return 1
  for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    case "$path" in
      $pattern) return 0 ;;
    esac
  done
  return 1
}

confirm_action() {
  local answer
  if [ "$ASSUME_YES" = "true" ] || [ "$DRY_RUN" = "true" ]; then
    return 0
  fi

  echo "Delete matched files/directories under: $TARGET_DIR"
  echo "Continue? [y/N]"
  read answer
  case "$(tolower "${answer:-n}")" in
    y|yes) return 0 ;;
    *) return 1 ;;
  esac
}

print_summary() {
  echo
  echo "Summary"
  echo "  Matched files      : $MATCHED_FILE_COUNT"
  echo "  Matched directories: $MATCHED_DIR_COUNT"
  echo "  Deleted files      : $DELETED_FILE_COUNT"
  echo "  Deleted directories: $DELETED_DIR_COUNT"
  echo "  Failed deletions   : $FAILED_DELETE_COUNT"
}

on_interrupt() {
  echo
  echo "[ABORTED] $(date +%Y-%m-%d' '%H:%M:%S) interrupted by user"
  print_summary
  exit 130
}

parse_args() {
  while [ $# -gt 0 ]; do
    case "$1" in
      -D)
        [ $# -lt 2 ] && { err "Missing value for -D"; exit 1; }
        add_dir_pattern "$2"
        shift 2
        ;;
      --directory)
        [ $# -lt 2 ] && { err "Missing value for --directory"; exit 1; }
        add_dir_pattern "$2"
        shift 2
        ;;
      --directory=*)
        add_dir_pattern "${1#*=}"
        shift
        ;;
      -F)
        [ $# -lt 2 ] && { err "Missing value for -F"; exit 1; }
        add_file_pattern "$2"
        shift 2
        ;;
      --file)
        [ $# -lt 2 ] && { err "Missing value for --file"; exit 1; }
        add_file_pattern "$2"
        shift 2
        ;;
      --file=*)
        add_file_pattern "${1#*=}"
        shift
        ;;
      -E)
        [ $# -lt 2 ] && { err "Missing value for -E"; exit 1; }
        add_exclude_pattern "$2"
        shift 2
        ;;
      --exclude)
        [ $# -lt 2 ] && { err "Missing value for --exclude"; exit 1; }
        add_exclude_pattern "$2"
        shift 2
        ;;
      --exclude=*)
        add_exclude_pattern "${1#*=}"
        shift
        ;;
      -T)
        if [ $# -ge 2 ]; then
          case "$2" in
            true|false|TRUE|FALSE|yes|no|YES|NO|on|off|ON|OFF|1|0)
              if is_false "$2"; then
                TEMPORARY=false
              else
                TEMPORARY=true
              fi
              shift 2
              ;;
            *)
              TEMPORARY=true
              shift
              ;;
          esac
        else
          TEMPORARY=true
          shift
        fi
        ;;
      --temporary)
        TEMPORARY=true
        shift
        ;;
      --temporary=*)
        if is_false "${1#*=}"; then
          TEMPORARY=false
        else
          TEMPORARY=true
        fi
        shift
        ;;
      -O|--output)
        OUTPUT_ENABLED=true
        if [ $# -ge 2 ]; then
          case "$2" in
            -*)
              shift
              ;;
            *)
              OUTPUT_FILE="$2"
              shift 2
              ;;
          esac
        else
          shift
        fi
        ;;
      --output=*)
        OUTPUT_ENABLED=true
        OUTPUT_FILE="${1#*=}"
        shift
        ;;
      -n|--dry-run)
        DRY_RUN=true
        shift
        ;;
      -y|--yes)
        ASSUME_YES=true
        shift
        ;;
      -v|--verbose)
        VERBOSE=true
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      --)
        shift
        break
        ;;
      -*)
        err "Unknown option: $1"
        usage
        exit 1
        ;;
      *)
        TARGET_DIR="$1"
        shift
        ;;
    esac
  done

  if [ $# -gt 0 ]; then
    TARGET_DIR="$1"
  fi
}

process_file_pattern() {
  local pattern="$1"
  local path

  log "Processing file pattern: $pattern"

  while IFS= read -r -d '' path; do
    if path_excluded "$path"; then
      log "Excluded file: $path"
      continue
    fi

    MATCHED_FILE_COUNT=$((MATCHED_FILE_COUNT + 1))

    if [ "$DRY_RUN" = "true" ]; then
      echo "[DRY-RUN][FILE] $path"
      continue
    fi

    if rm -f -- "$path" 2>/dev/null; then
      echo "[DELETED][FILE] $path"
      DELETED_FILE_COUNT=$((DELETED_FILE_COUNT + 1))
    else
      echo "[FAILED][FILE] $path" >&2
      FAILED_DELETE_COUNT=$((FAILED_DELETE_COUNT + 1))
    fi
  done < <(find "$TARGET_DIR" -type f -name "$pattern" -print0 2>/dev/null)
}

process_dir_pattern() {
  local pattern="$1"
  local path

  log "Processing directory pattern: $pattern"

  while IFS= read -r -d '' path; do
    if path_excluded "$path"; then
      log "Excluded directory: $path"
      continue
    fi

    MATCHED_DIR_COUNT=$((MATCHED_DIR_COUNT + 1))

    if [ "$DRY_RUN" = "true" ]; then
      echo "[DRY-RUN][DIR ] $path"
      continue
    fi

    if rm -rf -- "$path" 2>/dev/null; then
      echo "[DELETED][DIR ] $path"
      DELETED_DIR_COUNT=$((DELETED_DIR_COUNT + 1))
    else
      echo "[FAILED][DIR ] $path" >&2
      FAILED_DELETE_COUNT=$((FAILED_DELETE_COUNT + 1))
    fi
  done < <(find "$TARGET_DIR" -depth -type d -name "$pattern" -print0 2>/dev/null)
}

resolve_output() {
  [ "$OUTPUT_ENABLED" = "true" ] || return 0
  if [ -z "$OUTPUT_FILE" ]; then
    local base name
    base="$TARGET_DIR"
    [ "$base" = "." ] && base="$PWD"
    name="$(basename "$base")"
    name="${name// /_}"
    OUTPUT_FILE="${name}_$(date +%Y%m%d-%H%M%S).log"
  fi
}

run() {
  local os_type
  local p

  trap 'on_interrupt' INT TERM

  echo "[START] $(date +%Y-%m-%d' '%H:%M:%S) target=$TARGET_DIR"

  if [ ! -d "$TARGET_DIR" ]; then
    err "Target directory does not exist: $TARGET_DIR"
    exit 1
  fi

  os_type="$(detect_os)"

  log "Detected OS: $os_type"
  log "Target directory: $TARGET_DIR"
  log "Temporary cleanup enabled: $TEMPORARY"

  if [ "$TEMPORARY" = "true" ]; then
    add_default_temporary_patterns "$os_type"
  fi

  if [ "${#DIR_PATTERNS[@]}" -eq 0 ] && [ "${#FILE_PATTERNS[@]}" -eq 0 ]; then
    err "No patterns specified. Use -D/-F, or use default -T behavior."
    exit 1
  fi

  echo "Configuration"
  echo "  Target directory   : $TARGET_DIR"
  echo "  Detected OS        : $os_type"
  echo "  Temporary cleanup  : $TEMPORARY"
  echo "  Dry run            : $DRY_RUN"
  echo "  Auto confirm       : $ASSUME_YES"
  echo

  if [ "${#EXCLUDE_PATTERNS[@]}" -gt 0 ]; then
    echo "Exclude patterns"
    for p in "${EXCLUDE_PATTERNS[@]}"; do
      echo "  - $p"
    done
    echo
  fi

  if [ "${#FILE_PATTERNS[@]}" -gt 0 ]; then
    echo "File patterns"
    for p in "${FILE_PATTERNS[@]}"; do
      echo "  - $p"
    done
    echo
  fi

  if [ "${#DIR_PATTERNS[@]}" -gt 0 ]; then
    echo "Directory patterns"
    for p in "${DIR_PATTERNS[@]}"; do
      echo "  - $p"
    done
    echo
  fi

  if ! confirm_action; then
    warn "Cancelled by user."
    exit 1
  fi

  for p in "${FILE_PATTERNS[@]}"; do
    process_file_pattern "$p"
  done

  for p in "${DIR_PATTERNS[@]}"; do
    process_dir_pattern "$p"
  done

  print_summary
  echo "[END] $(date +%Y-%m-%d' '%H:%M:%S)"
}

main() {
  parse_args "$@"
  resolve_output

  if [ "$OUTPUT_ENABLED" = "true" ]; then
    if ! : > "$OUTPUT_FILE" 2>/dev/null; then
      err "Cannot create output file: $OUTPUT_FILE"
      exit 1
    fi
    set -o pipefail
    log "Writing output to: $OUTPUT_FILE"
    # tee ignores INT/TERM so it stays alive to flush run's final
    # (e.g. [ABORTED]) output instead of dying first and causing SIGPIPE.
    run 2>&1 | { trap '' INT TERM; exec tee -a "$OUTPUT_FILE"; }
    exit ${PIPESTATUS[0]}
  fi

  run
}

main "$@"