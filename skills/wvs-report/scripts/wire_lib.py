# -*- coding: utf-8 -*-
"""PRD 와이어프레임 공통 라이브러리 (matplotlib 전용, wvs-report). 제품별 값은 configure(...) 로 바꾼다.
데스크톱 좌표계: x 0~100, y 0~62.5 (y 위로 증가), figsize (13, 8.125) → 종횡비 1:1 좌표."""
import logging, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Wedge, Polygon

plt.rcParams["font.family"] = [os.environ.get("WVS_FONT") or "Apple SD Gothic Neo", "AppleGothic", "Noto Sans CJK KR", "NanumGothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

OUT = os.environ.get("WVS_WIRE_OUT") or os.getcwd()   # save() 저장 위치 — configure(out=...)
DPI = 170
import datetime as _dt
BRAND = "System"
FOOTER = f"와이어프레임 (자체 작성, {_dt.date.today().isoformat()}) — 가상 데이터"

NAVY, PRI = "#1F3864", "#2E74B5"
TXT, SUB, MUTED = "#222222", "#404040", "#868E96"
LINE, PANEL, WHITE = "#CED4DA", "#F8F9FA", "#FFFFFF"
PRI_L = "#E7F0FA"
CRIT, WARN, CAUT, OK, INFO = "#C92A2A", "#E8590C", "#F2C94C", "#2F9E44", "#0C8599"
STATUS = {"위험": CRIT, "경고": WARN, "주의": CAUT, "정상": OK, "정보": INFO}
# 주의(노랑) 배경 위 글자는 어둡게
DARK_ON = {CAUT}


# 레이아웃 상수(데스크톱)
TOP_H = 3.6
SIDE_W = 11.5
CX0, CX1 = 12.8, 98.8          # 콘텐츠 좌우
CY_TITLE = 56.4                # 화면 제목 기준선
CY_TOP, CY_BOT = 54.4, 2.0     # 콘텐츠 상하


# ───────────────────────── 기본 ─────────────────────────
def canvas(figsize=(13, 8.125), xmax=100.0, ymax=62.5, bg=WHITE):
    fig = plt.figure(figsize=figsize, dpi=DPI, facecolor=bg)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.set_aspect("auto")
    ax.axis("off")
    ax._ppu = figsize[0] * 72.0 / xmax  # points per data unit
    return fig, ax


def _cw(ch):
    o = ord(ch)
    if o < 128:
        if ch == " ":
            return 0.30
        if ch in "il.,:;|!'`":
            return 0.30
        if ch in "MWmw@%":
            return 0.85
        if ch.isupper():
            return 0.62
        if ch.isdigit():
            return 0.60
        return 0.50
    if ch in "·›":
        return 0.45
    if ch in "→←↑↓…○●■□▲▼◆✓✕①②③④⑤⑥⑦":
        return 0.85
    return 0.89


def tw(ax, s, fs):
    """문자열 폭 추정(데이터 단위)."""
    return sum(_cw(c) for c in str(s)) * fs / ax._ppu


def fit(ax, s, fs, maxw):
    s = str(s)
    if maxw is None or tw(ax, s, fs) <= maxw:
        return s
    while s and tw(ax, s + "…", fs) > maxw:
        s = s[:-1]
    return s + "…"


def txt(ax, x, y, s, fs=7.5, color=TXT, weight="normal", ha="left", va="center",
        maxw=None, **kw):
    return ax.text(x, y, fit(ax, s, fs, maxw), fontsize=fs, color=color, weight=weight,
                   ha=ha, va=va, zorder=kw.pop("zorder", 5), **kw)


def rbox(ax, x, y, w, h, fc=WHITE, ec=LINE, lw=0.8, r=0.6, z=1, **kw):
    r = min(r, w / 2.2, h / 2.2)
    p = FancyBboxPatch((x + r, y + r), max(w - 2 * r, 0.001), max(h - 2 * r, 0.001),
                       boxstyle=f"round,pad={r}", fc=fc, ec=ec, lw=lw, zorder=z, **kw)
    ax.add_patch(p)
    return p


def rect(ax, x, y, w, h, fc=WHITE, ec="none", lw=0.6, z=1, **kw):
    p = Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw, zorder=z, **kw)
    ax.add_patch(p)
    return p


