#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wvs-report 출력 폴더 결정 규칙 (정본) — deep · prd 공통.

  --out-dir 지정 시        → 그 폴더(상대 경로면 <root> 기준, 없으면 만든다)
  기본 폴더가 <root> 에 있음 → <root>/<기본 폴더>      deep: Miscellaneous-Data · prd: Need-to-be-organized-into-PRD
  기본 폴더가 없음          → <root> 바로 아래        (기본 폴더를 새로 만들지 않는다)

산출물(<Title>.docx/.pdf, <Brand>_..._PRD.docx/.pdf)과 자산 폴더(<Title>_assets/, <Brand>_assets/)는 결정된 폴더에 함께 둔다.

사용: out_dir.py deep|prd [--root DIR] [--out-dir DIR]     → 결정된 절대 경로 한 줄 출력
      python3 -c "from out_dir import resolve; print(resolve('deep', root))"
"""
import argparse, os

DEFAULT = {"deep": "Miscellaneous-Data", "prd": "Need-to-be-organized-into-PRD"}


def resolve(mode, root=".", out_dir=None):
    root = os.path.abspath(os.path.expanduser(root))
    if out_dir:
        p = out_dir if os.path.isabs(os.path.expanduser(out_dir)) else os.path.join(root, out_dir)
        p = os.path.abspath(os.path.expanduser(p))
        os.makedirs(p, exist_ok=True)
        return p
    pref = os.path.join(root, DEFAULT[mode])
    return pref if os.path.isdir(pref) else root


def report_candidates(name, root="."):
    """분석 보고서 이름 → 탐색 후보 경로(존재하는 것만): <root>/Miscellaneous-Data/<name>.docx|pdf → <root>/<name>.docx|pdf."""
    root = os.path.abspath(os.path.expanduser(root))
    stem = name[:-5] if name.endswith(".docx") else name[:-4] if name.endswith(".pdf") else name
    out = []
    for d in (os.path.join(root, DEFAULT["deep"]), root):
        for ext in (".docx", ".pdf"):
            p = os.path.join(d, stem + ext)
            if os.path.isfile(p): out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=sorted(DEFAULT))
    ap.add_argument("--root", default=".")
    ap.add_argument("--out-dir")
    a = ap.parse_args()
    print(resolve(a.mode, a.root, a.out_dir))


if __name__ == "__main__":
    main()
