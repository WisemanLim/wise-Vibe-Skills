# -*- coding: utf-8 -*-
"""wvs-report/scripts(툴킷) 위치 탐색 — find_kit() 참고."""
import os, sys

def find_kit():
    """wvs-report/scripts(툴킷) 위치 — 에이전트·설치 방식과 무관하게 찾는다.
    1) $WVS_KIT  2) 자산 폴더(또는 상위·형제 *_assets)의 .wvs_kit(setup_env.sh 가 기록)  3) 알려진 스킬 루트
    (Claude Code·공유 ~/.agents·Antigravity·Gemini CLI·Claude 플러그인 캐시·프로젝트 .claude/.agents)."""
    import glob
    here = os.path.dirname(os.path.abspath(__file__))
    cands = [os.environ.get("WVS_KIT", "")]
    d = here
    for _ in range(4):
        cands += [open(f, encoding="utf-8").read().strip() for f in [os.path.join(d, ".wvs_kit")] + glob.glob(os.path.join(d, "*_assets", ".wvs_kit")) if os.path.isfile(f)]
        d = os.path.dirname(d)
    home = os.path.expanduser("~")
    roots = [os.environ.get("CLAUDE_CONFIG_DIR", os.path.join(home, ".claude")) + "/skills", home + "/.agents/skills", home + "/.gemini/config/skills",
             os.path.join(os.environ.get("GEMINI_CLI_HOME", home), ".agents", "skills"), ".claude/skills", ".agents/skills"]
    cands += [os.path.join(r, "wvs-report", "scripts") for r in roots]
    cands += sorted(glob.glob(os.path.join(home, ".claude", "plugins", "**", "skills", "wvs-report", "scripts"), recursive=True))
    for c in cands:
        if c and os.path.exists(os.path.join(c, "docx_lib.py")):
            return os.path.abspath(c)
    sys.exit("wvs-report/scripts 를 찾을 수 없습니다 — WVS_KIT=<…/wvs-report/scripts> 를 지정하거나 setup_env.sh 로 자산 폴더를 준비하세요.")

KIT = find_kit()
if KIT not in sys.path:
    sys.path.insert(0, KIT)
