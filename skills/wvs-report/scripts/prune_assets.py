#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""보고서 완성 후 <Title>_assets/ 를 재작업용 최소 세트로 정리한다 (wvs-report repos · deep · prd 공통).

유지(재작업·버전업에 필요한 최소):
  - 코드·텍스트 데이터: *.py *.sh *.md *.tsv *.json *.jsonl *.txt *.csv *.yaml *.yml *.toml *.cfg *.ini *.sql *.js *.ts *.html *.css (파일당 2MB 이하, *.log 제외)
    → build_*.py · report_config.py · p_*.py · figs.py · sample/·exp/ 코드 · research/ 조사 원문 · measured.json · 실측 결과 JSON
  - 원본 입력: inputs/ (영상 제외, 파일당 15MB 이하) · source_infographic.* · infographic.*   (--drop-inputs 로 삭제)
  - .wvs_kit 표식
삭제: .venv · __pycache__ · .omc · node_modules · 각종 캐시 · clone 된 저장소(.git 포함 폴더) · 생성 그림(fig_*.png 등) · 영상 ·
      docx/pptx/pdf 중간 산출물 · 로그 · 대용량 파일 — 모두 setup_env.sh + 빌드 스크립트로 다시 만들 수 있는 것.
생성: requirements.txt (venv 동결 버전 — setup_env.sh 가 자동 설치) · ASSETS.md (정리 내역 · 재빌드 절차)

사용: prune_assets.py <assets_dir> [--dry-run] [--drop-inputs] [--force]
  --dry-run      지울 목록만 출력
  --force        이름이 *_assets 가 아니거나 옆에 최종 산출물(docx/pptx/pdf)이 없어도 진행
