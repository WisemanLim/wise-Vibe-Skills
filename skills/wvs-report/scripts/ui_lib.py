# -*- coding: utf-8 -*-
"""화면설계서(pptx) 생성 헬퍼 — python-pptx. 16:9(13.333×7.5in). (wvs-report)
제품별 값(시스템명·내비·레이어 색·가상 데이터)은 configure(...) 로 바꾼다.
콘솔 셸(상단 바: 기업·프로젝트·환경·⌘K·알림·사용자 / 좌 레이어 내비 / 하단 상태 바)과 설치 프로그램 프레임.
슬라이드 유형: cover / info / toc / text+table / screen(메타표 + 와이어프레임 + 기능설명표)."""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree
import math, os, sys

FONT = os.environ.get("WVS_FONT") or ("AppleGothic" if sys.platform == "darwin" else "Noto Sans CJK KR")
MONO = "Menlo"
IND, IND_L, IND_XL = "3F51E5", "8C97F0", "EEF0FD"
NAVY, GRAY, GRAY_L, LINE, BG, TXT, SUB = "1F3864", "868E96", "C9CDD6", "D9DCE5", "F6F7FB", "222222", "666B7A"
GREEN, YELLOW, RED, PURPLE, TEAL = "2F9E44", "E8A317", "C92A2A", "7048E8", "0C8599"
SW, SH = 13.333, 7.5

def rgb(h): return RGBColor.from_string(h)

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(SW), Inches(SH)
BLANK = prs.slide_layouts[6]
_slides = []

def new_slide():
    s = prs.slides.add_slide(BLANK); _slides.append(s); return s

# ---------- 기본 도형 ----------
def rect(slide, x, y, w, h, fill=None, line=LINE, lw=0.75, radius=None, dash=False, shape=None):
    shp = slide.shapes.add_shape(shape or (MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE),
                                 Inches(x), Inches(y), Inches(w), Inches(h))
    if radius is not None and shp.shape_type is not None:
        try: shp.adjustments[0] = min(0.5, radius / min(w, h)) if min(w, h) else 0.1
        except Exception: pass
    if fill: shp.fill.solid(); shp.fill.fore_color.rgb = rgb(fill)
    else: shp.fill.background()
    if line: shp.line.color.rgb = rgb(line); shp.line.width = Pt(lw)
    else: shp.line.fill.background()
    if dash: shp.line.dash_style = 4  # dash
    shp.shadow.inherit = False
    _strip_style(shp)
    shp.text_frame.text = ""
    return shp

def _strip_style(shp):
    st = shp._element.find(qn("p:style"))
    if st is not None: shp._element.remove(st)

def text(slide, x, y, w, h, s, size=10, bold=False, color=TXT, align="l", anchor="t", font=FONT, italic=False, wrap=True, margin=0.03):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = wrap
    tf.margin_left = tf.margin_right = Inches(margin); tf.margin_top = tf.margin_bottom = Inches(0.01)
    tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
    lines = s.split("\n") if isinstance(s, str) else s
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
        _runs(p, ln, size, bold, color, font, italic)
    return tb

def _runs(p, ln, size, bold, color, font, italic=False):
    """**굵게** 분해."""
    import re
    parts = re.split(r"(\*\*.+?\*\*)", ln)
    for part in parts:
        if not part: continue
        r = p.add_run()
        b = bold
        if part.startswith("**") and part.endswith("**"): part = part[2:-2]; b = True
        r.text = part; r.font.size = Pt(size); r.font.bold = b; r.font.italic = italic
        r.font.color.rgb = rgb(color); r.font.name = font
        rPr = r._r.get_or_add_rPr()
        for tag in ("a:latin", "a:ea"):
            el = rPr.find(qn(tag))
            if el is None: el = etree.SubElement(rPr, qn(tag))
            el.set("typeface", font)

def label_box(slide, x, y, w, h, s, fill, color="FFFFFF", size=9, bold=True, radius=0.06, align="c", line=None):
    rect(slide, x, y, w, h, fill=fill, line=line, radius=radius)
    text(slide, x, y, w, h, s, size=size, bold=bold, color=color, align=align, anchor="m")

def line(slide, x1, y1, x2, y2, color=GRAY, lw=1.0, arrow=False, dash=False):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = rgb(color); c.line.width = Pt(lw)
    _strip_style(c)
    if dash: c.line.dash_style = 4
    if arrow:
        ln = c.line._get_or_add_ln()
        tail = etree.SubElement(ln, qn("a:tailEnd")); tail.set("type", "triangle"); tail.set("w", "med"); tail.set("len", "med")
    return c

