# -*- coding: utf-8 -*-
"""공통 docx 헬퍼 — Summary-Repos / Miscellaneous-Data 분석 보고서 / PRD 템플릿 규격 (wvs-report).

규격: Letter(21.59×27.94cm) 여백 2.0cm, 본문 글꼴 Apple SD Gothic Neo(macOS) · Noto Sans CJK KR(그 외), Normal 10pt(sa 4pt),
H1 16pt bold 1F3864(앞에 페이지 나눔), H2 13pt bold 2E74B5, H3 11.5pt bold 404040,
표지: 제목 28pt / 부제 16pt / 태그라인 11pt / 작성일·출처, 목차: H1 9.2pt · H2 8.1pt(4칸 들여쓰기, 하위 3개 이상이면 한 줄로 묶음),
데이터 표: 헤더 1F3864 흰글씨 bold, 본문 8pt; 키-값 표: 첫 열 DEEAF6 bold 9pt; 코드: F5F5F5 Menlo 8pt;
그림: 중앙 + 캡션 8.5pt 666666 ("그림 N. 캡션 (출처)").

사용: 빌드 스크립트(보고서 _assets/ 안)에서
    import sys; sys.path.insert(0, KIT)      # KIT = <skills>/wvs-report/scripts
    import docx_lib as r
    r.COVER(...); r.H("1. 개요", 1); r.P(...); r.T([...], rows, widths=r.W([1, 3, 2])); r.FIG("fig.png", 16, "캡션", "자체 작성")
    r.SAVE("/abs/out/Report.docx", pdf=True)
환경변수: WVS_DOC_DATE(작성일, 기본 오늘) · WVS_ASSETS(상대 경로 기준, 기본 cwd) · WVS_FONT(본문 글꼴).
"""
import csv, datetime, os, re, subprocess, sys
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = os.environ.get("WVS_ASSETS") or os.getcwd()
KIT = os.path.dirname(os.path.abspath(__file__))
DOC_DATE = os.environ.get("WVS_DOC_DATE") or datetime.date.today().isoformat()
FONT = os.environ.get("WVS_FONT") or ("Apple SD Gothic Neo" if sys.platform == "darwin" else "Noto Sans CJK KR")
MONO = "Menlo" if sys.platform == "darwin" else "DejaVu Sans Mono"
C_TITLE, C_SUB, C_H3, C_GRAY, C_HDR, C_KV, C_CODE = "1F3864", "2E74B5", "404040", "666666", "1F3864", "DEEAF6", "F5F5F5"
TEXT_W = 17.59  # 본문 폭(cm) = 21.59 - 2×2.0

doc = Document()
_sec = doc.sections[0]
_sec.page_width, _sec.page_height = Emu(7772400), Emu(10058400)  # US Letter
for m in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(_sec, m, Cm(2.0))


def _set_style_font(st, size=None):
    st.font.name = FONT
    rpr = st.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.append(rf)
    for a in ("w:eastAsia", "w:ascii", "w:hAnsi"):
        rf.set(qn(a), FONT)
    if size: st.font.size = Pt(size)


for _n in ["Normal", "Heading 1", "Heading 2", "Heading 3", "List Bullet", "List Number"]:
    _set_style_font(doc.styles[_n])
doc.styles["Normal"].font.size = Pt(10)
doc.styles["Normal"].paragraph_format.space_after = Pt(4)


def set_font(run, size=None, bold=None, color=None, italic=None, name=None):
    fn = name or FONT
    run.font.name = fn
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.append(rf)
    for a in ("w:eastAsia", "w:ascii", "w:hAnsi"):
        rf.set(qn(a), fn)
    if size is not None: run.font.size = Pt(size)
    if bold is not None: run.font.bold = bold
    if italic is not None: run.font.italic = italic
    if color: run.font.color.rgb = RGBColor.from_string(color)


def shade(cell, hexcolor):
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


def PAGE_BREAK():
    p = doc.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)
    return p


# ---------------- 인라인 서식 (**bold**, `code`) ----------------
_RICH = re.compile(r"\*\*(.+?)\*\*|`([^`]+?)`", re.S)


def _rich(p, text, size=None, bold=False, italic=False, color=None, mono=False):
    """텍스트 안의 **굵게** 와 `코드` 를 런으로 분리해 넣는다(**`code`** 중첩 지원)."""
    base = MONO if mono else None
    pos = 0
    for m in _RICH.finditer(text):
        if m.start() > pos:
            rn = p.add_run(text[pos:m.start()])
            set_font(rn, size=size, bold=bold, italic=italic, color=color, name=base)
        if m.group(1) is not None:
            _rich(p, m.group(1), size=size, bold=True, italic=italic, color=color, mono=mono)
        else:
            rn = p.add_run(m.group(2))
            set_font(rn, size=(size - 0.5) if size else 9.0, bold=bold, italic=italic, color=color, name=MONO)
        pos = m.end()
    tail = text[pos:]
    if tail or pos == 0:
        rn = p.add_run(tail)
        set_font(rn, size=size, bold=bold, italic=italic, color=color, name=base)
    return p


