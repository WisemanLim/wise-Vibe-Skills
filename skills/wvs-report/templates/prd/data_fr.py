# -*- coding: utf-8 -*-
"""기능 요구사항(FR) 카탈로그 — research/r*.md 의 '## 4. FR 후보' 표를 읽어 도메인·단위 에이전트별로 정규화한다.
항목 튜플: (ID, 이름, 하는 일, 구현 요지, 우선순위, 참고 OSS, 근거, 단위 ID)
ID 는 조사 파일의 원래 ID(FR-<단위ID>-NN)를 그대로 쓴다 — 단위 에이전트와 1:1 추적.
도메인 목록(DOMAINS)은 units.py 에서 만든다(원본 도식의 레이어·카드 순서)."""
import glob, os, re
from units import UNITS, DOMAINS   # DOMAINS: [(도메인 ID, 레이어, 이름, 요지, [단위 ID…])]

_RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "research")
UNIT_NAME = {}   # 단위 ID → 에이전트명 (### 소제목에서 수집)
_ID = re.compile(r"^\**(FR-([A-Z0-9]+(?:-[A-Z0-9]+)*?)-(\d{2,3}))\**$")


def _split(line):
    """표 행 분리 — `코드` 안과 \\| 의 파이프는 구분자로 보지 않는다."""
    line = line.strip()
    if line.startswith("|"): line = line[1:]
    if line.endswith("|"): line = line[:-1]
    cells, cur, code, i = [], "", False, 0
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line) and line[i + 1] == "|":
            cur += "|"; i += 2; continue
        if ch == "`": code = not code
        if ch == "|" and not code:
            cells.append(cur); cur = ""
        else:
            cur += ch
        i += 1
    cells.append(cur)
    return [c.strip().replace("<br>", " / ") for c in cells]


def _rows():
    out = []
    for p in sorted(glob.glob(os.path.join(_RES, "r[0-9]*_*.md"))):
        on = False
        for l in open(p, encoding="utf-8").read().split("\n"):
            if l.startswith("## "):
                on = l.startswith("## 4"); continue
            if not on: continue
            if l.startswith("###"):
                m = re.match(r"^#+\s*([A-Z0-9]+(?:-[A-Z0-9]+)*)\s+(.*)$", l)
                if m: UNIT_NAME.setdefault(m.group(1), m.group(2).strip())
                continue
            if not l.startswith("|"): continue
            c = _split(l)
            m = _ID.match(c[0])
            if not m or len(c) < 7: continue
            name, does, impl, pri, oss, basis = [x.strip() for x in c[1:7]]
            pm = re.search(r"P[0-2]", pri)
            out.append((m.group(1), name.strip("*"), does, impl, pm.group(0) if pm else pri, oss, basis, m.group(2), os.path.basename(p)))
    return out


ITEMS = {d[0]: [] for d in DOMAINS}
_UNIT2DOM = {u: d[0] for d in DOMAINS for u in d[4]}
ORPHAN = []      # 단위 ID 가 카탈로그에 없는 FR — 빌드 게이트에서 0 이어야 함
_seen = set()
for row in _rows():
    fid, unit = row[0], row[7]
    if fid in _seen: continue
    _seen.add(fid)
    dom = _UNIT2DOM.get(unit)
    if not dom:
        ORPHAN.append(fid); continue
    ITEMS[dom].append(row[:8])
FR = {it[0]: it for v in ITEMS.values() for it in v}


def n_items():
    return sum(len(v) for v in ITEMS.values())


def by_unit(unit):
    return [it for v in ITEMS.values() for it in v if it[7] == unit]


def fr_find(*keywords, domain=None):
    out = []
    for d, v in ITEMS.items():
        if domain and d != domain: continue
        for it in v:
            s = (it[1] + " " + it[2]).lower()
            if all(k.lower() in s for k in keywords): out.append(it[0])
    return out


if __name__ == "__main__":
    for d, v in ITEMS.items():
        pc = {p: sum(1 for x in v if x[4] == p) for p in ("P0", "P1", "P2")}
        print(d, len(v), pc)
    print("total", n_items(), "· orphan", ORPHAN)
    print("units without FR:", [u[0] for u in UNITS if not by_unit(u[0])])