def hline(ax, x0, x1, y, color=LINE, lw=0.7, z=2, ls="-"):
    ax.plot([x0, x1], [y, y], color=color, lw=lw, zorder=z, ls=ls, solid_capstyle="butt")


def vline(ax, x, y0, y1, color=LINE, lw=0.7, z=2, ls="-"):
    ax.plot([x, x], [y0, y1], color=color, lw=lw, zorder=z, ls=ls, solid_capstyle="butt")


def icon(ax, x, y, s=0.9, color=MUTED, fill=False):
    """작은 사각 아이콘(중심 x,y)."""
    rbox(ax, x - s / 2, y - s / 2, s, s, fc=color if fill else "none", ec=color, lw=0.9,
         r=0.18, z=6)


# ───────────────────────── 위젯 ─────────────────────────
def badge(ax, x, y, text, color=PRI, fs=6.8, tc=None, ha="left", h=None, solid=True):
    """알약형 배지. (x,y)=왼쪽/가운데/오른쪽 기준 중앙 높이. 반환: 폭."""
    w = tw(ax, text, fs) + 1.0
    h = h or fs / ax._ppu * 1.55
    x0 = x if ha == "left" else (x - w / 2 if ha == "center" else x - w)
    if solid:
        fc, ec = color, color
        tc = tc or (TXT if color in DARK_ON else WHITE)
    else:
        fc, ec = WHITE, color
        tc = tc or color
    rbox(ax, x0, y - h / 2, w, h, fc=fc, ec=ec, lw=0.7, r=h / 2.05, z=7)
    ax.text(x0 + w / 2, y, text, fontsize=fs, color=tc, ha="center", va="center",
            weight="bold", zorder=8)
    return w


def status_badge(ax, x, y, st, fs=6.8, ha="left"):
    return badge(ax, x, y, st, STATUS.get(st, MUTED), fs=fs, ha=ha)


def chip(ax, x, y, text, fs=6.8, color=PRI, ha="left"):
    """연한 배경 칩."""
    w = tw(ax, text, fs) + 1.0
    h = fs / ax._ppu * 1.6
    x0 = x if ha == "left" else x - w / 2
    rbox(ax, x0, y - h / 2, w, h, fc=PRI_L, ec=color, lw=0.5, r=h / 2.05, z=7)
    ax.text(x0 + w / 2, y, text, fontsize=fs, color=color, ha="center", va="center", zorder=8)
    return w


def button(ax, x, y, w, h, label, kind="primary", fs=7.5):
    col = {"primary": (PRI, PRI, WHITE), "secondary": (WHITE, PRI, PRI),
           "danger": (CRIT, CRIT, WHITE), "ok": (OK, OK, WHITE), "ghost": (WHITE, LINE, SUB),
           "navy": (NAVY, NAVY, WHITE)}[kind]
    rbox(ax, x, y, w, h, fc=col[0], ec=col[1], lw=0.9, r=0.5, z=6)
    ax.text(x + w / 2, y + h / 2, label, fontsize=fs, color=col[2], ha="center", va="center",
            weight="bold", zorder=8)


def field(ax, x, y, w, h, label, value, fs=7.0, lab_w=None, dropdown=False, hi=False):
    """라벨 + 입력 상자. y=상자 하단."""
    if lab_w:
        if label:
            txt(ax, x, y + h / 2, label, fs, SUB, maxw=lab_w - 0.3)
        bx, bw = x + lab_w, w - lab_w
    else:
        txt(ax, x, y + h + 0.9, label, fs - 0.3, SUB)
        bx, bw = x, w
    rbox(ax, bx, y, bw, h, fc=PRI_L if hi else WHITE, ec=PRI if hi else LINE, lw=0.7, r=0.35, z=3)
    txt(ax, bx + 0.6, y + h / 2, value, fs, TXT, maxw=bw - (2.2 if dropdown else 1.0))
    if dropdown:
        ax.text(bx + bw - 0.9, y + h / 2, "▾", fontsize=fs, color=MUTED, ha="center",
                va="center", zorder=6)


