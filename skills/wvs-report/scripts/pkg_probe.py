#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""패키지 레지스트리 실측 (wvs-report) — 최신 버전·업로드일·언어 런타임 요구(requires_python 등).

입력 TSV: 이름<TAB>레지스트리(pypi|npm|crates|none)<TAB>패키지명   ('#' 주석 무시)
출력 TSV: 이름  레지스트리  패키지  버전  업로드일  요구(python/node 엔진)  라이선스

사용: pkg_probe.py research/pkg_map.tsv -o research/packages.tsv
"""
import argparse, json, sys, urllib.request


def _get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "wvs-report"}), timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def pypi(pkg):
    d = _get(f"https://pypi.org/pypi/{pkg}/json")
    if not d: return None
    i = d["info"]; v = i["version"]; files = d.get("releases", {}).get(v) or []
    date = max((f.get("upload_time", "")[:10] for f in files), default="-") or "-"
    lic = (i.get("license_expression") or i.get("license") or "-").split("\n")[0][:40]
    return v, date, i.get("requires_python") or "-", lic


def npm(pkg):
    d = _get(f"https://registry.npmjs.org/{pkg}")
    if not d: return None
    v = d.get("dist-tags", {}).get("latest", "-"); m = d.get("versions", {}).get(v, {})
    return v, (d.get("time", {}).get(v) or "-")[:10], (m.get("engines") or {}).get("node", "-"), str(m.get("license", "-"))[:40]


def crates(pkg):
    d = _get(f"https://crates.io/api/v1/crates/{pkg}")
    if not d: return None
    c = d["crate"]; v = c.get("max_stable_version") or c.get("max_version")
    ver = next((x for x in d.get("versions", []) if x["num"] == v), {})
    return v, (ver.get("created_at") or "-")[:10], ver.get("rust_version") or "-", (ver.get("license") or "-")[:40]


FN = {"pypi": pypi, "npm": npm, "crates": crates}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input"); ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    rows, err = [], []
    for ln in open(a.input, encoding="utf-8"):
        if not ln.strip() or ln.startswith("#"): continue
        c = ln.rstrip("\n").split("\t")
        name, reg, pkg = c[0], (c[1] if len(c) > 1 else "none"), (c[2] if len(c) > 2 else "-")
        res = FN.get(reg, lambda _: None)(pkg) if reg in FN else None
        if res is None and reg in FN: err.append(f"{name}({reg}:{pkg})")
        v, d, req, lic = res or ("-", "-", "-", "-")
        rows.append([name, reg, pkg, v, d, req, lic])
    with open(a.out, "w", encoding="utf-8") as f:
        for r in rows: f.write("\t".join(r) + "\n")
    print(f"packages {len(rows)} · not found {len(err)} → {a.out}")
    if err: print("  NOT FOUND:", ", ".join(err), file=sys.stderr)


if __name__ == "__main__":
    main()
