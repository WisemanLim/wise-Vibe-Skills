#!/usr/bin/env python3
"""wvs-report check_research.py smoke: 얕은 조사(요약 _SPEC·한 줄 소제목·출처 부족·sample 없음) → FAIL,
충실한 조사(템플릿 전체·사전 웹 확인·필수 소제목·코드·판정 표·출처) → PASS, --unit 단위 검사, final 의 sample/measured 검사."""
import json, os, subprocess, sys, tempfile
sys.dont_write_bytecode = True

KIT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills", "wvs-report", "scripts"))
T = tempfile.mkdtemp(prefix="wvs-research-")
B_SUBS = ["정의와 계보", "구성방식", "동작방식", "구현", "보안·운영 리스크", "사용 및 활용용도", "확장방안", "도식 판정"]


def gate(A, *a):
    return subprocess.run([sys.executable, os.path.join(KIT, "check_research.py"), "--assets", A, *a], capture_output=True, text=True)


def spec(rich):
    if not rich:
        return "# 리서치 공통 사양 — X\n요약 한 줄. 유형 B.\n판정: 부분일치.\n"
    s = ["# 리서치 공통 사양 — \"X\"", "원본 설명 줄."] + [f"설명 {i}" for i in range(20)]
    s += ["## 도식 전사"] + [f"- **항목{i}** — 카드 문구 {i}" for i in range(8)]
    s += ["## 사전 웹 확인", "| 확인 질문 | 출처 | URL | 결과 |", "|---|---|---|---|"]
    s += [f"| q{i} | 공식 문서 {i} | https://docs.example.com/p{i} | 확인 |" for i in range(3)]
    s += ["## 도식 판정 후보"] + [f"- 후보 {i}" for i in range(4)]
    s += ["## 각 항목 블록의 필수 소제목"] + [f"{i + 1}. `### {x}`" for i, x in enumerate(B_SUBS)]
    s += ["## 조사 단위", "| 파일 | 담당 | 블록 KEY |", "|---|---|---|",
          "| r1_a.md | 범주 1 | STEP_A · CMP_A |", "| r2_gap.md | 누락 | GAP_X |", "| r3_value.md | 통합 | VAL_USE |"]
    s += ["## 품질 규칙"] + [f"- 규칙 {i}" for i in range(6)] + ["## 파일 형식", "형식 설명"]
    return "\n".join(s) + "\n"


def item(key, rich):
    out = [f"# {key} 항목 {key}"]
    for x in B_SUBS:
        out.append(f"### {x}")
        if not rich:
            out.append("한 줄."); continue
        if x == "도식 판정":
            out += ["| 항목 | 판정 | 근거 |", "|---|---|---|"] + [f"| h{i} | 일치 | 공식 문서 {i} |" for i in range(4)]
        elif x == "구현":
            out += ["```bash", "aws example --flag 1"] + [f"aws example step{i}" for i in range(8)] + ["```"] + [f"- 옵션 {i}" for i in range(6)]
        else:
            out += [f"{x} 근거 {i}." for i in range(8)]
    return "\n".join(out) + "\n"


def other(key, rich):
    if not rich:
        return f"# {key} 기타\n### 요지\n한 줄.\n"
    return f"# {key} 기타\n" + "".join(f"### 관점 {j}\n" + "".join(f"- 내용 {j}.{i}\n" for i in range(12)) for j in range(3))


def refs(n):
    return "# PAPERS 참고문헌\n" + "".join(f"- STD | 공식 문서 {i} | 발행 | 2026 | https://docs.example.com/{i}\n" for i in range(n)) + "# REPOS 저장소\n- owner/repo\n"


def make(name, rich, sample):
    A = os.path.join(T, name); R = os.path.join(A, "research"); os.makedirs(R)
    open(os.path.join(R, "_SPEC.md"), "w", encoding="utf-8").write(spec(rich))
    files = {"r1_a.md": item("STEP_A", rich) + other("CMP_A", rich) + refs(6 if rich else 2),
             "r2_gap.md": other("GAP_X", rich) + refs(5 if rich else 1), "r3_value.md": other("VAL_USE", rich) + refs(5 if rich else 1)}
    for f, t in files.items():
        open(os.path.join(R, f), "w", encoding="utf-8").write(t)
    json.dump({"repos": [{}] * 5, "missing": [], "papers": {}, "bad_papers": []}, open(os.path.join(A, "measured.json"), "w"))
    for i in range(3):
        open(os.path.join(A, f"fig_{i}.png"), "wb").write(b"x")
    if sample:
        os.makedirs(os.path.join(A, "sample", "out"))
        open(os.path.join(A, "sample", "lab.py"), "w").write("print(1)\n")
        open(os.path.join(A, "sample", "out", "run.log"), "w").write("1\n")
    return A


shallow = make("shallow", False, False)
p = gate(shallow, "--stage", "final")
assert p.returncode == 1 and "_SPEC.md" in p.stdout and "사전 웹 확인" in p.stdout and "1줄" in p.stdout and "sample/" in p.stdout, p.stdout

rich = make("rich", True, True)
for st in ("spec", "research", "final"):
    p = gate(rich, "--stage", st)
    assert p.returncode == 0, (st, p.stdout)
p = gate(rich, "--unit", "r1_a.md")
assert p.returncode == 0, p.stdout

nosample = make("nosample", True, False)
assert gate(nosample, "--stage", "final").returncode == 1
assert gate(nosample, "--stage", "final", "--no-sample").returncode == 0

os.remove(os.path.join(rich, "research", "r2_gap.md"))
p = gate(rich)
assert p.returncode == 1 and "r2_gap.md: 파일 없음" in p.stdout, p.stdout
print("smoke dir:", T)
