#!/usr/bin/env bash
#
# archive-tgz.sh
#   GNU tar(gtar)를 사용하여 하나 이상의 파일/디렉토리로부터 .tar.gz 아카이브를
#   생성합니다. 일반적인 OS/빌드/VCS 임시 파일 및 디렉토리는 제외합니다.
#   Create .tar.gz archives from one or more files/directories using GNU tar
#   (gtar), excluding common OS/build/VCS temporary files and directories.
#   macOS 기본 bash 3.2와 호환됩니다.
#   Compatible with macOS default bash 3.2.
#
set -u

SCRIPT_NAME="$(basename "$0")"

DRY_RUN=false
VERBOSE=false
ASSUME_YES=false
REMOVE=false

SPLIT=false
SPLIT_LABEL=""
SPLIT_BYTES=0
DEFAULT_SPLIT_LABEL="2048m"

ARCHIVE_NAME=""

OUTPUT_ENABLED=false
OUTPUT_FILE=""

TAR_CMD=""

TARGETS=()
EXCLUDE_ARGS=()

MATCHED_COUNT=0
CREATED_COUNT=0
REMOVED_COUNT=0
FAILED_COUNT=0

#######################################
# Temporary / generated files and directories to exclude.
# Edit this array directly to add, change, or remove patterns.
# Used as gtar --exclude patterns (matched by name and as */pattern).
#######################################
EXCLUDE_PATTERNS=(
  # macOS
  ".DS_Store"
  "._*"
  ".AppleDouble"
  ".LSOverride"
  ".Spotlight-V100"
  ".Trashes"
  ".fseventsd"
  ".apdisk"

  # Synology / NAS
  "@eaDir"
  "@tmp"
  ".SynologyWorkingDirectory"
  "#recycle"
  "#snapshot"
  "@Recycle"

  # Windows
  "Thumbs.db"
  "ehthumbs.db"
  "Desktop.ini"
  "\$RECYCLE.BIN"
  "System Volume Information"

  # Node / JS
  "node_modules"
  ".npm"
  ".pnpm-store"
  ".yarn"
  ".yarn-cache"
  ".parcel-cache"
  ".turbo"
  ".next"
  ".nuxt"
  ".svelte-kit"
  ".eslintcache"
  "*.tsbuildinfo"

  # Python
  "__pycache__"
  "*.pyc"
  "*.pyo"
  ".pytest_cache"
  ".mypy_cache"
  ".ruff_cache"
  ".tox"
  ".nox"
  ".venv"
  "venv"

  # Build / coverage / cache
  ".cache"
  "dist"
  "build"
  "coverage"
  ".nyc_output"
  ".gradle"

  # IDE / editor
  ".idea"
  ".vscode"
  "*.swp"
  "*.swo"
  "*~"

  # VCS
  ".git"
  ".svn"
  ".hg"

  # Misc temp / backup
  "*.tmp"
  "*.temp"
  "*.bak"
  "*.old"
  "*.orig"
  ".Trash-*"
)

usage() {
  cat <<EOF
Usage:
  $SCRIPT_NAME [OPTIONS] <target> [target ...]

Description:
  GNU tar(gtar)를 사용하여 각 대상 파일/디렉토리마다 .tar.gz 아카이브를 생성합니다.
  디렉토리는 재귀적으로 아카이브되며, 일반적인 임시/생성 파일은 제외됩니다
  (이 스크립트 내부의 EXCLUDE_PATTERNS 참고). 대상마다 하나의 아카이브가 생성되고,
  대상의 상위 디렉토리에 "<target>.tar.gz" 이름으로 저장됩니다(같은 이름이 이미
  있으면 타임스탬프 접미사가 추가됩니다).
  Create a .tar.gz archive for each target file/directory using GNU tar (gtar).
  Directories are archived recursively, excluding common temporary/generated
  files (see EXCLUDE_PATTERNS inside this script). One archive is produced per
  target, named "<target>.tar.gz" in the target's parent directory (a timestamp
  suffix is added if that name already exists).