def table(slide, x, y, w, rows, col_w, font=8, header_fill=NAVY, header_color="FFFFFF", row_h=0.22, zebra=True, first_col_fill=None, body_font=None):
    rows = [[(c if str(c) != "" else " ") for c in r] for r in rows]
    """rows[0] = header. col_w: 인치 리스트(합 = w)."""
    n, m = len(rows), len(rows[0])
    shp = slide.shapes.add_table(n, m, Inches(x), Inches(y), Inches(w), Inches(row_h * n))
    tbl = shp.table
    tblPr = tbl._tbl.tblPr; tblPr.set("firstRow", "0"); tblPr.set("bandRow", "0")
    for j, cw in enumerate(col_w): tbl.columns[j].width = Inches(cw)
    for i in range(n):
        tbl.rows[i].height = Inches(row_h)
        for j in range(m):
            c = tbl.cell(i, j); c.margin_left = c.margin_right = Inches(0.04); c.margin_top = c.margin_bottom = Inches(0.015)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = c.text_frame; tf.word_wrap = True
            val = str(rows[i][j])
            p = tf.paragraphs[0]
            if i == 0:
                _runs(p, val, font, True, header_color, FONT); c.fill.solid(); c.fill.fore_color.rgb = rgb(header_fill)
            else:
                _runs(p, val, body_font or font, False, TXT, FONT)
                c.fill.solid()
                if first_col_fill and j == 0: c.fill.fore_color.rgb = rgb(first_col_fill)
                else: c.fill.fore_color.rgb = rgb("FFFFFF" if (not zebra or i % 2) else "F7F8FB")
    return shp

def kv_table(slide, x, y, w, rows, key_w=1.3, font=8, row_h=0.22):
    n = len(rows)
    shp = slide.shapes.add_table(n, 2, Inches(x), Inches(y), Inches(w), Inches(row_h * n))
    tbl = shp.table; tbl._tbl.tblPr.set("firstRow", "0"); tbl._tbl.tblPr.set("bandRow", "0")
    tbl.columns[0].width = Inches(key_w); tbl.columns[1].width = Inches(w - key_w)
    for i, (k, v) in enumerate(rows):
        tbl.rows[i].height = Inches(row_h)
        for j, val in enumerate((k, v)):
            c = tbl.cell(i, j); c.margin_left = c.margin_right = Inches(0.05); c.margin_top = c.margin_bottom = Inches(0.015)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE; c.text_frame.word_wrap = True
            _runs(c.text_frame.paragraphs[0], str(val), font, j == 0, TXT, FONT)
            c.fill.solid(); c.fill.fore_color.rgb = rgb("DEEAF6" if j == 0 else "FFFFFF")
    return shp

# ---------- 슬라이드 공통 ----------
import datetime as _dt
DOC = {"title": "화면설계서", "ver": "v1.0", "date": os.environ.get("WVS_DOC_DATE") or _dt.date.today().isoformat(), "author": "PRD 팀", "system": "System"}
_page = [0]
def footer(slide, section=""):
    _page[0] += 1
    text(slide, 0.4, SH - 0.32, 6, 0.25, f"{DOC['title']}  ·  {DOC['ver']}  ·  {section}", size=7.5, color=GRAY)
    text(slide, SW - 1.4, SH - 0.32, 1.0, 0.25, str(_page[0]), size=7.5, color=GRAY, align="r")

def title(slide, s, sub=None):
    text(slide, 0.4, 0.22, 10.5, 0.5, s, size=20, bold=True, color=NAVY)
    if sub: text(slide, 0.4, 0.68, 12.0, 0.3, sub, size=10, color=SUB)

def section_slide(s, sub, no):
    sl = new_slide()
    rect(sl, 0, 0, SW, SH, fill=NAVY, line=None)
    text(sl, 0.9, 2.3, 3, 0.6, f"PART {no}", size=16, bold=True, color=IND_L)
    text(sl, 0.9, 2.9, 11.5, 1.0, s, size=34, bold=True, color="FFFFFF")
    text(sl, 0.9, 4.0, 11.5, 1.2, sub, size=13, color="CADCFC")
    footer(sl, s)
    return sl