def checkbox(ax, x, y, label, checked=True, fs=7.0, color=PRI):
    s = 1.0
    rbox(ax, x, y - s / 2, s, s, fc=color if checked else WHITE, ec=color if checked else LINE,
         lw=0.8, r=0.15, z=6)
    if checked:
        ax.text(x + s / 2, y, "✓", fontsize=fs - 1, color=WHITE, ha="center", va="center",
                zorder=7, weight="bold")
    txt(ax, x + s + 0.5, y, label, fs, TXT)


def toggle(ax, x, y, on=True, w=2.4, h=1.2):
    rbox(ax, x, y - h / 2, w, h, fc=PRI if on else LINE, ec="none", r=h / 2.05, z=6)
    ax.add_patch(Circle((x + (w - h / 2) if on else x + h / 2, y), h * 0.38, fc=WHITE, zorder=7))


def progress(ax, x, y, w, h, frac, color=PRI, bg="#E9ECEF", label=None, fs=6.8):
    rbox(ax, x, y, w, h, fc=bg, ec="none", r=h / 2.05, z=3)
    if frac > 0:
        rbox(ax, x, y, max(w * min(frac, 1), h), h, fc=color, ec="none", r=h / 2.05, z=4)
    if label is not None:
        txt(ax, x + w + 0.6, y + h / 2, label, fs, SUB)


def card(ax, x, y, w, h, title=None, fs=8.2, fc=WHITE, ec=LINE, right=None, accent=None):
    """카드. (x,y)=좌하단. 제목 있으면 반환값=제목 아래 콘텐츠 시작 y."""
    rbox(ax, x, y, w, h, fc=fc, ec=ec, lw=0.8, r=0.7, z=1)
    if accent:
        rect(ax, x + 0.05, y + 0.6, 0.35, h - 1.2, fc=accent, z=2)
    if title:
        txt(ax, x + 1.0, y + h - 1.4, title, fs, TXT, weight="bold",
            maxw=w - 2 - (tw(ax, right, 6.8) + 1 if right else 0))
        if right:
            txt(ax, x + w - 1.0, y + h - 1.4, right, 6.8, PRI, ha="right")
        return y + h - 2.8
    return y + h - 0.8


def table(ax, x, y, w, headers, rows, col_widths, row_h=2.2, fs=7.0, head_fs=None,
          zebra=True, hi_rows=(), hi_color=PRI_L, head_bg="#EEF1F5", aligns=None):
    """y=표 상단. col_widths: 비율 목록. 셀: str 또는 ('badge',텍스트,색) / ('status',상태)
    / ('bar',frac,색,라벨) / ('color',텍스트,색) / ('bold',텍스트). 반환: 표 하단 y."""
    head_fs = head_fs or fs
    tot = sum(col_widths)
    ws = [w * c / tot for c in col_widths]
    xs = np.concatenate([[x], x + np.cumsum(ws)])
    aligns = aligns or ["left"] * len(headers)
    rect(ax, x, y - row_h, w, row_h, fc=head_bg, z=2)
    for i, hd in enumerate(headers):
        _cell_text(ax, xs[i], ws[i], y - row_h / 2, hd, head_fs, SUB, "bold", aligns[i])
    cy = y - row_h
    for r, row in enumerate(rows):
        if r in hi_rows:
            rect(ax, x, cy - row_h, w, row_h, fc=hi_color, z=2)
        elif zebra and r % 2 == 1:
            rect(ax, x, cy - row_h, w, row_h, fc="#FBFCFD", z=2)
        mid = cy - row_h / 2
        for i, cell in enumerate(row):
            if isinstance(cell, tuple):
                kind = cell[0]
                if kind == "badge":
                    badge(ax, xs[i] + 0.5, mid, cell[1], cell[2], fs=fs - 0.4)
                elif kind == "status":
                    status_badge(ax, xs[i] + 0.5, mid, cell[1], fs=fs - 0.4)
                elif kind == "bar":
                    bw = ws[i] - 1.0 - (tw(ax, cell[3], fs - 0.4) + 0.8 if len(cell) > 3 else 0)
                    progress(ax, xs[i] + 0.5, mid - 0.35, bw, 0.7, cell[1], cell[2],
                             label=cell[3] if len(cell) > 3 else None, fs=fs - 0.4)
                elif kind == "color":
                    _cell_text(ax, xs[i], ws[i], mid, cell[1], fs, cell[2], "bold", aligns[i])
                elif kind == "bold":
                    _cell_text(ax, xs[i], ws[i], mid, cell[1], fs, TXT, "bold", aligns[i])
                elif kind == "mono":
                    _cell_text(ax, xs[i], ws[i], mid, cell[1], fs, TXT, "normal", aligns[i],
                               family="DejaVu Sans Mono")
            else:
                _cell_text(ax, xs[i], ws[i], mid, cell, fs, TXT, "normal", aligns[i])
        hline(ax, x, x + w, cy - row_h, color="#E3E7EB", lw=0.5, z=3)
        cy -= row_h
    hline(ax, x, x + w, y, color=LINE, lw=0.7, z=3)
    hline(ax, x, x + w, y - row_h, color=LINE, lw=0.7, z=3)
    return cy


