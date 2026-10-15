# -*- coding: utf-8 -*-
"""화면설계서(pptx) 빌더 — wvs-report prd 표준 양식. <Brand>_UI_assets/pptx/ 에 복사해 쓴다. **이 파일의 구조·좌표는 수정하지 않는다.**
양식(이전 화면설계서 ObservaMesh·ProdAI-Atlas 와 동일):
  앞부속  표지 · 문서 정보·개정 이력 · 목차
  PART 1  개요·구조 — 1 시스템 개요 · 2 화면 ID 명명 규칙·슬라이드 구성 · 3~ 메뉴 구조도(IA) · 화면 목록 · 사용자×화면 매트릭스 · 화면 흐름도 ①~
          · 공통 UI 가이드(레이아웃·토큰·컴포넌트) · 공통 UI 가이드(상태·메시지·유효성·오류) · 사용자 유형·운용 모드별 UI 적응
  PART 2  화면별 설계 — 그룹 순, 화면 1개 = 슬라이드 1개(상단 메타 표 · 좌 와이어프레임 ①②③ · 우 기능 설명 표 · 하단 관련 FR · 발표자 노트)
  PART 3  부록 — A 모달·위저드 카탈로그 · B 메시지 정의 · C 요구사항 추적표(RTM) · D 비화면 요구 표출 위치 · E PRD 시나리오·그림 ↔ 화면 · F 참고 자료·한계
내용: ../ui_design_data.py(화면·그룹·사용자·컴포넌트·상태·메시지, FR 은 PRD 정본) · ../ui_spec.py(제품별 문구·표) · ui_screens_<x>.py(화면 스펙, ui_ids.FILES)
  --stub : 아직 없는 ui_screens_<x>.py 를 자리표시 스펙으로 대체(구조 검토용, 출력 stub_<…>.pptx)
  --pdf  : PDF 변환(툴킷 docx2pdf.sh)
"""
import glob, importlib, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)); UIA = os.path.dirname(HERE); OUTDIR = os.path.dirname(UIA)
sys.path.insert(0, HERE); sys.path.insert(0, UIA)


def _kit():
    """wvs-report/scripts(툴킷): $WVS_KIT → 상위·형제 *_assets/.wvs_kit → 알려진 스킬 루트·Claude 플러그인 캐시."""
    home = os.path.expanduser("~"); cands = [os.environ.get("WVS_KIT", "")]
    d = HERE
    for _ in range(4):
        cands += [open(f, encoding="utf-8").read().strip() for f in [os.path.join(d, ".wvs_kit")] + glob.glob(os.path.join(d, "*_assets", ".wvs_kit")) if os.path.isfile(f)]
        d = os.path.dirname(d)
    roots = [os.environ.get("CLAUDE_CONFIG_DIR", os.path.join(home, ".claude")) + "/skills", home + "/.agents/skills", home + "/.gemini/config/skills",
             os.path.join(os.environ.get("GEMINI_CLI_HOME", home), ".agents", "skills"), ".claude/skills", ".agents/skills"]
    cands += [os.path.join(r, "wvs-report", "scripts") for r in roots]
    cands += sorted(glob.glob(os.path.join(home, ".claude", "plugins", "**", "skills", "wvs-report", "scripts"), recursive=True))
    for c in cands:
        if c and os.path.exists(os.path.join(c, "ui_lib.py")): return os.path.abspath(c)
    sys.exit("wvs-report/scripts 를 찾을 수 없습니다 — WVS_KIT 지정 또는 setup_env.sh 로 자산 폴더를 준비하세요.")


KIT = _kit(); sys.path.insert(0, KIT)
from ui_lib import *  # noqa: E402,F401,F403
import ui_lib  # noqa: E402
from ui_design_data import SCREENS as UD, GROUPS, STATES, MESSAGES, COMPONENTS, FR, DOMAINS, USERS, FR_TOTAL, PRD_FILE, PRD_VER, PRD_DATE, SYSTEM  # noqa: E402
import ui_spec as SP  # noqa: E402
try:
    from ui_ids import FILES  # noqa: E402
except ImportError:
    FILES = {}

ui_lib.configure(system=SYSTEM, title=f"{SYSTEM} 화면설계서", ver=SP.DOC_VER, date=SP.DOC_DATE, author=SP.AUTHOR,
                 nav=SP.NAV, layer_colors=SP.LAYER_C, **SP.SHELL)
