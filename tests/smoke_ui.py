#!/usr/bin/env python3
"""wvs-report prd 화면설계서 스모크 — templates/prd/ui (표준 양식 빌더) → pptx → check_ui_design.py(양식·순서·밀도) 통과,
그리고 화면 FR 누락 시 빌드 실패를 확인한다. 화면 스펙은 ui_screens_example.py 를 그대로 쓴다."""
import os, re, shutil, subprocess, sys, tempfile
sys.dont_write_bytecode = True

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills", "wvs-report")
KIT, TPL = os.path.join(ROOT, "scripts"), os.path.join(ROOT, "templates", "prd")
PDF = "--pdf" in sys.argv
T = tempfile.mkdtemp(prefix="wvs-ui-")
A, U = os.path.join(T, "Demo_assets"), os.path.join(T, "Demo_UI_assets")
os.makedirs(os.path.join(A, "research")); os.makedirs(os.path.join(U, "pptx"))
for f in ("data.py", "data_fr.py"):
    shutil.copy2(os.path.join(TPL, f), A)
# PRD 정본(축소): 단위 4개 · FR 5개 · 화면 3개(위저드·페이지·모달) — ui_screens_example.py 의 FR 과 맞춘다
open(os.path.join(A, "units.py"), "w", encoding="utf-8").write('''
UNITS = [("PLT-PKG", "PLT", "P", "Packaging", "설치 패키지", "설치", "-", "x"), ("PLT-CON", "PLT", "P", "Console", "콘솔", "콘솔", "-", "x"),
         ("X-DASH", "X", "X", "Dashboard", "대시보드", "현황", "-", "x"), ("X-HITL", "X", "X", "Approval", "승인", "승인함", "x.hitl", "x")]
DOMAINS = [("PLT", "P", "플랫폼", "-", ["PLT-PKG", "PLT-CON"]), ("X", "X", "공통", "-", ["X-DASH", "X-HITL"])]
UNIT = {u[0]: u for u in UNITS}; AGENT_UNITS = []
''')
rows = [("PLT-PKG", "FR-PLT-PKG-01"), ("PLT-PKG", "FR-PLT-PKG-02"), ("PLT-CON", "FR-PLT-CON-01"), ("X-DASH", "FR-X-DASH-01"), ("X-HITL", "FR-X-HITL-01")]
md = ["## 4. FR 후보"]
for u, f in rows:
    md += [f"### {u} x", "| ID | 이름 | 하는 일 | 구현 요지 | 우선순위 | 참고 OSS | 근거 |", "|---|---|---|---|---|---|---|", f"| {f} | 기능 {f[-5:]} | 하는 일 | 요지 | P0 | - | RQ |"]
