#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub 저장소 실측 (wvs-report) — stars·forks·license(SPDX)·language·archived·pushed·created·default branch·
최신 릴리스·설명을 조회해 TSV 로 저장한다. 리다이렉트(저장소 이전)는 full_name 이 달라지는 것으로 드러난다.

입력: 'owner/repo' 한 줄씩(또는 탭 구분 첫 열 / --col N 열). '#' 주석 무시.
출력 열: query full_name stars forks license lang archived pushed created branch release release_date desc
조회 수단: gh api(인증, 권장) → 실패 시 https://api.github.com 익명(시간당 60회 제한).

사용: gh_probe.py repos.txt -o research/repos.tsv [--col 3] [--workers 8]
"""
import argparse, concurrent.futures as cf, json, shutil, subprocess, sys, urllib.request

COLS = ["query", "full_name", "stars", "forks", "license", "lang", "archived", "pushed", "created", "branch",
        "release", "release_date", "desc"]


def _api(path):
    if shutil.which("gh"):
        p = subprocess.run(["gh", "api", path], capture_output=True, text=True)
        if p.returncode == 0:
            return json.loads(p.stdout)
        if "Not Found" in p.stderr or "404" in p.stderr:
            return None
    try:
        req = urllib.request.Request("https://api.github.com/" + path, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def probe(q):
    d = _api(f"repos/{q}")
    if not d or "full_name" not in d:
        return {"query": q, "full_name": "ERR"}
    rel = _api(f"repos/{d['full_name']}/releases/latest") or {}
    return {
        "query": q, "full_name": d["full_name"], "stars": d.get("stargazers_count", 0), "forks": d.get("forks_count", 0),
        "license": ((d.get("license") or {}).get("spdx_id") or "NONE"), "lang": d.get("language") or "-",
        "archived": str(bool(d.get("archived"))).lower(), "pushed": (d.get("pushed_at") or "")[:10],
        "created": (d.get("created_at") or "")[:10], "branch": d.get("default_branch") or "-",
        "release": rel.get("tag_name") or "-", "release_date": (rel.get("published_at") or "-")[:10],
        "desc": (d.get("description") or "").replace("\t", " ").replace("\n", " ")[:200],
    }


def read_list(path, col):
    out = []
    for ln in open(path, encoding="utf-8"):
        if not ln.strip() or ln.startswith("#"): continue
        c = ln.rstrip("\n").split("\t")
        v = (c[col - 1] if len(c) >= col else c[0]).strip().strip("`")
        v = v.replace("https://github.com/", "").replace("github.com/", "").rstrip("/")
        if v.count("/") == 1 and v not in out: out.append(v)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input"); ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--col", type=int, default=1, help="owner/repo 가 있는 열(1부터)")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    qs = read_list(a.input, a.col)
    with cf.ThreadPoolExecutor(a.workers) as ex:
        rows = list(ex.map(probe, qs))
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\t".join(COLS) + "\n")
        for r in rows: f.write("\t".join(str(r.get(c, "")) for c in COLS) + "\n")
    err = [r["query"] for r in rows if r["full_name"] == "ERR"]
    moved = [f"{r['query']}→{r['full_name']}" for r in rows if r["full_name"] not in ("ERR", r["query"]) and r["full_name"].lower() != r["query"].lower()]
    print(f"probed {len(rows)} · err {len(err)} · moved {len(moved)} → {a.out}")
    if err: print("  ERR:", ", ".join(err), file=sys.stderr)
    if moved: print("  MOVED:", ", ".join(moved))


if __name__ == "__main__":
    main()