DOC = ui_lib.DOC
STUB = "--stub" in sys.argv
KINDNAME = {"P": "페이지", "M": "모달", "W": "위저드", "T": "탭·드로어·패널", "C": "공통 규약"}
UDM = {s[0]: s for s in UD}; _ORD = {s[0]: i for i, s in enumerate(UD)}
GN = {c: n for c, n, _, _ in GROUPS}
SECTION = {c: f"{c}. {n}" for c, n, _, _ in GROUPS}
FILES = FILES or {c.lower(): [c] for c, *_ in GROUPS}
def grp(sid): return UDM[sid][8]
ID_RE = re.compile(r"^(" + "|".join(re.escape(s) for s in sorted(_ORD, key=len, reverse=True)) + r")$")


def _stub_specs(key):
    out = []
    for s in UD:
        if s[8] not in FILES[key]: continue
        sid, name, path, perm, fr, prio, kind, purpose, g = s
        frs = fr.split()
        items = [(i + 1, FR[f][1], "기능", FR[f][2][:60], f) for i, f in enumerate(frs[:9])]
        pads = [("목록·표", "표", "화면 주요 데이터 목록(2단계 작성 예정)", "CMP-03"), ("상태 표시", "배지", "로딩·빈·오류·권한 상태(2단계 작성 예정)", "ST-01"),
                ("주 동작", "버튼", "저장·실행 등 주 동작(2단계 작성 예정)", "CMP-01"), ("필터", "선택", "검색·필터(2단계 작성 예정)", "CMP-02"), ("메시지", "안내", "메시지 규약", "MSG-001")]
        k = 0
        while len(items) < 5: items.append((len(items) + 1,) + pads[k]); k += 1
        def wire(w, sid=sid, name=name, g=g, path=path):
            cx = w.shell(nav=SP.GROUP_NAV.get(g), crumb=SECTION[g], title=name)
            w.empty(cx, 20, 98 - cx, 70, f"{sid} — 2단계 작성 예정 (자리표시 스텁)\n{path}")
        out.append(dict(id=sid, name=name, path=path, kind=KINDNAME.get(kind, kind) + "(스텁)", section=SECTION[g], perm=perm, prio=prio,
                        desc=purpose + " (자리표시 — 2단계에서 상세 설계)", fr=frs, items=items, wire=wire))
    return out


SCREENS, STUBBED = [], []
for key in FILES:
    try:
        SCREENS += importlib.import_module(f"ui_screens_{key}").SCREENS
    except ModuleNotFoundError:
        if not STUB: raise SystemExit(f"ui_screens_{key}.py 가 없습니다 — 작성하거나 --stub 으로 구조만 확인하세요.")
        SCREENS += _stub_specs(key); STUBBED.append(key)

assert sorted(s["id"] for s in SCREENS) == sorted(_ORD), ("화면 ID 누락·중복", sorted(set(_ORD) ^ {s["id"] for s in SCREENS}))
SCREENS.sort(key=lambda s: _ORD[s["id"]])
for s in SCREENS:
    assert s["fr"] == UDM[s["id"]][4].split(), ("PRD 추적 불일치", s["id"])
    assert s["section"] == SECTION[grp(s["id"])], (s["id"], s["section"])
    assert s["prio"] == UDM[s["id"]][5], ("우선순위 불일치", s["id"])
    assert len(s["items"]) >= 5, ("기능 표 5행 미만", s["id"])
    links = " ".join(str(it[4]) for it in s["items"])
    assert all(f in links for f in s["fr"]), ("기능 표 연계 누락", s["id"], [f for f in s["fr"] if f not in links])
PRD_IDS = list(FR)
assert len(PRD_IDS) == FR_TOTAL
N_FR, N_SCR, N_GRP = len(PRD_IDS), len(SCREENS), len(GROUPS)
N_P0 = sum(1 for f in FR.values() if f[4] == "P0")
NAME = f"{SP.FILE_PREFIX}_UI_Design.pptx"
OUT = os.path.join(UIA, "stub_" + NAME) if STUB else os.path.join(OUTDIR, NAME)
SECTIONS = [SECTION[c] for c, _, _, _ in GROUPS]
def by_sec(s): return [x for x in SCREENS if x["section"] == s]
MODAL = [s for s in SCREENS if UDM[s["id"]][6] in ("M", "W")]
KIND = lambda k: sum(1 for s in SCREENS if UDM[s["id"]][6] == k)
N_IA = len(SP.IA)
# 장 번호: 1 개요 · 2 명명 규칙 · 3..(2+N_IA) IA · 화면 목록 · 매트릭스 · 흐름도 · 가이드 2장 · 적응
NO = {"list": 3 + N_IA, "matrix": 4 + N_IA, "flow": 5 + N_IA, "guide1": 6 + N_IA, "guide2": 7 + N_IA, "adapt": 8 + N_IA}
CIRC = "①②③④⑤⑥⑦⑧⑨⑩"


