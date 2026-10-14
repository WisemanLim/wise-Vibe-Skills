#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRD 입력 수집·정규화 (wvs-report prd) — 여러 종류의 입력을 분류해 보존하고, 요구사항 문서에서 요구 항목(RQ)을 뽑는다.

입력 종류(자동 분류, 강제 지정 옵션 우선):
  report  분석 보고서 .docx/.pdf (+ 같은 이름 `<stem>_assets/` → research/·measured.json·source_infographic.png 재사용)
  req     요구사항·개발방향 문서 .md/.markdown/.txt/.rst (+ --req 로 지정한 .docx/.pdf, 파일명에 requirement·요구·prd·spec·기획·direction)
  image   첨부 이미지 .png/.jpg/.jpeg/.webp/.gif/.bmp/.svg (인포그래픽·도식·UI 시안·화면 캡처) 및 이미지 URL
  github  GitHub 저장소 URL (github.com/owner/repo/…)
  site    그 밖의 참고 사이트 URL
  prompt  --prompt 로 넘긴 요청문 텍스트(번호 항목이 RQ 로 추출됨)
디렉토리를 주면 보고서 _assets 폴더인지 판별하고, 아니면 안의 문서·이미지를 펼친다(깊이 2).

산출(<assets>/):
  inputs/IN-NN.*            원본 사본(이미지·문서), 사이트 텍스트 발췌(IN-NN.txt — 분석용, 보고서에 싣지 않음)
  research/inputs.json      입력 인벤토리(id·type·src·title·saved·status·github·note)
  research/_INPUTS.md       인벤토리 표 + 입력별 전사/요약 자리(에이전트가 채움)
  research/req_items.tsv    RQ 후보: id · input · line · section · type(fr|nfr|ui|constraint|goal|non-goal|info) · priority · text
                            (휴리스틱 추출 — 에이전트가 검토해 병합·분할·유형 수정)