open(os.path.join(A, "research", "r1_demo.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
open(os.path.join(A, "ui_data.py"), "w", encoding="utf-8").write('''
GROUPS = [("INS", "설치", "Platform"), ("HOM", "홈·개요", "홈"), ("X", "공통", "공통")]
SCREENS = [("S001", "설치 마법사 — 사전 점검", "(installer)", "설치자", "FR-PLT-PKG-01 FR-PLT-PKG-02", "P0", "W", "사전 점검", "INS"),
           ("S020", "개요", "/home", "전체", "FR-PLT-CON-01 FR-X-DASH-01", "P0", "P", "개요", "HOM"),
           ("S090", "승인함 — 송신 승인", "/inbox (모달)", "승인자", "FR-X-HITL-01", "P0", "M", "승인", "X")]
WIREFRAMES = []; SID = {s[0]: s for s in SCREENS}
''')
open(os.path.join(A, ".wvs_kit"), "w").write(KIT + "\n")
shutil.copy2(os.path.join(TPL, "ui", "ui_design_data.py"), U)
shutil.copy2(os.path.join(TPL, "ui", "ui_spec.py"), U)
for f in ("build_ui.py", "ui_ids.py"):
    shutil.copy2(os.path.join(TPL, "ui", "pptx", f), os.path.join(U, "pptx"))
shutil.copy2(os.path.join(TPL, "ui", "pptx", "ui_screens_example.py"), os.path.join(U, "pptx", "ui_screens_a.py"))
open(os.path.join(U, "pptx", "ui_ids.py"), "w").write('FILES = {"a": ["INS", "HOM", "X"]}\n')
sp = open(os.path.join(U, "ui_spec.py"), encoding="utf-8").read()
sp = sp.replace('FILE_PREFIX = "{Brand}"', 'FILE_PREFIX = "Demo"')
sp = sp.replace('NAV = [("홈", "홈", [("HOME", "개요")]), ("Platform", "Platform", [("MGR", "관리")])]',
                'NAV = [("홈", "홈", [("HOME", "개요")]), ("공통", "공통", [("X", "승인함")]), ("Platform", "Platform", [("MGR", "관리")])]')
sp = sp.replace('    ("운영", "{좌측 내비 상단 메뉴 설명}", [], "{진입·핵심 여정 설명}"),', '    ("운영", "좌측 내비 상단", ["HOM", "X"], "로그인 → 개요(S020)"),')
sp = sp.replace('    ("구성·관리 · 설치", "{좌측 내비 하단 + 셸 밖(설치 마법사·CLI)}", [], "{설명}"),', '    ("설치", "셸 밖 설치 마법사", ["INS"], "설치(S001) 후 개요"),')
sp = sp.replace("FLOWS = []", 'FLOWS = [("설치 → 개요 (FL-01)", "설치 후 첫 화면", [("s", "설치 시작", 0, 0, "start"), ("a", "S001 사전 점검", 1, 0, "screen"),'
                ' ("c", "통과?", 2, 0, "cond"), ("e", "S020 개요", 3, 0, "end"), ("m", "S090 승인", 2, 1, "popup")],'
                ' [("s", "a", ""), ("a", "c", ""), ("c", "e", "예"), ("e", "m", "승인 요청")], "흐름 설명")]')
sp = sp.replace('SCENARIOS = []', 'SCENARIOS = [("UJ-1", "5.4 사용자 여정", "설치 후 승인", "FR-X-HITL-01", "S001 S020 S090")]')
open(os.path.join(U, "ui_spec.py"), "w", encoding="utf-8").write(sp)

env = dict(os.environ, WVS_KIT=KIT)
b = subprocess.run([sys.executable, "build_ui.py"] + (["--pdf"] if PDF else []), cwd=os.path.join(U, "pptx"), env=env, capture_output=True, text=True)
assert b.returncode == 0, b.stdout + b.stderr
out = os.path.join(T, "Demo_UI_Design.pptx")
assert os.path.exists(out), "출력 위치 = UI 자산 폴더의 상위(PRD 와 같은 출력 폴더)"
c = subprocess.run([sys.executable, os.path.join(KIT, "check_ui_design.py"), out] + (["--pdf", "--render", os.path.join(T, "pages")] if PDF else []),
                   capture_output=True, text=True)
assert c.returncode == 0, c.stdout + c.stderr
chk = lambda p, *o: subprocess.run([sys.executable, os.path.join(KIT, "check_ui_design.py"), p, *o], capture_output=True, text=True)
# 표준 빌더 강제: 빌더를 고치면 FAIL
bp = os.path.join(U, "pptx", "build_ui.py"); orig = open(bp, encoding="utf-8").read()
open(bp, "w", encoding="utf-8").write(orig + "\n# local tweak\n")
r = chk(out); assert r.returncode != 0 and "빌더가 템플릿과 다름" in r.stdout, r.stdout
open(bp, "w", encoding="utf-8").write(orig)
# 표식 없는 문서(다른 빌더로 만든 문서) → FAIL, --legacy 면 양식만 검사해 통과
from pptx import Presentation
p = Presentation(out); p.core_properties.keywords = ""; other = os.path.join(T, "Other_UI_Design.pptx"); p.save(other)
r = chk(other); assert r.returncode != 0 and "표준 빌더 표식 없음" in r.stdout, r.stdout
assert chk(other, "--legacy").returncode == 0
# FR 누락 화면 → 빌드 실패
s = open(os.path.join(U, "pptx", "ui_screens_a.py"), encoding="utf-8").read()
open(os.path.join(U, "pptx", "ui_screens_a.py"), "w", encoding="utf-8").write(s.replace('"MSG-002 CMP-01")],\n  wire=w_s090m', '"CMP-01")],\n  wire=w_s090m').replace(
    '(1, "요청 요약", "안내", "대상·송신처·영향을 요약하고 비가역임을 명시", "FR-X-HITL-01")', '(1, "요청 요약", "안내", "대상·송신처·영향을 요약하고 비가역임을 명시", "MSG-001")'))
bad = subprocess.run([sys.executable, "build_ui.py"], cwd=os.path.join(U, "pptx"), env=env, capture_output=True, text=True)
assert bad.returncode != 0 and "기능 표 연계 누락" in (bad.stdout + bad.stderr), bad.stdout + bad.stderr
print("ui smoke ok:", T, c.stdout.strip().splitlines()[0])
