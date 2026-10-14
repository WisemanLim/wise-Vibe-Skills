# -*- coding: utf-8 -*-
"""Summary-Repos.docx 빌더 — wvs-report repos 템플릿 (<Project>/_assets/ 에 복사).
장 구성(이전 Summary-Repos.docx 와 동일):
  표지 → 목차 → 1 개요 및 분석 방법 → 2 종합 비교표 → 3 흐름(수명주기) 지도 → 4..(3+K) 분류별 상세
  → 인포그래픽 검증 → 라이선스 및 도입 시 유의사항 → 조합 시나리오 → 부록(클론 목록·출처·재현 절차)
분류별 상세: 분류 개요 · 도구 비교 · 선택 가이드 + 도구별 [개요 · 기본 정보 · 디렉토리 구조 · 설치 및 사용방법 · 활용분야/범위 · 대안 및 선택 기준 · 유의사항]
사용: <venv>/bin/python build_summary.py [--pdf]
"""
import glob, os, re, runpy, sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("WVS_ASSETS", HERE)
sys.path.insert(0, HERE)


def _kit():
    cands = [os.environ.get("WVS_KIT", "")]
    for root in ("~/.claude/skills", "~/.agents/skills", "~/.gemini/config/skills", ".claude/skills", ".agents/skills"):
        cands.append(os.path.join(os.path.expanduser(root), "wvs-report", "scripts"))
    for c in cands:
        if c and os.path.exists(os.path.join(c, "docx_lib.py")):
            return c
    sys.exit("wvs-report/scripts 를 찾을 수 없습니다 — WVS_KIT=<…/wvs-report/scripts> 를 지정하세요.")


sys.path.insert(0, _kit())
import docx_lib as r   # noqa: E402
import sr_data as D    # noqa: E402

X = D.X
PROJ_DIR = os.path.dirname(HERE)
DOCX = os.path.join(PROJ_DIR, "Summary-Repos.docx")
DATE = r.DOC_DATE

# ---------------- 콘텐츠 병합 (조사 에이전트 산출 part_*.py) ----------------
C, CAT = {}, {}
for f in sorted(glob.glob(os.path.join(HERE, "content", "part_*.py"))):
    d = runpy.run_path(f); C.update(d.get("C", {})); CAT.update(d.get("CAT", {}))
missing = [k for k in D.ORDER if k not in C] + [c for c in D.CATS if c not in CAT]
assert not missing, ("content 누락", missing)


def render_md(text):
    """```lang fenced``` → CODE 블록, 나머지 → 문단."""
    parts = re.split(r"```[a-zA-Z0-9_+-]*\n?", text)
    for i, seg in enumerate(parts):
        seg = seg.strip("\n")
        if not seg.strip(): continue
        if i % 2 == 1: r.CODE(seg)
        else:
            for para in seg.split("\n"):
                if para.strip(): r.P(para.strip())


def catname(cat): return CAT[cat]["title"]


N = len(D.ORDER); K = len(D.CATS)
CH0 = 3                                     # 분류 장 = 4 .. 3+K (분류 순서대로 재번호)
CHAP = {cat: CH0 + i + 1 for i, cat in enumerate(D.CATS)}
lic_count, lang_count = {}, {}
for k in D.ORDER:
    lic_count[D.META[k]["lic"]] = lic_count.get(D.META[k]["lic"], 0) + 1
    lang_count[D.META[k]["lang"]] = lang_count.get(D.META[k]["lang"], 0) + 1
STALE = [k for k in D.ORDER if D.stale(k)]
MOVED = [k for k in D.ORDER if D.META[k]["moved"]]
total_stars = sum(D.META[k]["stars"] for k in D.ORDER) or 1
size_note = f"{N}개" + (f"·약 {X['TOTAL_SIZE']}" if X.get("TOTAL_SIZE") else "")

