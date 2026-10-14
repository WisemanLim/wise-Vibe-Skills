# -*- coding: utf-8 -*-
"""research/r*.md 의 '## REPOS' 절 + 기초 보고서 저장소 + 사용자 스타 선별(stars_relevant.tsv)을 모아
repos_catalog.tsv(full_name·category·role_ko·adopt·note) 생성 → gh_probe 로 GitHub 실측 repos.tsv 생성.
사용: <venv>/bin/python collect_repos.py [--base <기초보고서 measured.json>]"""
import argparse, csv, glob, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "research")
sys.path.insert(0, HERE)
from kitpath import KIT  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument("--base", help="기초 분석 보고서 _assets/measured.json"); a = ap.parse_args()
cat = {}
for f in sorted(glob.glob(os.path.join(RES, "r[0-9]*_*.md"))):
    key = os.path.basename(f).split("_")[0]
    txt = open(f, encoding="utf-8").read()
    m = re.search(r"^## REPOS\s*$(.*?)(^## |\Z)", txt, re.S | re.M)
    for ln in (m.group(1).splitlines() if m else []):
        parts = [p.strip().strip("`") for p in ln.strip().lstrip("-* ").split("|")]
        if len(parts) < 3 or not re.fullmatch(r"[\w.-]+/[\w.-]+", parts[0]): continue
        cat.setdefault(parts[0].lower(), [parts[0], key, parts[1], parts[2][:1].upper(), " ".join(parts[3:])])
if a.base and os.path.exists(a.base):
    for x in json.load(open(a.base, encoding="utf-8")).get("repos", []):
        cat.setdefault(x["full_name"].lower(), [x["full_name"], "base", "기초 보고서 도출 스택", "R", ""])
p = os.path.join(RES, "stars_relevant.tsv")
if os.path.exists(p):
    for row in csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"):
        cat.setdefault(row["full_name"].lower(), [row["full_name"], "stars", row.get("use_ko", ""), row.get("adopt", "R")[:1], "★user"])
with open(os.path.join(RES, "repos_catalog.tsv"), "w", encoding="utf-8") as o:
    o.write("full_name\tcategory\trole_ko\tadopt\tnote\n")
    for r in cat.values(): o.write("\t".join(x.replace("\t", " ") for x in r) + "\n")
lst = os.path.join(RES, "_repo_list.txt")
open(lst, "w").write("\n".join(r[0] for r in cat.values()) + "\n")
print("catalog", len(cat))
subprocess.run([sys.executable, os.path.join(KIT, "gh_probe.py"), lst, "-o", os.path.join(RES, "repos.tsv")], check=True)
