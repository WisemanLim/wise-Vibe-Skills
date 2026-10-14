#!/usr/bin/env python3
"""wvs-report prd smoke test (offline): prd_intake (md · image · github/site URL · prompt) → FR with RQ basis → req_map → gates → docx.
Also checks that an unmapped RQ fails the gate."""
import base64, os, runpy, shutil, subprocess, sys, tempfile
sys.dont_write_bytecode = True

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills", "wvs-report")
KIT, TPL = os.path.join(ROOT, "scripts"), os.path.join(ROOT, "templates", "prd")
T = tempfile.mkdtemp(prefix="wvs-prd-")
IN, A = os.path.join(T, "in"), os.path.join(T, "Need-to-be-organized-into-PRD", "Demo_assets")
os.makedirs(IN); os.makedirs(A)
for f in os.listdir(TPL):
    if f.endswith(".py"): shutil.copy2(os.path.join(TPL, f), A)

open(os.path.join(IN, "requirements.md"), "w", encoding="utf-8").write(
    "# Demo 요구사항\n\n## 목표\n- 마감 누락 0건\n\n## 기능 요구사항\n1. 사용자는 프로필을 등록할 수 있어야 한다 (필수)\n2. 공고를 매일 수집해야 한다\n\n"
    "## 비기능 요구사항\n- 응답 p95 500ms 이하\n\n## 범위 제외\n- 자동 제출은 하지 않는다\n")
open(os.path.join(IN, "mock.png"), "wb").write(base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="))
env = dict(os.environ, WVS_KIT=KIT, WVS_ASSETS=A)
subprocess.run([sys.executable, os.path.join(KIT, "prd_intake.py"), os.path.join(IN, "requirements.md"), os.path.join(IN, "mock.png"),
                "https://github.com/langgenius/dify", "https://example.com/", "--prompt", "1. 단위는 독립 배포 가능해야 한다",
                "--assets", A, "--no-fetch"], check=True, capture_output=True)
R = os.path.join(A, "research")
_inp = open(os.path.join(R, "_INPUTS.md"), encoding="utf-8").read()
assert "/in/" not in _inp and IN not in _inp, "local absolute paths must not leak into _INPUTS.md"
_inp = __import__("re").sub(r"(?m)^(<!-- 채울 내용.*-->)$", r"\1\n- 요약: 테스트 입력", _inp)   # 에이전트가 채우는 단계 대신
open(os.path.join(R, "_INPUTS.md"), "w", encoding="utf-8").write(_inp)
rq = [l.split("\t") for l in open(os.path.join(R, "req_items.tsv"), encoding="utf-8").read().splitlines()[1:]]
types = {q[0]: q[4] for q in rq}
assert [i["type"] for i in __import__("json").load(open(os.path.join(R, "inputs.json")))] == ["req", "image", "github", "site", "prompt"], "input classification"
assert sorted(set(types.values())) == ["fr", "goal", "nfr", "non-goal"], types
fr_rq = [k for k, v in types.items() if v == "fr"]

units = runpy.run_path(os.path.join(A, "units.py"))["UNITS"]
lines = ["# r1", "## 4. FR 후보"]
for n, u in enumerate(units):
    basis = fr_rq[n] if n < len(fr_rq) else "도식"
    lines += [f"### {u[0]} {u[3]}", "| ID | 이름 | 하는 일 | 구현 요지 | 우선순위 | 참고 OSS | 근거 |", "|---|---|---|---|---|---|---|",
              f"| FR-{u[0]}-01 | {u[3]} | 하는 일 | `cfg.key` | P0 | langgenius/dify | {basis} |"]
open(os.path.join(R, "r1_demo.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
open(os.path.join(R, "repos.tsv"), "w").write("query\tfull_name\tstars\tlicense\tarchived\tpushed\trelease\trelease_date\n"
                                               "langgenius/dify\tlanggenius/dify\t150000\tNOASSERTION\tfalse\t2026-10-01\t-\t-\n")
nfr = [k for k, v in types.items() if v == "nfr"]
open(os.path.join(R, "req_map.tsv"), "w", encoding="utf-8").write("".join(f"{k}\tNFR-PERF-01 13장\t성능 목표\n" for k in nfr))
frs = " ".join(f"FR-{u[0]}-01" for u in units)
s = open(os.path.join(A, "ui_data.py"), encoding="utf-8").read().replace('"FR-PLT-CON-01", "P0", "P", "원본 도식', f'"{frs}", "P0", "P", "원본 도식')
open(os.path.join(A, "ui_data.py"), "w", encoding="utf-8").write(s)

ok = subprocess.run([sys.executable, "build_prd.py"], cwd=A, env=env, capture_output=True, text=True)
assert ok.returncode == 0, ok.stdout + ok.stderr
assert "gates PASS" in ok.stdout, ok.stdout
docx = [f for f in os.listdir(os.path.dirname(A)) if f.endswith(".docx")][0]
from docx import Document  # noqa: E402
text = "\n".join(p.text for p in Document(os.path.join(os.path.dirname(A), docx)).paragraphs)
tables = "\n".join(c.text for t in Document(os.path.join(os.path.dirname(A), docx)).tables for row in t.rows for c in row.cells)
for need in ["2.1 입력 인벤토리", "3.2 요구사항 문서 정리 (RQ)", "21.4 요구사항 문서(RQ)"]:
    assert need in text, need
for need in ["IN-03", "langgenius/dify", "https://example.com/"] + [q[0] for q in rq]:
    assert need in tables, need

open(os.path.join(R, "req_map.tsv"), "w").write("")               # NFR RQ 매핑 삭제 → 게이트 실패해야 함
bad = subprocess.run([sys.executable, "build_prd.py"], cwd=A, env=env, capture_output=True, text=True)
assert bad.returncode != 0 and "요구 항목" in bad.stdout, bad.stdout
open(os.path.join(R, "req_map.tsv"), "w", encoding="utf-8").write("".join(f"{k}\tNFR-PERF-01\t\n" for k in nfr))
open(os.path.join(R, "_INPUTS.md"), "w", encoding="utf-8").write(_inp.replace("- 요약: 테스트 입력", ""))   # 요약 비움 → 게이트 실패해야 함
bad2 = subprocess.run([sys.executable, "build_prd.py"], cwd=A, env=env, capture_output=True, text=True)
assert bad2.returncode != 0 and "_INPUTS.md" in bad2.stdout, bad2.stdout
print("prd smoke ok:", T)