# ---------------- 표지 ----------------
src_line = f"출처: 인포그래픽 「{X['INFOGRAPHIC']}」 ({X['AUTHOR']})" + (f" — {X['SOURCE_URL']}" if X.get("SOURCE_URL") else "")
r.COVER(X["TITLE"], X["SUBTITLE"],
        f"인포그래픽 「{X['INFOGRAPHIC']}」의 {K}개 분류·{N}개 도구를 GitHub 저장소로 매핑해\n"
        f"{X['PROJECT']} 프로젝트에 분류별로 클론하고, 디렉토리 구조·설치·사용방법·활용분야/범위·유의사항을 정리한다.",
        [(f"작성일: {DATE}", 10, None),
         (src_line, 9, r.C_GRAY),
         (f"오픈소스 실측: GitHub REST API(스타·포크·라이선스·아카이브·최종 푸시) + 패키지 레지스트리(최신 버전·런타임 요구), {DATE} 조회", 9, r.C_GRAY),
         (f"클론 위치: {X['PROJECT']}/<NN-분류>/<도구>/ (shallow clone, {size_note})", 9, r.C_GRAY),
         (f"저장 위치: {X['PROJECT']}/Summary-Repos.docx", 9, r.C_GRAY)])

# =============================================================== 1
r.H("1. 개요 및 분석 방법", 1)
r.P(f"본 보고서는 인포그래픽 「{X['INFOGRAPHIC']}」({X['INFOGRAPHIC_DESC']})의 **{K}개 분류·{N}개 도구** 각각에 대해 공식 GitHub 저장소를 "
    "**분류별 디렉토리로 클론** 하고, 저장소마다 개요·기본정보·디렉토리 구조·설치 및 사용방법·활용분야/범위·대안·유의사항을 정리한 요약 문서다. "
    f"분류마다 도구 비교표와 선택 가이드를, 말미에는 인포그래픽 표기와 {DATE} 실측의 차이를 검증한 표를 둔다.")
ok_n = sum(1 for k in D.ORDER if os.path.isdir(os.path.join(PROJ_DIR, k)))
r.KV([
    ("분석 대상", f"인포그래픽의 **{K}개 분류 × {N}개 도구**. 도구 1개 = 공식 저장소 1개"),
    ("저장소 선정", X["SELECTION_RULES"]),
    ("검증 방법", "① `gh api repos/{owner}/{repo}` 로 스타·포크·언어·라이선스(SPDX)·아카이브·최종 푸시·생성일 실측 "
                "② `releases/latest` 와 패키지 레지스트리(PyPI·npm·crates.io) 로 최신 버전·업로드일·런타임 요구 실측 "
                "③ `git clone --depth 1 --single-branch` 로 전부 클론 ④ 각 저장소의 README·매니페스트·docs·소스 트리를 직접 읽어 서술"),
    ("클론 결과", f"**{ok_n}/{N}개 성공**. `NN-분류/도구/` 구조"),
    ("기준 시점", f"**{DATE}**. 스타·버전·유지보수 상태는 변동하므로 조회 시점 기준"),
    ("디렉토리 트리", "깊이 2, 최상위 12개·하위 4개까지 표시, 숨김 파일(.github 등) 제외. 전체 구조는 클론 위치에서 확인"),
], key_width_cm=3.2)
NV, NL, NS = CH0 + K + 1, CH0 + K + 2, CH0 + K + 3
r.H("문서 구성 요약", 3)
r.T(["장", "내용"],
    [["1", "개요 및 분석 방법 — 선정·검증·클론 결과, 원본 인포그래픽"],
     ["2", f"종합 비교표 — {N}개 저장소의 분류·언어·라이선스·스타·최신 버전 + 스타·유지보수 신호 그림"],
     ["3", f"{X['FLOW_TITLE']} 지도 — {K}개 분류를 흐름 단계와 횡단 영역으로 재배치"],
     [f"4~{CH0 + K}", "분류별 상세 — 분류 개요·도구 비교표·선택 가이드 + 도구별 개요/기본정보/디렉토리 구조/설치·사용/활용분야·범위/대안/유의사항"],
     [str(NV), "인포그래픽 검증 — 저장소 이전·아카이브·명칭·범주 적합성 판정"],
     [str(NL), "라이선스 및 도입 시 유의사항"], [str(NS), "조합 시나리오 — 과제 유형별 도구 스택 예시"],
     ["부록", "클론 목록·출처·재현 절차"]], widths=r.W([1.6, 15.99]))
r.H("공통 특징", 3)
r.B(f"**GitHub 주 언어 분포** — " + ", ".join(f"{l} {c}" for l, c in sorted(lang_count.items(), key=lambda x: -x[1])) + ".")
r.B(f"**라이선스 분포** — " + ", ".join(f"{l} {c}" for l, c in sorted(lic_count.items(), key=lambda x: -x[1]))
    + ". NOASSERTION/NONE 은 원문 확인 필요(라이선스 장).")
