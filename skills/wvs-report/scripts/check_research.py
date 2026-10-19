#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""조사 깊이 게이트 (wvs-report deep) — 에이전트·모델과 무관하게 같은 품질 하한을 강제한다.

호스트(Claude Code · Cursor · Codex · Gemini CLI …)마다 조사 깊이가 달라지는 것을 막기 위해, 조사 원문(research/)을
기계적으로 검사한다. FAIL 이면 해당 블록을 보강한 뒤 다시 실행한다 — PASS 전에는 빌드하지 않는다.

stage
  spec     research/_SPEC.md — 필수 절·전사 항목 수·사전 웹 확인(1차 출처 URL)·판정 후보·조사 단위 표
  research (기본) spec + 조사 단위 표의 파일·블록 전부 — 블록 분량·필수 소제목·소제목 분량·구현 코드·판정 표·출처 수
  final    research + measured.json(missing 0 · bad_papers 0) · fig_*.png · sample/(실행 코드 + out/ 결과)

사용: check_research.py --assets <Title>_assets [--stage spec|research|final] [--unit r3_reco.md] [--no-sample]
종료 코드: 0 PASS · 1 FAIL (FAIL 항목마다 파일·블록·이유·보강 지시 출력)
"""
import argparse, glob, json, os, re, sys

# 기준치 — Claude Code 로 만든 양호 보고서(항목 블록 77~119줄, 소제목 3줄+, 파일당 출처 9~45건)와
# 저품질 보고서(항목 블록 19줄, 소제목 1줄, 출처 2~3건)를 가르는 하한. 분량은 공백 아닌 줄 수.
ITEM_MIN = 70          # 항목 블록(유형 A/B 필수 소제목을 가진 블록)
OTHER_MIN = 35         # 원리·비교·누락·통합 블록(FND_ CMP_ GAP_ VAL_ …)
OTHER_SUBS = 3         # 기타 블록 최소 소제목 수
SUB_MIN = 3            # 필수 소제목 하나의 최소 줄 수
IMPL_MIN = 12          # 구현·사용방법 소제목 최소 줄 수(코드 포함)
VERDICT_ROWS = 3       # 도식 판정 표 최소 데이터 행
SRC_PER_BLOCK = 3      # 파일 PAPERS 항목 수 ≥ 블록 수 × 3 (최소 5)
SPEC_MIN = 50          # _SPEC.md 최소 줄 수 — 템플릿을 한두 줄로 압축하는 것을 막는다
WEB_MIN = 3            # _SPEC.md '사전 웹 확인' 표의 1차 출처 URL 최소 수

TYPE_A = ["정의", "소스 저장소", "설치·환경설정", "사용방법", "동작방식", "성능·벤치마크", "사용 및 활용용도", "확장방안", "도식 판정"]
TYPE_B = ["정의와 계보", "구성방식", "동작방식", "구현", "보안·운영 리스크", "사용 및 활용용도", "확장방안", "도식 판정"]
CODE_SUBS = ("사용방법", "구현")
OTHER_PREFIX = ("FND", "CMP", "GAP", "VAL")
SPEC_SECTIONS = ["도식 전사", "사전 웹 확인", "도식 판정 후보", "필수 소제목", "조사 단위", "품질 규칙", "파일 형식"]

FAILS, WARNS = [], []


def fail(where, why, fix):
    FAILS.append(f"FAIL {where}: {why} → {fix}")


def nonempty(lines):
    return [l for l in lines if l.strip()]


def section(text, name):
    """'## <name>…' 절 본문(다음 '## ' 전까지)."""
    m = re.search(r"^##\s+[^\n]*" + re.escape(name) + r"[^\n]*\n(.*?)(?=^##\s|\Z)", text, re.S | re.M)
    return m.group(1) if m else None


def spec_units(text):
    """조사 단위 표 → {파일명: [KEY…]} — 셀의 rN_*.md 와 대문자 KEY 토큰을 읽는다."""
    units = {}
    body = section(text, "조사 단위") or ""
    for ln in body.splitlines():
        if not ln.strip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        m = re.search(r"(r\d+[\w\-]*\.md)", cells[0] if cells else "")
        if not m or "{" in m.group(1):
            continue
        keys = re.findall(r"\b([A-Z][A-Z0-9]*_[A-Z0-9_]*[A-Z0-9])\b", " ".join(cells[1:]))   # KEY = PREFIX_NAME
        units[m.group(1)] = list(dict.fromkeys(keys))
    return units


def check_spec(A):
    p = os.path.join(A, "research", "_SPEC.md")
    if not os.path.isfile(p):
        fail("_SPEC.md", "없음", "references/deep-research-spec.md 템플릿을 그대로 복사해 모든 절을 채운다")
        return {}
    t = open(p, encoding="utf-8").read()
    n = len(nonempty(t.splitlines()))
    if n < SPEC_MIN:
        fail("_SPEC.md", f"{n}줄 < {SPEC_MIN} (템플릿을 요약·압축함)", "템플릿의 모든 절을 원문 그대로 두고 { } 값만 채운다 — 품질 규칙·파일 형식 절도 삭제 금지")
    for s in SPEC_SECTIONS:
        if section(t, s) is None:
            fail("_SPEC.md", f"'## {s}' 절 없음", "템플릿 절 제목을 그대로 유지")
    tr = section(t, "도식 전사") or ""
    items = [l for l in tr.splitlines() if l.strip().startswith("- ")]
    if len(items) < 5:
        fail("_SPEC.md 도식 전사", f"전사 항목 {len(items)}개", "입력의 범주·항목·카드 문구를 빠짐없이 '- **항목** — 설명' 으로 전사(항목 수 = 도식 항목 수)")
    web = section(t, "사전 웹 확인") or ""
    urls = set(re.findall(r"https?://[^\s|)]+", web))
    if len(urls) < WEB_MIN:
        fail("_SPEC.md 사전 웹 확인", f"1차 출처 URL {len(urls)}개 < {WEB_MIN}",
             "조사 전에 대제목·제품명·핵심 용어를 웹 검색해 공식 문서·릴리스 노트·What's New·가격·GitHub 를 표로 기록(실존·출시일·현행 상태). 웹 도구가 없으면 curl 로 공식 URL 확인")
    cand = [l for l in (section(t, "도식 판정 후보") or "").splitlines() if l.strip().startswith("- ")]
    if len(cand) < 4:
        fail("_SPEC.md 도식 판정 후보", f"{len(cand)}개", "이 도식에 특화된 확인·반박 질문 4개+ (제품 실존·이름·수치·코드 예시·누락 기둥 등 — 일반론 복붙 금지)")
    units = spec_units(t)
    if len(units) < 3:
        fail("_SPEC.md 조사 단위", f"단위 {len(units)}개", "범주별 r1..rK + r(K+1)_gap + r(K+2)_value — 표에 파일명과 블록 KEY 를 적는다")
    return units


def blocks(text):
    out = []
    for m in re.finditer(r"^# (\S+)[^\n]*\n(.*?)(?=^# \S|\Z)", text, re.S | re.M):
        out.append((m.group(1), m.group(2)))
    return out


def subs(body):
    return [(m.group(1).strip(), m.group(2)) for m in re.finditer(r"^### ([^\n]+)\n(.*?)(?=^### |\Z)", body, re.S | re.M)]


def check_block(fn, key, body):
    where = f"{fn} # {key}"
    if re.search(r"^## ", body, re.M):
        fail(where, "'## ' 제목 사용", "블록 안 소제목은 '### ' 만")
    S = subs(body)
    names = [s[0] for s in S]
    # 원리·비교·누락·통합 블록은 자유 구성, 그 밖(TOOL_ STEP_ ITEM_ …)은 항목 블록 — 유형 A(패키지형) / B(개념형)
    req = None if key.split("_")[0] in OTHER_PREFIX else TYPE_A if "정의" in names or "소스 저장소" in names else TYPE_B
    n = len(nonempty(body.splitlines()))
    if req:
        if n < ITEM_MIN:
            fail(where, f"항목 블록 {n}줄 < {ITEM_MIN}", "소제목마다 표·코드·불릿으로 구체화(공식 API·명령·설정 키·수치+출처)")
        for r_ in req:
            hit = next((s for s in S if s[0].startswith(r_)), None)
            if not hit:
                fail(where, f"필수 소제목 '### {r_}' 없음", "템플릿 순서대로 모든 소제목 작성")
                continue
            lines = nonempty(hit[1].splitlines())
            if r_ == "도식 판정":
                rows = [l for l in lines if l.strip().startswith("|")]
                if len(rows) - 2 < VERDICT_ROWS:
                    fail(where, f"도식 판정 표 {max(len(rows) - 2, 0)}행 < {VERDICT_ROWS}", "도식 항목별로 판정·근거(1차 출처) 행 작성")
            elif r_ in CODE_SUBS:
                if "```" not in hit[1]:
                    fail(where, f"'{r_}' 코드 없음", "실제 API·CLI·IaC 로 동작 가능한 코드(40줄 이하) 1개 이상")
                if len(lines) < IMPL_MIN:
                    fail(where, f"'{r_}' {len(lines)}줄 < {IMPL_MIN}", "코드 + 옵션/설정 표 + 오픈소스 대안(gh api 실측) 추가")
            elif len(lines) < SUB_MIN:
                fail(where, f"'{r_}' {len(lines)}줄 < {SUB_MIN}", "한 줄 요약 금지 — 근거·수치·예를 붙여 3줄 이상")
            if r_ == "소스 저장소" and "|" not in hit[1]:
                fail(where, "'소스 저장소' 실측 표 없음", "gh api 로 ★·SPDX·언어·최근 push 표 작성")
    else:
        if n < OTHER_MIN:
            fail(where, f"블록 {n}줄 < {OTHER_MIN}", "표·코드·불릿으로 비교 기준·수치·출처를 구체화")
        if len(S) < OTHER_SUBS:
            fail(where, f"소제목 {len(S)}개 < {OTHER_SUBS}", "관점별 '### ' 소제목으로 나눠 작성")
        for name, b in S:
            if len(nonempty(b.splitlines())) < 2:
                fail(where, f"'{name}' 1줄", "한 줄 소제목 금지 — 근거·예를 붙인다")


def check_file(A, fn, keys):
    p = os.path.join(A, "research", fn)
    if not os.path.isfile(p):
        fail(fn, "파일 없음", "조사 단위 표대로 작성(서브에이전트 또는 순차)")
        return
    B = blocks(open(p, encoding="utf-8").read())
    have = {k for k, _ in B}
    for k in keys:
        if k not in have:
            fail(fn, f"블록 '# {k}' 없음", "_SPEC.md 조사 단위 표의 KEY 를 그대로 사용")
    content = [(k, b) for k, b in B if k not in ("PAPERS", "REPOS")]
    for k, b in content:
        check_block(fn, k, b)
    pap = dict(B).get("PAPERS")
    if pap is None or "REPOS" not in have:
        fail(fn, "'# PAPERS'·'# REPOS' 블록 없음", "파일 끝에 참고문헌·저장소 블록")
        return
    ent = [l for l in pap.splitlines() if l.strip().startswith("- ")]
    need = max(5, SRC_PER_BLOCK * len(content))
    if len(ent) < need:
        fail(fn, f"참고문헌 {len(ent)}건 < {need} (블록 {len(content)}개 × {SRC_PER_BLOCK})", "블록마다 1차 출처(공식 문서 페이지·릴리스 노트·논문·저장소) 3건+ 를 실제 조회해 기재")
    nourl = [l for l in ent if "arXiv:" not in l and not re.search(r"https?://", l)]
    if nourl:
        fail(fn, f"URL 없는 STD 출처 {len(nourl)}건", "STD 항목은 정식 제목 | 발행 주체 | 연도 | URL")


def check_final(A, no_sample):
    mp = os.path.join(A, "measured.json")
    if not os.path.isfile(mp):
        fail("measured.json", "없음", "verify_sources.py --assets <assets> 실행")
    else:
        m = json.load(open(mp, encoding="utf-8"))
        if m.get("missing"):
            fail("measured.json", f"없는 저장소 {m['missing']}", "본문에서 삭제하거나 정확한 owner/repo 로 수정 후 재검증")
        if m.get("bad_papers"):
            fail("measured.json", f"검증 실패 논문 {m['bad_papers']}", "본문에서 삭제 또는 정확한 arXiv ID")
        if len(m.get("repos", [])) < 5:
            WARNS.append(f"WARN 실측 저장소 {len(m.get('repos', []))}개 — 구현 관점 저장소(공식 SDK·샘플·대안 OSS)를 더 조사")
    figs = glob.glob(os.path.join(A, "fig_*.png"))
    if len(figs) < 3:
        fail("fig_*.png", f"{len(figs)}개 < 3", "재구성 지형도·원리/흐름·★·라이선스·비교 그림을 matplotlib 로 작성")
    if not no_sample:
        code = [f for f in glob.glob(os.path.join(A, "sample", "*")) if os.path.isfile(f) and f.endswith((".py", ".sh", ".ts", ".js", ".tf", ".bicep", ".sql"))]
        out = [f for f in glob.glob(os.path.join(A, "sample", "out", "**", "*"), recursive=True) if os.path.isfile(f)]
        if not code or not out:
            fail("sample/", f"코드 {len(code)}개 · 실행 결과 {len(out)}개",
                 "통합 구현 가이드용 참조 구현을 sample/ 에 작성하고 실제 실행해 sample/out/ 에 결과 저장(보고서에 인용). 실행 불가 환경이면 --no-sample 과 사유를 보고")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--assets", required=True)
    ap.add_argument("--stage", choices=["spec", "research", "final"], default="research")
    ap.add_argument("--unit", action="append", default=[], help="이 파일만 검사(순차 진행 시 단위마다)")
    ap.add_argument("--no-sample", action="store_true")
    a = ap.parse_args()
    A = a.assets
    units = check_spec(A)
    if a.stage != "spec":
        targets = {u: units.get(u, []) for u in a.unit} if a.unit else units
        extra = sorted(os.path.basename(f) for f in glob.glob(os.path.join(A, "research", "r*.md")))
        if not a.unit:
            for f in extra:
                targets.setdefault(f, [])
        for fn, keys in targets.items():
            check_file(A, fn, keys)
    if a.stage == "final":
        check_final(A, a.no_sample)
    for w in WARNS:
        print(w)
    for f in FAILS:
        print(f)
    print(f"{'PASS' if not FAILS else 'FAIL'} stage={a.stage} units={len(units)} fails={len(FAILS)}")
    sys.exit(0 if not FAILS else 1)


if __name__ == "__main__":
    main()