def _cell_text(ax, x0, w, y, s, fs, color, weight, align, family=None):
    kw = {"family": family} if family else {}
    if align == "right":
        txt(ax, x0 + w - 0.5, y, s, fs, color, weight, ha="right", maxw=w - 0.8, **kw)
    elif align == "center":
        txt(ax, x0 + w / 2, y, s, fs, color, weight, ha="center", maxw=w - 0.8, **kw)
    else:
        txt(ax, x0 + 0.5, y, s, fs, color, weight, maxw=w - 0.8, **kw)


# ───────────────────────── 차트 ─────────────────────────
def vbars(ax, x, y, w, h, labels, series, colors, vmax=None, fs=6.8, legend=None,
          value_fmt=None, gap=0.35, grid=4):
    """세로 막대(그룹). series: [값목록,...]. (x,y)=플롯 좌하단(라벨은 아래로)."""
    series = [list(s) for s in series]
    vmax = vmax or max(max(s) for s in series) * 1.15
    n, k = len(labels), len(series)
    for g in range(grid + 1):
        gy = y + h * g / grid
        hline(ax, x, x + w, gy, color="#EEF0F2", lw=0.5, z=2)
    slot = w / n
    bw = slot * (1 - gap) / k
    for i, lab in enumerate(labels):
        for j, s in enumerate(series):
            bx = x + i * slot + slot * gap / 2 + j * bw
            bh = h * s[i] / vmax
            rect(ax, bx, y, bw * 0.92, bh, fc=colors[j] if not isinstance(colors[j], list)
                 else colors[j][i], z=3)
            if value_fmt:
                txt(ax, bx + bw * 0.46, y + bh + 0.6, value_fmt(s[i]), fs - 0.3, SUB, ha="center")
        txt(ax, x + i * slot + slot / 2, y - 0.9, lab, fs, SUB, ha="center", maxw=slot)
    hline(ax, x, x + w, y, color=MUTED, lw=0.7, z=4)
    if legend:
        lx = x
        for j, lg in enumerate(legend):
            rect(ax, lx, y + h + 0.9, 0.9, 0.9, fc=colors[j], z=4)
            txt(ax, lx + 1.2, y + h + 1.35, lg, fs, SUB)
            lx += tw(ax, lg, fs) + 3.0


