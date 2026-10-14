# -*- coding: utf-8 -*-
"""Summary-Repos 그림 — 분류별 스타(로그), 흐름(수명주기) 지도, 유지보수 신호 산점도. wvs-report repos 템플릿."""
import datetime as dt, logging, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sr_data as D  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
for f in ["/System/Library/Fonts/Supplemental/AppleGothic.ttf", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
          "/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "C:/Windows/Fonts/malgun.ttf"]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f); plt.rcParams["font.family"] = font_manager.FontProperties(fname=f).get_name(); break
plt.rcParams["axes.unicode_minus"] = False
BLUE, ORANGE, GRAY, INK, INK2, GREEN = "#2a78d6", "#eb6834", "#9a9994", "#0b0b0b", "#52514e", "#1baf7a"
TODAY = D.TODAY
_CAT = {}
for _f in sorted(__import__("glob").glob(os.path.join(HERE, "content", "part_*.py"))):
    _CAT.update(__import__("runpy").run_path(_f).get("CAT", {}))
CATNAME = {c: _CAT.get(c, {}).get("title") or c[3:].replace("-", " ") for c in D.CATS}   # 인포그래픽 분류 표기

# 그림 — 분류별 스타
n = len(D.ORDER) + 1.4 * len(D.CATS)
fig, ax = plt.subplots(figsize=(8.4, max(4.0, 0.27 * n))); y = 0; yt, yl = [], []
for cat in D.CATS:
    ks = sorted([k for k in D.ORDER if D.META[k]["cat"] == cat], key=lambda k: -D.META[k]["stars"])
    ax.text(1.2, y - 0.15, cat[:2] + " " + CATNAME[cat], fontsize=8.5, weight="bold", color=INK, va="bottom"); y -= 1
    for k in ks:
        m = D.META[k]; s = D.stale(k)
        ax.barh(y, max(m["stars"], 1), height=0.72, color=GRAY if s else BLUE)
        ax.text(max(m["stars"], 1) * 1.08, y, f'{m["stars"]:,}' + ("  (아카이브)" if m["archived"] else ("  (1년+ 릴리스 없음)" if s else "")),
                va="center", fontsize=7, color=INK2)
        yt.append(y); yl.append(D.disp(k)); y -= 1
    y -= 0.4
ax.set_yticks(yt); ax.set_yticklabels(yl, fontsize=7.5); ax.set_xscale("log"); ax.set_ylim(y + 0.6, 1.4)
ax.set_xlim(1, max(10, max(D.META[k]["stars"] for k in D.ORDER)) * 8)
ax.set_xlabel(f"GitHub Stars (로그 스케일, {TODAY} 조회)", fontsize=8.5, color=INK2)
for s in ["top", "right", "left"]: ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0); ax.grid(axis="x", color="#e6e5e0", lw=0.6); ax.set_axisbelow(True)
ax.set_title("분류별 저장소 GitHub 스타 (회색 = 아카이브 또는 최근 1년 릴리스 없음)", fontsize=10, weight="bold", color=INK, pad=12)
plt.tight_layout(); plt.savefig(os.path.join(HERE, "fig_stars.png"), dpi=170); plt.close()

# 그림 — 흐름(수명주기) 지도: 주 흐름 단계(좌→우) + 횡단 띠
STAGES, CROSS = D.X["STAGES"], D.X.get("CROSS", [])
fig, ax = plt.subplots(figsize=(10, 6.0)); ax.set_xlim(0, 100); ax.set_ylim(0, 62); ax.axis("off")


def names(cat): return [D.disp(k) for k in D.ORDER if D.META[k]["cat"] == cat]


def box(x, y, w, h, title, items, fc="#eef4fc", ec=BLUE):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2", fc=fc, ec=ec, lw=1.1))
    ax.text(x + w / 2, y + h - 2.2, title, ha="center", va="top", fontsize=8.2, weight="bold", color=INK)
    ax.text(x + w / 2, y + h - 6.6, "\n".join(items), ha="center", va="top", fontsize=7.0, color=INK2, linespacing=1.35)


band_h = 5.2; top = 62 - (band_h + 0.8) * len(CROSS)
W = (97 - 1.6 * (len(STAGES) - 1)) / max(1, len(STAGES)); x = 1
for i, (title, cats) in enumerate(STAGES):
    items = []
    for c in cats:
        items += [c[:2] + " " + CATNAME.get(c, c)] + names(c) + [""]
    box(x, 2, W, top - 4, title, items[:-1])
    if i < len(STAGES) - 1:
        ax.annotate("", xy=(x + W + 1.5, top / 2), xytext=(x + W + 0.2, top / 2), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.2))
    x += W + 1.6
yb = top
for title, cats in CROSS:
    box(1, yb, 97, band_h, "", [], fc="#fdf0ea", ec=ORANGE)
    ax.text(49.5, yb + band_h / 2, title + ": " + " · ".join(n for c in cats for n in names(c)), ha="center", va="center", fontsize=7.8, color=INK)
    yb += band_h + 0.8
plt.savefig(os.path.join(HERE, "fig_lifecycle.png"), dpi=170, bbox_inches="tight"); plt.close()

# 그림 — 최신 릴리스 일자 × 스타
fig, ax = plt.subplots(figsize=(8.6, 5.0))
top_k = sorted(D.ORDER, key=lambda k: -D.META[k]["stars"])[:5]
for k in D.ORDER:
    m = D.META[k]
    try:
        xd = dt.date.fromisoformat(D.last_release(k))
    except ValueError:
        continue
    s = D.stale(k)
    ax.scatter(xd, max(m["stars"], 1), s=34, color=ORANGE if s else BLUE, edgecolor="white", lw=0.8, zorder=3)
    if s or k in top_k: ax.annotate(D.disp(k), (xd, max(m["stars"], 1)), xytext=(4, 3), textcoords="offset points", fontsize=6.8, color=INK2)
ax.axvline(TODAY - dt.timedelta(days=365), color=GRAY, lw=0.9, ls="--")
ax.set_yscale("log"); ax.set_ylabel("GitHub Stars (로그)", fontsize=8.5, color=INK2)
ax.set_xlabel("최신 릴리스 일자 (GitHub 릴리스·레지스트리 업로드 중 늦은 쪽)", fontsize=8.5, color=INK2)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m")); ax.tick_params(labelsize=7.5)
for s in ["top", "right"]: ax.spines[s].set_visible(False)
ax.grid(color="#e6e5e0", lw=0.6); ax.set_axisbelow(True)
ax.scatter([], [], color=BLUE, label="최근 1년 내 릴리스"); ax.scatter([], [], color=ORANGE, label="아카이브 또는 1년+ 릴리스 없음")
ax.legend(fontsize=7.5, frameon=False, loc="lower left")
ax.set_title("유지보수 신호: 최신 릴리스 시점 × 인지도 (점선 = 1년 기준선)", fontsize=10, weight="bold", color=INK)
plt.tight_layout(); plt.savefig(os.path.join(HERE, "fig_activity.png"), dpi=170); plt.close()
print("figs ok")