def check_ids(txt, where):
    for tok in re.split(r"[\s·,/()]+", str(txt)):
        if re.fullmatch(r"(SCR-)?[A-Z]{1,3}-?\d{2,3}", tok) and not tok.startswith(("FR-", "MSG-", "ST-", "CMP-", "FL-", "NFR-", "RQ-", "IN-")):
            assert ID_RE.match(tok) or ID_RE.match("SCR-" + tok), (where, "없는 화면 ID", tok)


# ============================ 표지 ============================
sl = new_slide(); rect(sl, 0, 0, SW, SH, fill=NAVY, line=None)
text(sl, 0.9, 1.6, 11, 0.6, "UI DESIGN DOCUMENT  ·  화면설계서", size=14, bold=True, color=IND_L)
text(sl, 0.9, 2.3, 11.5, 1.2, f"{SYSTEM} 화면설계서", size=40, bold=True, color="FFFFFF")
text(sl, 0.9, 3.5, 11.5, 0.9, SP.SUBTITLE + " — " + " / ".join(GN[c] for c in GN), size=12, color="CADCFC")
text(sl, 0.9, 4.75, 11.5, 1.6, f"기준 문서  {PRD_FILE} {PRD_VER} ({PRD_DATE}, {len(DOMAINS)} 도메인 · FR {N_FR} · P0 {N_P0})\n"
     f"화면 수  {N_SCR} (페이지 {KIND('P')} · 위저드 {KIND('W')} · 모달 {KIND('M')} · 탭·드로어·패널 {KIND('T')} · 공통 규약 {KIND('C')}) · {N_GRP} 그룹\n"
     f"버전 {DOC['ver']}  ·  작성일 {DOC['date']}  ·  작성 {DOC['author']}", size=11, color="E6E8F2")
_loc = os.path.join(os.path.basename(os.path.dirname(OUTDIR)) if os.path.basename(OUTDIR) == "Need-to-be-organized-into-PRD" else "", os.path.basename(OUTDIR), NAME).lstrip("/")
text(sl, 0.9, 6.6, 11.5, 0.5, f"저장 위치: {_loc} (자산: {os.path.basename(UIA)}/) · 와이어프레임의 조직·사람·수치는 모두 가상"
     + ("  ·  [스텁 빌드: " + ",".join(STUBBED) + "]" if STUBBED else ""), size=9, color="9AA0B4")
footer(sl, "표지")

# ============================ 문서 정보·개정 이력 ============================
sl = new_slide(); title(sl, "문서 정보 · 개정 이력", "화면설계서(UI Design Document) 관리 정보와 History")
kv_table(sl, 0.4, 1.1, 6.0, [["문서명", f"{SYSTEM} 화면설계서(UI Design Document)"]] + SP.DOC_INFO[:1] +
         [["기준 문서", f"{PRD_FILE} {PRD_VER} ({PRD_DATE}) · {len(DOMAINS)} 도메인 FR {N_FR}(P0 {N_P0}) · 화면 ID 는 PRD 15.4 화면 목록과 1:1"]] + SP.DOC_INFO[1:] +
         [["검증", f"빌드 시 PRD FR {N_FR} ↔ 화면 커버리지 assert(부록 C) · 화면 ID 순서·누락 · 화면별 PRD 추적·우선순위 = 화면 목록 정본 · 기능 표 연계 열에 화면의 모든 FR · 콜아웃 수 = 기능 표 행 수"]],
         key_w=1.4, font=8, row_h=0.42)
table(sl, 6.7, 1.1, 6.2, [["버전", "일자", "작성자", "변경 내용", "해당 페이지"], [DOC["ver"], DOC["date"], DOC["author"], f"초판. PRD {PRD_VER} 전 FR 기준 화면 {N_SCR}종 설계", "전체"],
                          ["", "", "", "", ""], ["", "", "", "", ""]], [0.7, 1.1, 1.2, 2.3, 0.9], font=8.5, row_h=0.36)
