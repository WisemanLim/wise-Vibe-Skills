# -*- coding: utf-8 -*-
"""첨부 자료(인포그래픽·링크) 상세 분석 보고서 빌더 — wvs-report deep 템플릿.

<Title>_assets/ 에 복사해 쓴다. 내용은 전부 report_config.py(CFG) + research/r*.md(조사 원문) + measured.json(검증)에서 온다.
장 구성(기본): 표지 → 목차 → 1 개요 및 분석 방법 → 2 원문 도식 전수 정리 → 3.. 범주/개념별 조사 장 → 통합 장(비교·활용·구현·확장·거버넌스)
            → 도식 검증 종합(각 절 '### 도식 판정' 표 자동 수집) → 결론 및 권고 → 부록 A 논문(arXiv 검증) · B 저장소 실측표 · C 출처 · D 그림·이미지 출처.
CFG["CUSTOM"] 의 모듈(p_*.py)은 지정 위치에서 import 되어 직접 docx_lib 로 장을 쓴다(실측 실험·참조 구현 등).

사용:  <venv>/bin/python build_report.py [--pdf]
"""
import importlib, json, os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("WVS_ASSETS", HERE)
sys.path.insert(0, HERE)


def _kit():
    """wvs-report/scripts(툴킷) 위치 — 에이전트·설치 방식과 무관하게 찾는다.
    1) $WVS_KIT  2) 자산 폴더(또는 상위·형제 *_assets)의 .wvs_kit(setup_env.sh 가 기록)  3) 알려진 스킬 루트
    (Claude Code·공유 ~/.agents·Antigravity·Gemini CLI·Claude 플러그인 캐시·프로젝트 .claude/.agents)."""
    import glob
    here = os.path.dirname(os.path.abspath(__file__))
    cands = [os.environ.get("WVS_KIT", "")]
    d = here
    for _ in range(4):
        cands += [open(f, encoding="utf-8").read().strip() for f in [os.path.join(d, ".wvs_kit")] + glob.glob(os.path.join(d, "*_assets", ".wvs_kit")) if os.path.isfile(f)]
        d = os.path.dirname(d)
    home = os.path.expanduser("~")
    roots = [os.environ.get("CLAUDE_CONFIG_DIR", os.path.join(home, ".claude")) + "/skills", home + "/.agents/skills", home + "/.gemini/config/skills",
             os.path.join(os.environ.get("GEMINI_CLI_HOME", home), ".agents", "skills"), ".claude/skills", ".agents/skills"]
    cands += [os.path.join(r, "wvs-report", "scripts") for r in roots]
    cands += sorted(glob.glob(os.path.join(home, ".claude", "plugins", "**", "skills", "wvs-report", "scripts"), recursive=True))
    for c in cands:
        if c and os.path.exists(os.path.join(c, "docx_lib.py")):
            return os.path.abspath(c)
    sys.exit("wvs-report/scripts 를 찾을 수 없습니다 — WVS_KIT=<…/wvs-report/scripts> 를 지정하거나 setup_env.sh 로 자산 폴더를 준비하세요.")


sys.path.insert(0, _kit())
import docx_lib as r   # noqa: E402
import md2docx as M    # noqa: E402
from report_config import CFG  # noqa: E402

ALL = M.load_all("research")
MEAS = json.load(open(os.path.join(HERE, "measured.json"), encoding="utf-8")) if os.path.exists(os.path.join(HERE, "measured.json")) \
    else {"repos": [], "missing": [], "papers": {}, "bad_papers": []}
LEVELS = CFG.get("LEVELS", ["일치", "부분일치", "표기오류", "해석주의", "누락", "과장"])

# 조사 블록 KEY → 'N.M절' 상호참조 (본문 속 KEY 토큰을 절 번호로 치환)
XREF, _n = {}, 2          # 1·2장 = 개요·원문 도식, 조사 장은 3장부터
for ch in CFG["CHAPTERS"]:
    _n += 1
    for i, it in enumerate(ch.get("blocks", [])):
        XREF[it[1]] = f"{_n}.{i + 1}절"
