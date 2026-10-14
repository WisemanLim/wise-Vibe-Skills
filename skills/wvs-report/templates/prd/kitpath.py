# -*- coding: utf-8 -*-
"""wvs-report/scripts 위치 탐색: $WVS_KIT → 알려진 스킬 루트(Claude Code · 공유 ~/.agents · Antigravity · 프로젝트)."""
import os, sys

def find_kit():
    cands = [os.environ.get("WVS_KIT", "")]
    for root in ("~/.claude/skills", "~/.agents/skills", "~/.gemini/config/skills", ".claude/skills", ".agents/skills"):
        cands.append(os.path.join(os.path.expanduser(root), "wvs-report", "scripts"))
    for c in cands:
        if c and os.path.exists(os.path.join(c, "docx_lib.py")):
            return os.path.abspath(c)
    sys.exit("wvs-report/scripts 를 찾을 수 없습니다 — WVS_KIT=<…/wvs-report/scripts> 를 지정하세요.")

KIT = find_kit()
if KIT not in sys.path:
    sys.path.insert(0, KIT)
