#!/usr/bin/env bash
# wise-Vibe-Skills test harness — skill metadata · syntax · installer parity · install/legacy-cleanup/uninstall · bin link · wvs CLI · report kit smoke build
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.."
pass() { printf 'PASS %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1"; exit 1; }

python3 tests/validate_skills.py >/dev/null && pass "skill frontmatter + bundled file references" || fail "skill frontmatter + bundled file references"
bash -n install.sh skills/wvs-tools/scripts/wvs && for f in skills/*/scripts/*.sh skills/*/scripts/lib/*.sh; do bash -n "$f"; done && pass "bash syntax" || fail "bash syntax"
if command -v shellcheck >/dev/null; then shellcheck -S warning install.sh skills/wvs-tools/scripts/wvs skills/wvs-report/scripts/*.sh && pass "shellcheck" || fail "shellcheck"; fi
node --check bin/wise-vibe-skills.mjs && pass "node syntax" || fail "node syntax"
python3 -c "import ast,sys; [ast.parse(open(f, encoding='utf-8').read(), f) for f in sys.argv[1:]]" \
  skills/*/scripts/*.py skills/*/templates/*/*.py skills/*/templates/*/ui/*.py skills/*/templates/*/ui/pptx/*.py tests/*.py && pass "python syntax" || fail "python syntax"
cmp -s skills/wvs-report/scripts/docx2pdf.sh skills/wvs-tools/scripts/lib/docx2pdf.sh && pass "docx2pdf.sh copies identical" || fail "docx2pdf.sh copies identical"
python3 -B tests/test_history.py && pass "session export adapters, incremental preservation, hooks and locking" || fail "session export adapters, incremental preservation, hooks and locking"
python3 -B tests/test_tools.py && pass "wvs file operations and PDF argument forwarding" || fail "wvs file operations and PDF argument forwarding"
python3 -B tests/test_hosts.py && pass "14 client installer routes (user/project) and bundled adapter" || fail "14 client installer routes (user/project) and bundled adapter"

H="$(mktemp -d)"; trap 'rm -rf "$H"' EXIT
mkdir -p "$H/.claude" "$H/.codex"
for sc in user project; do
  diff <(HOME=$H ./install.sh --client all --scope $sc --dry-run 2>/dev/null | grep -E '^  /') \
       <(HOME=$H node bin/wise-vibe-skills.mjs install --client all --scope $sc --dry-run 2>/dev/null | grep -E '^  /') && pass "install.sh ⇔ npx destination parity ($sc)" || fail "install.sh ⇔ npx destination parity ($sc)"
done
n=$(ls skills | wc -l | tr -d ' ')
# legacy v0.1 folder installed by us (marker) must be removed; a same-named folder without marker must stay
mkdir -p "$H/.agents/skills/analysis-source" "$H/.agents/skills/ref-sh"
touch "$H/.agents/skills/analysis-source/.wise-vibe-skills" "$H/.agents/skills/ref-sh/SKILL.md"
HOME=$H ./install.sh --client claude-code,codex,antigravity --bin-dir "$H/bin" -y >/dev/null 2>&1
for d in "$H/.claude/skills" "$H/.gemini/config/skills"; do [ "$(ls "$d" | wc -l | tr -d ' ')" = "$n" ]; done && pass "install.sh install ($n skills)" || fail "install.sh install ($n skills)"
[ ! -e "$H/.agents/skills/analysis-source" ] && [ -f "$H/.agents/skills/ref-sh/SKILL.md" ] && pass "legacy cleanup removes only marker folders" || fail "legacy cleanup removes only marker folders"
[ "$("$H/bin/wvs" version)" = "$(tr -d ' \n' < VERSION)" ] && pass "--bin-dir links wvs CLI" || fail "--bin-dir links wvs CLI"
HOME=$H ./install.sh --client claude-code,codex,antigravity --bin-dir "$H/bin" --uninstall -y >/dev/null 2>&1
[ "$(ls "$H/.agents/skills")" = "ref-sh" ] && [ -z "$(ls "$H/.claude/skills")" ] && [ ! -e "$H/bin/wvs" ] && pass "install.sh uninstall (+ bin link) keeps foreign folders" || fail "install.sh uninstall (+ bin link) keeps foreign folders"
mkdir -p "$H/.agents/skills/wise-report-kit" && touch "$H/.agents/skills/wise-report-kit/.wise-vibe-skills"
HOME=$H node bin/wise-vibe-skills.mjs install --client codex --skills wvs-tools --bin-dir "$H/bin2" -y >/dev/null 2>&1
[ -f "$H/.agents/skills/wvs-tools/scripts/wvs" ] && [ ! -e "$H/.agents/skills/wise-report-kit" ] && [ -x "$H/bin2/wvs" ] && pass "npx install (skill subset · legacy cleanup · bin link)" || fail "npx install (skill subset · legacy cleanup · bin link)"
HOME=$H node bin/wise-vibe-skills.mjs zip "$H/zips" >/dev/null && unzip -tq "$H/zips/wvs-report.zip" >/dev/null && pass "Claude Desktop zip integrity" || fail "Claude Desktop zip integrity"

# output-folder rule (deep · prd): default folder if it exists, else <root>; --out-dir wins; report lookup by name
O="$H/outrule"; mkdir -p "$O/with/Miscellaneous-Data" "$O/with/Need-to-be-organized-into-PRD" "$O/without"
od() { python3 skills/wvs-report/scripts/out_dir.py "$@"; }
[ "$(od deep --root "$O/with")" = "$O/with/Miscellaneous-Data" ] && [ "$(od prd --root "$O/with")" = "$O/with/Need-to-be-organized-into-PRD" ] \
  && [ "$(od deep --root "$O/without")" = "$O/without" ] && [ "$(od prd --root "$O/without")" = "$O/without" ] \
  && [ ! -e "$O/without/Miscellaneous-Data" ] && [ "$(od prd --root "$O/without" --out-dir x/y)" = "$O/without/x/y" ] && pass "out_dir rule (exists → inside · missing → root · --out-dir)" || fail "out_dir rule (exists → inside · missing → root · --out-dir)"
echo r > "$O/without/Rep.pdf"; echo r > "$O/with/Miscellaneous-Data/Rep2.docx"
python3 skills/wvs-report/scripts/prd_intake.py Rep --root "$O/without" --assets "$O/a1" --no-fetch >/dev/null
python3 skills/wvs-report/scripts/prd_intake.py Rep2 --root "$O/with" --assets "$O/a2" --no-fetch >/dev/null
grep -q '"type": "report"' "$O/a1/research/inputs.json" && grep -q 'Miscellaneous-Data/Rep2.docx' "$O/a2/research/inputs.json" && pass "prd report lookup by name (Miscellaneous-Data → root)" || fail "prd report lookup by name (Miscellaneous-Data → root)"

# assets pruning: keep code/research/inputs · drop venv/cache/clone/figures · requirements.txt + ASSETS.md · idempotent · refuse without final docx
P="$H/prune"; A="$P/Rep_assets"; mkdir -p "$A/.venv/lib" "$A/__pycache__" "$A/clone/.git" "$A/research" "$A/inputs" "$A/sample/out" "$P/Bare_assets"
echo x > "$A/.venv/lib/big"; echo x > "$A/__pycache__/a.pyc"; echo x > "$A/clone/a.py"; echo x > "$A/fig_a.png"; echo x > "$A/reel.mp4"; echo x > "$A/run.log"
echo 'print(1)' > "$A/build_report.py"; echo '# r1' > "$A/research/r1_x.md"; echo x > "$A/inputs/IN-01.png"; echo '{}' > "$A/sample/out/r.json"; echo d > "$P/Rep.docx"
pr() { python3 skills/wvs-report/scripts/prune_assets.py "$@"; }
pr "$A" >/dev/null && [ -f "$A/build_report.py" ] && [ -f "$A/research/r1_x.md" ] && [ -f "$A/inputs/IN-01.png" ] && [ -f "$A/sample/out/r.json" ] \
  && [ ! -e "$A/.venv" ] && [ ! -e "$A/__pycache__" ] && [ ! -e "$A/clone" ] && [ ! -e "$A/fig_a.png" ] && [ ! -e "$A/reel.mp4" ] && [ ! -e "$A/run.log" ] \
  && grep -q python-docx "$A/requirements.txt" && grep -q '재빌드' "$A/ASSETS.md" && pr "$A" | grep -q 'nothing to prune' && grep -q 'fig_a.png' "$A/ASSETS.md" \
  && ! pr "$P/Bare_assets" >/dev/null 2>&1 && ! pr "$P" >/dev/null 2>&1 && pass "prune_assets (keep · drop · requirements/ASSETS.md · idempotent · refusal)" || fail "prune_assets (keep · drop · requirements/ASSETS.md · idempotent · refusal)"

W=skills/wvs-tools/scripts/wvs
[ "$($W version)" = "$(tr -d ' \n' < VERSION)" ] && $W list >/dev/null && $W help clean >/dev/null && ! $W nope >/dev/null 2>&1 && pass "wvs CLI dispatch" || fail "wvs CLI dispatch"

PY="${WVS_TEST_PY:-}"
if [ -z "$PY" ]; then PY="$(bash skills/wvs-report/scripts/setup_env.sh "$H/venv" | tail -1)"; fi
"$PY" tests/smoke_kit.py >/dev/null && pass "wvs-report kit smoke build (docx/pptx/pdf + check_report)" || fail "wvs-report kit smoke build (docx/pptx/pdf + check_report)"
"$PY" tests/smoke_deep.py >/dev/null && pass "wvs-report deep build (Miscellaneous-Data present → inside · absent → root · md/site input without image · missing block)" || fail "wvs-report deep build (Miscellaneous-Data present → inside · absent → root · md/site input without image · missing block)"
python3 tests/smoke_research.py >/dev/null && pass "wvs-report research depth gate (shallow → FAIL · rich → PASS · --unit · sample/no-sample · missing unit)" || fail "wvs-report research depth gate (shallow → FAIL · rich → PASS · --unit · sample/no-sample · missing unit)"
"$PY" tests/smoke_prd.py >/dev/null && pass "wvs-report prd smoke (multi-input intake · RQ trace · gates pass/fail)" || fail "wvs-report prd smoke (multi-input intake · RQ trace · gates pass/fail)"
"$PY" tests/smoke_ui.py >/dev/null && pass "wvs-report UI design smoke (standard builder · form check · builder/marker enforcement · FR gate)" || fail "wvs-report UI design smoke (standard builder · form check · builder/marker enforcement · FR gate)"
echo "ALL TESTS PASSED"
