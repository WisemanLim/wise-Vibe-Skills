# -*- coding: utf-8 -*-
"""PRD 자동 생성 장·표 — 데이터(units·data_fr·ui_data·repos)에서 바로 만드는 부분. part 파일에서 호출한다.
  fr_chapter(no)        12장 기능 요구사항(도메인 요약 + 도메인별 FR 표)
  screen_list()         15.4 화면 목록 표
  repos_table(cats)     16.2 도메인별 실측 저장소 표
  trace_chapter(no, req_rows)  21장 추적성·누락 검증(도식 요소 → 단위 → FR, 요구 → 장, FR ↔ 화면, 검증 결과)
  appendix_repos()      부록 C 실측 저장소 전수 · appendix_stars() 부록 D 사용자 스타 교차 · r.FIG_TABLE() 부록 E
  inputs_table()        2.1 입력 인벤토리(분석 보고서·요구사항 문서·이미지·참고 URL·요청문 — research/inputs.json)
  req_table()           3.x 요구사항 문서 정리(RQ — research/req_items.tsv) + 매핑된 FR·NFR·장
  gates()               빌드 게이트 — 실패 목록 반환(build_prd 가 assert)
RQ 매핑: FR 의 '근거' 열에 RQ-ID 를 쓰면 자동 매핑. FR 이 아닌 곳(NFR·제약·장)으로 가는 RQ 는 research/req_map.tsv(rq_id<TAB>대상들<TAB>비고)에 적는다.
"""
import csv, json, os, re
import docx_lib as r
from data import RES, _R, N_REPOS, repo, star, lic, fav, cell
from units import UNITS, DOMAINS, UNIT
from data_fr import ITEMS, FR, ORPHAN, by_unit, n_items
from ui_data import SCREENS, screens_of


# ---------------- 입력·요구사항(RQ)
INPUTS = json.load(open(os.path.join(RES, "inputs.json"), encoding="utf-8")) if os.path.exists(os.path.join(RES, "inputs.json")) else []
RQ = list(csv.DictReader(open(os.path.join(RES, "req_items.tsv"), encoding="utf-8"), delimiter="\t")) if os.path.exists(os.path.join(RES, "req_items.tsv")) else []
REQ_MAP = {}
if os.path.exists(os.path.join(RES, "req_map.tsv")):
    for row in csv.reader(open(os.path.join(RES, "req_map.tsv"), encoding="utf-8"), delimiter="\t"):
        if row and re.match(r"RQ-\d+", row[0]): REQ_MAP[row[0]] = (row[1] if len(row) > 1 else "", row[2] if len(row) > 2 else "")
RQ_REQUIRED = ("fr", "ui", "nfr", "constraint")      # 반드시 FR·NFR·장으로 이어져야 하는 유형 (goal·non-goal·info 는 표에만)
TYPE_KO = {"report": "분석 보고서", "req": "요구사항·개발방향 문서", "image": "첨부 이미지", "github": "GitHub 저장소", "site": "참고 사이트",
           "prompt": "사용자 요청문", "fr": "기능", "ui": "UI/UX", "nfr": "비기능", "constraint": "제약", "goal": "목표", "non-goal": "범위 제외", "info": "참고"}


def inputs_of(*types):
    return [i for i in INPUTS if i["type"] in types]


def rq_targets(rq_id):
    """RQ → 매핑 대상(FR ID 들 + req_map 대상)."""
    frs = [f for f, it in FR.items() if re.search(rf"\b{re.escape(rq_id)}\b", it[6] + " " + it[2])]
    extra = REQ_MAP.get(rq_id, ("", ""))[0].split()
    return frs + [x for x in extra if x not in frs]


def inputs_unsummarized():
    """_INPUTS.md 의 '### IN-NN' 블록 중 메타 줄·주석 외 내용이 없는 입력 ID."""
    p = os.path.join(RES, "_INPUTS.md")
    if not INPUTS or not os.path.exists(p): return []
    blocks = re.split(r"^### ", re.sub(r"(?s)<!--.*?-->", "", open(p, encoding="utf-8").read()), flags=re.M)[1:]
    empty = []
    for b in blocks:
        head, *body = b.splitlines()
        body = [x for x in body if x.strip() and not x.lstrip().startswith("- 유형:") and not x.startswith("## ")]
        if head.split()[0].startswith("IN-") and not body: empty.append(head.split()[0])
    return empty