def hbars(ax, x, y, w, h, labels, values, colors, vmax=None, fs=6.8, lab_w=8, fmt=None,
          target=None):
    """가로 막대. (x,y)=좌하단, 라벨 폭 lab_w 포함. 위에서부터 그림."""
    n = len(labels)
    vmax = vmax or max(values) * 1.1
    slot = h / n
    pw = w - lab_w - (4 if fmt else 0.5)
    for i, (lab, v) in enumerate(zip(labels, values)):
        cy = y + h - slot * (i + 0.5)
        txt(ax, x, cy, lab, fs, SUB, maxw=lab_w - 0.4)
        rect(ax, x + lab_w, cy - slot * 0.28, pw, slot * 0.56, fc="#EEF1F4", z=2)
        c = colors[i] if isinstance(colors, list) else colors
        rect(ax, x + lab_w, cy - slot * 0.28, pw * v / vmax, slot * 0.56, fc=c, z=3)
        if target is not None:
            t = target[i] if isinstance(target, list) else target
            vline(ax, x + lab_w + pw * t / vmax, cy - slot * 0.4, cy + slot * 0.4, color=TXT,
                  lw=1.0, z=5)
        if fmt:
            txt(ax, x + lab_w + pw + 0.6, cy, fmt(v), fs, TXT)


def donut(ax, cx, cy, r, values, colors, center=None, sub=None, width=0.36, fs=11):
    tot = float(sum(values))
    a = 90.0
    for v, c in zip(values, colors):
        ang = 360 * v / tot
        ax.add_patch(Wedge((cx, cy), r, a - ang, a, width=r * width, fc=c, ec=WHITE, lw=1.0,
                           zorder=4))
        a -= ang
    if center:
        txt(ax, cx, cy + (0.5 if sub else 0), center, fs, TXT, "bold", ha="center")
    if sub:
        txt(ax, cx, cy - 1.3, sub, 6.8, MUTED, ha="center")


def gauge(ax, cx, cy, r, frac, color=OK, label=None, sub=None):
    ax.add_patch(Wedge((cx, cy), r, 0, 180, width=r * 0.28, fc="#E9ECEF", ec="none", zorder=3))
    ax.add_patch(Wedge((cx, cy), r, 180 - 180 * frac, 180, width=r * 0.28, fc=color, ec="none",
                       zorder=4))
    if label:
        txt(ax, cx, cy + r * 0.25, label, 12, TXT, "bold", ha="center")
    if sub:
        txt(ax, cx, cy - 1.0, sub, 6.8, MUTED, ha="center")


def radar(ax, cx, cy, r, labels, series, vmax=4, fs=6.8, rings=4, lab_pad=1.6):
    """series: [(값목록, 색, 채움여부), ...]"""
    n = len(labels)
    ang = [np.pi / 2 - 2 * np.pi * i / n for i in range(n)]
    for k in range(1, rings + 1):
        rr = r * k / rings
        pts = [(cx + rr * np.cos(a), cy + rr * np.sin(a)) for a in ang]
        ax.add_patch(Polygon(pts, closed=True, fc="none", ec="#DEE2E6", lw=0.6, zorder=2))
    for i, a in enumerate(ang):
        ax.plot([cx, cx + r * np.cos(a)], [cy, cy + r * np.sin(a)], color="#DEE2E6", lw=0.6,
                zorder=2)
        lx, ly = cx + (r + lab_pad) * np.cos(a), cy + (r + lab_pad) * np.sin(a)
        ha = "center" if abs(np.cos(a)) < 0.2 else ("left" if np.cos(a) > 0 else "right")
        txt(ax, lx, ly, labels[i], fs, SUB, ha=ha)
    for vals, col, filled in series:
        pts = [(cx + r * v / vmax * np.cos(a), cy + r * v / vmax * np.sin(a))
               for v, a in zip(vals, ang)]
        ax.add_patch(Polygon(pts, closed=True, fc=col if filled else "none", alpha=0.22 if filled
                             else 1, ec="none", zorder=3))
        ax.add_patch(Polygon(pts, closed=True, fc="none", ec=col, lw=1.3,
                             ls="-" if filled else "--", zorder=4))
        for px, py in pts:
            ax.add_patch(Circle((px, py), 0.28, fc=col, zorder=5))


