#!/usr/bin/env bash
{ # Truncation guard: bash reads the whole brace group before running anything, so a partial `curl | bash` download fails to parse instead of half-running.
set -euo pipefail

# wise-Vibe-Skills installer — skills: wvs-review (repo review, levels) · wvs-report (repos/deep/prd reports) · wvs-tools (wvs CLI)
#   curl -fsSL https://raw.githubusercontent.com/WisemanLim/wise-Vibe-Skills/main/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/WisemanLim/wise-Vibe-Skills/main/install.sh | bash -s -- --client claude-code,codex
#   ./install.sh --list | --dry-run | --uninstall | --scope project | --desktop-zip | --bin-dir ~/.local/bin
# Skill roots follow the client registry used by REA (github.com/morluto/rea, SupportedClients.ts):
#   Claude Code → ${CLAUDE_CONFIG_DIR:-~/.claude}/skills · Antigravity → ~/.gemini/config/skills · Gemini CLI → ${GEMINI_CLI_HOME:-~}/.agents/skills
#   Codex · Cursor · Windsurf · Devin · OpenCode · Copilot CLI · Command Code · Grok Build · OMP · VS Code → ~/.agents/skills (shared)
#   Claude Desktop → per-skill .zip for Settings › Capabilities › Skills upload (+ ~/.claude/skills for its Code tab)

REPO="${WVS_REPO:-WisemanLim/wise-Vibe-Skills}"
REF="${WVS_REF:-main}"
MARKER=".wise-vibe-skills"
# v0.1 skill names, superseded by wvs-* — removed on install when they carry our marker
LEGACY_SKILLS="analysis-source in-depth-review create-guide4junior code-review-by-levels totally-analysis-based-on-star convert-to-pdf ref-sh oss-clone-analysis attachment-deep-analysis requirement-based-prd wise-report-kit"
CLIENT_IDS="claude-code claude-desktop codex cursor gemini-cli windsurf devin opencode antigravity copilot-cli commandcode grok-build omp vscode"

clients="detected"; scope="user"; custom_dir=""; skills_sel="all"; mode="copy"; action="install"
dry_run=false; force=false; assume_yes=false; source_dir=""; zip_dir=""; bin_dir=""

say()  { printf '%s\n' "$*"; }
warn() { printf 'warn: %s\n' "$*" >&2; }
die()  { printf 'wise-Vibe-Skills install failed: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<'EOF'
Usage: install.sh [options]

Install the wise-Vibe-Skills skill set (SKILL.md folders) for coding agents.

Options
  --client <ids>     Comma list, "all" or "detected" (default). IDs:
                     claude-code claude-desktop codex cursor gemini-cli windsurf devin opencode
                     antigravity copilot-cli commandcode grok-build omp vscode
  --scope <s>        user (default, personal skill dirs) | project (./.claude/skills + ./.agents/skills)
  --dir <path>       Install into this skills root instead of client defaults
  --skills <list>    Comma list: wvs-review,wvs-report,wvs-tools (default: all)
  --link             Symlink from a local checkout instead of copying (development)
  --ref <git-ref>    Branch/tag to download (default: main, or $WVS_REF)
  --source <path>    Use a local checkout (default: this script's directory when it contains skills/)
  --desktop-zip [d]  Also build per-skill zips for Claude Desktop upload (default dir: ~/Downloads/wise-vibe-skills-desktop)
  --bin-dir <dir>    Also link the `wvs` tool CLI into <dir> (e.g. ~/.local/bin) — needs wvs-tools
  --force            Overwrite skill folders that were not installed by this installer
  --dry-run          Print the plan only
  --uninstall        Remove skills installed by this installer from the selected destinations
  --list             List skills, clients, detection status and destinations
  -y, --yes          Do not prompt
  -h, --help         Show this help
EOF
}

# ---------------------------------------------------------------- client registry
client_name() {
  case "$1" in
    claude-code) echo "Claude Code" ;; claude-desktop) echo "Claude Desktop" ;; codex) echo "Codex" ;;
    cursor) echo "Cursor" ;; gemini-cli) echo "Gemini CLI" ;; windsurf) echo "Windsurf" ;; devin) echo "Devin" ;;
    opencode) echo "OpenCode" ;; antigravity) echo "Antigravity" ;; copilot-cli) echo "GitHub Copilot CLI" ;;
    commandcode) echo "Command Code" ;; grok-build) echo "Grok Build" ;; omp) echo "OMP" ;; vscode) echo "VS Code" ;;
    *) return 1 ;;
  esac
}