text(sl, 6.7, 2.8, 6.2, 3.9, SP.NOTATION + "\n• 그룹 = " + " · ".join(f"{c} {n}" for c, n, _, _ in GROUPS), size=8.2, color=TXT)
footer(sl, "문서 정보")

# ============================ 목차 ============================
sl = new_slide(); title(sl, "목차", f"PART 1 개요·구조 → PART 2 화면별 설계({N_GRP}그룹) → PART 3 부록")
left = ["PART 1  개요·구조", "  1. 시스템 개요", "  2. 화면 ID 명명 규칙 · 슬라이드 구성"] + \
       [f"  {3 + i}. 메뉴 구조도(IA) {CIRC[i]} {ia[0]}" for i, ia in enumerate(SP.IA)] + \
       [f"  {NO['list']}. 화면 목록({N_SCR})", f"  {NO['matrix']}. 사용자 × 화면 매트릭스", f"  {NO['flow']}. 화면 흐름도 ①~{CIRC[max(0, len(SP.FLOWS) - 1)]}",
        f"  {NO['guide1']}. 공통 UI 가이드 — 레이아웃·토큰·컴포넌트", f"  {NO['guide2']}. 공통 UI 가이드 — 상태·메시지·유효성·오류", f"  {NO['adapt']}. 사용자 유형·운용 모드별 UI 적응"]
right = ["PART 2  화면별 설계"] + [f"  {s} ({len(by_sec(s))})" for s in SECTIONS] + ["", "PART 3  부록", "  A. 모달·위저드 카탈로그", f"  B. 메시지 정의(MSG-001~{len(MESSAGES):03d})",
         f"  C. 요구사항 추적표(RTM) PRD {N_FR} ↔ 화면", "  D. 비화면(NFR·백엔드) 요구 표출 위치", "  E. PRD 시나리오·그림 ↔ 화면 ID", "  F. 참고 자료·템플릿 출처·한계"]
text(sl, 0.6, 1.2, 6.0, 5.8, "\n".join(left), size=11.5, color=TXT)
text(sl, 6.9, 1.1, 6.0, 6.0, "\n".join(right), size=9.2 if len(right) <= 26 else 7.6, color=TXT)
footer(sl, "목차")

# ============================ PART 1 ============================
section_slide("개요 · 구조", "시스템 개요 · 명명 규칙 · IA · 화면 목록 · 사용자 매트릭스 · 화면 흐름도 · 공통 UI 가이드 · 사용자 유형·모드 적응", 1)

sl = new_slide(); title(sl, "1. " + getattr(SP, "OVERVIEW_TITLE", "시스템 개요"), SP.OVERVIEW_SUB)
table(sl, 0.4, 1.15, 6.4, SP.OVERVIEW_T1[0], SP.OVERVIEW_T1[1], font=7.3, row_h=0.36)
table(sl, 0.4, 1.15 + 0.36 * len(SP.OVERVIEW_T1[0]) + 0.25, 6.4, SP.OVERVIEW_T2[0], SP.OVERVIEW_T2[1], font=7.3, row_h=0.36)
text(sl, 7.1, 1.15, 5.8, 5.7, SP.OVERVIEW_TEXT + "\n\n사용자: " + " · ".join(f"{u[1]}({u[2]})" for u in USERS), size=8.4, color=TXT)
footer(sl, "PART 1 · 시스템 개요")

sl = new_slide(); title(sl, "2. 화면 ID 명명 규칙 · 슬라이드 구성", "국내 관행(구분_카테고리_순번, 팝업 접미사)과 PRD ID 체계(FR-<단위ID>-NN)를 결합")
table(sl, 0.4, 1.15, 6.2, SP.ID_RULES + [["그룹 코드", " ".join(f"{c} {n}" for c, n, _, _ in GROUPS), "-"]], [1.5, 3.3, 1.4], font=7.4, row_h=0.46)
table(sl, 6.8, 1.15, 6.1, [["화면별 슬라이드 구성", "내용"], ["상단 메타 표", "시스템 · 화면 ID · 유형 / 화면명 · 경로(라우트·CLI 명령) · 권한 / 우선순위 · PRD 추적 · 작성일/버전"],
  ["설명", "화면 목적·핵심 동작 2~3문장(PRD FR 요지)"], ["좌측 와이어프레임", "편집 가능한 도형, ①②③ 번호. 콘솔 셸 · 설치 창(frame) · 터미널(CLI)"],
  ["우측 기능 설명 표", "No · 구성요소 · 유형 · 기능 설명/동작(검증·상태·전이·예외·안전 규칙) · 연계(FR·화면·메시지)"], ["하단", "관련 PRD FR 전체 · 푸터(문서·버전·그룹·페이지)"],
  ["노트", "상태(ST)·메시지(MSG)·사용자 유형 적응·예외 흐름·API(발표자 노트)"]], [1.6, 4.5], font=8, row_h=0.46)