Arguments:
  target ...
      아카이브할 하나 이상의 파일 또는 디렉토리.
      One or more files or directories to archive.

Options:
  -R, --remove
      아카이브가 성공적으로 생성된 후 원본 대상을 삭제합니다.
      기본값은 원본 보존.
      Delete the original target after its archive is created successfully.
      Default: keep originals.

  -E, --exclude PATTERN
      추가 제외 패턴을 등록합니다(디렉토리 아카이브에 적용).
      여러 번 반복하여 지정할 수 있습니다.
      Add an extra exclude pattern (applied to directory archives).
      Can be repeated.

  -F, --file NAME
      생성할 아카이브 파일 이름을 지정합니다(단일 대상에만 사용).
      미지정 시 기본값은 "<target>.tar.gz" 입니다.
      ".tar.gz"가 없으면 자동으로 붙습니다(예: -F target 또는 -F target.tar.gz
      모두 target.tar.gz 생성). NAME에 경로가 포함되지 않으면 대상의 상위
      디렉토리에 생성됩니다.
      Set the output archive file name (single target only).
      Defaults to "<target>.tar.gz" if not given.
      ".tar.gz" is appended if missing (so -F target and -F target.tar.gz both
      produce target.tar.gz). If NAME contains no path, it is created in the
      target's parent directory.

  -S, --split [SIZE]
      아카이브를 각각 최대 SIZE 크기의 볼륨으로 분할합니다.
      SIZE는 단위 접미사 k/m/g(1024 기준)를 허용합니다(예: 1024m, 2g).
      SIZE를 생략하면 기본값은 ${DEFAULT_SPLIT_LABEL} 입니다.
      분할 조각은 "<archive>.tar.gz.aa", ".ab", ... 와 같이 이름이 지정됩니다.
      다음 명령으로 재조합합니다.
      Split the archive into volumes of at most SIZE each.
      SIZE accepts a unit suffix: k/m/g (1024-based), e.g. 1024m, 2g.
      If SIZE is omitted, the default is ${DEFAULT_SPLIT_LABEL}.
      Parts are named "<archive>.tar.gz.aa", ".ab", ...
      Reassemble with:  cat <archive>.tar.gz.* | tar -xzf -

  -O, --output [FILE]
      출력은 항상 로그 파일에도 저장됩니다(터미널에도 함께 출력).
      이 옵션은 로그 파일 이름을 변경할 때만 사용합니다.
      FILE을 생략하면(또는 -O를 사용하지 않으면) 공백을 '_'로 바꾼
      "<first-target>_<timestamp>.log" 형식을 사용합니다.
      Output is ALWAYS saved to a log file (also printed to the terminal).
      Use this option only to override the log file name.
      If FILE is omitted (or -O not used), use "<first-target>_<timestamp>.log"
      with spaces replaced by '_'.

  -n, --dry-run
      아카이브/삭제 대상을 미리 보여줍니다. 실제로 아카이브 생성이나 삭제는 하지 않습니다.
      gtar를 자동 설치하지 않습니다.
      Show what would be archived/removed; do not create archives or delete.
      Does not auto-install gtar.

  -y, --yes
      확인을 묻지 않습니다(--remove와 함께 사용할 때만 의미가 있습니다).
      Do not ask for confirmation (only relevant with --remove).

  -v, --verbose
      상세 출력.
      Verbose output.

  -h, --help
      이 도움말을 표시합니다.
      Show this help.

Examples:
  $SCRIPT_NAME mydir
  $SCRIPT_NAME file1.txt dir2 dir3
  $SCRIPT_NAME --remove mydir
  $SCRIPT_NAME -n -v -E '*.iso' /data/share
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

