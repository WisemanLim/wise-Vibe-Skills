"""Read supported local session formats without modifying their source files."""
import hashlib
import json
from collections import Counter
from pathlib import Path

AGENTS = ('claude-code', 'codex', 'gemini-cli')


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def jsonl(path):
    rows = []
    with path.open(encoding='utf-8') as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError('expected an object')
            except ValueError as exc:
                # Never silently report a complete backup after skipping corrupt data.
                raise ValueError(f'{path}:{number}: invalid JSONL (retry if session is being written)') from exc
            rows.append(row)
    return rows


def content_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return '\n\n'.join(filter(None, (content_text(v) for v in value)))
    if isinstance(value, dict):
        kind = value.get('type', '')
        if kind in ('thinking', 'redacted_thinking', 'reasoning'):
            return ''
        if isinstance(value.get('text'), str):
            return value['text']
        if kind in ('image', 'input_image', 'image_url') or 'inlineData' in value:
            return '[image: original attachment remains in source]'
        return json.dumps(value, ensure_ascii=False, indent=2)
    return '' if value is None else str(value)


def event(role, content, timestamp='', identity=''):
    text = content_text(content)
    if not text.strip():
        return None
    body = f'#### {role} · {timestamp}\n\n{text}'
    return {'key': digest(str(identity) + '\0' + body), 'body': body, '_anonymous': not identity}


def session(sid, cwd='', title='', parent=''):
    if not isinstance(sid, str) or not sid:
        raise ValueError('session ID is missing')
    return {'id': sid, 'cwd': cwd, 'title': title, 'parent': parent, 'events': []}


def add(s, item):
    if item is not None:
        if item.pop('_anonymous', False):
            # Preserve repeated identical turns without native IDs. The ordinal
            # distinguishes occurrences within each source snapshot.
            counts = s.setdefault('_occurrences', {})
            base = item['key']
            ordinal = counts.get(base, 0)
            counts[base] = ordinal + 1
            if ordinal:
                item['key'] = digest(base + ':' + str(ordinal))
        s['events'].append(item)


def project(projects, key, name, source):
    return projects.setdefault(key, {'key': key, 'name': name, 'source': str(source), 'sessions': {}, 'memory': {}})


def put_session(p, s):
    s.pop('_occurrences', None)
    previous = p['sessions'].get(s['id'])
    if previous is None:
        p['sessions'][s['id']] = s
    else:
        known = {e['key'] for e in previous['events']}
        for e in s['events']:
            if e['key'] not in known:
                previous['events'].append(e)
                known.add(e['key'])


def claude(src):
    projects = {}
    for directory in sorted(p for p in src.iterdir() if p.is_dir()):
        # Empty and memory-only projects must also be represented.
        p = project(projects, str(directory), directory.name.strip('-'), directory)
        files = sorted(directory.glob('*.jsonl'))
        files += sorted(f for f in directory.glob('*/**/*.jsonl') if f.relative_to(directory).parts[0] != 'memory')
        for path in files:
            rows = jsonl(path)
            if any(r.get('type') == 'session_meta' for r in rows):
                raise ValueError(f'{path}: Codex rollout found in Claude source; use --agent codex')
            rel = path.relative_to(directory)
            parent = rel.parts[0] if len(rel.parts) > 1 else ''
            sid = str(rel.with_suffix('')).replace('\\', '/') if parent else path.stem
            cwd = next((r.get('cwd') for r in rows if r.get('cwd')), '')
            if cwd:
                p['name'] = Path(cwd.replace('\\', '/')).name or 'home'
            s = session(sid, cwd, parent=parent)
            for i, row in enumerate(rows):
                kind = row.get('type')
                if kind in ('summary', 'ai-title', 'custom-title'):
                    s['title'] = row.get('summary') or row.get('aiTitle') or row.get('customTitle') or ''
                if kind in ('user', 'assistant'):
                    msg = row.get('message') or {}
                    if not isinstance(msg, dict):
                        raise ValueError(f'{path}: invalid message object')
                    role = 'Compact summary' if row.get('isCompactSummary') else kind
                    add(s, event(role, msg.get('content'), row.get('timestamp', ''), row.get('uuid', '')))
            put_session(p, s)
        for path in sorted((directory / 'memory').rglob('*.md')):
            p['memory'][path.relative_to(directory / 'memory').as_posix()] = path.read_text(encoding='utf-8')
    return projects


