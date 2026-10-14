# mode `prd` — 요구사항 기반 PRD 생성(UI 설계 포함) (구 requirement-based-prd, 요청 유형 --3)


> 인수 규칙·경로 변수(`SKILL_DIR`·`KIT`)는 `wvs-report` SKILL.md 를 따른다. `KIT` = `SKILL_DIR/scripts`.

## 요청 원형과 자동화 규칙
> 작성된/요청된 **{Miscellaneous-Data/9AI-Concepts-That-Put-You-Ahead-of-99%-in-2026.docx(pdf 포함)의 분석보고서}** 를 기반으로 요구사항 및 개발방향 등을 도출하고,
> 다음 요구사항을 추가하여 구현하기 위한 기술(소프트웨어) 스택 및 오픈소스 등을 조사하여 PRD 를 작성.
> 1. PRD 는 Need-to-be-organized-into-PRD 이하에 작성. 문서명은 **{'The map behind production AI Systems'}** 를 잘 나타낼 수 있도록 적절히 수정. docx 로 작성하고 pdf 로 변환.
> **[2.** 시스템 개요부터 에이전트(각 레이어의 구성 및 세부 항목, 예: Agentic Loops-Plan, ACT …)를 가능한 수준으로 분할하여 관리 등을 모두 포함하고, 해당 문서의 아키텍처·다이어그램을 최대한 참고하여 UI/UX 를 구성. PRD 에도 UI/UX 구성 예제 포함.
> **3.** 분석 보고서에서 도출된 오픈소스 스택을 모두 참고하고 github.com repo 주소 확인. 'https://github.com/<user>?tab=stars', '?tab=repositories' 목록도 참고.
> **4.** 세부 항목(기능, 컴포넌트)이 누락되지 않도록 상세 분석으로 목표 시스템을 정확히 표현. 각 항목은 이미지 내용에 충실하게, 구현 시 성실히 구현할 수 있는 내용으로.
> **5.** 분석 자료 외 정부 과제 조회 및 참여 가능한 과제 도출 등의 유사 시스템을 상세 조사해 기능을 준용하고, 누락·필수 세부 기능은 3항과 상용/오픈소스를 최대한 참고.
> **6.** 설치용 패키지는 멀티플랫폼, 릴리스 방법 포함. 에이전트는 개별·독립 구동·배포 가능, 에이전트 관리(등록·수정·삭제·배포 등) 매니징(오케스트레이터 포함 Multi-Agent Systems)도 구동·배포 가능.**]**
> \* 출처와 라이선스, 참고 이미지(첨부 이미지 등)를 항상 명시. \*\* 양식(템플릿)은 이전 문서를 참고하되 출처 명시 시 양식 문서는 생략.

- `{ }` = **자동 추출**: 기초 보고서(경로·제목·원본 이미지·조사 원문), 원본 도식의 핵심 문구(→ 제품명·문서명), 레이어·카드 구조.
- `[ ]` = **자동 도출해 PRD 에 반영**: 2~6항 — 단위 에이전트 분해(units.py), FR·화면·스택·유사 시스템·패키징/릴리스. 사용자 요청문에 다른 번호 항목이 있으면 그대로 1.1 대응표·21.2 추적표에 넣는다.

## 인수
| 인수 | 기본값 | 의미 |
|---|---|---|
| 위치 인수 | (필수) | 기초 분석 보고서 경로 또는 이름(`<root>/Miscellaneous-Data/<이름>.docx|pdf` 탐색) |
| `--root <dir>` | 현재 작업 디렉토리 | 작업 루트(예: wise-Analysis-Repos) |
| `--out-dir <rel>` | `Need-to-be-organized-into-PRD` | PRD 출력 폴더 |
| `--name <Brand>` | {핵심 문구에서 자동} | 제품명(파일명 접두) |
| `--github-user <id>` | `WisemanLim` | stars·repositories 교차 대상 |
| `--similar "<도메인>"` | [요청 5항에서 도출] | 유사 시스템 조사 도메인 |
| `--extra "<텍스트|파일>"` | — | 추가 요구사항(번호 항목으로 대응표에 추가) |
| `--ui-pptx <true|false>` | true | 화면설계서 `<Brand>_UI_Design.pptx/.pdf` 함께 생성 |
| `--no-pdf` · `--plan-only` | false | PDF 생략 · 4단계(카탈로그·조사 사양)까지만 |

## 산출물
```
<root>/<out-dir>/<Brand>_<Core-Phrase-Slug>_PRD.docx / .pdf
<root>/<out-dir>/<Brand>_UI_Design.pptx / .pdf            (--ui-pptx)
<root>/<out-dir>/<Brand>_assets/
├── source_infographic.png  research/(_SPEC.md r1~r7_*.md stars_all.tsv user_repos.tsv stars_relevant.tsv repos_catalog.tsv repos.tsv)
├── units.py data.py data_fr.py ui_data.py prd_auto.py kitpath.py collect_repos.py build_prd.py part*.py figs.py fig*.png ui/ui_<S-ID>.png .venv/
<root>/<out-dir>/<Brand>_UI_assets/pptx/ (build_ui.py ui_screens_*.py)  (--ui-pptx)
```