_XR = re.compile(r"\b(" + "|".join(sorted(map(re.escape, XREF), key=len, reverse=True)) + r")\b") if XREF else None


def xref(body):
    if not _XR: return body
    out, fence = [], False
    for ln in body.splitlines():
        if ln.strip().startswith("```"): fence = not fence
        out.append(ln if fence else _XR.sub(lambda m: XREF[m.group(1)], ln))
    return "\n".join(out)


WARN = []   # 빌드는 계속하고 끝에 모아 알린다 — 그림·조사 블록 하나 빠졌다고 docx/pdf 가 안 나오면 안 된다


def fig(path, width, caption, src):
    if not os.path.isfile(r._abs(path)):
        WARN.append(f"그림 없음(생략): {path}"); return
    r.FIG(path, width, caption, src)


def figs(lst):
    for f in lst or ():
        fig(f[0], f[2] if len(f) > 2 else 16.5, f[1], f[3] if len(f) > 3 else "본 보고서 작성")


def chapter(ch):
    r.CH(ch["title"])
    if ch.get("intro"): r.P(ch["intro"], size=9.3)
    for it in ch.get("blocks", []):
        tag, key = it[0], it[1]
        if (tag, key) not in ALL:
            WARN.append(f"조사 블록 없음: research/{tag}_*.md '# {key}'")
            r.SEC(key); r.P(f"[미확인] 조사 블록 {tag}/{key} 누락 — research/{tag}_*.md 에 '# {key} …' 블록을 채운 뒤 다시 빌드한다.", size=9.2)
            continue
        title, body = M.block(ALL, tag, key)
        r.SEC(title.split(" ", 1)[1] if " " in title else title)
        figs(it[2] if len(it) > 2 else None)
        M.render(r, xref(body), size=9.2, sub_level=3)
        figs(it[3] if len(it) > 3 else None)
    if ch.get("module"):
        importlib.import_module(ch["module"])


# ============================================================ 표지
r.COVER(CFG["TITLE"], CFG["SUBTITLE"], CFG["TAGLINE"],
        [(f"작성일: {r.DOC_DATE}", 10, None),
         (f"원본 자료: {CFG['SOURCE']}", 9, r.C_GRAY),
         (f"검증·확장 출처: 공식 저장소·문서·논문, GitHub REST API 실측 {r.DOC_DATE} (저장소 {len(MEAS['repos'])}개), arXiv 검증(논문 {len(MEAS['papers'])}편)"
          + (f", {CFG['EXTRA_SOURCES']}" if CFG.get("EXTRA_SOURCES") else ""), 9, r.C_GRAY),
         (f"저장 위치: {CFG['OUT_LABEL']}", 9, r.C_GRAY)])

# ============================================================ 1 개요 및 분석 방법
r.CH("개요 및 분석 방법")
r.SEC("분석 대상과 목적")
for p in CFG["PURPOSE"]: r.P(p, size=9.4)
r.SEC("분석 방법")
r.KV(CFG["METHOD"] + [("저장소 실측", f"GitHub REST API 로 {len(MEAS['repos'])}개 저장소의 stars · license(SPDX) · 언어 · pushed_at · archived 직접 조회({r.DOC_DATE}) — 부록 B"),
                      ("논문 검증", f"인용 arXiv ID 를 arxiv.org 메타데이터로 일괄 조회 — 검증 {len(MEAS['papers'])}편(부록 A). 확인 못 한 사실은 [미확인]"),
                      ("판정", "도식 항목마다 " + " / ".join(LEVELS) + " (각 절 끝 '도식 판정', 종합 장)"),
                      ("제외", "보고서 형식 참고용으로만 본 이전 보고서들은 출처에서 제외")])
r.SEC("문서 구성")
r.T(["장", "범주", "내용"], CFG["TOC_TABLE"], widths=r.W([1.2, 3, 12]), font=8)

