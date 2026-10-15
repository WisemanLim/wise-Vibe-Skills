#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""화면설계서(pptx) 표준 양식 검사 (wvs-report) — templates/prd/ui/pptx/build_ui.py 양식과 같은지 확인한다.
즉흥적으로 만든 빌더·다른 양식으로 만든 문서도 여기서 걸러진다.

검사: ① 슬라이드 순서(표지 → 문서 정보·개정 이력 → 목차 → PART 1 → 1. … → 화면 흐름도 → 공통 UI 가이드 2장 → 사용자 유형 적응
      → PART 2 → 화면 슬라이드 → PART 3 → A~F) ② 화면 슬라이드 수·메타표 ③ 화면당 콜아웃 ≥5 ④ 와이어프레임 밀도(도형 수)
      ⑤ 표준 빌더로 만든 문서인지 — pptx 표식(core_properties.keywords = TEMPLATE_ID) + 옆 <Brand>_UI_assets/pptx/build_ui.py 가 템플릿과 동일
      ⑥ (--pdf) PDF 변환·빈 쪽 ⑦ (--render DIR) 쪽 PNG
사용: check_ui_design.py <file.pptx> [--pdf] [--render DIR] [--min-shapes 25] [--legacy]
      --legacy : ⑤ 생략 — 표준 빌더 도입 전 문서(예: ObservaMesh_UI_Design.pptx)의 양식만 검사