def heatmap(ax, x, y, w, h, cols, rows, mat, colors, col_fs=6.5, row_w=6, fs=6.8,
            col_lab_h=6.0, rot=40, cell_text=None):
    """(x,y)=좌하단(열 라벨 영역 포함 X, 셀 영역 기준). 열 라벨은 셀 위로 회전 출력."""
    nr, nc = len(rows), len(cols)
    cw, ch = (w - row_w) / nc, h / nr
    for i, rl in enumerate(rows):
        ry = y + h - ch * (i + 1)
        txt(ax, x, ry + ch / 2, rl, fs, SUB, maxw=row_w - 0.3)
        for j in range(nc):
            v = mat[i][j]
            rect(ax, x + row_w + j * cw + 0.1, ry + 0.1, cw - 0.2, ch - 0.2, fc=colors(v), z=3)
            if cell_text:
                s = cell_text(v)
                if s:
                    txt(ax, x + row_w + (j + 0.5) * cw, ry + ch / 2, s, fs - 0.5,
                        WHITE if v >= 2 else SUB, ha="center")
    for j, cl in enumerate(cols):
        ax.text(x + row_w + (j + 0.35) * cw, y + h + 0.5, cl, fontsize=col_fs, color=SUB,
                rotation=rot, ha="left", va="bottom", rotation_mode="anchor", zorder=5)


def gantt(ax, x, y, w, h, tasks, periods, lab_w=12, fs=6.8, today=None):
    """tasks: [(라벨, 시작, 끝, 색, 막대글자)], periods: 눈금 라벨 목록(각 1칸). (x,y)=좌하단."""
    n = len(tasks)
    pw = w - lab_w
    np_ = len(periods)
    head = 1.8
    slot = (h - head) / n
    for k, p in enumerate(periods):
        px = x + lab_w + pw * k / np_
        vline(ax, px, y, y + h - head, color="#EEF0F2", lw=0.5)
        txt(ax, px + pw / np_ / 2, y + h - head / 2, p, fs - 0.3, MUTED, ha="center")
    hline(ax, x, x + w, y + h - head, color=LINE, lw=0.6)
    for i, t in enumerate(tasks):
        lab, s, e, c = t[:4]
        cy = y + h - head - slot * (i + 0.5)
        txt(ax, x, cy, lab, fs, TXT, maxw=lab_w - 0.4)
        bx0 = x + lab_w + pw * s / np_
        bx1 = x + lab_w + pw * e / np_
        rbox(ax, bx0, cy - slot * 0.3, bx1 - bx0, slot * 0.6, fc=c, ec="none", r=0.35, z=4)
        if len(t) > 4 and t[4]:
            txt(ax, bx0 + 0.5, cy, t[4], fs - 0.5, TXT if c in DARK_ON else WHITE,
                maxw=bx1 - bx0 - 0.8)
    if today is not None:
        tx = x + lab_w + pw * today / np_
        vline(ax, tx, y, y + h - head, color=CRIT, lw=1.0, ls="--", z=6)
        txt(ax, tx + 0.3, y + 0.6, "오늘", fs - 0.5, CRIT)


def spark(ax, x, y, w, h, vals, color=PRI, fill=True):
    vals = np.asarray(vals, float)
    lo, hi = vals.min(), vals.max()
    xs = x + np.linspace(0, w, len(vals))
    ys = y + (vals - lo) / (hi - lo + 1e-9) * h
    ax.plot(xs, ys, color=color, lw=1.1, zorder=5)
    if fill:
        ax.fill_between(xs, y, ys, color=color, alpha=0.12, zorder=4, lw=0)
    ax.add_patch(Circle((xs[-1], ys[-1]), 0.3, fc=color, zorder=6))


def line_chart(ax, x, y, w, h, series, colors, labels=None, vmax=None, fs=6.5, grid=3):
    vmax = vmax or max(max(s) for s in series) * 1.15
    for g in range(grid + 1):
        hline(ax, x, x + w, y + h * g / grid, color="#EEF0F2", lw=0.5)
    for s, c in zip(series, colors):
        xs = x + np.linspace(0, w, len(s))
        ax.plot(xs, y + np.asarray(s) / vmax * h, color=c, lw=1.2, zorder=4)
    if labels:
        for i, l in enumerate(labels):
            txt(ax, x + w * i / (len(labels) - 1), y - 0.9, l, fs, MUTED, ha="center")