# ============================================================ 2 원문 도식 전수 정리
r.CH("원문 도식 전수 정리")
r.SEC("원본 자료")
r.P(CFG["SOURCE_DESC"], size=9.3)
# 입력 = 첨부 이미지 · 첨부 파일(md 등) · 첨부 사이트 — prd_intake.py 가 만든 research/inputs.json 인벤토리(있으면)
INV = os.path.join(HERE, "research", "inputs.json")
INV = [x for x in json.load(open(INV, encoding="utf-8")) if x.get("type") != "missing"] if os.path.exists(INV) else []
if INV:
    KIND = {"image": "이미지", "req": "문서", "report": "보고서", "github": "GitHub", "site": "사이트", "prompt": "요청문"}
    r.T(["ID", "유형", "자료", "접근일"],
        [[x["id"], KIND.get(x["type"], x["type"]), x["src"] if x["src"].startswith("http") else (x.get("title") or os.path.basename(x["src"])),
          x.get("accessed", "")] for x in INV], widths=r.W([1.4, 1.8, 11.6, 2.4]), font=7.5)
SRC_IMGS = CFG.get("SOURCE_IMAGES") or [(CFG.get("SOURCE_IMAGE", "source_infographic.png"), CFG.get("SOURCE_CAPTION", ""), CFG.get("SOURCE_CREDIT", ""))]
for f in SRC_IMGS:   # 이미지가 없는 입력(md·사이트만)이면 건너뛴다
    if os.path.isfile(r._abs(f[0])): r.FIG(f[0], f[3] if len(f) > 3 else CFG.get("SOURCE_IMAGE_W", 12.5), f[1], f[2])
figs(CFG.get("RECON_FIGS"))
for title, body in CFG.get("TRANSCRIPTION", []):   # [(절 제목, 마크다운 본문)] — 범주별 전사표·저장소 현행 대조 등
    r.SEC(title); M.render(r, body, size=9.2, sub_level=3)

# ============================================================ 3.. 조사 장 + 통합 장
for ch in CFG["CHAPTERS"]:
    chapter(ch)

# ============================================================ 도식 검증 종합
r.CH("도식 검증 종합")
r.P("각 절 끝 '도식 판정' 표를 한곳에 모은다(조사 자료에서 자동 수집). 판정 단계: " + " / ".join(f"**{x}**" for x in LEVELS) + ".", size=9.2)
V = []
for (tag, key), (title, body) in sorted(ALL.items()):
    if key in ("PAPERS", "REPOS"): continue
    m = re.search(r"^### [^\n]*도식 판정[^\n]*\n(.*?)(?=^### |\Z)", body, re.S | re.M)
    if not m: continue
    lines = [l for l in m.group(1).splitlines() if l.strip().startswith("|")]
    if len(lines) < 3: continue
    hdr = M._cells(lines[0])
    ji = next((i for i, h in enumerate(hdr) if "판정" in h), 1)
    ei = next((i for i, h in enumerate(hdr) if any(k in h for k in ("근거", "보정", "설명", "이유"))), len(hdr) - 1)
    ii = 0 if ji != 0 else 1
    for l in lines[2:]:
        c = M._cells(l)
        if len(c) <= max(ji, ei): continue
        lv = next((x for x in LEVELS if c[ji].replace("**", "").strip().startswith(x)), None)
        if lv: V.append([XREF.get(key, "-").split(".")[0] + "장", c[ii].replace("**", ""), lv, c[ei].replace("**", "")])
V += CFG.get("EXTRA_VERDICTS", [])
r.SEC("판정표")
r.T(["장", "도식 항목", "판정", "근거·보정"], V, widths=r.W([1.2, 5.4, 1.8, 9.2]), font=6.9)
cnt = Counter(v[2] for v in V)
r.SEC("판정 분포와 총평")
if V:
    r.T(["판정", "건수", "비율"], [[k, str(cnt[k]), f"{100 * cnt[k] / len(V):.0f}%"] for k in LEVELS if cnt[k]], widths=r.W([5, 3, 3]), font=8)
for p in CFG.get("VERDICT_SUMMARY", []): r.P(p, size=9.2)

