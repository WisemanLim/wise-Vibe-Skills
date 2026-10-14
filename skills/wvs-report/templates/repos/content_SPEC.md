# 콘텐츠 작성 규격 (Summary-Repos, {INFOGRAPHIC})  — `<Project>/_assets/content/SPEC.md`

루트: {ABS_PROJECT_DIR}
- 클론: `<NN-Category>/<Tool>/` (git clone --depth 1, {DATE})
- 매핑: `_assets/research/map.tsv` (분류, 도구, owner/repo)
- 실측: `_assets/research/repos.tsv` (gh_probe — full_name·stars·license·archived·pushed·release …), `_assets/research/packages.tsv` (레지스트리 최신 버전·요구)
- 트리: `_assets/trees.json` (키 "NN-Category/Tool")
- 원본 이미지: `_assets/infographic.png` (Read 로 확인 가능)

담당: **{이 에이전트의 키 목록}** → 출력 `_assets/content/part_<X>.py` — 순수 파이썬 모듈, import 없음, 아래 두 dict 만 정의.

```python
C = {}   # 키 = "NN-Category/Tool" (map.tsv 1·2열을 / 로 결합)
C["02-Data-Preprocessing-Management/Polars"] = dict(
 label="Polars",                      # 인포그래픽 표기명
 pkg="polars",                        # 설치 패키지명(pip/npm/cargo/brew …, 여러 개면 쉼표)
 py=">=3.10",                         # 매니페스트에서 확인한 런타임 요구(Python/Node/Rust 버전 등)
 core="Rust 코어 + PyO3 바인딩",        # 구현 언어/구조 한 줄
 ov="개요 3~5문장 …",                  # 무엇인가·핵심 개념·아키텍처·최신 버전 특징
 dirs=[("crates/", "Rust 코어 크레이트 …"), ("py-polars/", "Python 패키지 …")],  # 주요 디렉토리 4~7개와 역할(트리에 실제 있는 경로만)
 use="설치·사용 — 마크다운. 코드는 ```bash / ```python 펜스. 설치 1블록 + 최소 예제 1~2블록(10~25줄)",
 app="활용분야/범위 3~5문장 — 어느 단계에서, 어떤 규모/데이터에, 대표 사용처",
 alt="같은 분류 내/외 대안과 선택 기준 1~2문장",
 note="유의사항 2~4문장 — 라이선스 특이점, 저장소 이전·아카이브·유지보수 상태, 호환성·파괴적 변경, 보안",
)
CAT = {}  # 분류 키 = "NN-Category" (담당 분류 전부)
CAT["02-Data-Preprocessing-Management"] = dict(
 title="Data Preprocessing & Management",  # 인포그래픽 표기 그대로
 ko="데이터 전처리·관리",
 intro="분류 개요 3~4문장(흐름 상 위치, 도구들 관계)",
 cmp=[["도구", "핵심 모델", "규모", "강점", "약점"], ["Polars", "…", "…", "…", "…"]],  # 첫 행=헤더, 5열 고정, 도구별 1행
 guide=["상황 → 선택 도구 (이유)", "…"],   # 선택 가이드 3~5개
 check=[["항목", "인포그래픽 표기/암시", "실측({DATE})", "판정"], ["…", "…", "…", "일치"]],  # 판정 ∈ {일치, 변경, 부정확, 주의}
)
```

## 작성 원칙
1. 한국어. 기술 용어·API 명은 원문. 문장체(~다). 과장·홍보 문구 금지.
2. **반드시 클론된 저장소의 README·매니페스트(pyproject.toml/setup.py/package.json/Cargo.toml/go.mod)·docs·소스를 직접 읽고** 쓴다.
   기억에 의존하지 말 것 — 버전·소유 조직·API 가 자주 바뀐다. 최신 버전·날짜는 repos.tsv / packages.tsv 값을 쓴다.
3. `use` 코드는 현재 API 기준으로 정확해야 한다(README Quickstart·docs 예제 참고). 순수 패키지 1~2개는
   `uv run --no-project --with <pkg> python -c ...` 로 실제 실행해 검증해도 좋다(대형 패키지는 생략).
4. 문자열 안 `**굵게**` 사용 가능. 백틱 코드 스팬 안에 `**` 금지. 파이썬 문자열 따옴표·이스케이프 주의(파일이 import 가능해야 함).
5. `dirs` 경로는 trees.json/실제 디렉토리에 존재하는 것만.
6. 조직·플랫폼·비공개 SDK 를 대표 저장소로 대체한 경우 `note` 에 사유를 쓴다.
7. 저장소 2~3개 끝낼 때마다 파일을 저장한다(중단 시 소실 방지).
8. 완료 후 `python3 -c "import runpy;d=runpy.run_path('_assets/content/part_<X>.py');print(len(d['C']),len(d['CAT']))"` 로 import 검증.
9. 형식 참고용 이전 보고서(다른 프로젝트의 Summary-Repos.docx 등)는 출처로 쓰지 않는다.
10. 최종 응답: 작성한 키 목록 + 특이 발견사항(이전·아카이브·라이선스·파괴적 변경) 5~10줄 요약만.