# Parse a size like "1024m", "2g", "512k", "1048576" into a byte count.
# Echoes the byte count on success, returns non-zero on invalid input.
parse_size() {
  local in="$1" num unit
  num="$(echo "$in" | sed -E 's/[^0-9].*$//')"
  unit="$(echo "$in" | sed -E 's/^[0-9]*//')"
  [ -n "$num" ] || return 1
  case "$(tolower "$unit")" in
    ""|b) echo "$num" ;;
    k|kb|kib) echo $((num * 1024)) ;;
    m|mb|mib) echo $((num * 1024 * 1024)) ;;
    g|gb|gib) echo $((num * 1024 * 1024 * 1024)) ;;
    *) return 1 ;;
  esac
}

detect_os() {
  case "$(uname -s 2>/dev/null || true)" in
    Darwin) echo "macos" ;;
    Linux) echo "linux" ;;
    *) echo "unknown" ;;
  esac
}

need_sudo() {
  [ "${EUID:-$(id -u)}" -ne 0 ]
}

run_with_sudo() {
  if need_sudo; then
    sudo "$@"
  else
    "$@"
  fi
}

add_target() {
  TARGETS+=("$1")
}

add_exclude_pattern() {
  local existing
  for existing in ${EXCLUDE_PATTERNS[@]+"${EXCLUDE_PATTERNS[@]}"}; do
    [ "$existing" = "$1" ] && return 0
  done
  EXCLUDE_PATTERNS+=("$1")
}

#######################################
# gtar installation routines, cleanly separated per OS.
#######################################
load_brew_env() {
  if [ -x /opt/homebrew/bin/brew ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [ -x /usr/local/bin/brew ]; then
    eval "$(/usr/local/bin/brew shellenv)"
  elif [ -x /home/linuxbrew/.linuxbrew/bin/brew ]; then
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
  elif [ -x "$HOME/.linuxbrew/bin/brew" ]; then
    eval "$("$HOME/.linuxbrew/bin/brew" shellenv)"
  fi
}

install_homebrew() {
  if command_exists brew; then
    load_brew_env
    return 0
  fi
  log "Homebrew not found. Installing Homebrew."
  NONINTERACTIVE=1 /bin/bash -c \
    "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || return 1
  load_brew_env
  command_exists brew
}

install_gtar_macos() {
  install_homebrew || { err "Homebrew installation failed."; return 1; }
  log "Installing gnu-tar via Homebrew."
  brew install gnu-tar || { err "brew install gnu-tar failed."; return 1; }
  command_exists gtar
}

install_gtar_linux() {
  log "Installing GNU tar via system package manager."
  if command_exists apt-get; then
    run_with_sudo apt-get update -y && run_with_sudo apt-get install -y tar
  elif command_exists dnf; then
    run_with_sudo dnf install -y tar
  elif command_exists yum; then
    run_with_sudo yum install -y tar
  elif command_exists pacman; then
    run_with_sudo pacman -Sy --noconfirm tar
  elif command_exists zypper; then
    run_with_sudo zypper --non-interactive install tar
  elif command_exists apk; then
    run_with_sudo apk add tar
  fi

  if command_exists gtar; then
    return 0
  fi

  # Some distros provide GNU tar only as "tar"; if gtar is required, fall back
  # to Homebrew's gnu-tar which installs the gtar binary.
  warn "gtar not present after native install; trying Homebrew gnu-tar."
  install_homebrew || { err "Homebrew installation failed."; return 1; }
  brew install gnu-tar || { err "brew install gnu-tar failed."; return 1; }
  command_exists gtar
}

# Resolve TAR_CMD. Prefer gtar (GNU tar) for consistent --exclude behavior.
# In dry-run mode, never auto-install: fall back to any available tar for the
# plan output and warn that a real run would install gnu-tar.
ensure_tar() {
  local os_type="$1"

  if command_exists gtar; then
    TAR_CMD="gtar"
    return 0
  fi

  if [ "$DRY_RUN" = "true" ]; then
    if command_exists tar; then
      TAR_CMD="tar"
      warn "gtar not found; dry-run will use 'tar'. A real run would install gnu-tar."
      return 0
    fi
    TAR_CMD="gtar"
    warn "Neither gtar nor tar found; a real run would install gnu-tar."
    return 0
  fi

  case "$os_type" in
    macos) install_gtar_macos ;;
    linux) install_gtar_linux ;;
    *) err "Unsupported OS: $(uname -s)"; return 1 ;;
  esac || return 1

  if command_exists gtar; then
    TAR_CMD="gtar"
    return 0
  fi
  err "gtar is not available after installation."
  return 1
}