if STALE:
    r.B(f"**유지보수 신호가 약한 도구 {len(STALE)}개** — " + ", ".join(D.disp(k) for k in STALE) + ". 아카이브되었거나 최근 1년간 릴리스가 없다.")
if MOVED:
    r.B(f"**저장소 이전 {len(MOVED)}건** — " + ", ".join(f"{D.disp(k)}→`{D.META[k]['repo']}`" for k in MOVED)
        + ". 과거 URL 은 리다이렉트되지만 의존성 고정(git URL)·CI 배지는 새 경로로 바꿔야 한다.")
top3 = sorted(D.ORDER, key=lambda k: -D.META[k]["stars"])[:3]
r.B(f"**인지도 편차** — 합계 스타 {total_stars:,}개 중 " + "·".join(D.disp(k) for k in top3)
    + f" 3개가 약 {round(100 * sum(D.META[k]['stars'] for k in top3) / total_stars)}% 를 차지한다. 스타는 채택도의 대리 지표일 뿐 품질 지표가 아니다.")
for b in X.get("COMMON", []): r.B(b)
r.P(f"원본 인포그래픽은 그림 1 과 같다. {X['INFOGRAPHIC_DESC']}.")
r.FIG("infographic.png", 11.5, f"원본 인포그래픽 「{X['INFOGRAPHIC']}」", f"{X['AUTHOR']} · 사용자 첨부 이미지, 분석 목적 인용")

# =============================================================== 2
r.H("2. 종합 비교표", 1)
r.P(f"인포그래픽 분류 순서대로 정리했다. 스타·라이선스는 GitHub API, 최신 버전은 패키지 레지스트리(없으면 GitHub 릴리스) 기준이며 모두 {DATE} 조회다. "
    "'상태' 열의 ▲ 는 아카이브 또는 최근 1년 릴리스 없음.")
rows = []
for i, k in enumerate(D.ORDER, 1):
    m, p = D.META[k], D.pkg(k)
    ver = p["ver"] if p["ver"] != "-" else m["release"]
    rows.append([str(i), m["cat"][:2], D.disp(k), m["repo"], m["lang"], m["lic"], f'{m["stars"]:,}', f"{ver} ({D.last_release(k)})", "▲" if D.stale(k) else ""])
r.T(["#", "분류", "도구", "GitHub 저장소", "언어", "라이선스", "스타", "최신 버전 (일자)", "상태"], rows,
    widths=r.W([0.7, 0.9, 2.9, 4.3, 1.8, 2.1, 1.4, 2.8, 0.69]), font=7)
r.FIG("fig_stars.png", 15.0, f"분류별 저장소 GitHub 스타 (로그 스케일, {DATE} 조회)", "본 보고서 작성")
r.P("그림 3 은 최신 릴리스 시점과 스타를 함께 보여준다. 점선 왼쪽(주황)이 유지보수 신호가 약한 도구다.")
r.FIG("fig_activity.png", 15.0, "유지보수 신호 — 최신 릴리스 일자(GitHub 릴리스·레지스트리 중 늦은 쪽) × GitHub 스타", "본 보고서 작성")

# =============================================================== 3
r.H(f"3. {X['FLOW_TITLE']} 지도", 1)
r.P(f"인포그래픽의 {K}개 분류를 **{X['FLOW_TITLE']}** 의 흐름 단계와 횡단 영역으로 재배치했다(보고서 재구성).")
r.FIG("fig_lifecycle.png", 17.0, f"{K}개 분류의 {X['FLOW_TITLE']} 배치", "본 보고서 재구성")
srows = []
for stage, cats in X["STAGES"] + X.get("CROSS", []):
    for cat in cats:
        if cat in D.CATS:
            srows.append([stage, f"{cat[:2]} {catname(cat)}", CAT[cat]["ko"],
                          ", ".join(D.disp(k) for k in D.ORDER if D.META[k]["cat"] == cat), f"{CHAP[cat]}장"])
r.T(["단계", "인포그래픽 분류", "국문", "도구", "상세"], srows, widths=r.W([3.2, 4.4, 2.8, 5.8, 1.39]), font=7.5)
r.P(X["FLOW_READING"])

