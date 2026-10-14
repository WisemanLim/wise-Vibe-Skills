# -*- coding: utf-8 -*-
"""Summary-Repos 데이터 계층 — wvs-report repos 템플릿 (<Project>/_assets/ 에 복사).
입력(모두 _assets/ 기준):
  research/map.tsv       분류(NN-Category)<TAB>도구(디렉토리명)<TAB>owner/repo     ← 첨부 전사 + 저장소 매핑 결과
  research/repos.tsv     gh_probe.py 출력(query full_name stars forks license lang archived pushed created branch release release_date desc)
  research/packages.tsv  pkg_probe.py 출력(이름 레지스트리 패키지 버전 업로드일 요구 라이선스)
  research/sizes.tsv     clone_repos.sh 출력(분류/도구 크기)
  trees.json             make_trees.py 출력
  content/extra.py       CFG(표지·출처·단계·시나리오·핵심 발견 등 보고서 고유 값)
"""
import csv, datetime as _dt, json, os, runpy

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "research")
X = runpy.run_path(os.path.join(HERE, "content", "extra.py"))["CFG"]
TODAY = _dt.date.fromisoformat(os.environ.get("WVS_DOC_DATE") or _dt.date.today().isoformat())


def _tsv(name):
    p = os.path.join(RES, name)
    if not os.path.exists(p): return []
    return [r for r in csv.reader(open(p, encoding="utf-8"), delimiter="\t") if r and not r[0].startswith("#")]


MAP = [(c[0], c[1], c[2]) for c in _tsv("map.tsv")]
_PROBE = {r["query"].lower(): r for r in csv.DictReader(open(os.path.join(RES, "repos.tsv"), encoding="utf-8"), delimiter="\t")}
META = {}
for cat, name, repo in MAP:
    p = _PROBE.get(repo.lower(), {})
    ok = p.get("full_name", "ERR") != "ERR"
    META[f"{cat}/{name}"] = {
        "cat": cat, "name": name, "asked": repo, "repo": p.get("full_name") if ok else repo,
        "stars": int(p.get("stars") or 0) if ok else 0, "forks": int(p.get("forks") or 0) if ok else 0,
        "lang": p.get("lang", "-"), "lic": p.get("license", "[미확인]"), "pushed": p.get("pushed", "-"),
        "created": p.get("created", "-"), "archived": p.get("archived") == "true", "branch": p.get("branch", "-"),
        "release": p.get("release", "-"), "release_date": p.get("release_date", "-"), "desc": p.get("desc", ""),
        "moved": ok and p.get("full_name", "").lower() != repo.lower(),
    }
ORDER = list(META)                       # 인포그래픽 분류 순서
CATS = []
for k in ORDER:
    if META[k]["cat"] not in CATS: CATS.append(META[k]["cat"])
PKG = {c[0]: {"reg": c[1], "pkg": c[2], "ver": c[3], "date": c[4], "req": c[5], "lic": c[6]} for c in _tsv("packages.tsv") if len(c) >= 7}
SIZES = {c[0]: c[1].strip() for c in _tsv("sizes.tsv") if len(c) >= 2}
TREES = json.load(open(os.path.join(HERE, "trees.json"), encoding="utf-8")) if os.path.exists(os.path.join(HERE, "trees.json")) else {}
DISPLAY = X.get("DISPLAY", {})          # 디렉토리명 → 인포그래픽 표기명


def disp(k):
    n = META[k]["name"]; return DISPLAY.get(n, n)


def pkg(k):
    return PKG.get(META[k]["name"], {"reg": "-", "pkg": "-", "ver": "-", "date": "-", "req": "-", "lic": "-"})


def last_release(k):
    """GitHub 최신 릴리스와 레지스트리 최신 업로드 중 늦은 날짜(둘 다 없으면 최종 push)."""
    ds = [d for d in (META[k]["release_date"], pkg(k)["date"]) if d and d != "-"]
    return max(ds) if ds else META[k]["pushed"]


def stale(k):
    lr = last_release(k)
    try:
        old = (TODAY - _dt.date.fromisoformat(lr)).days > 365
    except ValueError:
        old = False
    return META[k]["archived"] or old