# ---------- 화면 슬라이드 ----------
def screen_slide(spec):
    """spec: dict(id, name, path, kind, section, perm, prio, desc, fr[list], items[(no,name,type,desc,link)], wire=callable(Wire), notes)"""
    sl = new_slide()
    meta = [["시스템", DOC["system"], "화면 ID", spec["id"], "화면 유형", spec.get("kind", "화면")],
            ["화면명", spec["name"], "화면 경로", spec.get("path", "-"), "접근 권한", spec.get("perm", "로그인")],
            ["우선순위", spec.get("prio", "P0"), "PRD 추적", " ".join(spec["fr"][:6]) + (" …" if len(spec["fr"]) > 6 else ""), "작성일 / 버전", f"{DOC['date']} / {DOC['ver']}"]]
    shp = sl.shapes.add_table(3, 6, Inches(0.4), Inches(0.22), Inches(SW - 0.8), Inches(0.66))
    tbl = shp.table; tbl._tbl.tblPr.set("firstRow", "0"); tbl._tbl.tblPr.set("bandRow", "0")
    widths = [0.9, 2.3, 0.9, 3.9, 1.2, 3.33]
    for j, w in enumerate(widths): tbl.columns[j].width = Inches(w)
    for i in range(3):
        tbl.rows[i].height = Inches(0.22)
        for j in range(6):
            c = tbl.cell(i, j); c.margin_left = c.margin_right = Inches(0.05); c.margin_top = c.margin_bottom = Inches(0.01)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            _runs(c.text_frame.paragraphs[0], meta[i][j], 8, j % 2 == 0 or (i == 1 and j == 1), NAVY if j % 2 == 0 else TXT, FONT)
            c.fill.solid(); c.fill.fore_color.rgb = rgb("DEEAF6" if j % 2 == 0 else "FFFFFF")
    text(sl, 0.4, 0.92, SW - 0.8, 0.4, spec["desc"], size=8.2, color=TXT)
    WX, WY, WW, WH = 0.4, 1.34, 7.55, 5.5
    rect(sl, WX, WY, WW, WH, fill=BG, line=LINE)
    w = Wire(sl, WX + 0.08, WY + 0.08, WW - 0.16, WH - 0.16)
    spec["wire"](w)
    DX, DW = WX + WW + 0.15, SW - 0.4 - (WX + WW + 0.15)
    rows = [["No", "구성요소", "유형", "기능 설명 / 동작", "연계"]] + [[str(it[0]), it[1], it[2], it[3], it[4]] for it in spec["items"]]
    n = len(rows)
    rh = max(0.2, min(0.36, 5.0 / n))
    table(sl, DX, WY, DW, rows, [0.3, 0.9, 0.55, DW - 0.3 - 0.9 - 0.55 - 0.95, 0.95], font=6.8, row_h=rh)
    text(sl, 0.4, WY + WH + 0.03, SW - 0.8, 0.28, "관련 요구사항(PRD): " + " ".join(spec["fr"]), size=7.2, color=SUB)
    footer(sl, spec.get("section", "화면 설계"))
    if spec.get("notes"): sl.notes_slide.notes_text_frame.text = spec["notes"]
    return sl

# 좌 내비: (그룹키, 그룹명, [(nav 키, 라벨)]) — 그룹키는 LAYER_C 의 키. 원본 도식의 레이어·카드 구조로 configure(nav=...) 한다.
LAYER_C = {"홈": NAVY, "L1": "2E74B5", "L2": "2F9E44", "L3": "7048E8", "Platform": "B08900", "공통": "0C8599"}
NAV = [("홈", "홈", [("HOME", "개요 맵"), ("DASH", "대시보드")]),
       ("L1", "Layer 1", [("A", "01 Concept A"), ("B", "02 Concept B")]),
       ("Platform", "Platform", [("MGR", "에이전트 관리"), ("DEP", "배포·릴리스"), ("TEN", "기업 관리"), ("IAM", "사용자·권한")]),
       ("공통", "공통", [("X", "승인·알림·리포트"), ("SET", "설정")])]
ENVS = ["dev", "staging", "prod"]
# 셸 기본 가상 데이터(실존 개인정보 금지)
CFG = {"org": "한빛제조(주)", "project": "샘플 프로젝트", "user": "이", "search": "⌘K 검색", "status": "● Manager 연결 · 에이전트 가동 · 채널 stable", "alerts": 3}


