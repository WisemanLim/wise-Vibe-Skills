#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wvs-report sess-bak — Claude Code 프로젝트별 세션 히스토리를 <name>.md 로 증분 백업.

  export_history.py [OUT] [--src DIR]   OUT 기본 ~/.claude/session-history, SRC 기본 ~/.claude/projects
  export_history.py --install-hook      ~/.claude/settings.json 에 SessionEnd 자동 실행 훅 등록(기존 항목 교체)
  export_history.py --uninstall-hook    그 훅 제거

증분 규칙: 새 세션·메시지만 병합, 원본 jsonl 이 지워진 세션·서브에이전트·memory 는 기존 md 내용 보존,
세션 블록은 줄어들지 않음, 기존 세션이 빠지면 쓰지 않고 중단, 내용이 같은 파일은 다시 쓰지 않음(별도 백업 사본 없음).
"""
import argparse, glob, json, os, re, sys

HOME = os.path.expanduser('~')
ap = argparse.ArgumentParser(description='Claude Code 세션 히스토리 프로젝트별 md 증분 백업')
ap.add_argument('out', nargs='?', default=os.path.join(HOME, '.claude', 'session-history'))
ap.add_argument('--src', default=os.path.join(HOME, '.claude', 'projects'))
ap.add_argument('--install-hook', action='store_true')
ap.add_argument('--uninstall-hook', action='store_true')
ARGS = ap.parse_args()
SRC = os.path.abspath(os.path.expanduser(ARGS.src))
OUT = os.path.abspath(os.path.expanduser(ARGS.out))
SKIP_DIRS = {'.claude', '.omc', 'memory'}
_H = re.sub(r'[^A-Za-z0-9]', '-', HOME)  # Claude Code encodes /Users/x → -Users-x
PREFIXES = [_H + '-Downloads---Developer-backup-', _H + '-Developer-', '-private-tmp-claude-501-', _H + '-']
RE_SR = re.compile(r'<system-reminder>.*?</system-reminder>', re.S)
RE_SESS = re.compile(r'^## 세션 \d+: `([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})`\n\n?- 기간: ', re.M)
RE_CMD = re.compile(r'<command-name>(.*?)</command-name>.*?(?:<command-args>(.*?)</command-args>)?', re.S)


def short_name(d):
    n = d
    for p in PREFIXES:
        if n.startswith(p):
            n = n[len(p):]
            break
    n = re.sub(r'-{2,}', '-', n).strip('-')
    n = n or d.strip('-')
    # macOS FS is case-insensitive: claude.md would be loaded as CLAUDE.md instructions
    return 'claude-home' if n.lower() == 'claude' else n


def trunc(s, n):
    s = str(s)
    return s if len(s) <= n else s[:n] + f' …(+{len(s) - n} chars)'


def load(path):
    rows = []
    with open(path, errors='ignore') as fh:
        for line in fh:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows


def tool_summary(c):
    inp = c.get('input') or {}
    key = next((k for k in ('command', 'file_path', 'path', 'pattern', 'url', 'query',
                            'description', 'skill', 'prompt') if k in inp), None)
    val = trunc(str(inp[key]).replace('\n', ' '), 300) if key else trunc(json.dumps(inp, ensure_ascii=False), 200)
    return f'- 🔧 `{c.get("name")}` — {val}'


def user_text(o):
    m = o.get('message') or {}
    c = m.get('content')
    parts = []
    if isinstance(c, str):
        parts.append(c)
    elif isinstance(c, list):
        for b in c:
            if b.get('type') == 'text':
                parts.append(b.get('text', ''))
            elif b.get('type') == 'image':
                parts.append('[image]')
    t = RE_SR.sub('', '\n'.join(parts)).strip()
    mc = RE_CMD.search(t)
    if mc:
        t = f'/{mc.group(1).lstrip("/")} {(mc.group(2) or "").strip()}'.strip()
    elif '<local-command-stdout>' in t:
        t = trunc(re.sub(r'</?local-command-stdout>', '', t).strip(), 1500)
    return t


def render(rows, lines, full=True):
    for o in rows:
        t = o.get('type')
        if t not in ('user', 'assistant') or o.get('isMeta'):
            continue
        ts = (o.get('timestamp') or '')[:19].replace('T', ' ')
        if t == 'user':
            c = (o.get('message') or {}).get('content')
            if isinstance(c, list) and c and all(b.get('type') == 'tool_result' for b in c):
                continue
            txt = user_text(o)
            if not txt:
                continue
            label = '📋 Compact summary' if o.get('isCompactSummary') else '👤 User'
            if not full:
                txt = trunc(txt, 2000)
            lines += [f'#### {label} · {ts}', '', txt, '']
        else:
            content = (o.get('message') or {}).get('content') or []
            if isinstance(content, str):
                content = [{'type': 'text', 'text': content}]
            texts = [b.get('text', '') for b in content if b.get('type') == 'text' and b.get('text', '').strip()]
            tools = [tool_summary(b) for b in content if b.get('type') == 'tool_use']
            if not texts and not (tools and full):
                continue
            if texts:
                lines += [f'#### 🤖 Assistant · {ts}', '', '\n\n'.join(texts), '']
            if tools and full:
                lines += tools + ['']


def old_sessions(path):
    """Parse an existing export into {sid: (start, end, title, body_lines)}."""
    if not os.path.exists(path):
        return {}
    text = open(path, errors='ignore').read()
    ms = list(RE_SESS.finditer(text))
    out = {}
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        blk = '\n- 기간: ' + text[m.end():end]
        cut = blk.find('\n---\n\n## 프로젝트 메모리')
        if cut >= 0:
            blk = blk[:cut]
        blk = re.sub(r'\n---\n*$', '\n', blk.rstrip('\n') + '\n').strip('\n')
        pm = re.search(r'^- 기간: (\S*) ~ (\S*)$', blk, re.M)
        tm = re.search(r'^- 제목: (.*)$', blk, re.M)
        if m.group(1) not in out:
            blk = blk.strip('\n')
            out[m.group(1)] = ((pm.group(1) if pm else ''), (pm.group(2) if pm else ''),
                               (tm.group(1) if tm else ''), blk.split('\n'))
    return out


def old_memory(path):
    if not os.path.exists(path):
        return []
    text = open(path, errors='ignore').read()
    i = text.rfind('\n## 프로젝트 메모리 (memory/)\n')
    return text[i + 1:].rstrip('\n').split('\n') if i >= 0 else []


RE_DET = re.compile(r'^<details><summary>(.*?)</summary>\n.*?^</details>$', re.M | re.S)


def old_subs(body_lines):
    return {m.group(1): m.group(0) for m in RE_DET.finditer('\n'.join(body_lines))}


def meta(rows):
    ts = [o['timestamp'] for o in rows if o.get('timestamp')]
    cwd = next((o['cwd'] for o in rows if o.get('cwd')), '')
    br = next((o['gitBranch'] for o in rows if o.get('gitBranch')), '')
    title = next((o.get('summary') or o.get('aiTitle') or o.get('customTitle') for o in rows
                  if o.get('type') in ('summary', 'ai-title', 'custom-title')), '')
    return (min(ts) if ts else ''), (max(ts) if ts else ''), cwd, br, title


def anchored_names():
    """{source dir: existing md name} from previous exports, so names stay stable."""
    out = {}
    for f in glob.glob(os.path.join(OUT, '*.md')):
        with open(f, errors='ignore') as fh:
            m = re.search(r'^- 원본 디렉터리: `([^`]+)`$', fh.read(2000), re.M)
        if m:
            out[os.path.basename(m.group(1))] = os.path.basename(f)[:-3]
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    index, anchor = [], anchored_names()
    used = set(anchor.values())
    n_written = 0
    for d in sorted(os.listdir(SRC)):
        p = os.path.join(SRC, d)
        if not os.path.isdir(p) or d in SKIP_DIRS:
            continue
        name = anchor.get(d)
        if not name:
            name, k = short_name(d), 1
            while name in used:
                k += 1
                name = f'{short_name(d)}-{k}'
            used.add(name)
        sessions = []
        for f in glob.glob(os.path.join(p, '*.jsonl')):
            rows = load(f)
            sessions.append((meta(rows), os.path.basename(f)[:-6], rows))
        out = os.path.join(OUT, f'{name}.md')
        have = {sid for _, sid, _ in sessions}
        n_kept = 0
        olds = old_sessions(out)
        for sid, (st, en, ti, body) in olds.items():
            if sid not in have:
                sessions.append(((st, en, '', '', ti), sid, body))
                n_kept += 1
        sessions.sort(key=lambda s: s[0][0])
        lines = [f'# {name} — Claude Code 세션 히스토리', '',
                 f'- 원본 디렉터리: `{p}`', f'- 세션 수: {len(sessions)}', '']
        if sessions:
            lines += ['## 목차', '']
            for i, (m, sid, _) in enumerate(sessions, 1):
                lines.append(f'{i}. `{sid}` · {m[0][:16].replace("T", " ")} ~ {m[1][:16].replace("T", " ")}'
                             + (f' · {m[4]}' if m[4] else ''))
            lines.append('')
        else:
            lines += ['> 저장된 세션 대화(jsonl)가 없습니다.', '']
        n_sub = 0
        for i, (m, sid, rows) in enumerate(sessions, 1):
            if rows and isinstance(rows[0], str):  # preserved from previous export (source jsonl gone)
                lines += ['---', '', f'## 세션 {i}: `{sid}`', ''] + rows + ['']
                continue
            body = [f'- 기간: {m[0]} ~ {m[1]}', f'- cwd: `{m[2]}`', f'- branch: `{m[3]}`'] + \
                   ([f'- 제목: {m[4]}'] if m[4] else []) + ['']
            render(rows, body)
            if sid in olds:  # never shrink: keep old block if it holds more messages than the jsonl now does
                old_body = [x for x in olds[sid][3] if not x.startswith('### 서브에이전트')]
                cut = next((j for j, x in enumerate(old_body) if x.startswith('<details>')), len(old_body))
                if sum(x.startswith('#### ') for x in old_body[:cut]) > sum(x.startswith('#### ') for x in body):
                    body = old_body[:cut]
            lines += ['---', '', f'## 세션 {i}: `{sid}`', ''] + body
            subs = sorted(glob.glob(os.path.join(p, sid, '**', '*.jsonl'), recursive=True))
            gone = {k: v for k, v in old_subs(olds[sid][3]).items()
                    if k not in {os.path.relpath(x, os.path.join(p, sid)) for x in subs}} if sid in olds else {}
            if subs or gone:
                lines += [f'### 서브에이전트 ({len(subs) + len(gone)}) — 프롬프트·최종 응답 요약', '']
                for v in gone.values():  # preserved: subagent jsonl deleted since last export
                    n_sub += 1
                    lines += [v, '']
                for sf in subs:
                    srows = load(sf)
                    n_sub += 1
                    lines += [f'<details><summary>{os.path.relpath(sf, os.path.join(p, sid))}</summary>', '']
                    first = next((o for o in srows if o.get('type') == 'user' and user_text(o)), None)
                    last = next((o for o in reversed(srows) if o.get('type') == 'assistant' and any(
                        b.get('type') == 'text' and b.get('text', '').strip()
                        for b in ((o.get('message') or {}).get('content') or []) if isinstance(b, dict))), None)
                    render([x for x in (first, last) if x], lines, full=False)
                    lines += ['</details>', '']
        mem = sorted(glob.glob(os.path.join(p, 'memory', '*.md')))
        if mem:
            lines += ['---', '', '## 프로젝트 메모리 (memory/)', '']
            for mf in mem:
                lines += [f'### {os.path.basename(mf)}', '', open(mf, errors='ignore').read().strip(), '']
        elif old_memory(out):  # memory/ deleted since last export: keep previous copy
            lines += ['---', ''] + old_memory(out) + ['']
        others = [x for x in glob.glob(os.path.join(p, '*', '**', '*'), recursive=True)
                  if os.path.isfile(x) and not x.endswith('.jsonl') and '/memory/' not in x and '/tool-results/' not in x]
        if not sessions and others:
            lines += ['## 기타 파일', ''] + [f'- `{os.path.relpath(x, p)}`' for x in sorted(others)] + ['']
        text = '\n'.join(lines)
        lost = set(olds) - set(RE_SESS.findall(text))
        if lost:
            sys.exit(f'ABORT {name}.md: would lose sessions {sorted(lost)}')
        old_text = open(out, errors='ignore').read() if os.path.exists(out) else None
        if text != old_text:
            tmp = out + '.tmp'
            with open(tmp, 'w') as fh:
                fh.write(text)
            os.replace(tmp, out)
            n_written += 1
        index.append((name, d, len(sessions), n_sub, len(mem), os.path.getsize(out), n_kept))
    done = {r[0] for r in index}
    for f in sorted(glob.glob(os.path.join(OUT, '*.md'))):
        n = os.path.basename(f)[:-3]
        if n != 'INDEX' and n not in done:
            k = len(old_sessions(f))
            index.append((n, '(원본 디렉터리 삭제됨 — 기존 파일 보존)', k, 0, 0, os.path.getsize(f), k))
    with open(os.path.join(OUT, 'INDEX.md'), 'w') as fh:
        fh.write('# 프로젝트별 세션 히스토리 인덱스\n\n| 파일 | 세션 | 보존(원본 삭제) | 서브에이전트 | 메모리 | 크기 | 원본 디렉터리 |\n|---|---|---|---|---|---|---|\n')
        for n, d, s, sa, mm, sz, kp in index:
            fh.write(f'| [{n}.md]({n}.md) | {s} | {kp} | {sa} | {mm} | {sz // 1024}KB | `{d}` |\n')
    for r in index:
        print(*r, sep='\t')
    print(f'# files updated: {n_written}', file=sys.stderr)


def set_hook(install):
    """SessionEnd 훅 등록/제거 — 'export_history.py' 를 부르는 기존 항목은 교체한다."""
    p = os.path.join(HOME, '.claude', 'settings.json')
    d = json.load(open(p)) if os.path.exists(p) else {}
    hooks = d.setdefault('hooks', {})
    ends = [g for g in hooks.get('SessionEnd', [])
            if not any('export_history.py' in h.get('command', '') for h in g.get('hooks', []))]
    if install:
        os.makedirs(OUT, exist_ok=True)  # 훅의 로그 리다이렉트 대상
        log = os.path.join(OUT, '.export.log')
        cmd = f'(nohup "{sys.executable}" -I "{os.path.abspath(__file__)}" "{OUT}" --src "{SRC}" >"{log}" 2>&1 &) >/dev/null 2>&1'
        ends.append({'hooks': [{'type': 'command', 'command': cmd}]})
    if ends:
        hooks['SessionEnd'] = ends
    else:
        hooks.pop('SessionEnd', None)
    if not hooks:
        d.pop('hooks')
    tmp = p + '.tmp'
    with open(tmp, 'w') as fh:
        fh.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')
    os.replace(tmp, p)
    print(f'SessionEnd hook {"installed" if install else "removed"}: {p}')


if __name__ == '__main__':
    if ARGS.install_hook or ARGS.uninstall_hook:
        set_hook(ARGS.install_hook)
        sys.exit(0)
    os.makedirs(OUT, exist_ok=True)
    try:  # 동시에 끝난 세션 여러 개가 같은 OUT 을 쓰지 않도록
        import fcntl
        _lock = open(os.path.join(OUT, '.export.lock'), 'w')
        fcntl.flock(_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except ImportError:
        pass
    except OSError:
        sys.exit('another export is running')
    main()