has_cmd() { command -v "$1" >/dev/null 2>&1; }
has_dir() { [ -d "$1" ]; }

client_detected() {
  local h="$HOME" cfg="${XDG_CONFIG_HOME:-$HOME/.config}"
  case "$1" in
    claude-code)    has_cmd claude || has_dir "${CLAUDE_CONFIG_DIR:-$h/.claude}" ;;
    claude-desktop) has_dir "/Applications/Claude.app" || has_dir "$h/Library/Application Support/Claude" || has_dir "$cfg/Claude" || { [ -n "${APPDATA:-}" ] && has_dir "$APPDATA/Claude"; } ;;
    codex)          has_cmd codex || has_dir "${CODEX_HOME:-$h/.codex}" ;;
    cursor)         has_cmd cursor || has_cmd cursor-agent || has_dir "$h/.cursor" ;;
    gemini-cli)     has_cmd gemini || has_dir "${GEMINI_CLI_HOME:-$h}/.gemini" ;;
    windsurf)       has_cmd windsurf || has_dir "$h/.codeium/windsurf" ;;
    devin)          has_cmd devin || has_dir "$cfg/devin" ;;
    opencode)       has_cmd opencode || has_dir "$cfg/opencode" ;;
    antigravity)    has_cmd antigravity || has_dir "/Applications/Antigravity.app" || has_dir "$h/.gemini/antigravity" ;;
    copilot-cli)    has_cmd copilot || has_dir "$h/.copilot" ;;
    commandcode)    has_cmd commandcode || has_cmd command-code || has_dir "$h/.commandcode" ;;
    grok-build)     has_cmd grok || has_dir "${GROK_HOME:-$h/.grok}" ;;
    omp)            has_cmd omp || has_dir "$h/.omp" ;;
    vscode)         has_cmd code || has_dir "$h/.vscode" ;;
    *) return 1 ;;
  esac
}

# skills root for a client in the current scope ("" = no directory install, e.g. Claude Desktop zip-only)
client_root() {
  local id="$1"
  if [ "$scope" = "project" ]; then
    case "$id" in
      claude-code) echo "$PWD/.claude/skills" ;;
      claude-desktop) echo "" ;;
      *) echo "$PWD/.agents/skills" ;;
    esac
    return
  fi
  case "$id" in
    claude-code)    echo "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills" ;;
    claude-desktop) echo "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills" ;;   # Code tab shares Claude Code skills; chat uses the zips
    gemini-cli)     echo "${GEMINI_CLI_HOME:-$HOME}/.agents/skills" ;;
    antigravity)    echo "$HOME/.gemini/config/skills" ;;
    *)              echo "$HOME/.agents/skills" ;;
  esac
}

