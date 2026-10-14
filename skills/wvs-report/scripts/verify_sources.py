#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""조사 원문(research/*.md)의 저장소·논문 실존 검증 (wvs-report).

1) '# REPOS' 블록 또는 '## REPOS' 절의 'owner/repo' 를 GitHub API 로 실측(gh_probe.probe) → 실재·이전·라이선스·아카이브
2) 본문의 arXiv ID(YYMM.NNNNN) 를 arxiv.org 초록 페이지 메타(citation_title/author/date)로 조회, 실패분은 export API 배치 재조회
결과: <assets>/measured.json {repos:[…], missing:[…], papers:{id:{title,author,date}}, bad_papers:[…]} + stats.py(N_REPOS, N_PAPERS)
검증 실패(missing·bad_papers)는 보고서에서 삭제하거나 [미확인] 으로 표기한다 — 존재 확인 안 된 논문·저장소는 쓰지 않는다.

사용: verify_sources.py [--assets DIR] [--no-papers] [--workers 8]
"""
import argparse, concurrent.futures as cf, glob, html, json, os, re, subprocess, sys, time
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gh_probe import probe  # noqa: E402

REPO_LINE = re.compile(r"^\s*-?\s*`?([A-Za-z0-9][\w.-]*/[\w.-]+?)`?\s*(?:[—(|:\t].*)?$")


def collect(res):
    text = {os.path.basename(f): open(f, encoding="utf-8").read() for f in sorted(glob.glob(os.path.join(res, "r*.md")))}
    repos, src = [], {}
    for fn, t in text.items():
        for m in re.finditer(r"^#{1,2} REPOS.*?$(.*?)(?=^#{1,2} |\Z)", t, re.S | re.M):
            for ln in m.group(1).splitlines():
                mm = REPO_LINE.match(ln)
                if mm:
                    name = mm.group(1).rstrip(".")
                    if name not in repos: repos.append(name)
                    src.setdefault(name, set()).add(fn.split("_")[0])
    ids = []
    for t in text.values():
        for i in re.findall(r"(?<![\d.])(\d{4}\.\d{4,5})(?:v\d+)?(?!\d)", t):
            if i not in ids and 7 <= int(i[:2]) <= 99 and 1 <= int(i[2:4]) <= 12: ids.append(i)
    return repos, src, ids


def _meta(page, k):
    return [html.unescape(x) for x in re.findall(r'<meta name="%s" content="([^"]*)"' % k, page)]


def arxiv_abs(pid):
    page = ""
    for attempt in range(3):
        page = subprocess.run(["curl", "-s", "-m", "40", f"https://arxiv.org/abs/{pid}"], capture_output=True, text=True).stdout
        if "citation_title" in page or "not found" in page.lower(): break
        time.sleep(5 * (attempt + 1))
    t = _meta(page, "citation_title")
    if not t: return None
    au = _meta(page, "citation_author")
    d = (_meta(page, "citation_date") or ["-"])[0].replace("/", "-")
    return {"title": " ".join(t[0].split()), "author": au[0] if au else "-", "date": d}


def arxiv_api(ids):
    ns = {"a": "http://www.w3.org/2005/Atom"}; found = {}
    for k in range(0, len(ids), 10):
        chunk = ids[k:k + 10]; out = ""
        for attempt in range(4):
            out = subprocess.run(["curl", "-s", "-m", "90", "https://export.arxiv.org/api/query?max_results=20&id_list=" + ",".join(chunk)],
                                 capture_output=True, text=True).stdout
            if "<feed" in out: break
            time.sleep(15 * (attempt + 1))
        if "<feed" not in out: continue
        for e in ET.fromstring(out).findall("a:entry", ns):
            base = re.sub(r"v\d+$", "", e.find("a:id", ns).text.rsplit("/", 1)[-1])
            title = " ".join((e.find("a:title", ns).text or "").split())
            if not title or title == "Error": continue
            au = e.find("a:author/a:name", ns)
            found[base] = {"title": title, "author": au.text if au is not None else "-", "date": e.find("a:published", ns).text[:10]}
        time.sleep(4)
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--assets", default=os.environ.get("WVS_ASSETS") or os.getcwd())
    ap.add_argument("--no-papers", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    res = os.path.join(a.assets, "research")
    repos, src, ids = collect(res)
    with cf.ThreadPoolExecutor(a.workers) as ex:
        rows = list(ex.map(probe, repos))
    meas = [dict(r, src=sorted(src[r["query"]])) for r in rows if r["full_name"] != "ERR"]
    missing = [r["query"] for r in rows if r["full_name"] == "ERR"]
    meas.sort(key=lambda x: -int(x["stars"]))
    papers = {}
    if not a.no_papers:
        for pid in ids:
            m = arxiv_abs(pid)
            if m: papers[pid] = m
            time.sleep(1)
        rest = [i for i in ids if i not in papers]
        if rest: papers.update(arxiv_api(rest))
    bad = [i for i in ids if i not in papers] if not a.no_papers else []
    out = {"repos": meas, "missing": missing, "papers": papers, "bad_papers": bad}
    json.dump(out, open(os.path.join(a.assets, "measured.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(os.path.join(a.assets, "stats.py"), "w").write(f"N_REPOS = {len(meas)}\nN_PAPERS = {len(papers)}\n")
    print(f"repos {len(meas)} missing {missing}")
    print(f"papers {len(papers)} bad {bad}")


if __name__ == "__main__":
    main()