## 절차
`SKILL_DIR` = wvs-report 스킬 디렉토리, `KIT` = `SKILL_DIR/scripts`. 참고 문서: `references/prd-outline.md`(장 구성 정본·품질 게이트), `references/prd-research-spec.md`,
`references/prd-similar-systems.md`(5항), `references/prd-packaging-release.md`(6항), `references/prd-ui-design-doc.md`(화면설계서).

### 1. 기초 자료 읽기 ({ } 자동 추출)
1. 보고서 탐색·변환: `pandoc "<report>.docx" -t gfm -o /tmp/base.md`(pdf 만 있으면 `pdftotext -layout`). 장 구성·요약·도식 판정·도출 스택을 읽는다.
2. 보고서 `_assets/` 가 있으면 `research/r*.md`(개념별 조사 원문)·`measured.json`(검증 저장소)·`source_infographic.png` 를 쓴다. 없으면 보고서 본문·그림에서 추출.
3. 원본 이미지를 직접 보고 **레이어 띠 · 번호 카드 · 카드 속 흐름도/아이콘 타일/불릿 · 하단 띠** 를 원문 그대로 전사한다(이것이 단위 에이전트·UI 정보 구조의 정본).

### 2. 제품명·문서명 ({ })
핵심 문구(예: "The map behind production AI systems")의 의미를 담은 짧은 브랜드 후보 3개 + 근거를 만들고 첫 후보를 기본 채택(`--name` 우선).
`FILE_STEM = <Brand>_<Core-Phrase-Title-Case-Hyphen>_PRD` (예: `ProdAI-Atlas_The-Map-Behind-Production-AI-Systems_PRD`). 1.1 대응표 1행에 선택 근거를 남긴다.

### 3. 단위 에이전트 카탈로그 ([2·4항] — `units.py`)
- `SKILL_DIR/templates/prd/*.py` 를 `<Brand>_assets/` 로 복사. `units.py` 에 **세부 항목 1개 = 마이크로 에이전트 1개**: 각 카드의 흐름 단계·타일·불릿을 전부 단위로(`<DOMAIN>-<ITEM>`), '원본 도식 요소' 열에 원문을 그대로.
- 도식에 없지만 보고서가 '누락'으로 판정한 요소는 `(도식 누락 — 보완)` 단위로 추가. 하단 띠(성숙도 등)도 단위로.
- 플랫폼 PLT-MGR·DEP·TEN·IAM·SEC·PKG·REL·CON(6항), 공통 X-*(5항, 7단계에서 확정).
✅ 도식 전사의 모든 요소가 최소 1개 단위의 '원본 도식 요소'에 등장.

### 4. 사용자 GitHub 목록과 조사 사양 ([3항])
```bash
bash $KIT/setup_env.sh "<Brand>_assets"
python3 $KIT/github_user_lists.py <user> -o "<Brand>_assets/research"     # stars_all.tsv · user_repos.tsv
```
- 단위별 키워드로 stars_all.tsv 를 grep 해 `stars_relevant.tsv`(full_name·stars·license·unit·use_ko·adopt) 선별, user_repos.tsv 에서 재사용 후보 표시.
- `references/prd-research-spec.md` 로 `research/_SPEC.md` 작성(대상 시스템·기초 보고서 경로·단위 카탈로그 표·조사 단위 r1~r7·산출 형식·규칙).
✅ `--plan-only` 면 여기서 정지(units.py·_SPEC.md 경로 보고).

### 5. 병렬 조사 (서브에이전트 6~7개)
레이어·개념 묶음 r1~r5, `r6_platform`(packaging-release.md 기준), `r7_market`(similar-systems.md 기준). 각 에이전트: _SPEC.md → 기초 보고서 조사 원문 → 조사, 절마다 저장.
산출 절: `## 1. 원조 개념 분석` · `## 2. 대체·유사 시스템`(≥12) · `## 3. 기능 매트릭스` · `## 4. FR 후보`(단위당 5~10, `FR-<단위>-NN`, 구현 요지는 라이브러리·API·설정 키 수준) ·
`## 5. 컴포넌트·데이터`(에이전트 명세 표·엔터티·계약 JSON) · `## 6. UI/UX 참고` · `## 7. 동향·리스크` · `## REPOS`(gh api 확인분만, 결합방식 E/A/L/R/X) · `## SOURCES`.

### 6. 저장소 실측과 FR 정본
```bash
cd "<Brand>_assets"
WVS_KIT=$KIT .venv/bin/python collect_repos.py --base "<기초 보고서>_assets/measured.json"   # repos_catalog.tsv → repos.tsv
.venv/bin/python data_fr.py          # 도메인별 FR 수 · orphan · 'units without FR' = [] 이어야 함
```
FR 이 없는 단위·카탈로그 밖 FR·실측 안 된 참고 OSS 는 해당 조사 파일을 고치거나 해당 에이전트에 재요청.