사용: prd_intake.py <입력…> --assets <dir> [--req F]… [--report F]… [--image F]… [--url U]… [--links urls.txt] [--prompt "텍스트"] [--no-fetch]
"""
import argparse, datetime, html, json, os, re, shutil, subprocess, sys, urllib.request

IMG = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"}
TXT = {".md", ".markdown", ".txt", ".rst"}
DOC = {".docx", ".pdf"}
REQ_NAME = re.compile(r"(requirement|require|요구|prd|spec|기획|direction|방향|brief|backlog)", re.I)
TODAY = os.environ.get("WVS_DOC_DATE") or datetime.date.today().isoformat()

# ---------------------------------------------------------------- 분류
def classify(item, forced=None):
    if forced: return forced
    if re.match(r"^https?://", item, re.I):
        u = item.split("?")[0].split("#")[0]
        if os.path.splitext(u)[1].lower() in IMG: return "image"
        if re.match(r"^https?://(www\.)?github\.com/[\w.-]+/[\w.-]+", u, re.I): return "github"
        return "site"
    ext = os.path.splitext(item)[1].lower()
    if ext in IMG: return "image"
    if ext in TXT: return "req"
    if ext in DOC: return "req" if REQ_NAME.search(os.path.basename(item)) and not os.path.isdir(os.path.splitext(item)[0] + "_assets") else "report"
    return "unknown"


def expand(item):
    """디렉토리 → 보고서 _assets 이면 그대로, 아니면 안의 문서·이미지 목록."""
    if not os.path.isdir(item): return [(item, None)]
    if os.path.isdir(os.path.join(item, "research")) or os.path.exists(os.path.join(item, "measured.json")):
        return [(item, "report-assets")]
    out = []
    for root, dirs, files in os.walk(item):
        if root[len(item):].count(os.sep) >= 2: dirs[:] = []
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in sorted(files):
            if os.path.splitext(f)[1].lower() in IMG | TXT | DOC: out.append((os.path.join(root, f), None))
    return out


# ---------------------------------------------------------------- 보존·추출
def fetch_site(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (wvs-report prd intake)"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(2_000_000).decode(r.headers.get_content_charset() or "utf-8", "replace")
            status = r.status
    except Exception as e:  # 네트워크·403 등 — 에이전트가 브라우저/WebFetch 로 재시도
        return {"status": f"ERR {type(e).__name__}: {str(e)[:80]}"}, ""
    title = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S | re.I)
    desc = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', raw, re.S | re.I)
    body = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", raw)
    body = html.unescape(re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", " ", body))).strip()
    meta = {"status": str(status), "title": html.unescape(" ".join(title.group(1).split()))[:200] if title else "",
            "description": html.unescape(" ".join(desc.group(1).split()))[:300] if desc else ""}
    return meta, body[:20000]


def doc_to_text(path, out_md):
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".docx" and shutil.which("pandoc"):
            subprocess.run(["pandoc", path, "-t", "gfm", "-o", out_md], check=True, capture_output=True)
        elif ext == ".pdf" and shutil.which("pdftotext"):
            subprocess.run(["pdftotext", "-layout", path, out_md], check=True, capture_output=True)
        else:
            return None
        return out_md
    except subprocess.CalledProcessError:
        return None


# ---------------------------------------------------------------- RQ 추출(휴리스틱)
MODAL = re.compile(r"(must|shall|should|required|requires|need to|needs to|have to|has to|해야|하여야|되어야|필요|필수|반드시|지원|가능해야|할 수 있어야|제공|구현|포함)", re.I)
H_NONGOAL = re.compile(r"(non[- ]?goals?|out of scope|제외|범위 밖|하지 않|not in scope)", re.I)
H_GOAL = re.compile(r"(goals?|vision|objective|목표|비전|방향|direction|배경|background|overview|개요|summary|요약|motivation|why)", re.I)
H_NFR = re.compile(r"(non[- ]?functional|nfr|비기능|성능|performance|가용성|availability|보안|security|확장성|scalab|latency|지연|sla|접근성|accessib|i18n|국제화|호환|compatib|reliab|신뢰|운영|observab|관측|privacy|개인정보|규제|compliance|백업|backup)", re.I)
H_CONS = re.compile(r"(constraint|제약|기술 ?스택|tech ?stack|stack|언어|language|framework|프레임워크|라이선스|license|플랫폼|platform|infra|인프라)", re.I)
H_UI = re.compile(r"(\bui\b|\bux\b|화면|screen|layout|레이아웃|디자인|design|wireframe|와이어프레임|페이지|page|대시보드|dashboard)", re.I)
H_INFO = re.compile(r"(reference|참고|links?|링크|appendix|부록|glossary|용어|changelog|history|이력|문서 정보)", re.I)


def rq_type(heads, text):
    """가장 가까운 제목(nearest)과 그 상위(parent), 본문으로 유형 판정."""
    near = heads[-1] if heads else ""; par = heads[-2] if len(heads) > 1 else ""
    if H_NONGOAL.search(near) or H_NONGOAL.search(par): return "non-goal"
    if H_INFO.search(near): return "info"
    if H_NFR.search(near) or H_NFR.search(par) or (H_NFR.search(text) and not H_UI.search(near)): return "nfr"
    if H_CONS.search(near): return "constraint"
    if H_UI.search(near) or H_UI.search(text[:40]): return "ui"
    if H_GOAL.search(near): return "goal"
    return "fr"


def rq_priority(text):
    if re.search(r"(\bP0\b|must|shall|필수|반드시|critical|핵심)", text, re.I): return "P0"
    if re.search(r"(\bP2\b|could|may|nice to have|선택|optional|추후|later|향후)", text, re.I): return "P2"
    if re.search(r"(\bP1\b|should|권장|recommended|가능하면)", text, re.I): return "P1"
    return "-"


SEP = re.compile(r"^\|?\s*:?-{2,}")


def extract_rq(md_path, input_id):
    lines = open(md_path, encoding="utf-8", errors="replace").read().splitlines()
    rows, heads, fence = [], [], False
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("```") or s.startswith("~~~"):
            fence = not fence; continue
        if fence or not s: continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            lvl = len(m.group(1)); heads = heads[:lvl - 1] + [m.group(2).strip("# ").strip()]; continue
        text = None
        m = re.match(r"^(?:[-*+]|\d+[.)]|[a-zA-Z][.)]|\[[ xX]\])\s+(.*)$", s)
        if m:
            text = re.sub(r"^\[[ xX]\]\s+", "", m.group(1))
        elif s.startswith("|"):
            if SEP.match(s) or (i + 1 < len(lines) and SEP.match(lines[i + 1].strip())):
                continue                                  # 구분선 · 머리행
            text = " / ".join(c.strip() for c in s.strip("|").split("|") if c.strip())
        elif MODAL.search(s) and len(s) < 400:
            text = s
        if not text or len(text) < 4: continue
        text = re.sub(r"\s+", " ", text.replace("\t", " ")).strip()
        rows.append([input_id, str(i + 1), " › ".join(heads) or "(문서 앞부분)", rq_type(heads, text), rq_priority(text), text])
    return rows


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="*")
    ap.add_argument("--assets", required=True)
    for k in ("req", "report", "image", "url"):
        ap.add_argument(f"--{k}", action="append", default=[])
    ap.add_argument("--links", help="한 줄에 URL 하나인 파일")
    ap.add_argument("--prompt", help="요청문(번호 항목 → RQ)")
    ap.add_argument("--no-fetch", action="store_true", help="사이트 접속 생략(오프라인)")
    a = ap.parse_args()

    A = os.path.abspath(a.assets); INP = os.path.join(A, "inputs"); RES = os.path.join(A, "research")
    os.makedirs(INP, exist_ok=True); os.makedirs(RES, exist_ok=True)
    queue = []
    for it in a.inputs: queue += [(p, f) for p, f in expand(it)]
    for k in ("req", "report", "image"): queue += [(p, k) for p in getattr(a, k)]
    queue += [(u, None) for u in a.url]
    if a.links:
        queue += [(ln.strip(), None) for ln in open(a.links, encoding="utf-8") if re.match(r"^https?://", ln.strip())]
    if a.prompt:
        p = os.path.join(INP, "_prompt.md"); open(p, "w", encoding="utf-8").write("# 사용자 요청문\n\n" + a.prompt.strip() + "\n")
        queue.append((p, "prompt"))

    items, rq = [], []
    for n, (src, forced) in enumerate(queue, 1):
        iid = f"IN-{n:02d}"
        is_url = bool(re.match(r"^https?://", src, re.I))
        t = "report" if forced == "report-assets" else classify(src, forced)
        it = {"id": iid, "type": t, "src": src if is_url else os.path.abspath(src), "title": "", "saved": "", "status": "", "note": "", "accessed": TODAY}
        if not is_url and not os.path.exists(src):
            it.update(type="missing", status="ERR not found"); items.append(it); continue
        base = os.path.basename(src.rstrip("/").split("?")[0]) or iid
        if t == "image":
            ext = os.path.splitext(base)[1].lower() or ".png"
            dst = os.path.join(INP, iid + ext)
            if is_url:
                try:
                    urllib.request.urlretrieve(src, dst); it["status"] = "downloaded"
                except Exception as e:
                    it["status"] = f"ERR {type(e).__name__}"; dst = ""
            else:
                shutil.copy2(src, dst)
            it.update(saved=os.path.relpath(dst, A) if dst else "", title=base, note="이미지 — 인포그래픽/도식/UI 시안/캡처 여부를 _INPUTS.md 에 기록")
        elif t == "github":
            m = re.match(r"^https?://(?:www\.)?github\.com/([\w.-]+)/([\w.-]+)", src, re.I)
            it.update(github=f"{m.group(1)}/{m.group(2).removesuffix('.git')}", title=f"{m.group(1)}/{m.group(2)}",
                      note="gh_probe.py 로 실측, README 로 기능 요약")
        elif t == "site":
            if a.no_fetch:
                it["status"] = "skipped (--no-fetch)"
            else:
                meta, body = fetch_site(src)
                it.update(status=meta.get("status", ""), title=meta.get("title", ""), description=meta.get("description", ""))
                if body:
                    p = os.path.join(INP, iid + ".txt"); open(p, "w", encoding="utf-8").write(f"URL: {src}\n접근일: {TODAY}\n\n{body}\n")
                    it["saved"] = os.path.relpath(p, A)
            it["note"] = "참고 사이트 — 기능·정보 구조·UI 패턴·가격/라이선스만 참고(문구·이미지 복제 금지). 접속 실패 시 WebFetch/브라우저로 재확인"
        elif t in ("req", "prompt"):
            ext = os.path.splitext(src)[1].lower()
            md = src
            if ext in DOC:
                md = doc_to_text(src, os.path.join(INP, iid + ".md"))
                if not md: it.update(status="ERR no converter (pandoc/pdftotext)"); items.append(it); continue
            elif t == "req":
                shutil.copy2(src, os.path.join(INP, iid + (ext or ".md"))); md = os.path.join(INP, iid + (ext or ".md"))
            it.update(saved=os.path.relpath(md, A), title=base if t == "req" else "사용자 요청문")
            first = next((ln.lstrip("# ").strip() for ln in open(md, encoding="utf-8", errors="replace") if ln.startswith("#")), "")
            if first and t == "req": it["title"] = first[:120]
            rq += extract_rq(md, iid)
        elif t == "report":
            p = os.path.abspath(src)
            if os.path.isdir(p):
                it.update(assets=p, title=os.path.basename(p).removesuffix("_assets"))
            else:
                ad = os.path.splitext(p)[0] + "_assets"
                it.update(title=os.path.splitext(base)[0], assets=ad if os.path.isdir(ad) else "")
            ad = it.get("assets") or ""
            for f in ("source_infographic.png", "measured.json"):
                if ad and os.path.exists(os.path.join(ad, f)): it.setdefault("found", []).append(f)
            if ad and os.path.isdir(os.path.join(ad, "research")): it.setdefault("found", []).append("research/")
            it["note"] = "분석 보고서 — 조사 원문·검증 저장소·원본 도식 재사용"
        else:
            it["note"] = "분류 불가 — --req/--report/--image/--url 로 지정"
        items.append(it)

    for i, r in enumerate(rq, 1): r.insert(0, f"RQ-{i:03d}")
    with open(os.path.join(RES, "req_items.tsv"), "w", encoding="utf-8") as f:
        f.write("id\tinput\tline\tsection\ttype\tpriority\ttext\n")
        for r in rq: f.write("\t".join(r) + "\n")
    json.dump(items, open(os.path.join(RES, "inputs.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    md = [f"# 입력 인벤토리 (`research/_INPUTS.md`, {TODAY})", "",
          "| ID | 유형 | 제목 | 위치 | 상태 | 비고 |", "|---|---|---|---|---|---|"]
    disp = lambda it: it["src"] if re.match(r"^https?://", it["src"]) else os.path.basename(it["src"].rstrip("/"))   # 로컬 절대경로는 문서에 싣지 않음
    for it in items:
        md.append(f"| {it['id']} | {it['type']} | {it.get('title', '')} | {disp(it)} | {it.get('status') or 'ok'} | {it.get('note', '')} |")
    md += ["", "## 입력별 전사·요약", "<!-- 에이전트가 채운다: 각 IN 블록의 주석을 지우고 사실만 bullet 로. 원문 인용은 짧게, 출처·접근일 유지. 비어 있으면 PRD 빌드 게이트 실패 -->", ""]
    for it in items:
        guide = {"image": "도식이면 레이어·카드·흐름·타일·문구를 원문 그대로 / UI 시안이면 화면·영역·컴포넌트·상태 / 기타 이미지는 담긴 정보",
                 "site": "제품·서비스가 제공하는 기능 목록 · 정보 구조(메뉴) · UI 패턴 · 가격/라이선스 · 차별점 — PRD 에 준용할 것과 준용하지 않을 것",
                 "github": "저장소 목적 · 주요 기능 · 라이선스(SPDX) · 활성도 · PRD 에서의 역할(E/A/L/R/X)",
                 "req": "문서의 목표·범위·요구 목록 요약 — 세부 항목은 req_items.tsv(RQ)로 관리",
                 "prompt": "요청문의 번호 항목 → RQ", "report": "보고서 장 구성 · 요약 · 도식 판정 · 도출 스택"}.get(it["type"], "")
        md += [f"### {it['id']} {it.get('title', '')}", f"- 유형: {it['type']} · 위치: {disp(it)} · 접근일: {it['accessed']}", f"<!-- 채울 내용: {guide} -->", ""]
    md += ["## 입력 간 충돌·결정", "", "| # | 충돌 내용 | 관련 입력 | 결정 | 근거 |", "|---|---|---|---|---|", ""]
    open(os.path.join(RES, "_INPUTS.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")

    cnt = {}
    for it in items: cnt[it["type"]] = cnt.get(it["type"], 0) + 1
    tcnt = {}
    for r in rq: tcnt[r[4]] = tcnt.get(r[4], 0) + 1
    print("inputs:", " · ".join(f"{k} {v}" for k, v in cnt.items()) or "0", "→", os.path.join(RES, "inputs.json"))
    print("RQ candidates:", len(rq), "(" + " · ".join(f"{k} {v}" for k, v in tcnt.items()) + ")" if rq else "", "→", os.path.join(RES, "req_items.tsv"))
    bad = [it["id"] + " " + it["status"] for it in items if str(it.get("status", "")).startswith("ERR") or it["type"] in ("unknown", "missing")]
    if bad: print("CHECK:", "; ".join(bad), file=sys.stderr)


if __name__ == "__main__":
    main()