def inputs_table():
    if not INPUTS:
        r.P("입력 인벤토리 없음(research/inputs.json) — prd_intake.py 를 먼저 실행한다.", size=9); return
    r.T(["ID", "유형", "제목", "위치(경로·URL)", "접근일", "이용 범위·출처 표기"],
        [[i["id"], TYPE_KO.get(i["type"], i["type"]), i.get("title", "") or "-", i["src"] if i["src"].startswith("http") else os.path.basename(i["src"]),
          i.get("accessed", "-"), i.get("credit") or {"image": "사용자 첨부 이미지, 분석 목적 인용", "site": "기능·구조 참고(문구·이미지 복제 없음)",
                                                       "github": "저장소 실측·README 참고", "report": "기초 분석 보고서", "req": "요구사항 원천",
                                                       "prompt": "요구사항 원천"}.get(i["type"], "-")] for i in INPUTS],
        widths=r.W([1.1, 2.2, 4.2, 5.6, 1.7, 3.6]), font=6.8)


def req_table():
    if not RQ:
        r.P("요구사항 문서 입력 없음 — 요구는 원본 도식·분석 보고서·요청문에서 도출했다.", size=9); return
    r.T(["RQ", "입력", "구분", "P", "요구 내용(원문 요약)", "→ FR·NFR·장"],
        [[q["id"], q["input"], TYPE_KO.get(q["type"], q["type"]), q["priority"], q["text"],
          " ".join(rq_targets(q["id"])) or ("—" if q["type"] not in RQ_REQUIRED else "미매핑")] for q in RQ],
        widths=r.W([1.3, 1.2, 1.4, 0.7, 8.2, 4.8]), font=6.6)


def fr_chapter(no=12):
    r.H(f"{no}. 기능 요구사항", 1)
    r.P(f"{len(DOMAINS)}개 도메인 · 단위 {len(UNITS)}개 · FR {n_items()}개. ID 는 `FR-<단위ID>-NN` 이며 조사 원문(research/r*.md '## 4. FR 후보')을 그대로 옮겼다. "
        "구현 요지는 라이브러리·API·알고리즘·설정 키 수준이고, 참고 OSS 는 16장 실측 저장소다.", size=9.2)
    r.H(f"{no}.1 도메인 요약", 2)
    rows = []
    for d, layer, name, summ, units in DOMAINS:
        v = ITEMS[d]
        rows.append([d, layer, name, str(len(units)), str(len(v))] + [str(sum(1 for x in v if x[4] == p)) for p in ("P0", "P1", "P2")])
    r.T(["도메인", "레이어", "이름", "단위", "FR", "P0", "P1", "P2"], rows, widths=r.W([1.4, 1.2, 6, 1.2, 1.2, 1, 1, 1]), font=7.6)
    for i, (d, layer, name, summ, units) in enumerate(DOMAINS, 2):
        r.H(f"{no}.{i} {d} {name}", 2)
        r.P(f"도식 요지: {summ}", size=8.8)
        for u in units:
            its = by_unit(u)
            if not its: continue
            r.P(f"**{u} {UNIT[u][3]}** — {UNIT[u][5]}", size=8.8, sa=2)
            r.T(["ID", "이름", "하는 일", "구현 요지", "P", "참고 OSS"],
                [[it[0], it[1], it[2], it[3], it[4], it[5]] for it in its], widths=r.W([2.4, 2.4, 4.2, 6.0, 0.7, 2.6]), font=6.6)


def screen_list():
    r.T(["화면 ID", "화면명", "라우트", "권한", "유형", "P", "관련 FR"],
        [[s[0], s[1], s[2], s[3], s[6], s[5], " ".join(s[4].split()[:4]) + (f" 외 {len(s[4].split()) - 4}" if len(s[4].split()) > 4 else "")] for s in SCREENS],
        widths=r.W([1.3, 3.8, 3.4, 1.8, 0.8, 0.8, 5.6]), font=6.8)


def repos_table(categories=None):
    rows = []
    cat_path = os.path.join(RES, "repos_catalog.tsv")
    catalog = list(csv.DictReader(open(cat_path, encoding="utf-8"), delimiter="\t")) if os.path.exists(cat_path) else []
    for c in catalog:
        if categories and c["category"] not in categories: continue
        if c["full_name"].lower() not in _R: continue
        rows.append([cell(c["full_name"]), c["adopt"], c["role_ko"]])
    r.T(["저장소 (★ · 라이선스, * 사용자 스타)", "결합", "역할"], rows, widths=r.W([7.5, 1.2, 8.9]), font=6.8)


def appendix_repos():
    rows = sorted({v["full_name"]: v for v in _R.values()}.values(), key=lambda x: -int(x["stars"] or 0))
    r.T(["저장소", "★", "라이선스", "아카이브", "최근 push", "최신 릴리스"],
        [[x["full_name"] + fav(x["full_name"]), f"{int(x['stars'] or 0):,}", x["license"], "예" if x["archived"] == "true" else "",
          x.get("pushed", "-"), f"{x.get('release', '-')} {x.get('release_date', '')}".strip()] for x in rows],
        widths=r.W([6.2, 1.6, 2.4, 1.4, 2.0, 4.0]), font=6.4)


