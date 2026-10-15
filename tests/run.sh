#!/usr/bin/env bash
# wise-Vibe-Skills test harness — skill metadata · syntax · installer parity · install/legacy-cleanup/uninstall · bin link · wvs CLI · report kit smoke build
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.."
pass() { printf 'PASS %s\n' "$1"; }

python3 tests/validate_skills.py >/dev/null && pass "skill frontmatter + bundled file references"
bash -n install.sh skills/wvs-tools/scripts/wvs && for f in skills/*/scripts/*.sh skills/*/scripts/lib/*.sh; do bash -n "$f"; done && pass "bash syntax"
if command -v shellcheck >/dev/null; then shellcheck -S warning install.sh skills/wvs-tools/scripts/wvs skills/wvs-report/scripts/*.sh && pass "shellcheck"; fi
node --check bin/wise-vibe-skills.mjs && pass "node syntax"
python3 -c "import ast,sys; [ast.parse(open(f, encoding='utf-8').read(), f) for f in sys.argv[1:]]" \
  skills/*/scripts/*.py skills/*/templates/*/*.py skills/*/templates/*/ui/*.py skills/*/templates/*/ui/pptx/*.py tests/*.py && pass "python syntax"
cmp -s skills/wvs-report/scripts/docx2pdf.sh skills/wvs-tools/scripts/lib/docx2pdf.sh && pass "docx2pdf.sh copies identical"

H="$(mktemp -d)"; trap 'rm -rf "$H"' EXIT
mkdir -p "$H/.claude" "$H/.codex"
for sc in user project; do
  diff <(HOME=$H ./install.sh --client all --scope $sc --dry-run 2>/dev/null | grep -E '^  /') \
       <(HOME=$H node bin/wise-vibe-skills.mjs install --client all --scope $sc --dry-run 2>/dev/null | grep -E '^  /') && pass "install.sh ⇔ npx destination parity ($sc)"
done
n=$(ls skills | wc -l | tr -d ' ')
# legacy v0.1 folder installed by us (marker) must be removed; a same-named folder without marker must stay
mkdir -p "$H/.agents/skills/analysis-source" "$H/.agents/skills/ref-sh"
touch "$H/.agents/skills/analysis-source/.wise-vibe-skills" "$H/.agents/skills/ref-sh/SKILL.md"
HOME=$H ./install.sh --client claude-code,codex,antigravity --bin-dir "$H/bin" -y >/dev/null 2>&1
for d in "$H/.claude/skills" "$H/.gemini/config/skills"; do [ "$(ls "$d" | wc -l | tr -d ' ')" = "$n" ]; done && pass "install.sh install ($n skills)"
[ ! -e "$H/.agents/skills/analysis-source" ] && [ -f "$H/.agents/skills/ref-sh/SKILL.md" ] && pass "legacy cleanup removes only marker folders"
[ "$("$H/bin/wvs" version)" = "$(tr -d ' \n' < VERSION)" ] && pass "--bin-dir links wvs CLI"
HOME=$H ./install.sh --client claude-code,codex,antigravity --bin-dir "$H/bin" --uninstall -y >/dev/null 2>&1
[ "$(ls "$H/.agents/skills")" = "ref-sh" ] && [ -z "$(ls "$H/.claude/skills")" ] && [ ! -e "$H/bin/wvs" ] && pass "install.sh uninstall (+ bin link) keeps foreign folders"
mkdir -p "$H/.agents/skills/wise-report-kit" && touch "$H/.agents/skills/wise-report-kit/.wise-vibe-skills"
HOME=$H node bin/wise-vibe-skills.mjs install --client codex --skills wvs-tools --bin-dir "$H/bin2" -y >/dev/null 2>&1
[ -f "$H/.agents/skills/wvs-tools/scripts/wvs" ] && [ ! -e "$H/.agents/skills/wise-report-kit" ] && [ -x "$H/bin2/wvs" ] && pass "npx install (skill subset · legacy cleanup · bin link)"
HOME=$H node bin/wise-vibe-skills.mjs zip "$H/zips" >/dev/null && unzip -tq "$H/zips/wvs-report.zip" >/dev/null && pass "Claude Desktop zip integrity"

# output-folder rule (deep · prd): default folder if it exists, else <root>; --out-dir wins; report lookup by name
O="$H/outrule"; mkdir -p "$O/with/Miscellaneous-Data" "$O/with/Need-to-be-organized-into-PRD" "$O/without"
od() { python3 skills/wvs-report/scripts/out_dir.py "$@"; }
[ "$(od deep --root "$O/with")" = "$O/with/Miscellaneous-Data" ] && [ "$(od prd --root "$O/with")" = "$O/with/Need-to-be-organized-into-PRD" ] \
  && [ "$(od deep --root "$O/without")" = "$O/without" ] && [ "$(od prd --root "$O/without")" = "$O/without" ] \
  && [ ! -e "$O/without/Miscellaneous-Data" ] && [ "$(od prd --root "$O/without" --out-dir x/y)" = "$O/without/x/y" ] && pass "out_dir rule (exists → inside · missing → root · --out-dir)"
echo r > "$O/without/Rep.pdf"; echo r > "$O/with/Miscellaneous-Data/Rep2.docx"
python3 skills/wvs-report/scripts/prd_intake.py Rep --root "$O/without" --assets "$O/a1" --no-fetch >/dev/null
python3 skills/wvs-report/scripts/prd_intake.py Rep2 --root "$O/with" --assets "$O/a2" --no-fetch >/dev/null
grep -q '"type": "report"' "$O/a1/research/inputs.json" && grep -q 'Miscellaneous-Data/Rep2.docx' "$O/a2/research/inputs.json" && pass "prd report lookup by name (Miscellaneous-Data → root)"

W=skills/wvs-tools/scripts/wvs
[ "$($W version)" = "$(tr -d ' \n' < VERSION)" ] && $W list >/dev/null && $W help clean >/dev/null && ! $W nope >/dev/null 2>&1 && pass "wvs CLI dispatch"

PY="${WVS_TEST_PY:-}"
if [ -z "$PY" ]; then PY="$(bash skills/wvs-report/scripts/setup_env.sh "$H/venv" | tail -1)"; fi
"$PY" tests/smoke_kit.py >/dev/null && pass "wvs-report kit smoke build (docx/pptx/pdf + check_report)"
"$PY" tests/smoke_prd.py >/dev/null && pass "wvs-report prd smoke (multi-input intake · RQ trace · gates pass/fail)"
"$PY" tests/smoke_ui.py >/dev/null && pass "wvs-report UI design smoke (standard builder · form check · builder/marker enforcement · FR gate)"
echo "ALL TESTS PASSED"
