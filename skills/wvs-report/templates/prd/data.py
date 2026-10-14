# -*- coding: utf-8 -*-
"""PRD 공통 데이터 — 제품 정보, GitHub 실측(repos.tsv), 카탈로그(repos_catalog.tsv), 사용자 스타·저장소. wvs-report prd 템플릿.
{ } 값은 기초 보고서·첨부 이미지에서 자동 추출해 채운다."""
import csv, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "research")
OUT_DIR = os.path.dirname(HERE)                                   # <root>/Need-to-be-organized-into-PRD
SYSTEM = "{Brand}"                                                # 제품명(원본 핵심 문구를 드러내는 짧은 브랜드)
FILE_STEM = "{Brand}_{Core-Phrase-Slug}_PRD"                      # 예: ProdAI-Atlas_The-Map-Behind-Production-AI-Systems_PRD
SUBTITLE = "{원본 핵심 문구} — {N 레이어 · M 개념} 마이크로 에이전트 플랫폼 제품 요구사항 정의서 (PRD)"
SRC_TXT = "{인포그래픽 원제} — {핵심 문구} ({원저작자})"            # 원본 도식 표기
BASE_REPORT = "{기초 분석 보고서 파일명(확장자 제외)}"
GITHUB_USER = "{WisemanLim}"
VERSION = "v1.0"


def _tsv_dict(name):
    p = os.path.join(RES, name)
    return list(csv.DictReader(open(p, encoding="utf-8"), delimiter="\t")) if os.path.exists(p) else []


# ---------------- GitHub 실측 ----------------
_R = {}
for row in _tsv_dict("repos.tsv"):
    if not row.get("full_name") or row["full_name"] == "ERR": continue
    _R[row["query"].lower()] = row; _R[row["full_name"].lower()] = row
CAT = {row["full_name"].lower(): row for row in _tsv_dict("repos_catalog.tsv")}
_STARRED = set()
if os.path.exists(os.path.join(RES, "stars_all.tsv")):
    _STARRED = {r[0].lower() for r in csv.reader(open(os.path.join(RES, "stars_all.tsv"), encoding="utf-8"), delimiter="\t") if r}
N_STARS = len(_STARRED)
N_OWN = sum(1 for _ in open(os.path.join(RES, "user_repos.tsv"), encoding="utf-8")) if os.path.exists(os.path.join(RES, "user_repos.tsv")) else 0
N_REPOS = len({v["full_name"] for v in _R.values()})


def _row(name): return _R.get(name.lower())
def repo(name): r = _row(name); return r["full_name"] if r else name
def star(name):
    r = _row(name); return f"{int(r['stars']):,}" if r and str(r["stars"]).isdigit() else "[미확인]"
def fav(name): return " *" if repo(name).lower() in _STARRED else ""          # * = 사용자 스타
def arch(name): r = _row(name); return bool(r and r["archived"] == "true")
def lic(name):
    r = _row(name); spdx = r["license"] if r else "[미확인]"
    c = CAT.get(repo(name).lower())
    if c and c.get("note") and spdx in ("NOASSERTION", "NONE", "Other", ""):
        return re.split(r"\. |;| — |: ", c["note"])[0].replace("★user", "").strip()[:60]
    return spdx
def url(name): return f"https://github.com/{repo(name)}"
def cell(name):
    """표 셀용 'owner/repo (★ · SPDX)*' 표기."""
    return f"{repo(name)} (★{star(name)} · {lic(name)}){fav(name)}" + (" [archived]" if arch(name) else "")