def codex(src):
    projects = {}
    # --src is a Codex home OR a standalone sessions/archive directory.
    roots = [src / 'sessions', src / 'archived_sessions'] if (src / 'sessions').is_dir() or (src / 'archived_sessions').is_dir() else [src]
    for root in roots:
        if next(root.rglob('*.jsonl.zst'), None):
            raise ValueError(f'{root}: compressed .jsonl.zst is not supported; decompress a copy before exporting')
        for path in sorted(root.rglob('*.jsonl')):
            rows = jsonl(path)
            metadata = next((r.get('payload') for r in rows if r.get('type') == 'session_meta'), None)
            if not isinstance(metadata, dict):
                raise ValueError(f'{path}: missing Codex session_meta')
            sid = metadata.get('id') or metadata.get('session_id')
            cwd = metadata.get('cwd') or next((r.get('payload', {}).get('cwd') for r in rows if r.get('type') == 'turn_context' and r.get('payload', {}).get('cwd')), '')
            key = cwd or f'unknown:{sid}'
            p = project(projects, key, Path(cwd.replace('\\', '/')).name if cwd else f'unknown-{sid}', src)
            s = session(sid, cwd)
            response_copies = Counter(
                (r['payload'].get('role'), content_text(r['payload'].get('content')))
                for r in rows if r.get('type') == 'response_item' and isinstance(r.get('payload'), dict)
                and r['payload'].get('type') == 'message')
            for row in rows:
                data = row.get('payload') or {}
                if not isinstance(data, dict):
                    raise ValueError(f'{path}: invalid Codex payload')
                kind, role, value = data.get('type'), '', None
                if row.get('type') == 'response_item':
                    if kind == 'message' and data.get('role') in ('user', 'assistant'):
                        role, value = data['role'], data.get('content')
                    elif kind in ('function_call', 'custom_tool_call'):
                        role, value = 'tool call: ' + data.get('name', ''), data.get('arguments', data.get('input'))
                    elif kind in ('function_call_output', 'custom_tool_call_output'):
                        role, value = 'tool result', data.get('output')
                    elif kind == 'agent_message':
                        role, value = 'agent message', data.get('content')
                elif row.get('type') == 'event_msg':
                    # Match mirrors per content/occurrence, not per role: mixed
                    # older/newer rollouts can contain event-only earlier turns.
                    candidate = {'user_message': 'user', 'agent_message': 'assistant'}.get(kind)
                    if candidate:
                        fingerprint = (candidate, content_text(data.get('message')))
                        if response_copies[fingerprint]:
                            response_copies[fingerprint] -= 1
                        else:
                            role, value = candidate, data.get('message')
                elif row.get('type') == 'compacted':
                    role, value = 'Compact summary', data.get('message')
                if role:
                    add(s, event(role, value, row.get('timestamp', ''), data.get('id') or data.get('call_id') or ''))
            put_session(p, s)
    return projects


def gemini(src):
    projects = {}
    files = sorted(p for chats in src.glob('*/chats') for p in chats.rglob('*') if p.is_file())
    for path in files:
        if path.suffix not in ('.json', '.jsonl'):
            continue
        # Both legacy JSON and append-only JSONL are in use. Preserve recorded
        # revisions/rewinds as history instead of deleting previously seen turns.
        if path.suffix == '.json':
            data = json.loads(path.read_text(encoding='utf-8'))
            records = data.get('messages', []) if isinstance(data, dict) else None
        else:
            records = jsonl(path)
            data = next((r for r in records if 'sessionId' in r and 'projectHash' in r), {})
        if not isinstance(data, dict) or not isinstance(records, list):
            raise ValueError(f'{path}: invalid Gemini conversation')
        sid = data.get('sessionId')
        rel = path.relative_to(src)
        key = data.get('projectHash') or rel.parts[0]
        p = project(projects, key, key, src / rel.parts[0])
        s = session(sid, title=data.get('summary', ''), parent=rel.parts[2] if len(rel.parts) > 3 else '')
        messages = {}
        def record_message(row):
            identity = row.get('id', '')
            messages[identity] = row
            add(s, event(row.get('type', 'message'), row.get('content'), row.get('timestamp', ''), identity))
            add(s, event('tool calls', row.get('toolCalls'), row.get('timestamp', ''), identity))

        for row in records:
            if not isinstance(row, dict):
                raise ValueError(f'{path}: invalid Gemini message')
            if '$set' in row:
                s['title'] = row['$set'].get('summary', s['title'])
                for message in row['$set'].get('messages', []):
                    record_message(message)
            elif '$patch' in row:
                patch_data = row['$patch']
                patches = patch_data.get('updates', [])
                if 'id' in patch_data:
                    patches = [patch_data, *patches]
                for patch in patches:
                    identity = patch['id']
                    msg = {**messages.get(identity, {}), **patch}
                    record_message(msg)
            elif '$rewindTo' in row:
                add(s, event('rewind', row['$rewindTo'], identity='rewind'))
            elif row.get('type'):
                record_message(row)
        put_session(p, s)
    return projects


READERS = {'claude-code': claude, 'codex': codex, 'gemini-cli': gemini}
