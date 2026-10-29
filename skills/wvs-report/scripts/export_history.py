#!/usr/bin/env python3
"""Incremental, local Markdown history export for Claude Code, Codex and Gemini CLI.

Source adapters normalize records; Markdown contains stable machine markers so
source deletion, compaction and edited messages never erase earlier exports.
No credentials, source sessions or agent settings are changed during export.
"""
import argparse
import base64
from contextlib import contextmanager
import copy
import json
import os
from pathlib import Path
import re
import shlex
import sys
import tempfile
from urllib.parse import quote

# -I isolates the interpreter but deliberately excludes this bundled module.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from history_sources import AGENTS, READERS, digest, event, session

MARKER = re.compile(r'^<!-- wvs:(project|session|event|memory) ([A-Za-z0-9_=-]+) -->$', re.M)
LEGACY_SESSION = re.compile(r'^## 세션 \d+: `([^`\n]+)`\n', re.M)
RESERVED = {'index', 'agents', 'claude', 'gemini', 'skill', 'con', 'prn', 'aux', 'nul'}


def marker(kind, data):
    encoded = base64.urlsafe_b64encode(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).decode()
    return f'<!-- wvs:{kind} {encoded} -->'


def safe_name(value):
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f`#\[\]]', '-', str(value))
    value = re.sub('-+', '-', value).strip(' .-')[:100] or 'project'
    if value.casefold() in RESERVED or re.fullmatch(r'(com|lpt)[1-9]', value, re.I):
        value += '-history'
    return value


def quote_body(body):
    # Quoting also prevents headings or machine markers inside conversations
    # from becoming document structure on the next incremental run.
    return '\n'.join('> ' + line for line in body.split('\n'))


def unquote_body(body):
    return '\n'.join(line[2:] for line in body.split('\n') if line.startswith('> '))


def read_export(path):
    text = path.read_text(encoding='utf-8')
    matches = list(MARKER.finditer(text))
    if not matches:
        source = re.search(r'^- 원본 디렉터리: `([^`]+)`$', text, re.M)
        if not source:
            return None
        # One-time lossless migration of the old Claude-only format. Legacy
        # blocks have no event IDs, so retain a labeled snapshot per session.
        p = {'key': str(Path(source[1]).resolve()), 'agent': 'claude-code', 'name': path.stem,
             'source': source[1], 'sessions': {}, 'memory': {}}
        all_sessions = list(LEGACY_SESSION.finditer(text))
        for i, m in enumerate(all_sessions):
            end = all_sessions[i + 1].start() if i + 1 < len(all_sessions) else len(text)
            body = text[m.end():end].split('\n## 프로젝트 메모리 (memory/)')[0].strip()
            s = session(m[1]); s['events'] = [event('legacy snapshot', body, identity=m[1])]
            p['sessions'][m[1]] = s
        memory = text.split('\n## 프로젝트 메모리 (memory/)\n', 1)
        if len(memory) == 2:
            p['memory']['legacy-memory.md'] = memory[1].strip()
        return p
    if matches[0][1] != 'project':
        raise ValueError(f'{path}: malformed export markers')
    p, current = None, None
    for i, m in enumerate(matches):
        try:
            data = json.loads(base64.urlsafe_b64decode(m[2]))
        except (ValueError, UnicodeError) as exc:
            raise ValueError(f'{path}: corrupt export marker') from exc
        body = text[m.end():matches[i + 1].start() if i + 1 < len(matches) else len(text)].strip('\n')
        if m[1] == 'project':
            if p is not None:
                raise ValueError(f'{path}: duplicate project marker')
            p = {**data, 'sessions': {}, 'memory': {}}
        elif m[1] == 'session':
            current = {**data, 'events': []}
            if current['id'] in p['sessions']:
                raise ValueError(f'{path}: duplicate session marker')
            p['sessions'][current['id']] = current
        elif m[1] == 'event':
            if current is None:
                raise ValueError(f'{path}: event outside session')
            decoded = unquote_body(body)
            if data.get('sha256') and digest(decoded) != data['sha256']:
                raise ValueError(f'{path}: modified or corrupt event body')
            current['events'].append({'key': data['key'], 'body': decoded})
        elif m[1] == 'memory':
            p['memory'][data['name']] = unquote_body(body)
    return p


def merge(old, new):
    if old is None:
        old = {**new, 'sessions': {}, 'memory': {}}
    result = copy.deepcopy(old)
    result.update({k: v for k, v in new.items() if k not in ('sessions', 'memory')})
    for sid, incoming in new['sessions'].items():
        target = result['sessions'].setdefault(sid, {**incoming, 'events': []})
        for key in ('cwd', 'title', 'parent'):
            if incoming.get(key):
                target[key] = incoming[key]
        known = {e['key'] for e in target['events']}
        for item in incoming['events']:
            if item['key'] not in known:
                target['events'].append(item)
                known.add(item['key'])
    for name, body in new['memory'].items():
        # Keep deleted individual files and prior content after edits as well.
        previous = result['memory'].get(name)
        if previous is not None and previous != body:
            result['memory'].setdefault(name + '@' + digest(previous)[:16], previous)
        result['memory'][name] = body
    return result


def render(p):
    metadata = {k: v for k, v in p.items() if k not in ('sessions', 'memory')}
    lines = [f'# {p["name"]} — {p["agent"]} 세션 히스토리', '', marker('project', metadata), '',
             f'- 원본 디렉터리: `{p["source"]}`', f'- 세션 수: {len(p["sessions"])}', '',
             '> 기록된 대화·도구 입출력의 누적 이력입니다. 수정 전 내용도 보존합니다.',
             '> 이미지 원본·내부 추론·인증정보·실행 환경을 복원하는 원시 백업은 아닙니다.', '']
    for i, s in enumerate(p['sessions'].values(), 1):
        lines += [marker('session', {k: v for k, v in s.items() if k != 'events'}),
                  f'## 세션 {i}: `{s["id"]}`', '', f'- cwd: `{s.get("cwd", "")}`',
                  f'- 제목: {s.get("title", "")}', f'- 상위 세션: `{s.get("parent", "")}`', '']
        for item in s['events']:
            lines += [marker('event', {'key': item['key'], 'sha256': digest(item['body'])}), quote_body(item['body']), '']
    for name, body in p['memory'].items():
        lines += [marker('memory', {'name': name}), f'## 메모리: {name}', '', quote_body(body), '']
    return '\n'.join(lines)


def atomic_write(path, text):
    if path.exists() and path.read_text(encoding='utf-8') == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True


@contextmanager
def export_lock(out):
    out.mkdir(parents=True, exist_ok=True)
    with (out / '.export.lock').open('a+b') as lock:
        try:
            if os.name == 'nt':
                import msvcrt
                if lock.tell() == 0:
                    lock.write(b'0'); lock.flush()
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ValueError('another export is running or lock is unavailable') from exc
        try:
            yield
        finally:
            if os.name == 'nt':
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def locations():
    home = Path.home()
    claude = Path(os.environ.get('CLAUDE_CONFIG_DIR') or home / '.claude').expanduser().resolve()
    codex = Path(os.environ.get('CODEX_HOME') or home / '.codex').expanduser().resolve()
    gemini = Path(os.environ.get('GEMINI_CLI_HOME') or home).expanduser().resolve() / '.gemini'
    return {'claude-code': (claude / 'projects', claude / 'session-history'),
            'codex': (codex, codex / 'session-history'),
            'gemini-cli': (gemini / 'tmp', gemini / 'session-history')}


def detect(src=None):
    candidates = []
    if src is not None:
        if (src / 'sessions').is_dir() or (src / 'archived_sessions').is_dir() or next(src.rglob('rollout-*.jsonl'), None):
            candidates.append('codex')
        if next(src.glob('*/chats/session-*'), None):
            candidates.append('gemini-cli')
        if next(src.glob('*/*.jsonl'), None) or next(src.glob('*/memory/*.md'), None):
            # Do not confuse date-sharded Codex rollouts with Claude projects.
            if 'codex' not in candidates:
                candidates.append('claude-code')
    else:
        # An installed directory is not evidence of the currently running host.
        # Explicit --agent from the skill is preferred to environment inference.
        if os.environ.get('CODEX_THREAD_ID') or os.environ.get('CODEX_SESSION_ID'):
            candidates.append('codex')
        if os.environ.get('CLAUDECODE') == '1':
            candidates.append('claude-code')
        if os.environ.get('GEMINI_CLI') == '1':
            candidates.append('gemini-cli')
    if len(candidates) != 1:
        raise ValueError('cannot uniquely detect agent; pass --agent claude-code|codex|gemini-cli (no Claude fallback)')
    return candidates[0]


def export(agent, src, out):
    if not src.is_dir():
        raise ValueError(f'source directory does not exist: {src}')
    if src == out or src.is_relative_to(out):
        raise ValueError('output must not equal or contain the source directory')
    # Codex home is a container: its session-history sibling is the default.
    if out.is_relative_to(src) and not (agent == 'codex' and ((src / 'sessions').is_dir() or (src / 'archived_sessions').is_dir()) and not any(out.is_relative_to(src / n) for n in ('sessions', 'archived_sessions'))):
        raise ValueError('output must be outside the session source tree')
    with export_lock(out):
        incoming = READERS[agent](src)  # Parse every source before modifying backups.
        existing, used = {}, {p.stem.casefold() for p in out.glob('*.md')} | RESERVED
        for path in sorted(out.glob('*.md')):
            if path.name.casefold() == 'index.md':
                continue
            old = read_export(path)
            if old is not None:
                key = (old['agent'], old['key'])
                if key in existing:
                    raise ValueError(f'duplicate project identity in output: {path.name}')
                existing[key] = (path, old)
        index_path = out / 'INDEX.md'
        if index_path.exists() and not index_path.read_text(encoding='utf-8').startswith('# 프로젝트별 세션 히스토리 인덱스\n'):
            raise ValueError('INDEX.md exists and is not a history index; choose another output')
        planned = {}
        for key, fresh in incoming.items():
            identity = (agent, key)
            old_path, old = existing.get(identity, (None, None))
            fresh['agent'] = agent
            if old_path is None:
                base = safe_name(fresh['name'])
                name, n = base, 1
                while name.casefold() in used:
                    n += 1; name = f'{base}-{n}'
                used.add(name.casefold())
                old_path = out / (name + '.md')
            fresh['name'] = old_path.stem
            merged = merge(old, fresh)
            planned[identity] = (old_path, merged, render(merged))
        updated = 0
        for identity, (path, merged, text) in planned.items():
            updated += atomic_write(path, text)
            existing[identity] = (path, merged)
        lines = ['# 프로젝트별 세션 히스토리 인덱스', '',
                 '| 파일 | 에이전트 | 세션 | 메시지 | 메모리 | 상태 |', '|---|---|---:|---:|---:|---|']
        for identity, (path, p) in sorted(existing.items()):
            status = '원본 확인' if identity in planned else '기존 파일 보존 (이번 원본에서 미탐색)'
            count = sum(len(s['events']) for s in p['sessions'].values())
            lines.append(f'| [{path.name}]({quote(path.name)}) | {p["agent"]} | {len(p["sessions"])} | {count} | {len(p["memory"])} | {status} |')
        atomic_write(index_path, '\n'.join(lines) + '\n')
        # Verify the persisted artifact, not just the text about to be written.
        missing = 0
        for identity, fresh in (( (agent, key), p) for key, p in incoming.items()):
            saved = read_export(existing[identity][0])
            for sid, s in fresh['sessions'].items():
                saved_events = {e['key'] for e in saved['sessions'].get(sid, {}).get('events', [])}
                missing += int(sid not in saved['sessions'])
                missing += len({e['key'] for e in s['events']} - saved_events)
            missing += sum(saved['memory'].get(name) != body for name, body in fresh['memory'].items())
        if missing:
            raise ValueError(f'verification failed: missing={missing}')
        print(json.dumps({'agent': agent, 'source': str(src), 'out': str(out),
                          'projects': len(incoming), 'source_sessions': sum(len(p['sessions']) for p in incoming.values()),
                          'files_updated': updated, 'missing': missing,
                          'preserved_projects': sum(k not in planned for k in existing)}, ensure_ascii=False))


def set_hook(agent, src, out, install):
    if agent != 'claude-code':
        raise ValueError('--install-hook/--uninstall-hook currently supports only claude-code; no settings were changed')
    if os.name == 'nt':
        raise ValueError('automatic hook installation requires a POSIX shell; use manual export on Windows')
    settings = locations()['claude-code'][0].parent / 'settings.json'
    if not settings.exists() and not install:
        print('SessionEnd hook absent'); return
    data = json.loads(settings.read_text(encoding='utf-8')) if settings.exists() else {}
    groups = []
    script = str(Path(__file__).resolve())
    for group in data.get('hooks', {}).get('SessionEnd', []):
        keep = []
        for hook in group.get('hooks', []):
            command = hook.get('command', '')
            # Manage only our named hook or the original exporter's exact shape.
            legacy = (command.startswith('(nohup ') and ' -I ' in command
                      and (shlex.quote(script) in command or f'"{script}"' in command)
                      and '.export.log' in command)
            if hook.get('statusMessage') == 'wvs-report sess-bak' or legacy:
                continue
            keep.append(hook)
        if keep:
            groups.append({**group, 'hooks': keep})
    if install:
        out.mkdir(parents=True, exist_ok=True)
        command = ' '.join(shlex.quote(arg) for arg in (sys.executable, '-I', script, str(out), '--agent', agent, '--src', str(src)))
        command = f'(nohup {command} >>{shlex.quote(str(out / ".export.log"))} 2>&1 </dev/null &) >/dev/null 2>&1'
        groups.append({'hooks': [{'type': 'command', 'command': command, 'statusMessage': 'wvs-report sess-bak'}]})
    hooks = data.setdefault('hooks', {})
    if groups:
        hooks['SessionEnd'] = groups
    else:
        hooks.pop('SessionEnd', None)
    if not hooks:
        data.pop('hooks', None)
    atomic_write(settings, json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    print(f'SessionEnd hook {"installed" if install else "removed"}: {settings}')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('out', nargs='?')
    parser.add_argument('--agent', default='auto', help='auto | claude-code | codex | gemini-cli')
    parser.add_argument('--src', help='Claude projects, Codex home/sessions, or Gemini tmp directory')
    parser.add_argument('--list-agents', action='store_true')
    hooks = parser.add_mutually_exclusive_group()
    hooks.add_argument('--install-hook', action='store_true')
    hooks.add_argument('--uninstall-hook', action='store_true')
    args = parser.parse_args(argv)
    if args.list_agents:
        for agent, (src, out) in locations().items():
            print(f'{agent}\tsource={src}\tout={out}\thook={agent == "claude-code"}')
        return 0
    try:
        src = Path(args.src).expanduser().resolve() if args.src else None
        agent = detect(src) if args.agent == 'auto' else args.agent
        if agent not in AGENTS:
            raise ValueError(f'unsupported agent: {agent}; supported: {", ".join(AGENTS)}; no backup was created')
        default_src, default_out = locations()[agent]
        src = src or default_src
        out = Path(args.out).expanduser().resolve() if args.out else default_out
        if args.install_hook or args.uninstall_hook:
            set_hook(agent, src, out, args.install_hook)
        else:
            export(agent, src, out)
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