text(sl, 6.8, 4.6, 6.1, 2.1, SP.TYPE_VOCAB, size=9, color=SUB)
footer(sl, "PART 1 · 명명 규칙")


def ia_slide(ttl, sub, cols, note, sec):
    sl = new_slide(); title(sl, ttl, sub)
    cols = cols or [("(그룹 없음)", ["ui_spec.IA 에 그룹 코드를 지정"])]
    n = len(cols); cw = (SW - 0.8 - (n - 1) * 0.12) / n
    pitch = min(0.37, 4.55 / max(1, max(len(c[1]) for c in cols)))
    for i, (name, subs) in enumerate(cols):
        x = 0.4 + i * (cw + 0.12)
        label_box(sl, x, 1.15, cw, 0.4, name, IND, size=9)
        for j, s in enumerate(subs):
            rect(sl, x, 1.68 + j * pitch, cw, pitch - 0.05, fill="FFFFFF", line=LINE, radius=0.05)
            text(sl, x + 0.04, 1.68 + j * pitch, cw - 0.08, pitch - 0.05, s, size=6.2 if pitch > 0.33 else 5.6, anchor="m")
    text(sl, 0.4, 6.35, 12.5, 0.75, note, size=8.2, color=SUB)
    footer(sl, sec)


def ids(g): return [f"{s[1]} ({s[0]})" for s in UD if s[8] == g]
covered_ia = set()
for i, (tail, sub, codes, note) in enumerate(SP.IA):
    covered_ia |= set(codes)
    ia_slide(f"{3 + i}. 메뉴 구조도(IA) {CIRC[i]} — {tail}", sub, [(GN[c], ids(c)) for c in codes], note, f"PART 1 · IA {CIRC[i]}")
assert covered_ia == set(GN), ("IA 에 빠진 그룹", sorted(set(GN) - covered_ia))

rows_all = [[s["id"], s["name"], GN[grp(s["id"])], KINDNAME.get(UDM[s["id"]][6], UDM[s["id"]][6]), s.get("path", "-"), s.get("perm", ""), s.get("prio", ""),
             " ".join(s["fr"][:4]) + (" …" if len(s["fr"]) > 4 else "")] for s in SCREENS]
per = 21
for k in range(0, len(rows_all), per):
    sl = new_slide(); title(sl, f"{NO['list']}. 화면 목록 ({k+1}~{min(k+per, len(rows_all))} / {len(rows_all)})", "화면ID · 화면명 · 그룹 · 유형 · 라우트 · 권한 · 우선순위 · PRD 추적(요약). 화면 ID 는 PRD 15.4 화면 목록과 같다")
    table(sl, 0.4, 1.1, SW - 0.8, [["화면 ID", "화면명", "그룹", "유형", "라우트", "권한", "P", "PRD 추적(요약)"]] + rows_all[k:k + per], [0.85, 2.7, 1.3, 0.95, 2.5, 1.6, 0.35, 2.28], font=6.6, row_h=0.245)
    footer(sl, "PART 1 · 화면 목록")

sl = new_slide(); title(sl, f"{NO['matrix']}. 사용자 × 화면 매트릭스", SP.MATRIX_SUB)
table(sl, 0.4, 1.1, SW - 0.8, [["화면 그룹"] + [u[1] for u in USERS]] + [[f"{c} {GN[c]}"] + (SP.MATRIX.get(c) or ["—"] * len(USERS)) for c, _, _, _ in GROUPS],
      [2.4] + [(SW - 0.8 - 2.4) / len(USERS)] * len(USERS), font=7.2, row_h=min(0.33, 4.8 / (len(GROUPS) + 1)))
text(sl, 0.4, 6.1, 12.5, 0.8, SP.MATRIX_NOTE, size=8.3, color=SUB)
footer(sl, "PART 1 · 사용자 매트릭스")