"""
import argparse, datetime, os, shutil, subprocess, sys

TEXT_EXT = {".py", ".sh", ".md", ".tsv", ".json", ".jsonl", ".txt", ".csv", ".yaml", ".yml", ".toml",
            ".cfg", ".ini", ".sql", ".js", ".mjs", ".ts", ".html", ".css"}
TEXT_MAX = 2 * 1024 * 1024
INPUT_MAX = 15 * 1024 * 1024
VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v"}
DROP_DIRS = {".venv", "venv", "__pycache__", ".omc", "node_modules", ".pytest_cache", ".mypy_cache",
             ".ruff_cache", ".cache", ".ipynb_checkpoints", ".tox"}
ORIGINAL_STEMS = {"source_infographic", "infographic"}
KEEP_NAMES = {".wvs_kit", "requirements.txt", "ASSETS.md"}
BUILDERS = ["build_report.py", "build_summary.py", "build_prd.py", "pptx/build_ui.py"]
BASE_PKGS = ["python-docx", "python-pptx", "matplotlib", "pymupdf"]


def human(n):
    for u in ("B", "K", "M", "G"):
        if n < 1024: return f"{n:.0f}{u}"
        n /= 1024
    return f"{n:.1f}T"


def du(p):
    if os.path.isfile(p) or os.path.islink(p):
        return os.lstat(p).st_size
    t = 0
    for d, _, fs in os.walk(p):
        for f in fs:
            try: t += os.lstat(os.path.join(d, f)).st_size
            except OSError: pass
    return t


def keep_file(rel, size, drop_inputs):
    name = os.path.basename(rel)
    stem, ext = os.path.splitext(name)
    ext = ext.lower()
    if rel in KEEP_NAMES or name == ".wvs_kit":
        return True
    original = rel.split(os.sep)[0] == "inputs" or (os.sep not in rel and stem in ORIGINAL_STEMS)
    if original:
        return not drop_inputs and ext not in VIDEO_EXT and size <= INPUT_MAX
    return ext in TEXT_EXT and size <= TEXT_MAX


def plan(A, drop_inputs):
    """→ (삭제 경로 목록, 유지 파일 목록) — 경로는 A 기준 상대."""
    drop, keep = [], []
    for d, dirs, files in os.walk(A):
        rd = os.path.relpath(d, A)
        for x in list(dirs):
            p = os.path.join(d, x)
            if x in DROP_DIRS or os.path.islink(p) or os.path.exists(os.path.join(p, ".git")):
                drop.append(os.path.normpath(os.path.join(rd, x))); dirs.remove(x)
        for f in files:
            rel = os.path.normpath(os.path.join(rd, f))
            (keep if keep_file(rel, os.lstat(os.path.join(d, f)).st_size, drop_inputs) else drop).append(rel)
    return drop, keep


def freeze(A):
    """venv 동결 → requirements 줄 목록. venv 가 없으면 기존 requirements.txt, 그것도 없으면 기본 패키지."""
    py = os.path.join(A, ".venv", "bin", "python")
    if os.path.exists(py):
        for cmd in (["uv", "pip", "freeze", "--python", py], [py, "-m", "pip", "freeze"]):
            try:
                out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            except (OSError, subprocess.TimeoutExpired):
                continue
            lines = [l.strip() for l in out.stdout.splitlines()
                     if l.strip() and not l.startswith(("-e", "#")) and " @ file:" not in l
                     and not l.lower().startswith(("pip==", "setuptools==", "wheel=="))]
            if out.returncode == 0 and lines:
                return lines
    req = os.path.join(A, "requirements.txt")
    if os.path.isfile(req):
        return [l.rstrip("\n") for l in open(req, encoding="utf-8") if l.strip()]
    return list(BASE_PKGS)


def outputs_beside(A):
    """자산 폴더 옆의 최종 산출물: <Title>.docx/.pdf, <Brand>_..._PRD.docx, <Brand>_UI_Design.pptx, Summary-Repos.docx."""
    parent, base = os.path.dirname(A), os.path.basename(A)
    stem = base[:-len("_assets")] if base.endswith("_assets") else base
    if stem.endswith("_UI"): stem = stem[:-3]
    found = []
    for f in sorted(os.listdir(parent)):
        if os.path.splitext(f)[1].lower() in (".docx", ".pptx", ".pdf") and stem and f.startswith(stem):
            found.append(f)
    if base == "_assets":                                   # repos 모드: <Project>/_assets ↔ <Project>/Summary-Repos.docx
        found = [f for f in os.listdir(parent) if f.startswith("Summary-Repos")]
    return found


def write_manifest(A, drop, keep, sizes, reqs, outputs, drop_inputs):
    today = datetime.date.today().isoformat()
    kit = open(os.path.join(A, ".wvs_kit"), encoding="utf-8").read().strip() if os.path.isfile(os.path.join(A, ".wvs_kit")) else "<wvs-report>/scripts"
    steps = [f'A="{A}"   # 폴더를 옮겼으면 새 경로', 'bash "$KIT/setup_env.sh" "$A"            # .venv 재생성 + requirements.txt 설치']
    if os.path.isfile(os.path.join(A, "sample/run_all.py")):
        steps.append('# (선택) 실측 다시: (cd "$A" && .venv/bin/python sample/run_all.py)')
    if os.path.isfile(os.path.join(A, "figs.py")):
        steps.append('(cd "$A" && .venv/bin/python figs.py)            # fig_*.png 재생성')
    for b in BUILDERS:
        if os.path.isfile(os.path.join(A, b)):
            steps.append(f'(cd "$A/{os.path.dirname(b)}" && WVS_KIT="$KIT" "$A/.venv/bin/python" {os.path.basename(b)} --pdf)'.replace('$A/"', '$A"'))
    big = sorted(((sizes[p], p) for p in drop), reverse=True)[:25]
    L = [f"# {os.path.basename(A)} — 정리된 재작업 자산", "",
         f"- 정리일: {today} (`wvs-report/scripts/prune_assets.py`)",
         f"- 최종 산출물: {', '.join(outputs) if outputs else '(옆 폴더에서 찾지 못함)'}",
         f"- 유지 {len(keep)}개 · 삭제 {len(drop)}개 항목 · 확보 {human(sum(sizes.values()))}",
         f"- 원본 입력(inputs/ · source_infographic.*): {'삭제' if drop_inputs else '유지'}", "",
         "## 재빌드 (버전업·재작업)", "", "```bash", f'KIT="{kit}"   # 다른 위치면 설치된 wvs-report/scripts', *steps, "```", "",
         "- 생성 그림(fig_*.png)·sample/exp 실행 결과 중 삭제된 것은 위 순서로 다시 만든다. 실측 결과 JSON 은 유지돼 있어 재실행 없이도 빌드된다.",
         "- 조사 원문 research/*.md · measured.json 은 그대로 — 보강할 블록만 고쳐 다시 빌드하고 게이트(check_research.py · check_report.py)를 돌린다.",
         "- clone 저장소·외부 다운로드(영상 등)는 research/ 의 URL·map.tsv 로 다시 받는다.", "",
         "## requirements.txt", "", "```", *reqs, "```", "",
         "## 삭제 항목 (큰 순, 최대 25)", "", "| 경로 | 크기 |", "|---|---|", *[f"| `{p}` | {human(s)} |" for s, p in big], ""]
    open(os.path.join(A, "ASSETS.md"), "w", encoding="utf-8").write("\n".join(L))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("assets")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--drop-inputs", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    A = os.path.abspath(os.path.expanduser(a.assets))
    if not os.path.isdir(A):
        sys.exit(f"ERROR: not a directory: {A}")
    if os.path.exists(os.path.join(A, ".git")):
        sys.exit(f"ERROR: {A} is a git repository — refusing")
    outputs = outputs_beside(A)
    if not a.force and not os.path.basename(A).endswith("_assets"):
        sys.exit(f"ERROR: '{os.path.basename(A)}' is not a *_assets folder (use --force)")
    if not a.force and not any(f.lower().endswith((".docx", ".pptx")) for f in outputs):
        sys.exit("ERROR: no final docx/pptx beside the assets folder — build the report first (or --force)")

    drop, keep = plan(A, a.drop_inputs)
    sizes = {p: du(os.path.join(A, p)) for p in drop}
    print(f"assets : {A}\noutputs: {', '.join(outputs) or '-'}\nkeep   : {len(keep)} files ({human(sum(du(os.path.join(A, k)) for k in keep))})\n"
          f"drop   : {len(drop)} items ({human(sum(sizes.values()))})")
    for s, p in sorted(((sizes[p], p) for p in drop), reverse=True)[:15]:
        print(f"  - {human(s):>6}  {p}")
    if a.dry_run:
        return
    if not drop:                                             # 이미 정리됨 — ASSETS.md 기록 보존
        print("OK nothing to prune")
        return
    reqs = freeze(A)                                         # venv 삭제 전에 동결
    open(os.path.join(A, "requirements.txt"), "w", encoding="utf-8").write("\n".join(reqs) + "\n")
    for p in drop:
        full = os.path.join(A, p)
        if os.path.isdir(full) and not os.path.islink(full): shutil.rmtree(full, ignore_errors=True)
        elif os.path.lexists(full): os.remove(full)
    for d, dirs, files in os.walk(A, topdown=False):         # 빈 폴더 정리
        if d != A and not os.listdir(d): os.rmdir(d)
    write_manifest(A, drop, keep, sizes, reqs, outputs, a.drop_inputs)
    print(f"OK pruned → {A} ({human(du(A))}) · requirements.txt {len(reqs)} pkgs · ASSETS.md")


if __name__ == "__main__":
    main()