def configure(system=None, title=None, ver=None, date=None, author=None, nav=None, layer_colors=None, envs=None, **cfg):
    """제품별 값 설정. cfg 키: org, project, user, search, status, alerts."""
    global NAV, ENVS
    if system: DOC["system"] = system
    DOC["title"] = title or (DOC["system"] + " 화면설계서")
    for k, v in (("ver", ver), ("date", date), ("author", author)):
        if v: DOC[k] = v
    if nav: NAV = nav
    if layer_colors: LAYER_C.update(layer_colors)
    if envs: ENVS = envs
    CFG.update({k: v for k, v in cfg.items() if v is not None})

class Wire:
    """와이어프레임 DSL — 0..100 × 0..100 가상 좌표를 영역에 매핑."""
    def __init__(self, slide, x, y, w, h):
        self.s, self.x0, self.y0, self.w, self.h = slide, x, y, w, h
    def X(self, x): return self.x0 + self.w * x / 100
    def Y(self, y): return self.y0 + self.h * y / 100
    def W(self, w): return self.w * w / 100
    def H(self, h): return self.h * h / 100
    def box(self, x, y, w, h, fill="FFFFFF", line=LINE, radius=0.08, dash=False, lw=0.75):
        return rect(self.s, self.X(x), self.Y(y), self.W(w), self.H(h), fill=fill, line=line, radius=radius, dash=dash, lw=lw)
    def t(self, x, y, w, h, s, size=7, bold=False, color=TXT, align="l", anchor="t", font=FONT):
        return text(self.s, self.X(x), self.Y(y), self.W(w), self.H(h), s, size=size, bold=bold, color=color, align=align, anchor=anchor, font=font)
    def btn(self, x, y, w, h, s, primary=True, danger=False, size=7):
        fill = RED if danger else (IND if primary else "FFFFFF")
        col = "FFFFFF" if (primary or danger) else IND
        rect(self.s, self.X(x), self.Y(y), self.W(w), self.H(h), fill=fill, line=None if (primary or danger) else IND, radius=0.06)
        self.t(x, y, w, h, s, size=size, bold=True, color=col, align="c", anchor="m")
    def input(self, x, y, w, h, label, value, size=6.5):
        if label: self.t(x, y - 4.2, w, 4, label, size=size - 0.5, color=SUB)
        self.box(x, y, w, h, fill="FFFFFF", radius=0.05)
        self.t(x + 1, y, w - 2, h, value, size=size, anchor="m")
    def select(self, x, y, w, h, label, value, size=6.5):
        self.input(x, y, w, h, label, value, size); self.t(x + w - 5, y, 4, h, "▾", size=size, anchor="m", color=SUB)
    def toggle(self, x, y, on=True, label=""):
        self.box(x, y, 5, 3.2, fill=IND if on else GRAY_L, line=None, radius=0.12)
        self.box(x + (2.6 if on else 0.4), y + 0.4, 2, 2.4, fill="FFFFFF", line=None, radius=0.12)
        if label: self.t(x + 6, y - 0.4, 40, 4, label, size=6.5, anchor="m")
    def check(self, x, y, on, label):
        self.box(x, y, 2.2, 2.9, fill=IND if on else "FFFFFF", line=IND if on else GRAY_L, radius=0.03)
        if on: self.t(x, y - 0.3, 2.2, 3, "✓", size=6, color="FFFFFF", align="c", anchor="m")
        self.t(x + 3, y - 0.3, 60, 3.5, label, size=6.5, anchor="m")
    def radio(self, x, y, on, label):
        self.box(x, y, 2.2, 2.9, fill="FFFFFF", line=IND if on else GRAY_L, radius=0.5)
        if on: self.box(x + 0.6, y + 0.8, 1.0, 1.3, fill=IND, line=None, radius=0.5)
        self.t(x + 3, y - 0.3, 60, 3.5, label, size=6.5, anchor="m")
    def badge(self, x, y, s, fill=IND_XL, color=IND, w=None, size=5.8):
        w = w or (len(s) * 1.25 + 2.5)
        self.box(x, y, w, 3.0, fill=fill, line=None, radius=0.15)
        self.t(x, y - 0.2, w, 3.2, s, size=size, color=color, align="c", anchor="m", bold=True)
        return w
    def dot(self, x, y, c=GREEN, label=None, size=6):
        rect(self.s, self.X(x), self.Y(y), 0.07, 0.07, fill=c, line=None, shape=MSO_SHAPE.OVAL)
        if label: self.t(x + 1.6, y - 1.4, 30, 3.6, label, size=size, color=c, anchor="m")
    def bar(self, x, y, w, pct, c=IND, h=1.0):
        rect(self.s, self.X(x), self.Y(y), self.W(w), self.H(h), fill="E5E7F0", line=None)
        rect(self.s, self.X(x), self.Y(y), self.W(w) * max(0.02, pct), self.H(h), fill=c, line=None)
    def callout(self, n, x, y):
        d = 0.19
        rect(self.s, self.X(x) - d / 2, self.Y(y) - d / 2, d, d, fill=RED, line="FFFFFF", lw=0.75, shape=MSO_SHAPE.OVAL)
        text(self.s, self.X(x) - d / 2, self.Y(y) - d / 2, d, d, str(n), size=6.5, bold=True, color="FFFFFF", align="c", anchor="m", margin=0)
    def tbl(self, x, y, w, rows, col_pct, size=5.8, row_h=None):
        rows = [[(c if str(c) != "" else " ") for c in r] for r in rows]  # 빈 셀 기본 18pt 행 높이 방지
        n = len(rows); row_h = row_h or min(4.5, 60 / n)
        cw = [self.W(w) * p / 100 for p in col_pct]
        table(self.s, self.X(x), self.Y(y), self.W(w), rows, cw, font=size, header_fill="EEF0FD", header_color=NAVY, row_h=self.H(row_h), zebra=True)
    def code(self, x, y, w, h, s, size=5.2):
        self.box(x, y, w, h, fill="1F2333", line=None, radius=0.06)
        self.t(x + 1.5, y + 1, w - 3, h - 2, s, size=size, color="E6E8F2", font=MONO)
    def tabs(self, x, y, w, names, active=0, size=6):
        n = len(names); tw = w / n
        for i, nm in enumerate(names):
            self.t(x + i * tw, y, tw, 4, nm, size=size, bold=(i == active), color=IND if i == active else SUB, align="c", anchor="m")
            if i == active: rect(self.s, self.X(x + i * tw), self.Y(y + 4), self.W(tw), 0.018, fill=IND, line=None)
        rect(self.s, self.X(x), self.Y(y + 4.2), self.W(w), 0.008, fill=LINE, line=None)
    # 앱 셸 --------------------------------------------------------------
    def shell(self, nav=None, crumb=None, title=None, env="prod", org=None, project=None,
              user=None, status=None, tabs=None, active_tab=0, alerts=None):
        """콘솔 셸(DOC["system"]). 상단 바(0~6): 로고·기업·프로젝트·환경 dev/staging/prod·⌘K·알림·사용자
        좌 레이어 내비(0~13, 6~96): 홈/L1/L2/L3/Platform/공통 그룹과 항목(nav 키 강조) / 하단 상태 바(96~100).
        tabs: 화면 안 탭 목록(y 19.5). 반환 = 콘텐츠 시작 x(=14.5). 콘텐츠 영역 x 14.5..99, y 12(crumb)/14.5(title)..95 (tabs 있으면 25..95)."""
        org = org or CFG["org"]; project = project or CFG["project"]; user = user or CFG["user"]
        alerts = CFG["alerts"] if alerts is None else alerts
        self.box(0, 0, 100, 100, fill="FFFFFF", line=LINE, radius=0.02)
        rect(self.s, self.X(0), self.Y(0), self.W(100), self.H(6), fill=NAVY, line=None)
        self.box(0.8, 1.2, 2.6, 3.6, fill="2E74B5", line=None, radius=0.2)
        self.t(0.8, 1.1, 2.6, 3.8, DOC["system"][:1], size=6.4, bold=True, color="FFFFFF", align="c", anchor="m")
        self.t(3.8, 0.6, 11, 5, DOC["system"], size=6.4, bold=True, color="FFFFFF", anchor="m")
        self.t(15.5, 0.6, 17, 5, "기업 " + org + " ▾", size=4.8, color="DCE4F0", anchor="m")
        self.t(33, 0.6, 18.5, 5, "프로젝트 " + project + " ▾", size=4.8, color="DCE4F0", anchor="m")
        x = 52.0
        for e in ENVS:
            w = len(e) * 0.8 + 1.6; on = (e == env)
            self.box(x, 1.4, w, 3.3, fill="FFFFFF" if on else "2B4A7E", line=None, radius=0.2)
            self.t(x, 1.4, w, 3.3, e, size=4.6, bold=on, color=NAVY if on else "AFC0D8", align="c", anchor="m")
            x += w + 0.6
        self.box(71, 1.2, 13.5, 3.7, fill="2B4A7E", line=None, radius=0.2)
        self.t(71, 1.2, 13.5, 3.7, CFG["search"], size=4.5, color="AFC0D8", align="c", anchor="m")
        self.t(85.5, 1.2, 6, 3.7, f"알림 {alerts}", size=4.6, color="DCE4F0", anchor="m")
        self.box(95.3, 1.2, 3.7, 3.7, fill="DCE4F0", line=None, radius=0.5)
        self.t(95.3, 1.1, 3.7, 3.7, user, size=5, bold=True, color=NAVY, align="c", anchor="m")
        # 좌 내비
        rect(self.s, self.X(0), self.Y(6), self.W(13), self.H(90), fill="F1F3F6", line=None)
        y = 7.3
        for gk, gname, items in NAV:
            c = LAYER_C[gk]
            self.t(0.8, y, 12, 2.8, gname, size=4.4, bold=True, color=c, anchor="m"); y += 3.0
            for key, lab in items:
                on = (key == nav)
                if on: self.box(0.5, y - 0.1, 12, 3.0, fill="FFFFFF", line=c, radius=0.15)
                self.t(1.6, y - 0.1, 11, 3.0, lab, size=4.4, bold=on, color=c if on else SUB, anchor="m")
                y += 3.0
            y += 0.9
        # 상태 바
        rect(self.s, self.X(0), self.Y(96), self.W(100), self.H(4), fill=NAVY, line=None)
        self.t(1, 96, 90, 4, status or CFG["status"],
               size=4.4, color="DCE4F0", anchor="m")
        cx = 14.5
        if crumb: self.t(cx, 7.4, 60, 3, crumb, size=4.8, color=SUB)
        if title: self.t(cx, 10.2, 70, 4.5, title, size=8.2, bold=True)
        if tabs: self.tabs(cx, 15.5, min(85, len(tabs) * 12), tabs, active_tab, size=5.4)
        return cx
    def frame(self, title, right="한국어 ▾   ◐ 고대비", os_name=None):
        """설치 프로그램·첫 실행 등 셸 없는 전체화면 창. os_name: 'win'|'mac'|'linux' 창 장식."""
        self.box(0, 0, 100, 100, fill="ECEEF3", line=None, radius=0.02)
        self.box(0, 0, 100, 7, fill="FFFFFF", line=LINE, radius=0.02)
        deco = {"mac": "● ● ●  ", "win": "", "linux": ""}.get(os_name or "", "")
        self.t(1.5, 1, 70, 5, deco + "▣  " + DOC["system"] + " · " + title, size=6.6, bold=True, anchor="m")
        self.t(66, 1, 32, 5, ("—  ▢  ✕   " if os_name == "win" else "") + right, size=4.8, color=SUB, align="r", anchor="m")
    def terminal(self, title, lines_, x=0, y=0, w=100, h=100, size=5.0, step=3.6):
        """CLI 터미널 창. lines_: 문자열 또는 (문자열, 색) 목록. 색: 'ok'|'err'|'warn'|'cmd'|None. 반환 = 다음 줄 y."""
        self.box(x, y, w, h, fill="1F2333", line=None, radius=0.03)
        self.box(x, y, w, 5.5, fill="2E3345", line=None, radius=0.03)
        self.t(x + 1.5, y + 0.5, w - 3, 4.5, "● ● ●   " + title, size=5.0, color="AFB6CC", anchor="m")
        cy = y + 7.5
        cmap = {"ok": "69DB7C", "err": "FF8787", "warn": "FFD43B", "cmd": "8CE0C8", None: "E6E8F2"}
        for ln in lines_:
            s_, c = (ln, None) if isinstance(ln, str) else ln
            self.t(x + 2, cy, w - 4, step, s_, size=size, color=cmap.get(c, c), font=MONO)
            cy += step
        return cy
    def health(self, x, y, st="healthy", w=10):
        """헬스 배지. st: healthy|degraded|down|unknown"""
        f, c = {"healthy": ("E9F7EF", GREEN), "degraded": ("FFF4E0", "7A4E00"), "down": ("FDECEC", RED), "unknown": ("EEF0F4", "555555")}[st]
        return self.badge(x, y, st, fill=f, color=c, w=w, size=4.8)
    def agent_card(self, x, y, w, h, name, ver, trust="official", domain="공통", installs="1.2k", status="설치됨", price=None, desc=None):
        """마켓·에이전트 목록 카드. trust: official/partner/community/external"""
        self.box(x, y, w, h, fill="FFFFFF", line=LINE, radius=0.1)
        self.box(x + 1.5, y + 1.5, 5.5, 7, fill=IND_XL, line=None, radius=0.5); self.t(x + 1.5, y + 1.3, 5.5, 7, "◈", size=7, color=IND, align="c", anchor="m")
        wide = w >= 36
        self.t(x + 8, y + 1.2, (w - 24) if (status and wide) else (w - 10), 4, name, size=6.2, bold=True)
        self.t(x + 8, y + 5.0, (w - 10) if (not status or wide) else (w - 23), 3.5, f"v{ver} · {domain}", size=5, color=SUB)
        tc = {"official": (IND_XL, IND), "partner": ("E6F7F4", TEAL), "community": ("FFF4E0", "7A4E00"), "external": ("F1ECFF", PURPLE)}.get(trust, (IND_XL, IND))
        self.badge(x + 1.5, y + h - 4.6, trust, fill=tc[0], color=tc[1], size=4.8, w=len(trust) * 1.3 + 2)
        if desc: self.t(x + 1.5, y + 9.5, w - 3, h - 15.5, desc, size=4.8, color="444444")
        right = f"↓ {installs}" + (f" · {price}" if price else "")
        self.t(x + w - 24, y + h - 4.6, 22, 3.2, right, size=4.8, color=SUB, align="r", anchor="m")
        if status: self.badge(x + w - 14, y + (1.5 if wide else 5.0), status, fill="E9F7EF" if status in ("설치됨", "healthy") else ("FFF4E0" if status in ("업데이트", "심사중") else "EEF0F4"), color=GREEN if status in ("설치됨", "healthy") else ("7A4E00" if status in ("업데이트", "심사중") else "555555"), size=4.6, w=12)
    def chat(self, x, y, w, role, s, h=None, size=5.4):
        """대화 버블. role: user/assistant/system"""
        h = h or max(5, 3 + s.count("\n") * 3.2 + 3)
        if role == "user":
            self.box(x + w * 0.35, y, w * 0.65, h, fill=IND_XL, line=None, radius=0.12); self.t(x + w * 0.35 + 1.5, y + 0.8, w * 0.65 - 3, h - 1.5, s, size=size)
        else:
            self.box(x, y, w * 0.8, h, fill="FFFFFF", line=LINE, radius=0.12); self.t(x + 1.5, y + 0.8, w * 0.8 - 3, h - 1.5, s, size=size)
        return y + h + 1.5
    def card(self, x, y, w, h, title, body=None, status=None, color=IND, fill="FFFFFF"):
        """AG-UI 도구·승인·리뷰·서브에이전트 카드 등 범용 카드(좌측 색 띠)"""
        self.box(x, y, w, h, fill=fill, line=LINE, radius=0.08)
        rect(self.s, self.X(x), self.Y(y), 0.04, self.H(h), fill=color, line=None)
        self.t(x + 1.5, y + 0.8, w - 16, 3.6, title, size=5.6, bold=True)
        if status: self.badge(x + w - 14, y + 1.0, status, fill=IND_XL, color=color, size=4.6, w=12.5)
        if body: self.t(x + 1.5, y + 4.5, w - 3, h - 5, body, size=4.9, color="444444")
    def stepper(self, y, steps, active=1, x0=20, span_total=60):
        n = len(steps); span = span_total / (n - 1) if n > 1 else 0
        for i, s in enumerate(steps):
            x = x0 + i * span
            self.box(x, y, 4, 5.2, fill=IND if i + 1 <= active else "E5E7F0", line=None, radius=0.5)
            self.t(x, y - 0.2, 4, 5.4, str(i + 1), size=6, bold=True, color="FFFFFF" if i + 1 <= active else "666666", align="c", anchor="m")
            self.t(x + 5, y + 0.4, span - 7 if n > 1 else 20, 4.6, s, size=5.6, bold=(i + 1 == active), color=IND if i + 1 == active else "777777", anchor="m")
    def dialog(self, title, w=80, h=86, x=None, y=None):
        x = (100 - w) / 2 if x is None else x; y = (100 - h) / 2 if y is None else y
        self.box(0, 0, 100, 100, fill="D9DCE5", line=None, radius=0.02)
        self.box(x, y, w, h, fill="FFFFFF", line=LINE, radius=0.12)
        self.t(x + 3, y + 2, w - 12, 6, title, size=9, bold=True)
        self.t(x + w - 6, y + 1.8, 4, 6, "✕", size=8, color=SUB, anchor="m")
        return x + 3, y + 10, w - 6, h - 14   # 내용 영역
    def dialog_buttons(self, x, y, w, labels, danger_last=False):
        bx = x + w
        for i, lb in enumerate(reversed(labels)):
            bw = max(12, len(lb) * 1.6 + 4); bx -= bw + 1.5
            primary = (i == 0); self.btn(bx, y, bw, 5.5, lb, primary=primary, danger=(danger_last and i == 0))
    def empty(self, x, y, w, h, msg, action=None):
        self.box(x, y, w, h, fill="FBFBFF", line=IND_L, dash=True, radius=0.1)
        self.t(x, y + h * 0.3, w, 6, msg, size=6, color=SUB, align="c")
        if action: self.btn(x + w / 2 - 10, y + h * 0.55, 20, 5.5, action)


