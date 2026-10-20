# mode `repos` — 오픈소스(GitHub) 클론·분석 요약 보고서 (구 oss-clone-analysis, 요청 유형 --1)


> 인수 규칙·경로 변수(`SKILL_DIR`·`KIT`)는 `wvs-report` SKILL.md 를 따른다. `KIT` = `SKILL_DIR/scripts`.

## 요청 원형과 자동화 규칙
> 첨부이미지를 참고하여, **{Python-Tools-for-AI-Projects}** 프로젝트에 **{각 분류 Model & Data Security, Data Visualization 등의 세부 프로젝트}** 들을 clone 하고
> 각각 디렉토리 구조를 포함하여, 사용방법 및 활용분야/범위 등에 대해서 요약 보고서를 작성. 요약보고서는 해당 프로젝트의 Summary-Repos.docx.
> 문서 템플릿은 이전 Summary-Repos.docx 를 참고하고, 완료 후 pdf 로 변환.

- `{ }` = **첨부에서 자동 추출**: 프로젝트명(인포그래픽 대제목 → `Title-Case-Hyphen` 디렉토리명), 분류 목록(표기 순서대로 `NN-Category`), 분류별 도구명·로고·주소, 원저작자.
  사용자가 값을 주면 그 값이 우선(예: `--project`, `--categories "Model & Data Security, Data Visualization"` → 해당 분류만, 번호는 원래 NN 유지).
- `[ ]` = **첨부에서 도출하는 세부 분석**: 도구별 저장소 매핑·선정 사유, 분류 내 비교·선택 가이드, 흐름(수명주기) 단계 재배치, 인포그래픽 표기 검증(일치/변경/부정확/주의).

## 인수
| 인수 | 기본값 | 의미 |
|---|---|---|
| 위치 인수 | (대화의 첨부) | 이미지 경로·URL(이미지/게시물/README) — 여러 개 가능 |
| `--root <dir>` | 현재 작업 디렉토리 | 작업 루트(예: wise-Analysis-Repos). 프로젝트는 `<root>/<Project>/` |
| `--project <name>` | {첨부 대제목에서 자동} | 프로젝트(클론 루트) 디렉토리명 |
| `--categories "<a, b>"` | 전체 | 일부 분류만(표기명 또는 NN) |
| `--template <docx>` | `<root>/*/Summary-Repos.docx` 중 최신 | 형식 참고 문서(출처에 넣지 않음) |
| `--parallel <N>` | 6 | 클론 병렬 수 |
| `--no-pdf` | false | PDF 변환 생략 |
| `--plan-only` | false | 1~2단계(전사·매핑표)만 만들고 멈춤 |

## 산출물
```
<root>/<Project>/
├── NN-Category/Tool/          ← shallow clone (git clone --depth 1 --single-branch)
├── Summary-Repos.docx / .pdf
└── _assets/                   ← 재현 자산(출처·실측·빌드 스크립트)
    ├── infographic.png        ← 원본 첨부(링크면 이미지 저장 또는 페이지 캡처)
    ├── research/ _SPEC.md map.tsv repos.tsv pkg_map.tsv packages.tsv sizes.tsv
    ├── content/  SPEC.md extra.py part_A.py …   ← 조사 에이전트 산출
    ├── trees.json  fig_*.png  sr_data.py  figs.py  build_summary.py  .venv/
```

## 절차 (순서대로, 단계마다 성공 기준 확인)
경로: `SKILL_DIR` = wvs-report 스킬 디렉토리, `KIT` = `SKILL_DIR/scripts`.

### 1. 입력 확보와 전사 ({ } 자동 추출)
1. 첨부 이미지를 `_assets/infographic.png` 로 저장(URL 이면 이미지 직접 다운로드, 게시물이면 이미지 URL 추출, 실패 시 사용자에게 이미지 파일 요청).
2. 이미지를 직접 보고 `_assets/research/_SPEC.md` 에 전사: 대제목·부제·작성자/출처 표기·레이아웃 설명, **분류(표기 순서, 색) → 도구(표기명, 로고만 있으면 로고로 판독, 주소가 있으면 그대로)**, 푸터 문구.
3. 프로젝트명·분류 번호(`01-…` 두 자리)·도구 디렉토리명(공백·특수문자 → `-`)을 확정. 판독이 애매한 항목은 `[판독 불확실]` 로 두고 4단계에서 확인.
✅ 분류 수·도구 수가 이미지와 일치. 사용자에게 한 줄 요약(분류 K · 도구 N · 프로젝트명)을 알리고 계속(`--plan-only` 면 여기서 매핑표까지 만들고 정지).

### 2. 저장소 매핑 (`map.tsv`)
- 규칙: ① 도구의 **공식 저장소(조직 계정)** ② 이전된 경우 **현재 소유 저장소**(gh 리다이렉트로 확인) ③ 조직명만 표기·비공개 SDK·플랫폼 우산 항목은 **대표 저장소로 대체하고 사유 기록**.
- 찾기: `gh search repos "<tool>" --sort stars -L 5`, 공식 사이트·PyPI/npm 메타의 Source URL, WebSearch.
- `_assets/research/map.tsv` = `NN-Category<TAB>Tool<TAB>owner/repo`(인포그래픽 순서), `pkg_map.tsv` = `Tool<TAB>pypi|npm|crates|none<TAB>패키지명`.