# ---------------------------------------------------------------- args
while [ $# -gt 0 ]; do
  case "$1" in
    --client) [ $# -ge 2 ] || die "--client needs a value"; clients="$2"; shift 2 ;;
    --client=*) clients="${1#*=}"; shift ;;
    --scope) [ $# -ge 2 ] || die "--scope needs a value"; scope="$2"; shift 2 ;;
    --scope=*) scope="${1#*=}"; shift ;;
    --dir) [ $# -ge 2 ] || die "--dir needs a value"; custom_dir="$2"; shift 2 ;;
    --dir=*) custom_dir="${1#*=}"; shift ;;
    --skills) [ $# -ge 2 ] || die "--skills needs a value"; skills_sel="$2"; shift 2 ;;
    --skills=*) skills_sel="${1#*=}"; shift ;;
    --link) mode="link"; shift ;;
    --ref) [ $# -ge 2 ] || die "--ref needs a value"; REF="$2"; shift 2 ;;
    --ref=*) REF="${1#*=}"; shift ;;
    --source) [ $# -ge 2 ] || die "--source needs a value"; source_dir="$2"; shift 2 ;;
    --source=*) source_dir="${1#*=}"; shift ;;
    --desktop-zip) zip_dir="$HOME/Downloads/wise-vibe-skills-desktop"; if [ $# -ge 2 ] && [ "${2#-}" = "$2" ]; then zip_dir="$2"; shift; fi; shift ;;
    --bin-dir) [ $# -ge 2 ] || die "--bin-dir needs a value"; bin_dir="$2"; shift 2 ;;
    --bin-dir=*) bin_dir="${1#*=}"; shift ;;
    --force) force=true; shift ;;
    --dry-run) dry_run=true; shift ;;
    --uninstall) action="uninstall"; shift ;;
    --list) action="list"; shift ;;
    -y|--yes) assume_yes=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown option: $1 (see --help)" ;;
  esac
done
case "$scope" in user|project) ;; *) die "--scope must be user or project" ;; esac

# ---------------------------------------------------------------- source
cleanup_tmp=""
trap '[ -n "$cleanup_tmp" ] && rm -rf "$cleanup_tmp"' EXIT

resolve_source() {
  if [ -n "$source_dir" ]; then
    [ -d "$source_dir/skills" ] || die "--source $source_dir has no skills/ directory"
    source_dir="$(cd "$source_dir" && pwd)"; return
  fi
  local here=""
  if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; fi
  if [ -n "$here" ] && [ -d "$here/skills" ]; then source_dir="$here"; return; fi
  [ "$mode" = "link" ] && die "--link needs a local checkout (--source)"
  cleanup_tmp="$(mktemp -d)"
  say "downloading $REPO@$REF ..."
  if curl -fsSL --proto '=https' --tlsv1.2 --retry 3 "https://codeload.github.com/$REPO/tar.gz/$REF" | tar -xz -C "$cleanup_tmp" 2>/dev/null; then :
  elif has_cmd gh && gh api "repos/$REPO/tarball/$REF" > "$cleanup_tmp/src.tgz" 2>/dev/null && tar -xzf "$cleanup_tmp/src.tgz" -C "$cleanup_tmp"; then :   # private repo via gh auth
  elif has_cmd git && git clone -q --depth 1 --branch "$REF" "https://github.com/$REPO.git" "$cleanup_tmp/repo" 2>/dev/null; then :
  else die "could not download $REPO@$REF (check network, --ref, or gh auth for a private repo)"; fi
  local d; source_dir=""
  for d in "$cleanup_tmp"/*/; do [ -d "${d}skills" ] && { source_dir="${d%/}"; break; }; done
  [ -n "$source_dir" ] || die "downloaded archive has no skills/ directory"
}

all_skills() { local d; for d in "$source_dir"/skills/*/; do [ -f "$d/SKILL.md" ] && basename "$d"; done; }

selected_skills() {
  if [ "$skills_sel" = "all" ]; then all_skills; return; fi
  local s out=""
  for s in $(printf '%s' "$skills_sel" | tr ',' ' '); do
    [ -f "$source_dir/skills/$s/SKILL.md" ] || die "unknown skill: $s (try --list)"
    out="$out $s"
  done
  printf '%s\n' $out
}

selected_clients() {
  local c out=""
  case "$clients" in
    all) out="$CLIENT_IDS" ;;
    detected)
      for c in $CLIENT_IDS; do client_detected "$c" && out="$out $c"; done
      [ -n "$out" ] || out="claude-code codex"   # nothing detected: Claude Code dir + shared ~/.agents/skills
      ;;
    *) for c in $(printf '%s' "$clients" | tr ',' ' '); do client_name "$c" >/dev/null || die "unknown client: $c (try --list)"; out="$out $c"; done ;;
  esac
  printf '%s\n' $out
}

