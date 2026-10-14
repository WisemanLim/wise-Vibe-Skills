#!/usr/bin/env python3
"""wvs-report kit smoke test: docx_lib + md2docx + wire_lib + ui_lib → docx/pptx (+pdf when LibreOffice exists) → check_report."""
import os, shutil, subprocess, sys, tempfile
sys.dont_write_bytecode = True

KIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills", "wvs-report", "scripts")
T = tempfile.mkdtemp(prefix="wvs-smoke-")
os.environ["WVS_ASSETS"] = T
os.makedirs(os.path.join(T, "research"))
open(os.path.join(T, "research", "r1_demo.md"), "w", encoding="utf-8").write(
    "# TOOL_A Alpha — 데모\n### 정의\nAlpha 는 **데모** `alpha.run()`.\n### 사용방법\n| 옵션 | 의미 |\n|---|---|\n| --x | 테스트 |\n"
    "```python\nimport alpha\n```\n- 불릿\n  - 하위\n1. 번호\n# REPOS 저장소\n- py-pdf/pypdf\n")
sys.path.insert(0, KIT)
import docx_lib as r, md2docx as M, wire_lib as wl, ui_lib as U  # noqa: E402

wl.configure(brand="Smoke", nav=[("홈", [("HOME", "개요 맵")])], out=T)
fig, ax, _ = wl.frame("개요 맵", "S001", stage="HOME"); wl.footer(ax); png = wl.save(fig, "wire.png")
r.COVER("Smoke Report", "부제", "태그라인", [(f"작성일: {r.DOC_DATE}", 10, None)])
r.CH("개요"); r.SEC("목적"); r.P("본문 **굵게** `code`."); r.KV([("키", "값")]); r.T(["a", "b"], [["1", "2"]], widths=r.W([1, 2]))
r.FIG(png, 15, "와이어프레임", "자체 작성")
ALL = M.load_all("research"); t, b = M.block(ALL, "r1", "TOOL_A"); r.CH("조사"); r.SEC(t.split(" ", 1)[1]); M.render(r, b, sub_level=3)
assert M.repos(ALL) == ["py-pdf/pypdf"]
r.CH("부록"); r.FIG_TABLE()
pdf = shutil.which("soffice") or os.path.exists("/Applications/LibreOffice.app/Contents/MacOS/soffice")
docx, out_pdf = r.SAVE(os.path.join(T, "Smoke Report+%.docx"), pdf=bool(pdf))
U.configure(system="Smoke", nav=[("홈", "홈", [("HOME", "개요 맵")])])
U.screen_slide(dict(id="SCR-A01", name="개요", path="/", kind="페이지", section="A", perm="전체", prio="P0", desc="d", fr=["FR-A-01"],
                    items=[(1, "카드", "카드", "설명", "FR-A-01")], wire=lambda w: (w.shell(nav="HOME", title="개요"), w.callout(1, 20, 20))))
U.prs.save(os.path.join(T, "ui.pptx"))
cmd = [sys.executable, os.path.join(KIT, "check_report.py"), docx, "--require", "Alpha", "--forbid", "Summary-Repos.docx"]
if out_pdf: cmd += ["--pdf", out_pdf]
rc = subprocess.run(cmd).returncode
print("smoke dir:", T, "· pdf:", bool(out_pdf))
sys.exit(rc)