### 7. 유사 시스템·공통 기능 ([5항])
r7 결과로 4장(공통 기능군·유사 시스템 ≥12·기능 매트릭스·비워 둔 기능·필수도 판정)을 쓰고, 필수·권장 기능을 X-* 단위·FR 로 units.py/r7 에 반영.
요청 예시 도메인(예: 정부 과제 조회)이 목표 범주와 다르면 해석을 1.1 대응표에 명시(similar-systems.md §1).

### 8. UI/UX ([2항]) — 화면 목록·와이어프레임
- `ui_data.py`: GROUPS = 도식 레이어·카드 순서(설치·로그인·홈(개요 맵)·카드별·플랫폼·공통), SCREENS = 모든 FR 을 최소 1개 화면 PRD 추적 열에 매핑(비화면 FR 은 설정·상태 화면).
- 와이어프레임 PNG(`ui/ui_<S-ID>.png`, 15~25개 = `WIREFRAMES`): `wire_lib.configure(brand=SYSTEM, nav=<도식 기반 내비>, footer=…)` 후 `frame()`+위젯.
  **개요 맵은 원본 도식 배치(레이어 띠·번호 카드) 그대로**, 카드 개요 화면은 카드의 흐름도·타일을 그대로 그리고 상태·지표를 겹친다. 가상 데이터만.

### 9. 본문 작성 (part 파일)
`references/prd-outline.md` 의 장 구성(1~21장 + 부록 A~F)대로 `part01_front.py` … `part22_appendix.py` 를 쓴다(장 번호 순 파일명).
자동 생성: 12장 `fr_chapter(12)`, 15.4 `screen_list()`, 16.2 `repos_table()`, 21장 `trace_chapter(21, REQ_ROWS)`, 부록 C `appendix_repos()` · D `appendix_stars()` · E `FIG_TABLE()`.
그림(자체 작성): 개요(레이어 × 단위) · 배포 아키텍처(컨트롤/데이터 플레인) · 에이전트 해부도 · 요청 흐름 · 릴리스 파이프라인 · 테넌트 모델 · 로드맵 — 캡션 출처 "본 문서 작성".
6항(packaging-release.md)의 배포 단위·실행 모드·설치 패키지 매트릭스·릴리스 파이프라인·채널·서명·SBOM·관리면 체크리스트가 11·14·18장과 PLT-* FR 에 모두 있어야 한다.

### 10. 빌드·게이트·검사
```bash
WVS_KIT=$KIT .venv/bin/python build_prd.py --pdf        # 게이트 실패 시 중단(FR 없는 단위·화면 미커버 FR·유령 FR·실측 안 된 OSS)
.venv/bin/python -c "import data_fr;print('\n'.join(data_fr.FR))" > /tmp/fr_ids.txt
.venv/bin/python $KIT/check_report.py "../<FILE_STEM>.docx" --pdf "../<FILE_STEM>.pdf" --render /tmp/prd_pages \
   --require-file /tmp/fr_ids.txt --forbid "<형식 참고 PRD 파일명>" --min-h1 20
```
✅ 게이트 PASS · check PASS(빈 쪽 0, FR 전부 등장). 렌더 쪽을 열어 표 넘침·그림 겹침 확인.

### 11. 화면설계서 pptx (`--ui-pptx`, 기본)
- `references/prd-ui-design-doc.md` 구조(앞부속 → PART1 개요·IA·화면 목록·역할 매트릭스·흐름도·공통 가이드 → PART2 화면별 → PART3 부록 RTM)로 `<Brand>_UI_assets/pptx/build_ui.py` 작성,
  `ui_lib.configure(system=SYSTEM, nav=…)`. 화면 스펙 `ui_screens_<x>.py` 는 그룹별 서브에이전트 병렬(화면 3~4개마다 저장, 담당 화면 전부·순서 유지, fr 전부가 items 연계 열에 등장).
- 빌드 assert: 화면 ID 누락·중복 0, PRD 추적 일치, 기능 표 연계 누락 0, FR 전수 커버. → `bash $KIT/docx2pdf.sh <Brand>_UI_Design.pptx` → 모든 쪽 렌더 확인.

### 12. 보고
경로(docx·pdf·pptx·pdf) · 단위 수 · FR 수(P0/P1/P2) · 화면 수 · 실측 저장소/스타 교차 수 · 게이트 결과 · 주요 결정 5줄 · [미확인] 개수.

## 규칙
- 각 FR 은 도식 내용에 충실하고 그대로 구현 가능한 수준(하는 일 + 구현 요지(라이브러리·API·알고리즘·설정 키) + 우선순위 + 참고 OSS + 근거).
- **출처·라이선스·참고 이미지 항상 명시**(2장·부록 B·E, 표의 ★·SPDX, 그림 캡션 출처). AGPL/SSPL/BUSL/ELv2/비상업 라이선스는 경고하고 결합방식 A/L/X 로.
- **형식 참고용 이전 PRD·화면설계서는 출처에 넣지 않는다**(check_report `--forbid`).
- 가상 데이터만(실존 개인정보 금지). 공통 규칙은 references/kit.md §3.