# =============================================================== 분류별
for cat in D.CATS:
    cc = CAT[cat]; n = CHAP[cat]
    r.H(f"{n}. {catname(cat)} — {cc['ko']}", 1)
    r.P(cc["intro"])
    r.H("도구 비교", 3)
    hdr, *body = cc["cmp"]
    r.T(hdr, body, widths=r.W([2.6, 3.9, 2.6, 4.3, 4.19][:len(hdr)]), font=7.5)
    r.H("선택 가이드", 3)
    for g in cc["guide"]: r.B(g)
    for j, k in enumerate([k for k in D.ORDER if D.META[k]["cat"] == cat], 1):
        m, c, p = D.META[k], C[k], D.pkg(k)
        r.H(f"{n}.{j} {D.disp(k)}", 2)
        r.H("개요", 3); r.P(c["ov"])
        r.H("기본 정보", 3)
        r.KV([
            ("GitHub 저장소", f"`{m['repo']}`  (https://github.com/{m['repo']})" + ("  **[아카이브됨]**" if m["archived"] else "")
             + (f"  — 인포그래픽·요청 표기 `{m['asked']}` 에서 이전" if m["moved"] else "")),
            ("클론 위치", f"`{X['PROJECT']}/{k}/`  ({D.SIZES.get(k, '-')}, 기본 브랜치 `{m['branch']}`)"),
            ("설치 패키지", f"`{c.get('pkg', p['pkg'])}`  — {p['reg']} 최신 {p['ver']} ({p['date']}), 요구 {c.get('py') or p['req']}"),
            ("GitHub 최신 릴리스", f"{m['release']} ({m['release_date']})" if m["release"] != "-" else "릴리스 없음"),
            ("구현 / 언어", f"{c.get('core', '-')}  (GitHub 주 언어: {m['lang']})"),
            ("라이선스", m["lic"]), ("스타 / 포크", f"{m['stars']:,} / {m['forks']:,}"),
            ("생성 / 최종 푸시", f"{m['created']} / {m['pushed']}"),
        ], key_width_cm=3.4, font=8.5)
        r.H("디렉토리 구조", 3)
        r.CODE(D.TREES.get(k, "(트리 없음 — make_trees.py 실행 필요)"), font=7.5)
        if c.get("dirs"):
            r.T(["경로", "역할"], [[f"`{a}`", b] for a, b in c["dirs"]], widths=r.W([4.2, 13.39]), font=7.5)
        r.H("설치 및 사용방법", 3); render_md(c["use"])
        r.H("활용분야 / 범위", 3); r.P(c["app"])
        if c.get("alt"):
            r.H("대안 및 선택 기준", 3); r.P(c["alt"])
        r.H("유의사항", 3); r.P(c["note"])

# =============================================================== 인포그래픽 검증
r.H(f"{NV}. 인포그래픽 검증", 1)
r.P(f"인포그래픽의 도구 표기·분류가 {DATE} 실제 상태와 맞는지 분류별로 확인했다. 판정 기준 — **일치**: 표기대로 사용 가능 / "
    "**변경**: 이전·개명·세대교체로 표기 갱신 필요 / **부정확**: 범주·명칭이 사실과 다름 / **주의**: 사용은 가능하나 유지보수·라이선스 리스크.")
vrows, tally = [], {}
for cat in D.CATS:
    hdr, *body = CAT[cat]["check"]
    for row in body:
        vrows.append([cat[:2]] + list(row))
        v = re.sub(r"[^가-힣]", "", str(row[-1]))[:3]
        tally[v] = tally.get(v, 0) + 1
r.T(["분류", "항목", "인포그래픽 표기/암시", f"실측({DATE})", "판정"], vrows, widths=r.W([1.0, 3.0, 4.3, 7.6, 1.69]), font=7)
r.H("판정 집계", 3)
r.T(["판정", "건수"], [[k, str(v)] for k, v in sorted(tally.items(), key=lambda x: -x[1])], widths=r.W([8, 9.59]), font=8)
r.H("핵심 발견", 3)
for b in X.get("FINDINGS", []): r.B(b)