종료 코드: 0 통과 · 1 실패
"""
import argparse, filecmp, os, re, subprocess, sys

TEMPLATE_ID = "wvs-report/ui-design-template/1"      # templates/prd/ui/pptx/build_ui.py 가 pptx 에 기록
TEMPLATE_BUILDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates", "prd", "ui", "pptx", "build_ui.py")

REQUIRED = [  # (이름, 슬라이드 앞부분 텍스트 정규식) — 이 순서로 나타나야 한다
    ("표지", r"UI DESIGN DOCUMENT.*화면설계서"), ("문서 정보·개정 이력", r"^문서 정보 · 개정 이력"), ("목차", r"^목차"),
    ("PART 1", r"PART 1"), ("1. 시스템 개요", r"^1\. "), ("2. 화면 ID 명명 규칙", r"^2\. 화면 ID 명명 규칙"),
    ("메뉴 구조도(IA)", r"^\d+\. 메뉴 구조도\(IA\)"), ("화면 목록", r"^\d+\. 화면 목록"), ("사용자 × 화면 매트릭스", r"^\d+\. 사용자 × 화면 매트릭스"),
    ("화면 흐름도", r"^\d+-[①-⑩] "), ("공통 UI 가이드 — 레이아웃", r"^\d+\. 공통 UI 가이드 — 레이아웃"),
    ("공통 UI 가이드 — 상태", r"^\d+\. 공통 UI 가이드 — 상태"), ("사용자 유형·운용 모드별 UI 적응", r"^\d+\. 사용자 유형"),
    ("PART 2", r"PART 2"), ("화면 슬라이드", r"^시스템 .* 화면 ID "), ("PART 3", r"PART 3"),
    ("A. 모달·위저드 카탈로그", r"^A\. 모달"), ("B. 메시지 정의", r"^B\. 메시지 정의"), ("C. 요구사항 추적표", r"^C\. 요구사항 추적표"),
    ("D. 비화면 요구", r"^D\. 비화면"), ("E. PRD 시나리오", r"^E\. "), ("F. 참고 자료", r"^F\. 참고 자료"),
]


def template_fails(path, prs):
    """표준 빌더 사용 여부: pptx 표식 + 자산 폴더의 build_ui.py 가 스킬 템플릿과 바이트 동일."""
    fails = []
    if (prs.core_properties.keywords or "") != TEMPLATE_ID:
        fails.append(f"표준 빌더 표식 없음(keywords ≠ {TEMPLATE_ID}) — templates/prd/ui/pptx/build_ui.py 를 복사해 빌드하세요(빌더를 새로 쓰지 않는다)")
    stem = os.path.basename(path)
    stem = stem[len("stub_"):] if stem.startswith("stub_") else stem
    prefix = stem[:-len("_UI_Design.pptx")] if stem.endswith("_UI_Design.pptx") else None
    d = os.path.dirname(os.path.abspath(path))
    cands = [os.path.join(d, "pptx", "build_ui.py")] if os.path.basename(d).endswith("_UI_assets") else []   # stub_ 출력은 _UI_assets 안
    if prefix: cands.append(os.path.join(d, f"{prefix}_UI_assets", "pptx", "build_ui.py"))
    b = next((c for c in cands if os.path.isfile(c)), None)
    if not b:
        fails.append(f"빌더 없음: {cands[-1] if cands else '<Brand>_UI_assets/pptx/build_ui.py'} — 화면설계서는 <Brand>_UI_assets/pptx/build_ui.py(템플릿 사본)로 만든다")
    elif os.path.isfile(TEMPLATE_BUILDER) and not filecmp.cmp(b, TEMPLATE_BUILDER, shallow=False):
        fails.append(f"빌더가 템플릿과 다름: {b} — build_ui.py 는 수정하지 않는다(제품별 내용은 ui_spec.py·ui_design_data.py·ui_screens_<x>.py)")
    return fails


def slide_texts(prs):
    from pptx.enum.shapes import MSO_SHAPE
    out = []
    for sl in prs.slides:
        parts, ovals, shapes = [], 0, 0
        for sh in sl.shapes:
            shapes += 1
            if sh.has_text_frame and sh.text_frame.text.strip():
                parts.append(" ".join(sh.text_frame.text.split()))
            if getattr(sh, "has_table", False) and sh.has_table:
                parts.append(" ".join(c.text for r in sh.table.rows for c in r.cells))
            try:
                if sh.shape_type == 1 and sh.auto_shape_type == MSO_SHAPE.OVAL and sh.width < 200000: ovals += 1
            except Exception:
                pass
        out.append({"text": " ".join(parts), "ovals": ovals, "shapes": shapes})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pptx"); ap.add_argument("--pdf", action="store_true"); ap.add_argument("--render")
    ap.add_argument("--min-shapes", type=int, default=25, help="화면 슬라이드 최소 도형 수(와이어프레임 밀도)")
    ap.add_argument("--legacy", action="store_true", help="표준 빌더 표식·빌더 동일성 검사 생략(빌더 도입 전 문서)")
    a = ap.parse_args()
    from pptx import Presentation
    prs = Presentation(a.pptx)
    S = slide_texts(prs)
    fails, i = ([] if a.legacy else template_fails(a.pptx, prs)), 0
    pos = {}
    for name, pat in REQUIRED:
        rx = re.compile(pat)
        j = next((k for k in range(i, len(S)) if rx.search(S[k]["text"][:160])), None)
        if j is None:
            fails.append(f"누락 또는 순서 어긋남: {name}"); continue
        pos[name] = j; i = j + 1
    screens = [k for k, s in enumerate(S) if re.search(r"^시스템 .* 화면 ID ", s["text"][:160])]
    thin = [k + 1 for k in screens if S[k]["shapes"] < a.min_shapes]
    few = [k + 1 for k in screens if S[k]["ovals"] < 5]
    n_flow = sum(1 for s in S if re.search(r"^\d+-[①-⑩] ", s["text"][:40]))
    n_ia = sum(1 for s in S if re.search(r"^\d+\. 메뉴 구조도", s["text"][:40]))
    print(f"slides {len(S)} · screens {len(screens)} · flow {n_flow} · IA {n_ia}")
    if not screens: fails.append("화면 슬라이드 없음")
    if few: fails.append(f"콜아웃 5개 미만 화면 쪽 {few[:15]}")
    if thin: fails.append(f"와이어프레임 밀도 낮음(도형 < {a.min_shapes}) 쪽 {thin[:15]}")
    if a.pdf or a.render:
        here = os.path.dirname(os.path.abspath(__file__))
        subprocess.run(["bash", os.path.join(here, "docx2pdf.sh"), a.pptx], check=True, capture_output=True)
        pdf = os.path.splitext(a.pptx)[0] + ".pdf"
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
        d = fitz.open(pdf); blank = [k + 1 for k, pg in enumerate(d) if not pg.get_text().strip() and not pg.get_images()]
        if blank: fails.append(f"빈 쪽 {blank}")
        if a.render:
            os.makedirs(a.render, exist_ok=True)
            for k, pg in enumerate(d): pg.get_pixmap(dpi=55).save(os.path.join(a.render, f"p{k + 1:03d}.png"))
        print(f"pdf {pdf} · pages {len(d)}" + (f" · rendered → {a.render}" if a.render else ""))
    for f in fails: print("FAIL", f)
    print("PASS" if not fails else "FAIL")
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()