# ---------------- 문단 ----------------
def P(text="", bold=False, size=None, italic=False, align=None, color=None, sa=4, style=None, mono=False):
    p = doc.add_paragraph(style=style) if style else doc.add_paragraph()
    if text:
        _rich(p, text, size=size, bold=bold, italic=italic, color=color, mono=mono)
    if align == "center": p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(sa)
    return p


def B(text, level=0):
    p = doc.add_paragraph(style="List Bullet")
    if level: p.paragraph_format.left_indent = Cm(0.6 + 0.6 * level)
    _rich(p, text, size=10)
    p.paragraph_format.space_after = Pt(2)
    return p


_NUM = [0]


def NUM_RESET(): _NUM[0] = 0


def N(text):
    _NUM[0] += 1
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.9)
    p.paragraph_format.first_line_indent = Cm(-0.6)
    p.paragraph_format.space_after = Pt(2)
    _rich(p, f"{_NUM[0]}. {text}", size=10)
    return p


# ---------------- 제목 (목차 자동 수집) ----------------
_HEADINGS = []      # (level, text)
_TOC_ANCHOR = [None]
_FIRST_H1 = [True]


def H(text, level=1):
    h = doc.add_heading("", level=level)
    if level == 1:
        if not _FIRST_H1[0]:
            h.paragraph_format.page_break_before = True   # 빈 페이지 방지(PAGE_BREAK 대신)
        _FIRST_H1[0] = False
    r = h.add_run(text)
    if level == 1: set_font(r, size=16, bold=True, color=C_TITLE)
    elif level == 2: set_font(r, size=13, bold=True, color=C_SUB)
    else: set_font(r, size=11.5, bold=True, color=C_H3)
    h.paragraph_format.keep_with_next = True
    if level <= 2:
        _HEADINGS.append((level, text))
    return h


def CH(title):
    """장 번호 자동 증가 H1 — CH.n 현재 장 번호, CH.sec 절 카운터."""
    CH.n += 1; CH.sec = 0
    H(f"{CH.n}. {title}", 1)
    return CH.n


CH.n = 0
CH.sec = 0


def SEC(title):
    """현재 장의 다음 절(H2) — '3.2 제목'."""
    CH.sec += 1
    H(f"{CH.n}.{CH.sec} {title}", 2)
    return CH.sec


# ---------------- 표지 / 목차 ----------------
def COVER(title, subtitle, tagline, meta_lines):
    """meta_lines: [(text, size, color)] — 예: (f"작성일: {DOC_DATE}", 10, None), ("출처: …", 9, C_GRAY).
    출처 줄에는 원본 자료(첨부 이미지·링크·기초 보고서)만 쓴다. 형식 참고용 이전 문서는 넣지 않는다."""
    for _ in range(3): doc.add_paragraph()
    P(title, size=28, bold=True, align="center", color=C_TITLE)
    P(subtitle, size=16, bold=True, align="center", color=C_SUB)
    doc.add_paragraph()
    P(tagline, size=11, align="center")
    for _ in range(4): doc.add_paragraph()
    for text, size, color in meta_lines:
        P(text, size=size, align="center", color=color)
    PAGE_BREAK()
    H("목차", 1)
    _HEADINGS.clear()                      # '목차' 자체는 목차에 넣지 않음
    _TOC_ANCHOR[0] = doc.add_paragraph()   # 자리표시자 — FINALIZE 시 앞에 항목 삽입
    _FIRST_H1[0] = False                   # 본문 첫 H1 이 page_break_before 로 넘김


def FINALIZE(group_min=3, line_max=78):
    """수집된 H1/H2로 목차를 자리표시자 앞에 삽입. 하위(H2)가 group_min개 이상이면 한 줄에 이어 붙인다(괄호 보조설명 제거)."""
    anchor = _TOC_ANCHOR[0]
    if anchor is None: return

    def add(text, sub=False):
        p = anchor.insert_paragraph_before("")
        r = p.add_run(("    " + text) if sub else text); set_font(r, size=8.1 if sub else 9.2)
        p.paragraph_format.space_after = Pt(0 if sub else 1)
    i, n = 0, len(_HEADINGS)
    while i < n:
        level, text = _HEADINGS[i]
        if level == 1:
            add(text); i += 1
            subs = []
            while i < n and _HEADINGS[i][0] == 2:
                subs.append(_HEADINGS[i][1]); i += 1
            if len(subs) >= group_min:
                short = [re.sub(r"(\s*[\(（—–]| - ).*$", "", t).strip() for t in subs]
                line = ""
                for t in short:
                    cand = (line + "  " + t) if line else t
                    if len(cand) > line_max:
                        add(line, sub=True); line = t
                    else:
                        line = cand
                if line: add(line, sub=True)
            else:
                for t in subs: add(t, sub=True)
        else:
            add(text, sub=True); i += 1
    anchor._element.getparent().remove(anchor._element)   # 빈 자리표시자 제거 — 목차가 꽉 찼을 때 빈 쪽 방지
    _TOC_ANCHOR[0] = None


