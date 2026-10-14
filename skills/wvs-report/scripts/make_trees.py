#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""클론된 저장소별 compact 디렉토리 트리 → trees.json (wvs-report)
깊이 2, 최상위 12개·하위 4개까지, 숨김 파일(.git·.github 등) 제외 — Summary-Repos '디렉토리 구조' 절용.

사용: make_trees.py <map.tsv> <project_root> [-o <assets>/trees.json]
map.tsv: 분류<TAB>도구<TAB>owner/repo (키 = '분류/도구')
"""
import argparse, json, os


def ents(p):
    try:
        xs = [e for e in os.listdir(p) if not e.startswith(".")]
    except OSError:
        return []
    return sorted(xs, key=lambda e: (not os.path.isdir(os.path.join(p, e)), e.lower()))


def walk(p, prefix, depth, out, maxn=8):
    xs = ents(p); shown = xs[:maxn]
    for i, e in enumerate(shown):
        last = (i == len(shown) - 1 and len(xs) <= maxn)
        fp = os.path.join(p, e); isd = os.path.isdir(fp)
        out.append(prefix + ("└─ " if last else "├─ ") + e + ("/" if isd else ""))
        if isd and depth < 2:
            walk(fp, prefix + ("   " if last else "│  "), depth + 1, out, maxn=4)
    if len(xs) > maxn:
        out.append(prefix + f"└─ … (+{len(xs) - maxn} more)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("map"); ap.add_argument("root"); ap.add_argument("-o", "--out")
    a = ap.parse_args()
    out_path = a.out or os.path.join(a.root, "_assets", "trees.json")
    T = {}
    for ln in open(a.map, encoding="utf-8"):
        if not ln.strip() or ln.startswith("#"): continue
        c = ln.rstrip("\n").split("\t"); key = c[0] + "/" + c[1]
        lines = [c[1] + "/"]; walk(os.path.join(a.root, key), "", 1, lines, maxn=12); T[key] = "\n".join(lines)
    json.dump(T, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(T), "trees →", out_path)


if __name__ == "__main__":
    main()