# ───────────────────────── 크롬 ─────────────────────────
def footer(ax, x=None, y=None):
    xmax = ax.get_xlim()[1]
    ax.text(x if x is not None else xmax - 0.8, y if y is not None else 0.7, FOOTER, fontsize=6.5,
            color="#9AA0A6", ha="right", va="center", zorder=20)


def title_row(ax, title, sid, x=CX0, y=CY_TITLE, right=None):
    w = badge(ax, x, y, sid, NAVY, fs=7.5)
    txt(ax, x + w + 0.8, y, title, 11.5, TXT, "bold")
    if right:
        txt(ax, CX1, y, right, 7.0, MUTED, ha="right")


# 좌 내비: (그룹명, [(stage 키, 라벨)]) — 그룹명 앞 2글자가 LAYER_C 키. 원본 도식 레이어·카드 구조로 configure(nav=...) 한다.
NAV = [("홈", [("HOME", "개요 맵"), ("DASH", "대시보드")]),
       ("L1 Layer 1", [("A", "01 Concept A"), ("B", "02 Concept B")]),
       ("Platform", [("PLT-MGR", "에이전트 관리"), ("PLT-DEP", "배포·릴리스"), ("PLT-TEN", "기업·프로젝트"), ("PLT-IAM", "사용자·권한"), ("X", "승인·알림·설정")])]
LAYER_C = {"L1": "#2E74B5", "L2": "#2F9E44", "L3": "#7048E8", "Pl": "#B08900", "홈": NAVY}
TENANT, PROJECT, USER = "한빛제조(주)", "샘플 프로젝트", "이운영 (Operator)"
SEARCH, STATUS_TXT = "⌘K 검색", "● Manager 연결 · 에이전트 가동 · 채널 stable"


def configure(brand=None, footer=None, nav=None, layer_colors=None, tenant=None, project=None, user=None, search=None, status=None, out=None):
    """제품별 값 설정(모듈 전역)."""
    g = globals()
    for k, v in (("BRAND", brand), ("FOOTER", footer), ("NAV", nav), ("TENANT", tenant), ("PROJECT", project),
                 ("USER", user), ("SEARCH", search), ("STATUS_TXT", status), ("OUT", out)):
        if v is not None: g[k] = v
    if layer_colors: LAYER_C.update(layer_colors)
TOP_H, SIDE_W, STATUS_H = 3.8, 13.0, 1.6
CX0, CX1 = 14.4, 99.0
CY_TITLE = 56.2
CY_TOP, CY_BOT = 54.2, 2.4


