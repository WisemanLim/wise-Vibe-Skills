# -*- coding: utf-8 -*-
"""research/*.md(조사 원문) → docx_lib 호출 (wvs-report).

조사 파일 형식(research/_SPEC.md 의 '파일 형식'):
  '# <KEY> <제목>'  최상위 블록(KEY = 영문 대문자 토큰) → 보고서 절(H2) 하나
  '### <소제목>'     블록 안 소제목 → H3 (sub_level=3)
  본문: 문단 · '- ' 불릿(2칸 들여쓰기=하위) · '1. ' 번호 · 마크다운 표(헤더+구분줄) · ``` 코드 펜스(40줄 초과는 생략 표시) · **굵게** · `코드`.

사용:
    import docx_lib as r, md2docx as M
    ALL = M.load_all("research")                  # {(파일태그, KEY): (제목, 본문)}
    title, body = ALL[("r1", "NP_PYPDF")]
    r.H(title.split(" ", 1)[1], 2); M.render(r, body, sub_level=3)
"""
import glob, os, re, unicodedata


def load_all(res_dir="research", pattern="r*.md"):
    """{(태그, KEY): (제목, 본문)} — 태그 = 파일명 '_' 앞(r1, r2 …), KEY = '# ' 제목 첫 토큰."""
    if not os.path.isabs(res_dir):
        res_dir = os.path.join(os.environ.get("WVS_ASSETS") or os.getcwd(), res_dir)
    out = {}
    for fp in sorted(glob.glob(os.path.join(res_dir, pattern))):
        tag = os.path.basename(fp).split("_")[0]
        cur, buf, fence = None, [], False
        for ln in open(fp, encoding="utf-8").read().splitlines():
            if ln.startswith("```"):
                fence = not fence
            if not fence and re.match(r"^# (?!#)", ln):
                if cur: out[(tag, cur[0])] = (cur[1], "\n".join(buf).strip())
                title = ln[2:].strip()
                cur, buf = (title.split()[0], title), []
            else:
                buf.append(ln)
        if cur: out[(tag, cur[0])] = (cur[1], "\n".join(buf).strip())
    return out


def block(all_blocks, tag, key):
    v = all_blocks.get((tag, key))
    if v is None:
        raise KeyError(f"research block not found: {tag} {key}")
    return v


def subsections(body):
    """'## ' 단위 [(제목, 본문)]. 첫 '## ' 앞 내용은 ('', 본문)."""
    res, cur, buf, fence = [], "", [], False
    for ln in body.splitlines():
        if ln.startswith("```"): fence = not fence
        if not fence and ln.startswith("## "):
            if (buf and any(x.strip() for x in buf)) or cur: res.append((cur, "\n".join(buf).strip()))
            cur, buf = ln[3:].strip(), []
        else:
            buf.append(ln)
    if cur or any(x.strip() for x in buf): res.append((cur, "\n".join(buf).strip()))
    return [x for x in res if x[0] or x[1]]


def _cells(ln):
    s = ln.strip()
    if s.startswith("|"): s = s[1:]
    if s.endswith("|"): s = s[:-1]
    return [c.strip().replace("<br>", "\n") for c in re.split(r"(?<!\\)\|", s)]


def _dw(s):
    """표시 폭 — 한글·CJK 전각 문자는 2, 그 외 1."""
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in s)


def _widths(hdr, rows, total=17.4):
    n = len(hdr)
    lens = [max([_dw(hdr[i])] + [_dw(r[i]) if i < len(r) else 0 for r in rows]) for i in range(n)]
    lens = [min(max(l, 7), 70) for l in lens]
    s = sum(lens)
    return [round(total * l / s, 2) for l in lens]


def render(r, text, size=9.2, sub_level=None, code_max=40):
    """본문 렌더. sub_level 지정 시 '#' 줄을 해당 레벨 제목으로, 아니면 굵은 문단으로."""
    lines = text.splitlines()
    i, n = 0, len(lines)
    para = []

    def flush():
        if para:
            r.P(" ".join(x.strip() for x in para), size=size)
            para.clear()

    while i < n:
        ln = lines[i]
        s = ln.strip()
        if s.startswith("```"):
            flush()
            code = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i].rstrip()); i += 1
            i += 1
            while code and not code[-1].strip(): code.pop()
            if code: r.CODE("\n".join(code[:code_max]) + ("\n..." if len(code) > code_max else ""), font=7.6)
            continue
        if s.startswith("|") and i + 1 < n and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]):
            flush()
            hdr = _cells(s); rows = []
            i += 2
            while i < n and lines[i].strip().startswith("|"):
                c = _cells(lines[i])
                rows.append((c + [""] * len(hdr))[:len(hdr)]); i += 1
            r.T(hdr, rows, widths=_widths(hdr, rows), font=7.4 if len(hdr) >= 5 else 7.8)
            continue
        if s.startswith("#"):
            flush()
            t = s.lstrip("#").strip()
            if sub_level: r.H(t, sub_level)
            else: r.P(t, bold=True, size=size + 0.6, sa=2)
            i += 1; continue
        m = re.match(r"^(\s*)[-*]\s+(.*)$", ln)
        if m:
            flush()
            r.B(m.group(2).strip(), level=min(len(m.group(1)) // 2, 2))
            i += 1; continue
        m = re.match(r"^(\s*)(\d+)[.)]\s+(.*)$", ln)
        if m:
            flush()
            from docx.shared import Cm
            p = r.P(f"{m.group(2)}. {m.group(3).strip()}", size=size, sa=2)
            p.paragraph_format.left_indent = Cm(0.9 + 0.5 * min(len(m.group(1)) // 2, 2))
            p.paragraph_format.first_line_indent = Cm(-0.6)
            i += 1; continue
        if not s or s == "---":
            flush(); i += 1; continue
        para.append(s)
        i += 1
    flush()


def repos(all_blocks, key="REPOS"):
    """'# REPOS' 블록(또는 '## REPOS' 절)의 owner/repo 목록(중복 제거, 순서 유지)."""
    names = []
    for (tag, k), (_, body) in all_blocks.items():
        if k != key: continue
        for ln in body.splitlines():
            m = re.match(r"^\s*-\s*`?([A-Za-z0-9][\w.-]*/[\w.-]+)`?", ln)
            if m and m.group(1).rstrip(".") not in names: names.append(m.group(1).rstrip("."))
    return names