def appendix_stars():
    p = os.path.join(RES, "stars_relevant.tsv")
    if not os.path.exists(p):
        r.P("사용자 스타 선별표 없음(stars_relevant.tsv).", size=9); return
    rows = list(csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"))
    r.T(["저장소", "★", "라이선스", "단위", "용도", "결합"],
        [[x["full_name"], x.get("stars", "-"), x.get("license", "-"), x.get("unit", "-"), x.get("use_ko", ""), x.get("adopt", "")] for x in rows],
        widths=r.W([5.4, 1.4, 2.2, 1.6, 5.8, 1.2]), font=6.6)


def trace_chapter(no=21, req_rows=()):
    r.H(f"{no}. 추적성·누락 검증", 1)
    r.H(f"{no}.1 원본 도식 요소 → 단위 에이전트 → FR", 2)
    r.T(["원본 도식 요소(원문)", "단위", "에이전트", "FR"],
        [[u[4], u[0], u[3], ", ".join(it[0] for it in by_unit(u[0]))] for u in UNITS], widths=r.W([5.6, 1.8, 3.0, 7.2]), font=6.4)
    r.H(f"{no}.2 사용자 요구 → 장", 2)
    r.T(["#", "사용자 요구", "반영 장"], list(req_rows), widths=r.W([0.6, 12, 5]), font=7.2)
    r.H(f"{no}.3 FR ↔ 화면 커버리지", 2)
    rows = []
    for d, *_ in DOMAINS:
        v = ITEMS[d]; cov = sum(1 for it in v if screens_of(it[0]))
        rows.append([d, str(len(v)), str(cov), f"{100 * cov / len(v):.0f}%" if v else "-"])
    r.T(["도메인", "FR", "화면 매핑", "커버리지"], rows, widths=r.W([4, 3, 3, 3]), font=7.6)
    sec = 4
    if RQ:
        r.H(f"{no}.4 요구사항 문서(RQ) → FR·NFR·장", 2); sec = 5
        r.T(["RQ", "입력", "구분", "→ FR·NFR·장"],
            [[q["id"], q["input"], TYPE_KO.get(q["type"], q["type"]),
              " ".join(rq_targets(q["id"])) or ("—" if q["type"] not in RQ_REQUIRED else "미매핑")] for q in RQ],
            widths=r.W([1.4, 1.3, 1.6, 13.3]), font=6.6)
    r.H(f"{no}.{sec} 검증 결과", 2)
    fails = gates()
    req_rq = [q for q in RQ if q["type"] in RQ_REQUIRED]
    r.KV([("입력", " · ".join(f"{TYPE_KO.get(t, t)} {sum(1 for i in INPUTS if i['type'] == t)}" for t in dict.fromkeys(i["type"] for i in INPUTS)) or "-"),
          ("단위 수", str(len(UNITS))), ("FR 수", str(n_items())), ("요구 항목(RQ)", f"{len(RQ)}개 (추적 대상 {len(req_rq)}개)"),
          ("화면 수", str(len(SCREENS))), ("실측 저장소", str(N_REPOS)), ("게이트", "모두 통과" if not fails else " / ".join(fails))])


def gates():
    fails = []
    no_fr = [u[0] for u in UNITS if not by_unit(u[0])]
    if no_fr: fails.append(f"FR 없는 단위 {no_fr}")
    if ORPHAN: fails.append(f"카탈로그 밖 단위의 FR {ORPHAN[:10]}")
    uncovered = [f for f in FR if not screens_of(f)]
    if uncovered: fails.append(f"화면 미커버 FR {len(uncovered)}개 {uncovered[:10]}")
    ghost = sorted({f for s in SCREENS for f in s[4].split() if f not in FR})
    if ghost: fails.append(f"화면의 유령 FR {ghost[:10]}")
    bad_oss = sorted({o.strip() for it in FR.values() for o in it[5].replace("·", " ").replace(",", " ").split()
                      if o.count("/") == 1 and o.strip().lower() not in _R})
    if bad_oss: fails.append(f"실측 안 된 참고 OSS {bad_oss[:10]}")
    unmapped = [q["id"] for q in RQ if q["type"] in RQ_REQUIRED and not rq_targets(q["id"])]
    if unmapped: fails.append(f"FR·NFR·장으로 이어지지 않은 요구 항목 {len(unmapped)}개 {unmapped[:10]}")
    empty = inputs_unsummarized()
    if empty: fails.append(f"_INPUTS.md 에 전사·요약이 없는 입력 {empty}")
    bad_map = sorted({x for v in REQ_MAP.values() for x in v[0].split() if x.startswith("FR-") and x not in FR})
    if bad_map: fails.append(f"req_map.tsv 의 없는 FR {bad_map[:10]}")
    return fails