# unique destination roots for the selected clients
destinations() {
  if [ -n "$custom_dir" ]; then echo "$custom_dir"; return; fi
  local c r seen=""
  for c in $(selected_clients); do
    r="$(client_root "$c")"; [ -n "$r" ] || continue
    case " $seen " in *" $r "*) ;; *) seen="$seen $r"; echo "$r" ;; esac
  done
}

version_of() { [ -f "$source_dir/VERSION" ] && tr -d ' \n' < "$source_dir/VERSION" || echo "0.0.0"; }

confirm() {
  $assume_yes && return 0
  [ -r /dev/tty ] || return 0          # non-interactive (curl | bash without tty): proceed
  printf '%s [Y/n] ' "$1" > /dev/tty; local a; read -r a < /dev/tty || a=""
  case "$a" in n|N|no|NO) return 1 ;; *) return 0 ;; esac
}

# ---------------------------------------------------------------- actions
do_list() {
  say "wise-Vibe-Skills $(version_of) — source: $source_dir"
  say ""; say "Skills:"
  local s; for s in $(all_skills); do say "  - $s"; done
  say ""; say "Clients (scope=$scope):"
  local c st; for c in $CLIENT_IDS; do
    if client_detected "$c"; then st="detected"; else st="-"; fi
    printf '  %-15s %-20s %-9s %s\n' "$c" "$(client_name "$c")" "$st" "$(client_root "$c")"
  done
}

install_one() {   # $1 skill $2 root
  local s="$1" root="$2" dst="$2/$1"
  if [ -e "$dst" ] && [ ! -f "$dst/$MARKER" ] && [ ! -L "$dst" ] && ! $force; then
    warn "skip $dst (exists, not installed by wise-Vibe-Skills; use --force)"; return
  fi
  if $dry_run; then say "  would $mode $s → $dst"; return; fi
  mkdir -p "$root"
  rm -rf "$dst"
  if [ "$mode" = "link" ]; then
    ln -s "$source_dir/skills/$s" "$dst"
  else
    cp -R "$source_dir/skills/$s" "$dst"
    find "$dst" \( -name '.DS_Store' -o -name '__pycache__' -o -name '.venv' \) -prune -exec rm -rf {} + 2>/dev/null || true
    printf 'name=%s\nversion=%s\nsource=%s@%s\ninstalled=%s\n' "$s" "$(version_of)" "$REPO" "$REF" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$dst/$MARKER"
  fi
  say "  ✓ $s → $dst"
}

uninstall_root() {
  local root="$1" d n=0
  [ -d "$root" ] || return 0
  for d in "$root"/*/; do
    d="${d%/}"
    if [ -f "$d/$MARKER" ] || { [ -L "$d" ] && case "$(readlink "$d")" in *wise-Vibe-Skills*|*wise-vibe-skills*) true ;; *) false ;; esac; }; then
      if $dry_run; then say "  would remove $d"; else rm -rf "$d"; say "  ✗ removed $d"; fi
      n=$((n + 1))
    fi
  done
  [ "$n" -gt 0 ] || say "  (nothing installed in $root)"
}

build_zips() {
  local dir="$1" s
  has_cmd zip || { warn "zip not found — skip Claude Desktop zips (install zip or use: npx wise-vibe-skills zip)"; return; }
  if $dry_run; then say "  would write Claude Desktop zips → $dir"; return; fi
  mkdir -p "$dir"
  for s in $(selected_skills); do
    rm -f "$dir/$s.zip"
    (cd "$source_dir/skills" && zip -qr "$dir/$s.zip" "$s" -x '*/.DS_Store' '*/__pycache__/*' '*/.venv/*')
  done
  say "  ✓ Claude Desktop zips → $dir (Settings › Capabilities › Skills › Upload; enable Code execution)"
}

cleanup_legacy() {   # remove v0.1 skill folders that this installer created (marker present); never touch others
  local root="$1" s d
  for s in $LEGACY_SKILLS; do
    d="$root/$s"
    [ -f "$d/$MARKER" ] || continue
    if $dry_run; then say "  would remove legacy $d (superseded by wvs-*)"; else rm -rf "$d"; say "  ✗ legacy $s removed (superseded by wvs-*)"; fi
  done
}

warn_claude_commands() {
  local root="$1" s cmd_dir found=""
  case "$root" in */.claude/skills) cmd_dir="${root%/skills}/commands" ;; *) return 0 ;; esac
  for s in $LEGACY_SKILLS; do [ -f "$cmd_dir/$s.md" ] && found="$found $s"; done
  [ -n "$found" ] && warn "legacy slash commands in $cmd_dir:$found — superseded by /wvs-review · /wvs-report · /wvs-tools (keep or remove them yourself)"
  return 0
}