# ============================================================ 결론 및 권고
r.CH("결론 및 권고")
r.SEC("결론")
for p in CFG["CONCLUSION"]: r.P(p, size=9.3)
r.SEC("권고")
r.NUM_RESET()
for p in CFG["RECOMMEND"]: r.N(p)

# ============================================================ 부록
r.H("부록 A. 논문 목록 (arXiv 검증)", 1)
P = MEAS["papers"]
TXT = {os.path.basename(f): open(f, encoding="utf-8").read()
       for f in sorted(__import__("glob").glob(os.path.join(HERE, "research", "r*.md")))}
r.P(f"조사 자료에 인용된 arXiv ID 를 arxiv.org 메타데이터로 조회해 제목 · 제1저자 · 제출일을 확인한 {len(P)}편이다({r.DOC_DATE}). 조회되지 않은 ID 는 제외했다.", size=9.0)
rows = sorted(([k, v["title"], v["author"], v["date"], ", ".join(f.split("_")[0] for f, t in TXT.items() if k in t)] for k, v in P.items()),
              key=lambda x: x[3])
if rows: r.T(["arXiv ID", "제목", "제1저자", "제출일", "조사"], rows, widths=r.W([1.9, 8.4, 2.8, 2.0, 1.5]), font=6.8)

r.H("부록 B. 저장소 실측표", 1)
Rp = MEAS["repos"]
r.P(f"gh api repos/OWNER/REPO 로 조회한 {len(Rp)}개 저장소(스타 내림차순, {r.DOC_DATE}). 'NOASSERTION' 은 GitHub 가 SPDX 로 판별하지 못한 경우(자체·변형 라이선스)."
    + (f" 조회 실패(본문에서 제외·[미확인]): {', '.join(MEAS['missing'])}." if MEAS["missing"] else ""), size=9.0)
for f in CFG.get("APPENDIX_FIGS", []): figs([f])
if Rp:
    r.T(["저장소", "★", "라이선스", "언어", "최근 push", "조사"],
        [[x["full_name"] + (" (archived)" if x["archived"] == "true" else "") + (f" ← {x['query']}" if x["query"].lower() != x["full_name"].lower() else ""),
          f"{int(x['stars']):,}", x["license"], x["lang"], x["pushed"], ",".join(x.get("src", []))] for x in Rp],
        widths=r.W([6.4, 1.6, 2.6, 2.0, 2.0, 1.6]), font=6.7)

r.H("부록 C. 출처", 1)
r.H("원자료", 3)
for b in CFG["PRIMARY_SOURCES"]: r.B(b)
r.H("표준 · 명세 · 백서 · 공식 문서 · 블로그", 3)
seen = set()
for t in TXT.values():
    m = re.search(r"^# PAPERS.*?$(.*?)(?=^# |\Z)", t, re.S | re.M)
    for ln in (m.group(1).splitlines() if m else []):
        s = ln.strip()
        if not s.startswith("- ") or "arXiv" in s[:12]: continue
        s = re.sub(r"^-\s*(STD\s*\|\s*)?", "", s)
        k = s.split("|")[0].strip().lower()[:60]
        if k in seen: continue
        seen.add(k); r.B(" · ".join(p.strip() for p in s.split("|") if p.strip()))
r.H("라이선스 고지", 3)
for b in CFG.get("LICENSE_NOTES", ["부록 B 의 저장소 라이선스는 GitHub API 의 SPDX 조회값이며, 모델 가중치·데이터 라이선스는 별도다. 실제 사용 전 각 저장소의 LICENSE 와 모델 카드를 확인해야 한다.",
                                   "본 보고서의 재구성 그림(fig_*.png)과 예제 코드(sample/)는 본 보고서가 작성한 것이다."]):
    r.B(b)
r.H("부록 D. 그림 · 이미지 출처", 1)
r.FIG_TABLE()

r.SAVE(CFG["OUT"], pdf="--pdf" in sys.argv, group_min=3, line_max=100)
for w in WARN: print("WARN:", w, file=sys.stderr)