# ---------------- 표 ----------------
def W(ratios, total=TEXT_W):
    """열 비율 리스트 → cm 너비(합 = 본문 폭)."""
    s = sum(ratios); w = [round(total * x / s, 2) for x in ratios]
    w[-1] = round(total - sum(w[:-1]), 2)
    return w


def T(headers, rows, widths=None, font=8, header_fill=C_HDR):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]; c.text = ""
        _rich(c.paragraphs[0], str(h), size=font, bold=True, color="FFFFFF")
        shade(c, header_fill)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            _rich(cells[i].paragraphs[0], str(v), size=font)
    if widths:
        _fix_layout(t, widths)
    _gap()
    return t


def _gap(pt=4):
    """표/코드 뒤 간격 문단 — 빈 페이지를 유발하지 않도록 높이를 줄인다."""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    set_font(p.add_run(""), size=pt)
    return p


def _fix_layout(t, widths_cm):
    """LibreOffice 가 열 너비를 반영하도록 tblLayout=fixed + tblGrid/gridCol 설정."""
    tbl = t._tbl
    tblPr = tbl.tblPr
    el = tblPr.find(qn("w:tblLayout"))
    if el is not None: tblPr.remove(el)
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    grid = tbl.find(qn("w:tblGrid"))
    if grid is not None: tbl.remove(grid)
    grid = OxmlElement("w:tblGrid")
    for w in widths_cm:
        gc = OxmlElement("w:gridCol"); gc.set(qn("w:w"), str(int(w * 567)))
        grid.append(gc)
    tbl.insert(list(tbl).index(tblPr) + 1, grid)
    for row in t.rows:
        for i, w in enumerate(widths_cm):
            row.cells[i].width = Cm(w)


def KV(rows, key_width_cm=3.74, font=9):
    """키-값 표: 첫 열 DEEAF6 bold."""
    t = doc.add_table(rows=0, cols=2)
    t.style = "Table Grid"
    for k, v in rows:
        cells = t.add_row().cells
        cells[0].text = ""; cells[1].text = ""
        _rich(cells[0].paragraphs[0], str(k), size=font, bold=True); shade(cells[0], C_KV)
        _rich(cells[1].paragraphs[0], str(v), size=font)
    _fix_layout(t, [key_width_cm, TEXT_W - key_width_cm])
    _gap()
    return t


def CODE(text, font=8):
    t = doc.add_table(rows=1, cols=1)
    t.style = "Table Grid"
    c = t.rows[0].cells[0]; c.text = ""; shade(c, C_CODE)
    lines = text.split("\n")
    p = c.paragraphs[0]
    set_font(p.add_run(lines[0]), size=font, name=MONO)
    for ln in lines[1:]:
        p = c.add_paragraph(); set_font(p.add_run(ln), size=font, name=MONO)
        p.paragraph_format.space_after = Pt(0)
    _gap()
    return t


def CAP(text):
    p = doc.add_paragraph()
    set_font(p.add_run(text), size=8.5, color=C_GRAY)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(4)
    return p


def _abs(path):
    return path if os.path.isabs(path) else os.path.join(HERE, path)


def IMG(path, width_cm, caption):
    doc.add_picture(_abs(path), width=Cm(min(width_cm, 17.5)))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    CAP(caption)


# ---------------- 그림 자동 번호 + 출처 레지스트리 ----------------
FIGS = []   # (번호, 경로, 캡션, 출처) — 부록 '그림·이미지 출처' 표 생성용


def FIG(path, width_cm, caption, src="자체 작성"):
    """그림 N. 캡션 (출처). 원본 첨부 이미지는 src 에 '원저작자 · 사용자 첨부 이미지, 분석 목적 인용' 을 쓴다."""
    n = len(FIGS) + 1
    FIGS.append((n, path, caption, src))
    IMG(path, width_cm, f"그림 {n}. {caption} ({src})")
    return n


def FIG_TABLE():
    """부록용 그림·이미지 출처 표."""
    T(["그림", "파일", "캡션", "출처"],
      [[str(n), os.path.basename(p), c, s] for n, p, c, s in FIGS], widths=W([1, 4, 8, 4.5]), font=7.5)


def load_tsv(name):
    with open(_abs(name), encoding="utf-8") as f:
        return [row for row in csv.reader(f, delimiter="\t") if row and not row[0].startswith("#")]


# ---------------- 저장 / PDF ----------------
def SAVE(out_docx, pdf=False, group_min=3, line_max=78):
    """목차 확정 → docx 저장 → (선택) LibreOffice 로 같은 이름 .pdf 생성. 반환: (docx, pdf|None)."""
    FINALIZE(group_min=group_min, line_max=line_max)
    out_docx = os.path.abspath(out_docx)
    os.makedirs(os.path.dirname(out_docx), exist_ok=True)
    doc.save(out_docx)
    print("saved:", out_docx)
    out_pdf = None
    if pdf:
        subprocess.run(["bash", os.path.join(KIT, "docx2pdf.sh"), out_docx], check=True)
        out_pdf = out_docx[:-5] + ".pdf"
    return out_docx, out_pdf