def flow_slide(ttl, sub, nodes, edges, notes):
    sl = new_slide(); title(sl, ttl, sub)
    X0, Y0, DX, DY, NW, NH = 0.4, 1.35, 2.12, 1.22, 1.92, 0.6
    pos = {}
    for (nid, label, col, row, kind) in nodes:
        x, y = X0 + col * DX, Y0 + row * DY
        fill = {"screen": "FFFFFF", "popup": IND_XL, "start": NAVY, "end": "E9F7EF", "cond": "FFF4E0"}[kind]
        colr = "FFFFFF" if kind == "start" else TXT
        shape = MSO_SHAPE.DIAMOND if kind == "cond" else (MSO_SHAPE.OVAL if kind == "start" else MSO_SHAPE.ROUNDED_RECTANGLE)
        rect(sl, x, y, NW, NH, fill=fill, line=IND if kind == "popup" else (NAVY if kind == "start" else LINE), radius=0.08, shape=shape)
        text(sl, x + (0.25 if kind == "cond" else 0.05), y, NW - (0.5 if kind == "cond" else 0.1), NH, label, size=7.0 if kind != "cond" else 6.6, color=colr, align="c", anchor="m", bold=(kind == "start"))
        pos[nid] = (x, y, col, row)
        if kind in ("screen", "popup", "end"): check_ids(label.split()[0], ttl)
    used = {}
    for (a, b, lab) in edges:
        ax, ay, ac, ar = pos[a]; bx, by, bc, br = pos[b]
        if ar == br:
            x1, x2 = (ax + NW, bx) if bc > ac else (ax, bx + NW)
            y1 = ay + NH / 2
            line(sl, x1, y1, x2, y1, color=GRAY, lw=1.0, arrow=True)
            if lab: text(sl, (x1 + x2) / 2 - 0.7, ay - 0.24, 1.4, 0.22, lab, size=6.5, color=IND, align="c")
        else:
            down = br > ar
            gy_base = (ay + NH + (DY - NH) / 2) if down else (ay - (DY - NH) / 2)
            k = used.get(min(ar, br), 0); used[min(ar, br)] = k + 1
            gy = gy_base + (k % 3 - 1) * 0.09
            cxa, cxb = ax + NW / 2, bx + NW / 2
            ys = ay + NH if down else ay
            line(sl, cxa, ys, cxa, gy, color=GRAY, lw=1.0)
            if abs(cxa - cxb) > 0.01: line(sl, cxa, gy, cxb, gy, color=GRAY, lw=1.0)
            ye = by if down else by + NH
            line(sl, cxb, gy, cxb, ye, color=GRAY, lw=1.0, arrow=True)
            if lab:
                if abs(cxa - cxb) > 0.3: text(sl, min(cxa, cxb), gy - 0.22, abs(cxb - cxa), 0.2, lab, size=6.5, color=IND, align="c")
                else: text(sl, cxa + 0.05, (ys + ye) / 2 - 0.1, 1.2, 0.2, lab, size=6.5, color=IND)
    text(sl, 0.4, 6.35, 12.5, 0.7, notes, size=8.3, color=SUB)
    footer(sl, "PART 1 · 화면 흐름도")


assert SP.FLOWS, "ui_spec.FLOWS 가 비었습니다 — 핵심 여정 흐름도를 2~4개 작성(설치→첫 실행→메인, 주요 업무, 관리·배포 등)"
for i, (ttl, sub, nodes, edges, notes) in enumerate(SP.FLOWS):
    flow_slide(f"{NO['flow']}-{CIRC[i]} {ttl}", sub, nodes, edges, notes)

sl = new_slide(); title(sl, f"{NO['guide1']}. 공통 UI 가이드 — 레이아웃 · 디자인 토큰 · 컴포넌트", SP.GUIDE_SUB)
table(sl, 0.4, 1.1, 6.1, SP.TOKENS, [1.9, 2.3, 1.9], font=7.0, row_h=0.4)
text(sl, 0.4, 1.1 + 0.4 * len(SP.TOKENS) + 0.2, 6.1, 2.3, SP.LAYOUT_TEXT, size=8.0, color=TXT)
table(sl, 6.7, 1.1, 6.2, [["ID", "컴포넌트", "상태·변형", "규칙"]] + [[c[0], c[1], c[3], c[4]] for c in COMPONENTS], [0.6, 1.2, 2.0, 2.4], font=6.2,
      row_h=min(0.31, 5.4 / (len(COMPONENTS) + 1)))
footer(sl, "PART 1 · 공통 UI 가이드")

