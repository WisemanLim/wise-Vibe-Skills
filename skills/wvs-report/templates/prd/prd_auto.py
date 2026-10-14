# -*- coding: utf-8 -*-
"""PRD 자동 생성 장·표 — 데이터(units·data_fr·ui_data·repos)에서 바로 만드는 부분. part 파일에서 호출한다.
  fr_chapter(no)        12장 기능 요구사항(도메인 요약 + 도메인별 FR 표)
  screen_list()         15.4 화면 목록 표
  repos_table(cats)     16.2 도메인별 실측 저장소 표
  trace_chapter(no, req_rows)  21장 추적성·누락 검증(도식 요소 → 단위 → FR, 요구 → 장, FR ↔ 화면, 검증 결과)
  appendix_repos()      부록 C 실측 저장소 전수 · appendix_stars() 부록 D 사용자 스타 교차 · r.FIG_TABLE() 부록 E
  gates()               빌드 게이트 — 실패 목록 반환(build_prd 가 assert)
"""
import csv, os
import docx_lib as r
from data import RES, _R, N_REPOS, repo, star, lic, fav, cell
from units import UNITS, DOMAINS, UNIT
from data_fr import ITEMS, FR, ORPHAN, by_unit, n_items
from ui_data import SCREENS, screens_of


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
    r.H(f"{no}.4 검증 결과", 2)
    fails = gates()
    r.KV([("단위 수", str(len(UNITS))), ("FR 수", str(n_items())), ("화면 수", str(len(SCREENS))), ("실측 저장소", str(N_REPOS)),
          ("게이트", "모두 통과" if not fails else " / ".join(fails))])


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
    return fails