build_exclude_args() {
  local pattern
  EXCLUDE_ARGS=()
  for pattern in ${EXCLUDE_PATTERNS[@]+"${EXCLUDE_PATTERNS[@]}"}; do
    EXCLUDE_ARGS+=(--exclude="$pattern")
    EXCLUDE_ARGS+=(--exclude="*/$pattern")
  done
}

confirm_action() {
  local answer
  if [ "$ASSUME_YES" = "true" ] || [ "$DRY_RUN" = "true" ] || [ "$REMOVE" != "true" ]; then
    return 0
  fi
  echo "Originals will be DELETED after successful archiving."
  echo "Continue? [y/N]"
  read answer
  case "$(tolower "${answer:-n}")" in
    y|yes) return 0 ;;
    *) return 1 ;;
  esac
}

create_archive() {
  local target="$1"

  if [ ! -e "$target" ]; then
    err "Target does not exist: $target"
    FAILED_COUNT=$((FAILED_COUNT + 1))
    return 1
  fi

  local abs target_parent name archive_abs exists_path
  abs="$(cd "$(dirname "$target")" 2>/dev/null && pwd)/$(basename "$target")"
  target_parent="$(dirname "$abs")"
  name="$(basename "$abs")"

  # Resolve the output archive path. -F/--file overrides the default
  # "<target>.tar.gz" placed next to the target.
  if [ -n "$ARCHIVE_NAME" ]; then
    local custom="$ARCHIVE_NAME"
    case "$custom" in
      *.tar.gz) ;;
      *) custom="${custom}.tar.gz" ;;
    esac
    case "$custom" in
      */*)
        local cdir cbase
        cdir="$(dirname "$custom")"
        cbase="$(basename "$custom")"
        if [ ! -d "$cdir" ]; then
          err "Output directory does not exist: $cdir"
          FAILED_COUNT=$((FAILED_COUNT + 1))
          return 1
        fi
        archive_abs="$(cd "$cdir" && pwd)/$cbase"
        ;;
      *)
        archive_abs="$target_parent/$custom"
        ;;
    esac
  else
    archive_abs="$target_parent/${name}.tar.gz"
  fi

  if [ "$SPLIT" = "true" ]; then
    exists_path="${archive_abs}.aa"
  else
    exists_path="$archive_abs"
  fi
  if [ -e "$exists_path" ]; then
    archive_abs="${archive_abs%.tar.gz}_$(date +%Y%m%d_%H%M%S).tar.gz"
  fi

  MATCHED_COUNT=$((MATCHED_COUNT + 1))

  if [ "$DRY_RUN" = "true" ]; then
    if [ "$SPLIT" = "true" ]; then
      echo "[DRY-RUN][SPLIT $SPLIT_LABEL] ${archive_abs}.*  <=  $abs"
    else
      echo "[DRY-RUN][ARCHIVE] $archive_abs  <=  $abs"
    fi
    [ "$REMOVE" = "true" ] && echo "[DRY-RUN][REMOVE ] $abs"
    return 0
  fi

  local rc
  if [ -d "$abs" ]; then
    log "Archiving directory: $abs"
  else
    log "Archiving file: $abs"
  fi

  if [ "$SPLIT" = "true" ]; then
    if [ -d "$abs" ]; then
      ( set -o pipefail; cd "$target_parent" && "$TAR_CMD" -czf - ${EXCLUDE_ARGS[@]+"${EXCLUDE_ARGS[@]}"} "$name" | split -b "$SPLIT_BYTES" - "${archive_abs}." )
    else
      ( set -o pipefail; cd "$target_parent" && "$TAR_CMD" -czf - "$name" | split -b "$SPLIT_BYTES" - "${archive_abs}." )
    fi
    rc=$?
  else
    if [ -d "$abs" ]; then
      ( cd "$target_parent" && "$TAR_CMD" -czf "$archive_abs" ${EXCLUDE_ARGS[@]+"${EXCLUDE_ARGS[@]}"} "$name" )
    else
      ( cd "$target_parent" && "$TAR_CMD" -czf "$archive_abs" "$name" )
    fi
    rc=$?
  fi

  if [ $rc -ne 0 ]; then
    echo "[FAILED][ARCHIVE] $archive_abs" >&2
    FAILED_COUNT=$((FAILED_COUNT + 1))
    return 1
  fi

  if [ "$SPLIT" = "true" ]; then
    echo "[CREATED][ARCHIVE] ${archive_abs}.* (split $SPLIT_LABEL)"
    local part
    for part in "${archive_abs}."*; do
      [ -e "$part" ] || continue
      echo "[PART] $part"
    done
  else
    echo "[CREATED][ARCHIVE] $archive_abs"
  fi
  CREATED_COUNT=$((CREATED_COUNT + 1))

  print_extract_guide "$archive_abs" "$SPLIT"

  if [ "$REMOVE" = "true" ]; then
    if rm -rf -- "$abs" 2>/dev/null; then
      echo "[REMOVED][SOURCE] $abs"
      REMOVED_COUNT=$((REMOVED_COUNT + 1))
    else
      echo "[FAILED][REMOVE] $abs" >&2
      FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
  fi
}

print_extract_guide() {
  local arch="$1" split_flag="$2"
  local x="$TAR_CMD"

  echo
  echo "  ── 압축 해제 가이드 / Extraction guide ──"
  if [ "$split_flag" = "true" ]; then
    echo "     분할 아카이브입니다. 조각을 합쳐서 풀어야 합니다."
    echo "     This is a split archive; reassemble the parts to extract."
    echo
    echo "     # 바로 풀기 (합치며 추출) / extract directly (concatenate + extract):"
    echo "       cat \"${arch}.\"* | $x -xzf -"
    echo
    echo "     # 내용 목록만 보기 / list contents only:"
    echo "       cat \"${arch}.\"* | $x -tzf -"
    echo
    echo "     # 먼저 하나의 파일로 합친 뒤 풀기 / merge into one file first, then extract:"
    echo "       cat \"${arch}.\"* > \"$arch\" && $x -xzf \"$arch\""
  else
    echo "     # 현재 위치에 풀기 / extract here:"
    echo "       $x -xzf \"$arch\""
    echo
    echo "     # 특정 디렉토리에 풀기 / extract into a directory:"
    echo "       $x -xzf \"$arch\" -C /path/to/dest"
    echo
    echo "     # 내용 목록만 보기 / list contents only:"
    echo "       $x -tzf \"$arch\""
  fi
  echo
  echo "     참고: macOS에서는 gtar(GNU tar) 또는 기본 tar 모두 .tar.gz 추출이 가능합니다."
  echo "           Linux에서는 보통 tar 가 GNU tar 입니다."
  echo "     Note: on macOS, either gtar (GNU tar) or the default tar can extract .tar.gz;"
  echo "           on Linux, 'tar' is usually GNU tar."
  echo
}

print_summary() {
  echo
  echo "Summary"
  echo "  Targets processed  : $MATCHED_COUNT"
  echo "  Archives created   : $CREATED_COUNT"
  echo "  Sources removed    : $REMOVED_COUNT"
  echo "  Failures           : $FAILED_COUNT"
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
      -R|--remove)
        REMOVE=true
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
      -F)
        [ $# -lt 2 ] && { err "Missing value for -F"; exit 1; }
        ARCHIVE_NAME="$2"
        shift 2
        ;;
      --file)
        [ $# -lt 2 ] && { err "Missing value for --file"; exit 1; }
        ARCHIVE_NAME="$2"
        shift 2
        ;;
      --file=*)
        ARCHIVE_NAME="${1#*=}"
        shift
        ;;
      -S|--split)
        SPLIT=true
        if [ $# -ge 2 ] && parse_size "$2" >/dev/null 2>&1; then
          SPLIT_LABEL="$2"
          shift 2
        else
          shift
        fi
        ;;
      --split=*)
        SPLIT=true
        SPLIT_LABEL="${1#*=}"
        shift
        ;;
      -O|--output)
        OUTPUT_ENABLED=true
        if [ $# -ge 2 ]; then
          case "$2" in
            -*) shift ;;
            *) OUTPUT_FILE="$2"; shift 2 ;;
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
        while [ $# -gt 0 ]; do add_target "$1"; shift; done
        ;;
      -*)
        err "Unknown option: $1"
        usage
        exit 1
        ;;
      *)
        add_target "$1"
        shift
        ;;
    esac
  done
}

resolve_output() {
  [ "$OUTPUT_ENABLED" = "true" ] || return 0
  if [ -z "$OUTPUT_FILE" ]; then
    local base name
    if [ "${#TARGETS[@]}" -gt 0 ]; then
      base="${TARGETS[0]}"
    else
      base="archive"
    fi
    name="$(basename "$base")"
    name="${name// /_}"
    OUTPUT_FILE="${name}_$(date +%Y%m%d-%H%M%S).log"
  fi
}

run() {
  local os_type t

  trap 'on_interrupt' INT TERM

  echo "[START] $(date +%Y-%m-%d' '%H:%M:%S) targets=${#TARGETS[@]} remove=$REMOVE dry_run=$DRY_RUN"

  if [ "${#TARGETS[@]}" -eq 0 ]; then
    err "No targets specified."
    usage
    exit 1
  fi

  if [ -n "$ARCHIVE_NAME" ] && [ "${#TARGETS[@]}" -gt 1 ]; then
    err "-F/--file can only be used with a single target."
    exit 1
  fi

  os_type="$(detect_os)"
  log "Detected OS: $os_type"

  if ! ensure_tar "$os_type"; then
    exit 1
  fi
  log "Using tar command: $TAR_CMD"

  if [ "$SPLIT" = "true" ]; then
    [ -z "$SPLIT_LABEL" ] && SPLIT_LABEL="$DEFAULT_SPLIT_LABEL"
    SPLIT_BYTES="$(parse_size "$SPLIT_LABEL")" || { err "Invalid split size: $SPLIT_LABEL"; exit 1; }
    if ! command_exists split; then
      err "'split' command not found; cannot split archives."
      exit 1
    fi
  fi

  build_exclude_args

  echo "Configuration"
  echo "  tar command        : $TAR_CMD"
  echo "  Targets            : ${#TARGETS[@]}"
  echo "  Remove originals   : $REMOVE"
  echo "  Dry run            : $DRY_RUN"
  echo "  Exclude patterns   : ${#EXCLUDE_PATTERNS[@]}"
  if [ "$SPLIT" = "true" ]; then
    echo "  Split volumes      : $SPLIT_LABEL ($SPLIT_BYTES bytes)"
  fi
  echo

  if ! confirm_action; then
    warn "Cancelled by user."
    exit 1
  fi

  for t in "${TARGETS[@]}"; do
    create_archive "$t"
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
