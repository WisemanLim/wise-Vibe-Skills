# -*- coding: utf-8 -*-
"""PRD 빌더 — part*.py(장별 본문)를 한 네임스페이스에서 번호 순으로 실행해 docx 생성 → (선택) PDF.
wvs-report prd 템플릿. <출력 폴더>/<Brand>_assets/ 에 복사해 쓴다 — 출력 폴더 = <root>/Need-to-be-organized-into-PRD(있을 때) 또는 <root>(없을 때), scripts/out_dir.py.

네임스페이스: docx_lib(r.* 와 H/P/T/KV/CODE/FIG/W …), data, units, data_fr, ui_data, prd_auto, md2docx(M)
게이트(prd_auto.gates): FR 없는 단위·카탈로그 밖 FR·화면 미커버 FR·유령 FR·실측 안 된 참고 OSS — 하나라도 있으면 실패(--no-strict 로 경고만).
사용: <venv>/bin/python build_prd.py [--pdf] [--no-strict]
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("WVS_ASSETS", HERE)
sys.path.insert(0, HERE); os.chdir(HERE)
from kitpath import KIT  # noqa: E402,F401
import docx_lib, md2docx, data, units, data_fr, ui_data, prd_auto  # noqa: E402

ns = {"r": docx_lib, "M": md2docx}
for m in (docx_lib, data, units, data_fr, ui_data, prd_auto):
    ns.update({k: v for k, v in vars(m).items() if not k.startswith("__")})
parts = sorted([f for f in os.listdir(HERE) if re.fullmatch(r"part\d+.*\.py", f)], key=lambda f: int(re.findall(r"\d+", f)[0]))
assert parts, "part*.py 가 없습니다"
for f in parts:
    exec(compile(open(f, encoding="utf-8").read(), f, "exec"), ns)

fails = prd_auto.gates()
for x in fails: print("GATE FAIL:", x)
if fails and "--no-strict" not in sys.argv:
    sys.exit("게이트 실패 — 조사 원문(FR·REPOS)·ui_data 를 고친 뒤 다시 빌드하세요(경고만 보려면 --no-strict).")
out = os.path.join(data.OUT_DIR, data.FILE_STEM + ".docx")
docx_lib.SAVE(out, pdf="--pdf" in sys.argv)
print(f"parts {len(parts)} · units {len(units.UNITS)} · FR {data_fr.n_items()} · screens {len(ui_data.SCREENS)} · gates {'PASS' if not fails else 'WARN'}")
