#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""산출 문서 검증 (wvs-report) — 빌드 후 반드시 실행.

docx: 장(H1)·절(H2) 수, 표·그림 수, 금지 문자열(형식 참고용 이전 문서명 등 — 출처에 넣으면 안 되는 것) 검사,
      --require 정규식(예: FR ID)의 등장 여부, '[미확인]' 개수 보고.
pdf : 쪽 수, 빈 쪽(텍스트·이미지 없음) 탐지, --render DIR 지정 시 쪽별 PNG(dpi 60)를 만들어 눈으로 확인할 수 있게 한다.

사용: check_report.py Report.docx [--pdf Report.pdf] [--forbid "Summary-Repos.docx" --forbid "AgentPlaza_PRD"]
                      [--require-file ids.txt] [--render /tmp/pages] [--min-h1 5] [--min-tables 50 --min-pages 40]
종료 코드: 0 통과 · 1 실패(빈 쪽·금지 문자열·필수 ID 누락·장/표/쪽 수 부족)
"""
import argparse, os, re, sys


def docx_stats(path):
    from docx import Document
    d = Document(path)
    h1 = [p.text for p in d.paragraphs if p.style.name == "Heading 1"]
    h2 = [p.text for p in d.paragraphs if p.style.name == "Heading 2"]
    text = "\n".join(p.text for p in d.paragraphs)
    for t in d.tables:
        for row in t.rows:
            text += "\n" + " | ".join(c.text for c in row.cells)
    n_img = len(d.inline_shapes)
    return {"h1": h1, "h2": h2, "tables": len(d.tables), "images": n_img, "text": text}


def pdf_stats(path, render=None):
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz
    doc = fitz.open(path)
    blank = []
    for i, pg in enumerate(doc):
        if not pg.get_text().strip() and not pg.get_images():
            blank.append(i + 1)
        if render:
            os.makedirs(render, exist_ok=True)
            pg.get_pixmap(dpi=60).save(os.path.join(render, f"p{i + 1:03d}.png"))
    return {"pages": len(doc), "blank": blank}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docx"); ap.add_argument("--pdf")
    ap.add_argument("--forbid", action="append", default=[])
    ap.add_argument("--require", action="append", default=[], help="반드시 등장해야 하는 문자열(여러 번)")
    ap.add_argument("--require-file", help="한 줄에 하나씩 필수 문자열(예: 전체 FR ID 목록)")
    ap.add_argument("--render"); ap.add_argument("--min-h1", type=int, default=3)
    ap.add_argument("--min-tables", type=int, default=0, help="표 수 하한(deep 권장 50)")
    ap.add_argument("--min-pages", type=int, default=0, help="PDF 쪽 수 하한(deep 권장 40) — 조사 깊이 부족 탐지")
    a = ap.parse_args()
    ok = True
    s = docx_stats(a.docx)
    print(f"docx  {a.docx}\n  H1 {len(s['h1'])} · H2 {len(s['h2'])} · tables {s['tables']} · images {s['images']} · [미확인] {s['text'].count('[미확인]')}")
    if len(s["h1"]) < a.min_h1:
        print(f"  FAIL H1 {len(s['h1'])} < {a.min_h1}"); ok = False
    if s["tables"] < a.min_tables:
        print(f"  FAIL tables {s['tables']} < {a.min_tables} — 조사 블록이 얕음(check_research.py 로 보강 위치 확인)"); ok = False
    for f in a.forbid:
        if f in s["text"]:
            print(f"  FAIL forbidden text present: {f}"); ok = False
    req = list(a.require)
    if a.require_file:
        req += [ln.strip() for ln in open(a.require_file, encoding="utf-8") if ln.strip()]
    miss = [x for x in req if x not in s["text"]]
    if req:
        print(f"  required {len(req) - len(miss)}/{len(req)}")
        if miss:
            print("  FAIL missing:", ", ".join(miss[:30]) + (" …" if len(miss) > 30 else "")); ok = False
    if a.pdf:
        p = pdf_stats(a.pdf, a.render)
        print(f"pdf   {a.pdf}\n  pages {p['pages']} · blank {p['blank'] or '-'}" + (f" · rendered → {a.render}" if a.render else ""))
        if p["blank"]:
            ok = False
        if p["pages"] < a.min_pages:
            print(f"  FAIL pages {p['pages']} < {a.min_pages} — 조사 블록이 얕음(check_research.py 로 보강 위치 확인)"); ok = False
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