# ---------- 와이어프레임 공통 헬퍼(화면설계서 표준 밀도) — ui_screens_<x>.py 에서 그대로 쓴다 ----------
OK_F, WARN_F, BAD_F, INFO_F, EXT_F, WARN_T = "E9F7EF", "FFF4E0", "FDECEC", "E6F7F4", "F1ECFF", "7A4E00"


def panel(w, x, y, wd, h, title, cur=False, done=False, fill="FFFFFF"):
    """제목 있는 패널(카드 영역). cur=현재 강조, done=완료(녹색 제목)."""
    w.box(x, y, wd, h, fill=fill, line=IND if cur else LINE, radius=0.08, lw=1.2 if cur else 0.75)
    w.t(x + 1.5, y + 1, wd - 3, 4, title, size=6, bold=True, color=IND if cur else (GREEN if done else TXT))


def lines(w, x, y, wd, rows, step=4.2, size=5.2, color="444444"):
    """텍스트 줄 목록."""
    for i, r in enumerate(rows):
        w.t(x, y + i * step, wd, 4, r, size=size, color=color)


def checks(w, x, y, wd, rows, step=4.2, size=5.1):
    """(텍스트, 색) 목록 → 상태 점 + 텍스트."""
    for i, (s, c) in enumerate(rows):
        w.dot(x, y + i * step + 1.6, c)
        w.t(x + 1.8, y + i * step, wd - 2, 3.6, s, size=size, color=TXT if c != GRAY_L else SUB, anchor="m")