link_bin() {
  local root="$1" src="$1/wvs-tools/scripts/wvs"
  [ -n "$bin_dir" ] || return 0
  if [ ! -f "$src" ] && ! $dry_run; then warn "--bin-dir: wvs-tools not installed in $root — skip"; return 0; fi
  if $dry_run; then say "  would link $bin_dir/wvs → $src"; return 0; fi
  mkdir -p "$bin_dir"
  if [ -e "$bin_dir/wvs" ] && [ ! -L "$bin_dir/wvs" ]; then warn "$bin_dir/wvs exists and is not a symlink — skip"; return 0; fi
  ln -sfn "$src" "$bin_dir/wvs"
  say "  ✓ wvs → $bin_dir/wvs"
  case ":$PATH:" in *":$bin_dir:"*) ;; *) warn "$bin_dir is not on PATH — add it to your shell profile" ;; esac
}

unlink_bin() {
  [ -n "$bin_dir" ] && [ -L "$bin_dir/wvs" ] || return 0
  case "$(readlink "$bin_dir/wvs")" in
    */wvs-tools/scripts/wvs) if $dry_run; then say "  would remove $bin_dir/wvs"; else rm -f "$bin_dir/wvs"; say "  ✗ removed $bin_dir/wvs"; fi ;;
  esac
}

main() {
  resolve_source
  if [ "$action" = "list" ]; then do_list; return; fi
  local roots; roots="$(destinations)"
  local sel_clients; sel_clients="$(selected_clients | tr '\n' ' ')"
  say "wise-Vibe-Skills $(version_of) · action=$action · scope=$scope · clients: $sel_clients"
  say "skills: $(selected_skills | tr '\n' ' ')"
  say "destinations:"; printf '%s\n' "$roots" | sed 's/^/  /'
  if [ "$action" = "uninstall" ]; then
    $dry_run || confirm "Remove wise-Vibe-Skills from these destinations?" || die "cancelled"
    local r; while IFS= read -r r; do [ -n "$r" ] && uninstall_root "$r"; done <<EOF
$roots
EOF
    unlink_bin
    return
  fi
  $dry_run || confirm "Install now?" || die "cancelled"
  local r s
  while IFS= read -r r; do
    [ -n "$r" ] || continue
    for s in $(selected_skills); do install_one "$s" "$r"; done
    cleanup_legacy "$r"
    warn_claude_commands "$r"
  done <<EOF
$roots
EOF
  link_bin "$(printf '%s\n' "$roots" | head -1)"
  case " $sel_clients " in *" claude-desktop "*) [ -n "$zip_dir" ] || zip_dir="$HOME/Downloads/wise-vibe-skills-desktop" ;; esac
  [ -n "$zip_dir" ] && build_zips "$zip_dir"
  $dry_run && return
  say ""
  say "Done. Restart running agents (new session) so they pick up the skills. wvs-report needs python3 · gh (auth) · LibreOffice; wvs-tools pdf needs pandoc · xelatex · mmdc."
  say "Try:  /wvs-review · /wvs-report repos|deep|prd · /wvs-tools  (Claude Code)  — or ask your agent to use the skill by name."
}

main
}