sl = new_slide(); title(sl, f"{NO['guide2']}. 공통 UI 가이드 — 상태 · 메시지 · 유효성 · 오류 처리", "화면별 설계에서는 이 규칙을 반복 기술하지 않고 ST·MSG ID 로 참조한다")
_sh = min(0.3, 3.6 / (len(STATES) + 1))
table(sl, 0.4, 1.1, 6.2, [["상태", "발생", "화면 표현"]] + [[f"{i} {n}", wn, h] for i, n, wn, h in STATES], [1.4, 1.6, 3.2], font=6.8, row_h=_sh)
table(sl, 0.4, 1.1 + _sh * (len(STATES) + 1) + 0.25, 6.2, SP.FEEDBACK, [1.4, 4.8], font=7.0, row_h=0.36)
table(sl, 6.8, 1.1, 6.1, SP.VALIDATION, [1.9, 4.2], font=7.0, row_h=0.34)
table(sl, 6.8, 1.1 + 0.34 * len(SP.VALIDATION) + 0.25, 6.1, SP.ERRORS, [2.2, 3.9], font=7.0, row_h=0.36)
footer(sl, "PART 1 · 공통 UI 가이드")

sl = new_slide(); title(sl, f"{NO['adapt']}. 사용자 유형 · 운용 모드별 UI 적응", SP.ADAPT_SUB)
table(sl, 0.4, 1.1, SW - 0.8, SP.ADAPT, [2.8, 7.4, 2.33], font=7.4, row_h=min(0.46, 5.2 / len(SP.ADAPT)))
footer(sl, "PART 1 · 사용자 유형·모드 적응")

# ============================ PART 2 ============================
section_slide("화면별 설계", f"{N_SCR} 화면 · {N_GRP} 그룹 — 상단 메타 표 · 좌측 와이어프레임(①②③) · 우측 기능 설명 표 · 하단 관련 PRD FR", 2)
for sec in SECTIONS:
    for spec in by_sec(sec):
        _sl = screen_slide(spec)
        if not spec["kind"].endswith("(스텁)"):
            _n = sum(1 for sh in _sl.shapes if sh.shape_type == 1 and sh.auto_shape_type == MSO_SHAPE.OVAL and abs(sh.width - Inches(0.19)) < 2000)
            assert _n == len(spec["items"]), ("콜아웃 수 ≠ items 수", spec["id"], _n, len(spec["items"]))

# ============================ PART 3 부록 ============================
section_slide("부록", "모달·위저드 카탈로그 · 메시지 정의 · 요구사항 추적표(RTM) · 비화면 요구 표출 위치 · PRD 시나리오 매핑 · 참고 자료", 3)
for k in range(0, max(1, len(MODAL)), 14):
    sl = new_slide(); title(sl, f"A. 모달·위저드 카탈로그 ({min(k+1, len(MODAL))}~{min(k+14, len(MODAL))} / {len(MODAL)})", "화면 ID · 이름 · 유형 · 경로 · 주요 버튼 · 파괴적/외부 전송/승인 여부")
    rows = [["화면 ID", "이름", "유형", "경로", "주요 버튼", "주의"]]
    for s in MODAL[k:k + 14]:
        btns = " / ".join(it[1] for it in s["items"] if "버튼" in it[2])[:70]
        danger = any(("위험" in it[2]) or ("MSG-002" in str(it[4])) for it in s["items"])
        rows.append([s["id"], s["name"], KINDNAME.get(UDM[s["id"]][6], ""), s.get("path", "-"), btns or "-", "●" if danger else "-"])
    table(sl, 0.4, 1.1, SW - 0.8, rows, [1.0, 2.8, 1.0, 3.4, 3.8, 0.53], font=7.2, row_h=0.34)
    footer(sl, "부록 A")

for k in range(0, len(MESSAGES), 26):
    sl = new_slide(); title(sl, "B. 메시지 정의 — 상황 · 종류 · 문구(ko/en)" + (f" ({k+1}~{min(k+26, len(MESSAGES))})" if len(MESSAGES) > 26 else ""), "i18n 키로 관리(ko 기본·en 폴백). {변수} 는 런타임 치환")
    table(sl, 0.4, 1.05, SW - 0.8, [["ID", "상황", "종류", "문구(ko)", "문구(en)"]] + [list(m) for m in MESSAGES[k:k + 26]], [0.85, 1.6, 0.75, 5.4, 3.93], font=6.2, row_h=0.2)
    footer(sl, "부록 B")

cov = {}
for s in SCREENS:
    for f in s["fr"]: cov.setdefault(f, []).append(s["id"])