def co(w, pts):
    """콜아웃 ①②③ — 요소 좌상단 바로 왼쪽(라벨을 가리지 않게). pts 개수 = 기능 표 items 수."""
    for n, (x, y) in enumerate(pts, 1):
        w.callout(n, max(1.2, x - 1.6), y)


def note(w, x, y, wd, h, s, kind="warn", size=5):
    """안내 배너. kind: warn|bad|ok|info|ext"""
    f, c, l = {"warn": (WARN_F, WARN_T, YELLOW), "bad": (BAD_F, RED, RED), "ok": (OK_F, GREEN, GREEN),
               "info": (INFO_F, TEAL, TEAL), "ext": (EXT_F, PURPLE, PURPLE)}[kind]
    w.box(x, y, wd, h, fill=f, line=l, radius=0.06)
    w.t(x + 1, y, wd - 2, h, s, size=size, color=c, anchor="m")


def kpi(w, x, y, wd, h, label, value, sub, color=TXT):
    """KPI 카드(라벨 · 큰 값 · 보조 설명)."""
    w.box(x, y, wd, h, fill="FFFFFF", line=LINE, radius=0.08)
    w.t(x + 1.2, y + 0.8, wd - 2, 3.4, label, size=4.8, color=SUB)
    w.t(x + 1.2, y + 4.2, wd - 2, 5, value, size=8, bold=True, color=color)
    w.t(x + 1.2, y + h - 4.2, wd - 2, 3.4, sub, size=4.6, color=SUB)


def spark(w, x, y, wd, h, pts, c=IND):
    """간이 시계열 막대(편집 가능한 도형). pts: 0~1 값 목록."""
    n = len(pts); bw = wd / n
    for i, v in enumerate(pts):
        w.box(x + i * bw + 0.15, y + h * (1 - v), bw - 0.3, h * v, fill=c, line=None, radius=0.01)