def frame(title, screen_id, stage=None, sub_tabs=None, active_sub=0, url=None, mode=None,
          user=None, right=None, tray=None, status=None, env="prod"):
    """콘솔 공통 프레임(BRAND).
    상단 바: 로고·기업(테넌트)·프로젝트·환경(dev/staging/prod)·⌘K·알림·사용자, 좌: 레이어별 내비(stage=활성 키),
    하단: 상태 바(Manager 연결·에이전트 가동 수·게이트웨이 p95·오늘 비용). 선택: sub_tabs(화면 안 탭). 반환: fig, ax, (x0, y0, x1, y1)."""
    user = user or USER
    fig, ax = canvas()
    H = 62.5
    rect(ax, 0, H - TOP_H, 100, TOP_H, fc=NAVY, z=2)
    ym = H - TOP_H / 2
    rbox(ax, 0.8, ym - 0.85, 1.7, 1.7, fc=PRI, ec=WHITE, lw=0.8, r=0.3, z=3)
    txt(ax, 1.65, ym, BRAND[:1], 7.5, WHITE, "bold", ha="center")
    txt(ax, 3.0, ym, BRAND, 9.0, WHITE, "bold", maxw=10.8)
    txt(ax, 14.4, ym, "기업 " + TENANT + " ▾", 7.0, "#DCE4F0", maxw=15)
    txt(ax, 30.0, ym, "프로젝트 " + PROJECT + " ▾", 7.0, "#DCE4F0", maxw=18)
    ex = 50.0
    for e in ["dev", "staging", "prod"]:
        on = e == env
        w = tw(ax, e, 6.6) + 1.6
        rbox(ax, ex, ym - 0.85, w, 1.7, fc=WHITE if on else "#2B4A7E", ec="#4A6A9E", lw=0.5, r=0.4, z=3)
        txt(ax, ex + w / 2, ym, e, 6.6, NAVY if on else "#AFC0D8", "bold" if on else "normal", ha="center")
        ex += w + 0.4
    rbox(ax, 66.0, ym - 0.95, 15.5, 1.9, fc="#2B4A7E", ec="#4A6A9E", lw=0.6, r=0.5, z=3)
    txt(ax, 66.8, ym, SEARCH, 6.6, "#AFC0D8", maxw=14)
    txt(ax, 83.2, ym, "알림 3", 6.8, "#DCE4F0")
    ax.add_patch(Circle((87.6, ym), 0.8, fc="#DCE4F0", zorder=4))
    txt(ax, 87.6, ym, user[0], 6.6, NAVY, "bold", ha="center")
    txt(ax, 88.8, ym, user, 6.6, WHITE, maxw=10.5)
    # 좌 내비
    rect(ax, 0, STATUS_H, SIDE_W, H - TOP_H - STATUS_H, fc="#F1F3F6", z=1)
    vline(ax, SIDE_W, STATUS_H, H - TOP_H, color=LINE)
    yy = H - TOP_H - 1.6
    for grp, items in NAV:
        c = LAYER_C.get(grp[:2], NAVY)
        txt(ax, 0.9, yy, grp, 6.4, c, "bold", maxw=SIDE_W - 1.4); yy -= 1.75
        for key, lab in items:
            on = stage is not None and (key == stage or (str(stage).startswith(key) and len(key) > 2))
            if on:
                rbox(ax, 0.5, yy - 0.8, SIDE_W - 1.0, 1.6, fc=WHITE, ec=c, lw=0.8, r=0.3, z=3)
            txt(ax, 1.5, yy, lab, 6.4, c if on else SUB, "bold" if on else "normal", maxw=SIDE_W - 2.4)
            yy -= 1.75
        yy -= 0.5
    # 상태 바
    rect(ax, 0, 0, 100, STATUS_H, fc=NAVY, z=2)
    st = status or STATUS_TXT
    txt(ax, 1.0, STATUS_H / 2, st, 6.2, "#DCE4F0", maxw=64)
    txt(ax, 99.2, STATUS_H / 2, f"{screen_id} · " + FOOTER, 5.6, "#8FA3C4", ha="right", maxw=34)
    # 제목 + 하위 탭
    txt(ax, CX0, CY_TITLE, title, 10.5, NAVY, "bold", maxw=58)
    txt(ax, CX0 + min(tw(ax, title, 10.5), 58) + 1.0, CY_TITLE, screen_id, 7.0, MUTED)
    if right:
        txt(ax, CX1, CY_TITLE, right, 7.0, SUB, ha="right", maxw=26)
    top = CY_TOP
    if sub_tabs:
        tx = CX0
        for k, t in enumerate(sub_tabs):
            w = tw(ax, t, 6.9)
            txt(ax, tx, CY_TOP - 0.4, t, 6.9, PRI if k == active_sub else SUB, "bold" if k == active_sub else "normal")
            if k == active_sub:
                hline(ax, tx - 0.2, tx + w + 0.2, CY_TOP - 1.4, color=PRI, lw=1.8, z=6)
            tx += w + 2.2
        hline(ax, CX0, CX1, CY_TOP - 1.5, color=LINE)
        top = CY_TOP - 2.6
    return fig, ax, (CX0, CY_BOT, CX1, top)


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=DPI, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path