ghost = {f for f in cov if f not in FR}
assert not ghost, ("PRD 에 없는 ID", sorted(ghost))
missing = [f for f in PRD_IDS if f not in cov]
assert not missing, ("PRD 미커버", missing[:20])
rtm = [[f, FR[f][1][:24], FR[f][4], " ".join(cov[f][:7]) + (" …" if len(cov[f]) > 7 else ""), str(len(cov[f]))] for f in PRD_IDS]
per = 44
for k in range(0, len(rtm), per):
    sl = new_slide(); title(sl, f"C. 요구사항 추적표(RTM) PRD ↔ 화면 ({k+1}~{min(k+per, len(rtm))} / {len(rtm)})", f"PRD FR {N_FR} 전부가 최소 1개 화면에 매핑(빌드 assert). 미커버 {len(missing)} · 유령 ID {len(ghost)}")
    half = per // 2
    for col, chunk in enumerate([rtm[k:k + half], rtm[k + half:k + per]]):
        if chunk:
            table(sl, 0.4 + col * 6.3, 1.05, 6.15, [["FR", "기능", "P", "화면 ID", "수"]] + chunk, [0.95, 1.85, 0.35, 2.6, 0.4], font=6.1, row_h=0.235)
    footer(sl, "부록 C")

for r in SP.NONUI[1:]: check_ids(r[2], "부록 D")
sl = new_slide(); title(sl, "D. 비화면(NFR·백엔드·파이프라인) 요구의 표출 위치", "직접 조작 화면이 없는 PRD FR·NFR 은 '설정·상태를 보여주는 화면'을 커버 화면으로 본다(누락 방지)")
table(sl, 0.4, 1.1, SW - 0.8, SP.NONUI, [2.6, 3.6, 2.9, 3.43], font=7.2, row_h=min(0.46, 5.2 / len(SP.NONUI)))
footer(sl, "부록 D")

for p in SP.SCENARIOS: check_ids(p[4], "부록 E")
sl = new_slide(); title(sl, "E. PRD 시나리오·그림 ↔ 화면설계서 화면 ID", SP.SCENARIO_SUB)
table(sl, 0.4, 1.05, SW - 0.8, [["PRD", "시나리오·그림", "요지", "관련 FR", "화면 ID"]] + [list(p) for p in SP.SCENARIOS], [0.7, 2.3, 4.6, 2.2, 2.73],
      font=7.2, row_h=min(0.62, 4.4 / (len(SP.SCENARIOS) + 1)))
if SP.SCENARIO_NOTE: text(sl, 0.4, 5.6, 12.5, 1.2, SP.SCENARIO_NOTE, size=8.4, color=SUB)
footer(sl, "부록 E")

sl = new_slide(); title(sl, "F. 참고 자료 · 템플릿 출처 · 한계", "표준·관행 조사: wvs-report references/prd-ui-design-doc.md (출처 URL 포함)")
table(sl, 0.4, 1.1, SW - 0.8, SP.REFS + [["기준", f"{SYSTEM} PRD {PRD_VER} ({PRD_DATE}) — FR {N_FR} · 화면 목록(15.4) · 아키텍처(14장) · 보안(19장)", "화면 범위·동작·안전 규칙·라우트"]],
      [1.0, 6.2, 5.33], font=7.2, row_h=0.6)
text(sl, 0.4, 5.0, 12.5, 1.9, SP.LIMITS, size=8.2, color=SUB)
footer(sl, "부록 F")

prs.core_properties.title = f"{SYSTEM} 화면설계서"
prs.core_properties.keywords = "wvs-report/ui-design-template/1"      # check_ui_design.py 가 확인하는 표준 빌더 표식
prs.save(OUT)
print("saved", OUT, "slides", len(prs.slides), "screens", N_SCR, "modals", len(MODAL), "FR covered", len(cov), "/", N_FR, "stubbed", STUBBED)
if not STUB:   # 양식 게이트: 슬라이드 순서·화면 밀도·표식·빌더 동일성 — 실패하면 중단
    if subprocess.run([sys.executable, os.path.join(KIT, "check_ui_design.py"), OUT]).returncode:
        sys.exit("check_ui_design.py FAIL — 화면설계서 표준 양식과 다릅니다(위 FAIL 항목을 고치세요)")
if "--pdf" in sys.argv:
    subprocess.run(["bash", os.path.join(KIT, "docx2pdf.sh"), OUT], check=True)
