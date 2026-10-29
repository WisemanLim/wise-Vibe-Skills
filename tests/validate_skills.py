#!/usr/bin/env python3
"""Validate every skills/<name>/SKILL.md: frontmatter (name == dir, kebab-case, description 1..1024 chars), referenced bundled files exist."""
import os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills")
bad = []
for name in sorted(os.listdir(ROOT)):
    p = os.path.join(ROOT, name, "SKILL.md")
    if not os.path.isfile(p):
        continue
    s = open(p, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", s, re.S)
    if not m:
        bad.append(f"{name}: no frontmatter"); continue
    fm = dict(re.findall(r'^(\w[\w-]*):\s*"?(.*?)"?\s*$', m.group(1), re.M))
    if fm.get("name") != name: bad.append(f"{name}: name '{fm.get('name')}' != dir")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64: bad.append(f"{name}: invalid skill name")
    d = fm.get("description", "")
    if not (1 <= len(d) <= 1024): bad.append(f"{name}: description length {len(d)}")
    if '<' in d or '>' in d: bad.append(f"{name}: description contains angle brackets")
    for directory, _, files in os.walk(os.path.join(ROOT, name)):
        for filename in files:
            if not filename.endswith('.md'): continue
            markdown = open(os.path.join(directory, filename), encoding='utf-8').read()
            for ref in re.findall(r"`((?:scripts|templates|references)/[\w./-]+\.(?:py|sh|md))`", markdown):
                if not os.path.exists(os.path.join(ROOT, name, ref)):
                    bad.append(f"{name}/{filename}: missing bundled file {ref}")
    print(f"ok  {name:32s} desc {len(d):4d} chars")
if bad:
    print("\n".join("FAIL " + b for b in bad)); sys.exit(1)