### 3. 실측·클론·트리
```bash
cd <root>/<Project>
bash $KIT/setup_env.sh _assets                                  # venv
python3 $KIT/gh_probe.py _assets/research/map.tsv --col 3 -o _assets/research/repos.tsv   # ERR 0, MOVED 확인
python3 $KIT/pkg_probe.py _assets/research/pkg_map.tsv -o _assets/research/packages.tsv
WVS_ASSETS=_assets bash $KIT/clone_repos.sh _assets/research/map.tsv . ${PARALLEL:-6}     # FAIL 0 (실패 시 저장소 재확인)
python3 $KIT/make_trees.py _assets/research/map.tsv . -o _assets/trees.json
```
✅ 모든 도구 클론 성공, repos.tsv ERR 0. 대용량(>1GB)은 사용자에게 알리고 진행.

### 4. 콘텐츠 조사 (병렬 서브에이전트)
1. `SKILL_DIR/templates/repos/content_SPEC.md` 를 `_assets/content/SPEC.md` 로 채워 쓴다({ } 치환: 경로·날짜·인포그래픽명).
2. 도구를 4개 내외 그룹(그룹당 8~10개, 분류 단위로 묶음)으로 나눠 **서브에이전트를 병렬 실행**(Agent/Task 도구가 없으면 순차). 각 에이전트: SPEC.md 를 먼저 읽고, **클론된 저장소의 README·매니페스트·docs·소스를 직접 읽어** `content/part_<X>.py`(C·CAT dict) 작성, 2~3개마다 저장, import 검증.
3. 반환 요약에서 이전·아카이브·라이선스·파괴적 변경을 모아 `content/extra.py` 의 `FINDINGS`·`ADOPTION_NOTES` 에 반영.
✅ `C` 키 = map.tsv 전 도구, `CAT` 키 = 전 분류. dirs 경로가 trees.json 에 실재.

### 5. 보고서 고유 값 (`content/extra.py`)
`SKILL_DIR/templates/repos/extra.py` 를 복사해 채운다: TITLE·SUBTITLE·INFOGRAPHIC·AUTHOR·SOURCE_URL·INFOGRAPHIC_DESC, 흐름 지도(`FLOW_TITLE`·`STAGES`·`CROSS` — 분류를 업무 흐름 단계와 횡단 영역으로 재배치),
DISPLAY(디렉토리명 → 표기명), SELECTION_RULES, COMMON(실측 수치와 일치), FINDINGS, ADOPTION_NOTES(버전 하한·상한 교집합, 네이티브 의존, 보안 기본값), SCENARIOS(과제 유형별 최소 스택).

### 6. 그림·빌드·PDF
```bash
cp $SKILL_DIR/templates/repos/{sr_data.py,figs.py,build_summary.py} _assets/
WVS_KIT=$KIT _assets/.venv/bin/python _assets/figs.py            # fig_stars · fig_lifecycle · fig_activity
WVS_KIT=$KIT _assets/.venv/bin/python _assets/build_summary.py --pdf
```
장 구성(이전 Summary-Repos 와 동일): 표지 → 목차 → 1 개요 및 분석 방법(선정·검증·클론 결과·공통 특징·원본 인포그래픽) → 2 종합 비교표(+스타·유지보수 그림) →
3 흐름 지도 → 4.. 분류별(개요·도구 비교·선택 가이드 + 도구별 개요/기본 정보/**디렉토리 구조**/**설치 및 사용방법**/**활용분야·범위**/대안/유의사항) →
인포그래픽 검증 → 라이선스 및 도입 시 유의사항 → 조합 시나리오 → 부록(클론 목록·출처·재현 절차).

### 7. 검증 (완료 선언 전 필수)
```bash
_assets/.venv/bin/python $KIT/check_report.py Summary-Repos.docx --pdf Summary-Repos.pdf --render /tmp/sr_pages \
  --forbid "<템플릿 문서 경로/이름>" --min-h1 6
```
✅ PASS, 빈 쪽 0. 렌더된 쪽을 열어 표 넘침·그림 겹침 확인 후 수정·재빌드. 
### 8. 자산 정리 (`--keep-assets` 면 생략)
7단계 PASS 후 `python3 $KIT/prune_assets.py <Project>/_assets`(`--dry-run` 먼저) — `_assets/` 의 venv·그림·캐시만 정리한다. 분류별 clone(`NN-Category/Tool/`)은 산출물이므로 지우지 않는다.

최종 보고: 경로(docx·pdf)·분류/도구 수·클론 용량·이전/아카이브/라이선스 특이사항 5줄 + 자산 정리 결과.

## 규칙
- 서술은 클론한 실제 파일 근거. 기억 의존 금지(버전·소유 조직·API 는 자주 바뀜). 실측값은 repos.tsv·packages.tsv 를 쓴다.
- 출처: 인포그래픽(원저작자, 첨부 이미지 분석 목적 인용) · GitHub REST API · 레지스트리 API · 각 저장소 README/매니페스트. **형식 참고용 이전 Summary-Repos.docx 는 출처에 넣지 않는다.**
- 클론은 shallow 로만. 클론한 저장소의 코드를 실행하지 않는다(설치 예제 검증은 `uv run --no-project --with <pkg>` 격리 환경에서 선택적으로).
- 공통 규칙은 references/kit.md §3.
