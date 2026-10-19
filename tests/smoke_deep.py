#!/usr/bin/env python3
"""wvs-report deep template smoke: out_dir rule → prd_intake(이미지·md·사이트) → build_report.py → <OUT>/<Title>.docx(+pdf).
case with:    <root>/Miscellaneous-Data 있음 + 이미지 입력        → <root>/Miscellaneous-Data/<Title>.docx
case without: 폴더 없음 + md·사이트만(이미지 없음) + 조사 블록 누락 → <root>/<Title>.docx (WARN, 중단 없음)"""
import os, shutil, subprocess, sys, tempfile
sys.dont_write_bytecode = True

SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills", "wvs-report")
KIT = os.path.abspath(os.path.join(SK, "scripts"))
T = tempfile.mkdtemp(prefix="wvs-deep-")
TITLE = "OCR+PDF Extractors"
PDF = bool(shutil.which("soffice") or os.path.exists("/Applications/LibreOffice.app/Contents/MacOS/soffice"))
BLOCKS = {"r1_a.md": ["FND_X", "TOOL_A", "CMP_X"], "r5_gap.md": ["GAP_TOOLS"],
          "r6_value.md": ["VAL_COMPARE", "VAL_USE", "VAL_ARCH", "VAL_ROADMAP", "VAL_GOV"]}


def run(*a):
    p = subprocess.run(a, capture_output=True, text=True)
    assert p.returncode == 0, (a, p.stdout, p.stderr)
    return p


def case(name, misc, inputs, drop=None):
    root = os.path.join(T, name); os.makedirs(os.path.join(root, "Miscellaneous-Data") if misc else root)
    out = run(sys.executable, os.path.join(KIT, "out_dir.py"), "deep", "--root", root).stdout.strip()
    assert out == (os.path.join(root, "Miscellaneous-Data") if misc else root), out
    A = os.path.join(out, TITLE + "_assets")
    run(sys.executable, os.path.join(KIT, "prd_intake.py"), *inputs(root), "--assets", A, "--root", root, "--no-fetch")
    if os.path.exists(os.path.join(A, "inputs", "IN-01.png")): shutil.copy(os.path.join(A, "inputs", "IN-01.png"), os.path.join(A, "source_infographic.png"))
    for f in ("build_report.py", "report_config.py"): shutil.copy(os.path.join(SK, "templates", "deep", f), A)
    cfg = os.path.join(A, "report_config.py"); s = open(cfg, encoding="utf-8").read()
    open(cfg, "w", encoding="utf-8").write(s.replace('TITLE_FILE = "{OCR+PDF Extractors}"', f'TITLE_FILE = "{TITLE}"'))
    for f, keys in BLOCKS.items():
        body = "".join(f"# {k} 제목 {k}\n본문 {k}.\n\n### 도식 판정\n| 항목 | 판정 | 근거 |\n|---|---|---|\n| {k} | 일치 | ok |\n" for k in keys if k != drop)
        open(os.path.join(A, "research", f), "w", encoding="utf-8").write(body)
    if not misc: assert not os.path.exists(os.path.join(root, "Miscellaneous-Data"))
    p = run(sys.executable, os.path.join(A, "build_report.py"), *(["--pdf"] if PDF else []))
    docx = os.path.join(out, TITLE + ".docx")
    assert os.path.isfile(docx), docx
    if PDF: assert os.path.isfile(docx[:-5] + ".pdf")
    if drop: assert f"조사 블록 없음" in p.stderr and "source_infographic" not in p.stderr, p.stderr
    run(sys.executable, os.path.join(KIT, "check_report.py"), docx, "--require", "원본 인포그래픽" if misc else "OCR 도구")   # 입력 표는 md 제목을 싣는다
    return docx


def img(root):
    import zlib, struct
    raw = b"".join(b"\x00" + b"\xff\x00\x00" * 4 for _ in range(4))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    p = os.path.join(root, "infographic.png")
    open(p, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    return [p]


def md_site(root):
    p = os.path.join(root, "notes.md"); open(p, "w", encoding="utf-8").write("# OCR 도구\n- Tool A\n- Tool B\n")
    return [p, "https://example.com/ocr-tools"]


print(case("with", True, img))
print(case("without", False, md_site, drop="CMP_X"))
print("smoke dir:", T, "· pdf:", PDF)
