#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub 사용자의 Stars·Repositories 전수 수집 (wvs-report) — PRD 의 오픈소스 후보·자체 저장소 재사용 교차용.
(https://github.com/<user>?tab=stars, ?tab=repositories 와 같은 목록)

출력(<out>/):
  stars_all.tsv  : full_name  stars  license  lang  desc  archived  starred_at
  user_repos.tsv : name  fork  archived  lang  license  pushed  stars  visibility  desc
gh 인증 사용자가 <user> 본인이면 비공개 저장소까지 포함(user/repos), 아니면 공개 저장소만(users/<user>/repos).

사용: github_user_lists.py WisemanLim -o research/
"""
import argparse, json, os, subprocess, sys

STAR_JQ = ('.[] | [.repo.full_name, (.repo.stargazers_count|tostring), (.repo.license.spdx_id // "NONE"), (.repo.language // "-"), '
           '((.repo.description // "") | gsub("[\\t\\n]"; " ") | .[0:200]), (.repo.archived|tostring), .starred_at] | @tsv')
REPO_JQ = ('.[] | [.name, (.fork|tostring), (.archived|tostring), (.language // "-"), (.license.spdx_id // "NONE"), '
           '(.pushed_at[0:10]), (.stargazers_count|tostring), (.visibility|ascii_upcase), ((.description // "") | gsub("[\\t\\n]"; " ") | .[0:200])] | @tsv')


def gh(args):
    p = subprocess.run(["gh", "api", "--paginate"] + args, capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"gh api failed: {' '.join(args)}\n{p.stderr.strip()}")
    return p.stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("user"); ap.add_argument("-o", "--out", default="research")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    stars = gh(["-H", "Accept: application/vnd.github.star+json", f"users/{a.user}/starred?per_page=100", "--jq", STAR_JQ])
    open(os.path.join(a.out, "stars_all.tsv"), "w", encoding="utf-8").write(stars)
    me = subprocess.run(["gh", "api", "user", "--jq", ".login"], capture_output=True, text=True).stdout.strip()
    path = "user/repos?per_page=100&affiliation=owner" if me.lower() == a.user.lower() else f"users/{a.user}/repos?per_page=100"
    repos = gh([path, "--jq", REPO_JQ])
    open(os.path.join(a.out, "user_repos.tsv"), "w", encoding="utf-8").write(repos)
    print(f"stars {len(stars.splitlines())} · repos {len(repos.splitlines())} ({'owner incl. private' if path.startswith('user/') else 'public'}) → {a.out}")


if __name__ == "__main__":
    main()