# =============================================================== 라이선스
r.H(f"{NL}. 라이선스 및 도입 시 유의사항", 1)
r.H("라이선스 분포", 3)
LICDESC = {"Apache-2.0": "허용적 + 특허 라이선스 명시. NOTICE 파일 고지 유지", "MIT": "허용적 — 저작권·라이선스 고지 유지 시 자유 사용·수정·재배포",
           "BSD-3-Clause": "허용적 — 고지 유지 + 저작자 이름의 홍보 사용 금지", "BSD-2-Clause": "허용적 — 고지 유지",
           "GPL-3.0": "강한 copyleft — 배포 시 소스 공개 의무 전파", "AGPL-3.0": "네트워크 copyleft — SaaS 제공 시에도 소스 공개 의무",
           "LGPL-3.0": "약한 copyleft — 동적 링크 시 완화", "MPL-2.0": "파일 단위 copyleft",
           "NOASSERTION": "GitHub 가 SPDX 로 판정 못함(복수·커스텀 라이선스) — LICENSE 원문 확인", "NONE": "LICENSE 미인식 — 저장소 내 라이선스 파일 직접 확인"}
r.T(["라이선스", "개수", "도구", "의미·주의"],
    [[lic, str(cnt), ", ".join(D.disp(k) for k in D.ORDER if D.META[k]["lic"] == lic), LICDESC.get(lic, "원문 확인")]
     for lic, cnt in sorted(lic_count.items(), key=lambda x: -x[1])], widths=r.W([2.6, 1.1, 7.4, 6.49]), font=7.5)
r.H("도구별 라이선스 특이사항", 3)
for k in D.ORDER:
    if D.META[k]["lic"] in ("NOASSERTION", "NONE") or D.META[k]["archived"] or "GPL" in D.META[k]["lic"]:
        r.B(f"**{D.disp(k)}** ({D.META[k]['lic']}) — " + C[k]["note"].split(". ")[0].rstrip(".") + ".")
r.H("도입 시 공통 유의", 3)
for b in X.get("ADOPTION_NOTES", []): r.B(b)

# =============================================================== 조합 시나리오
r.H(f"{NS}. 조합 시나리오", 1)
r.P("과제 유형별로 각 분류(단계)에서 1개씩 고른 최소 스택 예시다. 괄호는 대체 후보.")
sc = X["SCENARIOS"]
r.T(sc["header"], sc["rows"], widths=r.W([3.4] + [3.5] * (len(sc["header"]) - 1)), font=7.5)
for p in sc.get("notes", []): r.P(p)

# =============================================================== 부록
r.H("부록. 클론 목록·출처·재현 절차", 1)
r.H("클론 목록", 3)
r.T([f"클론 경로({X['PROJECT']}/)", "원격 저장소", "크기", "브랜치"],
    [[k, D.META[k]["repo"], D.SIZES.get(k, "-"), D.META[k]["branch"]] for k in D.ORDER], widths=r.W([7.4, 6.2, 1.7, 2.29]), font=7)
r.H("출처", 3)
r.B(f"인포그래픽 「{X['INFOGRAPHIC']}」 — {X['AUTHOR']}." + (f" {X['SOURCE_URL']}" if X.get("SOURCE_URL") else " 원 게시 URL [미확인]."))
r.B(f"GitHub REST API `repos/{{owner}}/{{repo}}`, `repos/{{owner}}/{{repo}}/releases/latest` ({DATE} 조회).")
r.B(f"패키지 레지스트리 API — PyPI `https://pypi.org/pypi/{{pkg}}/json` · npm `https://registry.npmjs.org/{{pkg}}` · crates.io ({DATE} 조회).")
r.B("각 저장소의 README·매니페스트(pyproject.toml·package.json·Cargo.toml 등)·docs (클론 시점 기본 브랜치 HEAD).")
for b in X.get("EXTRA_SOURCES", []): r.B(b)
r.H("재현 절차", 3)
r.CODE(f"cd {X['PROJECT']}\n"
       "KIT=<skills>/wvs-report/scripts\n"
       "# 1. 매핑표(분류\\t도구\\towner/repo) → GitHub·레지스트리 실측\n"
       "python3 $KIT/gh_probe.py _assets/research/map.tsv --col 3 -o _assets/research/repos.tsv\n"
       "python3 $KIT/pkg_probe.py _assets/research/pkg_map.tsv -o _assets/research/packages.tsv\n"
       "# 2. 분류별 shallow clone (6 병렬) + 트리\n"
       "bash $KIT/clone_repos.sh _assets/research/map.tsv . 6\n"
       "python3 $KIT/make_trees.py _assets/research/map.tsv . -o _assets/trees.json\n"
       "# 3. 그림·보고서 빌드 (+PDF)\n"
       "_assets/.venv/bin/python _assets/figs.py\n"
       "_assets/.venv/bin/python _assets/build_summary.py --pdf")

r.SAVE(DOCX, pdf="--pdf" in sys.argv)
