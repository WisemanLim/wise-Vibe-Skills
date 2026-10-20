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

출력 위치 규칙: `<root>/Need-to-be-organized-into-PRD` 가 있으면 그 안, 없으면 `<root>/<Brand>_…_PRD.docx/.pdf` (`--out-dir` 우선, `scripts/out_dir.py prd`).
> 위 1항의 "Need-to-be-organized-into-PRD 이하에 작성" 은 **이 규칙을 뜻한다 — 폴더가 없으면 만들지 않고 `<root>` 에 쓴다.** 출력 폴더는 항상 `out_dir.py` 결과만 쓰고 `mkdir` 로 기본 폴더를 만들지 않는다(`setup_env.sh`·`prd_intake.py` 는 출력 폴더가 없으면 중단).

- `{ }` = **자동 추출**: 입력(분석 보고서·요구사항/개발방향 문서·첨부 이미지·참고 링크·요청문)의 제목·핵심 문구(→ 제품명·문서명), 구조(도식 레이어·카드 / 문서의 장·기능 묶음).
- `[ ]` = **자동 도출해 PRD 에 반영**: 2~6항 — 단위 분해(units.py), FR·화면·스택·유사 시스템·패키징/릴리스. 사용자 요청문에 다른 번호 항목이 있으면 그대로 1.1 대응표·21.2 추적표에 넣는다.

## 입력 — 여러 종류를 함께 받는다
| 종류 | 예 | PRD 에서의 쓰임 |
|---|---|---|
| **분석 보고서** `.docx`/`.pdf` (+ `<이름>_assets/`) | `Miscellaneous-Data/9AI-….docx` (deep 모드 산출물) | 조사 원문(research/r*.md)·검증 저장소(measured.json)·원본 도식 재사용, 도출 스택 전부 참고 |
| **요구사항·개발방향 문서** `.md`(·`.txt`·`.rst`, `--req` 지정 시 `.docx`/`.pdf`) | `requirements.md`, `PRD-draft.md`, `direction.md` | 요구 항목(RQ) 추출 → 모든 기능·UI·비기능·제약 RQ 를 FR·NFR·장으로 추적(게이트) |
| **첨부 이미지** `.png`/`.jpg`/`.webp`/`.svg` · 이미지 URL | 인포그래픽·아키텍처 도식·UI 시안·화이트보드·경쟁 제품 캡처 | 도식 → 단위·정보 구조의 정본 / UI 시안 → 화면·레이아웃 / 캡처 → 레퍼런스 패턴 |
| **참고 링크** 사이트 URL | 경쟁·유사 제품, 공공 서비스, 문서 페이지 | 기능·정보 구조·UI 패턴·가격/라이선스 비교(4장·15장) — 문구·이미지 복제 금지 |
| **GitHub 저장소 URL** | `https://github.com/owner/repo` | 실측(gh_probe) + README → 참고 OSS·결합방식(16장) |
| **요청문** (`--prompt` 또는 대화 본문) | 번호 항목 1~6·*·** | RQ 와 1.1 사용자 요구 대응표 |
여러 종류를 섞어 줄 수 있고(예: 요구사항 md + UI 시안 2장 + 참고 사이트 3개), **분석 보고서 없이도** 동작한다.
우선순위(충돌 시): 요청문 > 요구사항 문서 > 분석 보고서·도식 > 이미지(시안) > 참고 사이트. 충돌과 결정은 `_INPUTS.md` '입력 간 충돌·결정' 표에 남기고 3.4 에 싣는다.

## 인수
| 인수 | 기본값 | 의미 |
|---|---|---|
| 위치 인수 | (1개 이상) | 입력 — 파일(보고서·문서·이미지)·폴더·URL 을 섞어서. 보고서는 이름만 줘도 `<root>/Miscellaneous-Data/<이름>.docx|pdf` → `<root>/<이름>.docx|pdf` 순으로 탐색. 대화에 붙은 이미지·링크도 입력 |
| `--req <file>` · `--report <file>` · `--image <file>` · `--url <url>` | — | 자동 분류를 덮어쓰는 강제 지정(반복 가능) |
| `--links <file>` | — | 한 줄에 URL 하나인 목록 파일 |
| `--root <dir>` | 현재 작업 디렉토리 | 작업 루트(예: wise-Analysis-Repos) |
| `--out-dir <dir>` | 자동 | PRD 출력 폴더(`OUT`). 기본: `<root>/Need-to-be-organized-into-PRD` 가 **있으면** 그곳, **없으면** `<root>` 바로 아래(폴더를 새로 만들지 않음) — `scripts/out_dir.py prd`. 지정하면 그 폴더(상대 경로는 `<root>` 기준) |
| `--name <Brand>` | {핵심 문구에서 자동} | 제품명(파일명 접두) |
| `--github-user <id>` | `WisemanLim` | stars·repositories 교차 대상 |
| `--similar "<도메인>"` | [요청 5항에서 도출] | 유사 시스템 조사 도메인 |
| `--extra "<텍스트|파일>"` | — | 추가 요구사항 — 텍스트는 요청문(prompt), 파일은 요구사항 문서 입력으로 처리 |
| `--ui-pptx <true|false>` | true | 화면설계서 `<Brand>_UI_Design.pptx/.pdf` 함께 생성 |
| `--no-pdf` · `--plan-only` | false | PDF 생략 · 4단계(카탈로그·조사 사양)까지만 |

## 산출물
```
OUT = <root>/Need-to-be-organized-into-PRD (있을 때) | <root> (없을 때) | --out-dir
OUT/<Brand>_<Core-Phrase-Slug>_PRD.docx / .pdf
OUT/<Brand>_UI_Design.pptx / .pdf            (--ui-pptx)
OUT/<Brand>_assets/
├── inputs/ (IN-NN.* 입력 사본 · 사이트 텍스트 발췌)   source_infographic.png (구조 도식이 있을 때)
├── research/(inputs.json _INPUTS.md req_items.tsv req_map.tsv _SPEC.md r1~r7_*.md stars_all.tsv user_repos.tsv stars_relevant.tsv repos_catalog.tsv repos.tsv)
├── units.py data.py data_fr.py ui_data.py prd_auto.py kitpath.py collect_repos.py build_prd.py part*.py figs.py fig*.png ui/ui_<S-ID>.png .venv/
OUT/<Brand>_UI_assets/                       (--ui-pptx, SKILL_DIR/templates/prd/ui/ 사본)
├── ui_design_data.py ui_spec.py               (제품별 내용 — 채운다)
└── pptx/ build_ui.py(수정 금지) ui_ids.py AGENT_BRIEF.md ui_screens_<key>.py
```

## 절차
`SKILL_DIR` = wvs-report 스킬 디렉토리, `KIT` = `SKILL_DIR/scripts`. 참고 문서: `references/prd-outline.md`(장 구성 정본·품질 게이트), `references/prd-research-spec.md`,
`references/prd-similar-systems.md`(5항), `references/prd-packaging-release.md`(6항), `references/prd-ui-design-doc.md`(화면설계서).

### 1. 입력 수집·정규화 ({ } 자동 추출)
```bash
OUT=$(python3 $KIT/out_dir.py prd --root <root> [--out-dir <dir>])      # 출력 폴더 결정(이하 <Brand>_assets = $OUT/<Brand>_assets)
mkdir -p "$OUT/<Brand 미정이면 _work>_assets" && bash $KIT/setup_env.sh "$OUT/<…>_assets"
python3 $KIT/prd_intake.py <입력…> --root <root> --assets "$OUT/<…>_assets" [--req F] [--image F] [--url U] [--links urls.txt] [--prompt "<요청문>"]
#  → inputs/IN-NN.* · research/inputs.json · research/_INPUTS.md · research/req_items.tsv (출력에 분류 결과·RQ 수·CHECK 경고)
```
대화에 붙은 이미지는 파일로 저장해 `--image` 로, 요청문은 `--prompt` 로 넘긴다. 브랜드가 정해지면 폴더를 `<Brand>_assets` 로 바꾼다.
그 다음 **입력마다 직접 읽고** `_INPUTS.md` 의 IN 블록을 채운다(주석 안내를 지우고 사실만 bullet — 비어 있으면 빌드 게이트 실패):
1. **분석 보고서**: `pandoc "<report>.docx" -t gfm -o /tmp/base.md`(pdf 면 `pdftotext -layout`) → 장 구성·요약·도식 판정·도출 스택. `_assets/` 의 `research/r*.md`·`measured.json`·`source_infographic.png` 를 쓴다.
2. **요구사항·개발방향 문서**: 목표·범위·비범위·기능·비기능·제약·우선순위를 요약하고, `req_items.tsv`(휴리스틱 추출)를 검토해 **병합·분할·유형(fr·ui·nfr·constraint·goal·non-goal·info)·우선순위 수정**. 빠진 요구는 행을 추가(ID 연번 유지). 출처 줄(`line`)은 유지.
3. **이미지**: 직접 보고 — 도식이면 **레이어 띠·번호 카드·카드 속 흐름도/아이콘 타일/불릿·하단 띠** 원문 전사(단위·정보 구조의 정본, 대표 도식은 `source_infographic.png` 로 복사) / UI 시안이면 화면·영역·컴포넌트·상태·문구 / 캡처면 담긴 패턴.
4. **참고 사이트**: `inputs/IN-NN.txt`(자동 발췌)로 부족하면 WebFetch·브라우저로 열어 기능 목록·메뉴 구조·UI 패턴·가격/라이선스·차별점 정리. 로그인 필요·접속 실패는 `[미확인]` 으로 두고 사용자에게 캡처를 요청. 문구·이미지는 복제하지 않는다.
5. **GitHub URL**: `gh_probe.py` 실측 + README → 목적·기능·SPDX·활성도·결합방식(E/A/L/R/X).
6. 입력 간 충돌(예: 문서는 웹 전용, 시안은 데스크톱 앱)은 우선순위 규칙으로 결정해 '입력 간 충돌·결정' 표에 기록.
✅ inputs.json 에 ERR·unknown 없음(있으면 재지정·재수집), 모든 IN 블록 요약 완료, req_items.tsv 검토 완료.

### 2. 제품명·문서명 ({ })
핵심 문구(도식 대제목 예: "The map behind production AI systems", 없으면 요구사항 문서의 제목·비전 문장)의 의미를 담은 짧은 브랜드 후보 3개 + 근거를 만들고 첫 후보를 기본 채택(`--name` 우선).
`FILE_STEM = <Brand>_<Core-Phrase-Title-Case-Hyphen>_PRD` (예: `ProdAI-Atlas_The-Map-Behind-Production-AI-Systems_PRD`). 1.1 대응표 1행에 선택 근거를 남긴다.

### 3. 단위 카탈로그 ([2·4항] — `units.py`)
- `SKILL_DIR/templates/prd/*.py` 를 `<Brand>_assets/` 로 복사. **세부 항목 1개 = 독립 구동·배포 단위 1개**(`<DOMAIN>-<ITEM>`):
  - 구조 도식(이미지·보고서)이 있으면: 각 카드의 흐름 단계·타일·불릿을 전부 단위로, '원본 도식 요소' 열에 원문 그대로.
  - 요구사항 문서만 있으면: 문서의 장(Epic) → 도메인, 기능 묶음(Feature) → 단위, '원본 도식 요소' 열에 `IN-NN §절 RQ-…`.
  - 에이전트형 시스템이면 단위 = 마이크로 에이전트(A2A skill), 아니면 독립 배포 모듈·서비스(A2A 열 "-").
- 도식에 없지만 보고서가 '누락'으로 판정한 요소는 `(도식 누락 — 보완)` 단위로 추가. 하단 띠(성숙도 등)도 단위로.
- 플랫폼 PLT-MGR·DEP·TEN·IAM·SEC·PKG·REL·CON(6항), 공통 X-*(5항, 7단계에서 확정).
✅ 도식 전사의 모든 요소와 기능·UI 유형 RQ 전부가 최소 1개 단위로 이어짐.

### 4. 사용자 GitHub 목록과 조사 사양 ([3항])
```bash
bash $KIT/setup_env.sh "<Brand>_assets"
python3 $KIT/github_user_lists.py <user> -o "<Brand>_assets/research"     # stars_all.tsv · user_repos.tsv
```
- 단위별 키워드로 stars_all.tsv 를 grep 해 `stars_relevant.tsv`(full_name·stars·license·unit·use_ko·adopt) 선별, user_repos.tsv 에서 재사용 후보 표시.
- `references/prd-research-spec.md` 로 `research/_SPEC.md` 작성(대상 시스템·입력 인벤토리(_INPUTS.md·req_items.tsv)·단위 카탈로그 표·조사 단위 r1~r7·산출 형식·규칙).
- 참고 사이트·GitHub URL 입력은 r7_market(유사 시스템)·해당 개념 조사 단위에 배정한다.
✅ `--plan-only` 면 여기서 정지(units.py·_SPEC.md 경로 보고).

### 5. 병렬 조사 (서브에이전트 6~7개)
레이어·개념 묶음 r1~r5, `r6_platform`(packaging-release.md 기준), `r7_market`(similar-systems.md 기준). 각 에이전트: _SPEC.md → _INPUTS.md·req_items.tsv → (있으면) 기초 보고서 조사 원문 → 조사, 절마다 저장.
**FR 표 '근거' 열에 해당 RQ-ID(·IN-ID)를 반드시 적는다** — RQ↔FR 자동 추적의 근거.
산출 절: `## 1. 원조 개념 분석` · `## 2. 대체·유사 시스템`(≥12) · `## 3. 기능 매트릭스` · `## 4. FR 후보`(단위당 5~10, `FR-<단위>-NN`, 구현 요지는 라이브러리·API·설정 키 수준) ·
`## 5. 컴포넌트·데이터`(에이전트 명세 표·엔터티·계약 JSON) · `## 6. UI/UX 참고` · `## 7. 동향·리스크` · `## REPOS`(gh api 확인분만, 결합방식 E/A/L/R/X) · `## SOURCES`.

### 6. 저장소 실측과 FR 정본
```bash
cd "<Brand>_assets"
WVS_KIT=$KIT .venv/bin/python collect_repos.py --base "<기초 보고서>_assets/measured.json"   # repos_catalog.tsv → repos.tsv
.venv/bin/python data_fr.py          # 도메인별 FR 수 · orphan · 'units without FR' = [] 이어야 함
```
FR 이 없는 단위·카탈로그 밖 FR·실측 안 된 참고 OSS 는 해당 조사 파일을 고치거나 해당 에이전트에 재요청.
FR 로 이어지지 않는 RQ(비기능·제약 등)는 `research/req_map.tsv` 에 `RQ-ID<TAB>대상(NFR-…·FR-…·13장)<TAB>비고` 로 적는다.

### 7. 유사 시스템·공통 기능 ([5항])
r7 결과로 4장(공통 기능군·유사 시스템 ≥12·기능 매트릭스·비워 둔 기능·필수도 판정)을 쓰고, 필수·권장 기능을 X-* 단위·FR 로 units.py/r7 에 반영.
요청 예시 도메인(예: 정부 과제 조회)이 목표 범주와 다르면 해석을 1.1 대응표에 명시(similar-systems.md §1).

### 8. UI/UX ([2항]) — 화면 목록·와이어프레임
- `ui_data.py`: GROUPS = 도식 레이어·카드 순서(설치·로그인·홈(개요 맵)·카드별·플랫폼·공통), SCREENS = 모든 FR 을 최소 1개 화면 PRD 추적 열에 매핑(비화면 FR 은 설정·상태 화면).
- **UI 시안 이미지 입력이 있으면 해당 화면은 시안의 영역·컴포넌트 배치를 따르고**, 참고 사이트에서 정리한 UI 패턴은 15.2·레퍼런스 제품 패턴에 근거(IN-ID)와 함께 쓴다.
- 와이어프레임 PNG(`ui/ui_<S-ID>.png`, 15~25개 = `WIREFRAMES`): `wire_lib.configure(brand=SYSTEM, nav=<도식 기반 내비>, footer=…)` 후 `frame()`+위젯.
  **개요 맵은 원본 도식 배치(레이어 띠·번호 카드) 그대로**, 카드 개요 화면은 카드의 흐름도·타일을 그대로 그리고 상태·지표를 겹친다. 가상 데이터만.

### 9. 본문 작성 (part 파일)
`references/prd-outline.md` 의 장 구성(1~21장 + 부록 A~F)대로 `part01_front.py` … `part22_appendix.py` 를 쓴다(장 번호 순 파일명).
자동 생성: 2.1 `inputs_table()`, 3장 `part03_inputs.py`(입력별 전사·요약 · RQ `req_table()` · 단위 카탈로그 · 충돌·결정), 12장 `fr_chapter(12)`, 15.4 `screen_list()`, 16.2 `repos_table()`,
21장 `trace_chapter(21, REQ_ROWS)`(21.4 RQ → FR·NFR·장), 부록 C `appendix_repos()` · D `appendix_stars()` · E `FIG_TABLE()`. 첨부 이미지는 1.2 에 자동 인용(출처: 사용자 첨부 이미지).
그림(자체 작성): 개요(레이어 × 단위) · 배포 아키텍처(컨트롤/데이터 플레인) · 에이전트 해부도 · 요청 흐름 · 릴리스 파이프라인 · 테넌트 모델 · 로드맵 — 캡션 출처 "본 문서 작성".
6항(packaging-release.md)의 배포 단위·실행 모드·설치 패키지 매트릭스·릴리스 파이프라인·채널·서명·SBOM·관리면 체크리스트가 11·14·18장과 PLT-* FR 에 모두 있어야 한다.

### 10. 빌드·게이트·검사
```bash
WVS_KIT=$KIT .venv/bin/python build_prd.py --pdf        # 게이트 실패 시 중단(FR 없는 단위·화면 미커버 FR·유령 FR·실측 안 된 OSS·미매핑 RQ·요약 없는 입력)
.venv/bin/python -c "import data_fr,prd_auto;print('\n'.join(list(data_fr.FR)+[q['id'] for q in prd_auto.RQ]))" > /tmp/fr_ids.txt
.venv/bin/python $KIT/check_report.py "$OUT/<FILE_STEM>.docx" --pdf "$OUT/<FILE_STEM>.pdf" --render /tmp/prd_pages \
   --require-file /tmp/fr_ids.txt --forbid "<형식 참고 PRD 파일명>" --min-h1 20
```
✅ 게이트 PASS · check PASS(빈 쪽 0, FR 전부 등장). 렌더 쪽을 열어 표 넘침·그림 겹침 확인.

### 11. 화면설계서 pptx (`--ui-pptx`, 기본) — 표준 빌더 템플릿으로만 만든다
양식은 고정(ObservaMesh·AegisMesh 화면설계서와 동일): 표지 → 문서 정보·개정 이력 → 목차 → PART 1(1 시스템 개요 · 2 화면 ID 명명 규칙 · IA ①② · 화면 목록 ·
사용자×화면 매트릭스 · 화면 흐름도 ①~ · 공통 UI 가이드 2장 · 사용자 유형·모드 적응) → PART 2 화면별 → PART 3 부록 A~F. 상세: `references/prd-ui-design-doc.md`.
```bash
mkdir -p "$OUT/<Brand>_UI_assets" && cp -R $SKILL_DIR/templates/prd/ui/. "$OUT/<Brand>_UI_assets/"      # 빌더·예시·지침 복사
#  채우기: ui_spec.py({ } 자리 전부) · ui_design_data.py(USERS·_DESC·COMPONENTS·STATES·MESSAGES) · pptx/ui_ids.py(FILES = 키 → 그룹 코드)
cd "$OUT/<Brand>_UI_assets/pptx"
<venv>/bin/python build_ui.py --stub         # 화면 스펙 전 구조·assert 확인 → ../stub_<Brand>_UI_Design.pptx
#  화면 스펙 ui_screens_<key>.py: 그룹별 서브에이전트 병렬 — 각자 pptx/AGENT_BRIEF.md + ui_screens_example.py 를 먼저 읽는다
WVS_KIT=$KIT <venv>/bin/python build_ui.py --pdf     # → $OUT/<Brand>_UI_Design.pptx/.pdf, 저장 직후 check_ui_design.py 자동 실행(FAIL 이면 중단)
<venv>/bin/python $KIT/check_ui_design.py "$OUT/<Brand>_UI_Design.pptx" --pdf --render /tmp/ui_pages
```
- **금지**: `build_ui.py`·`ui_lib.py` 수정, 빌더를 새로 작성, 다른 슬라이드 구성·화면 ID 체계(`SCR-…`·`S0nn` 등 PRD 15.4 와 다른 ID). 제품별 차이는 `ui_spec.py`·`ui_design_data.py`·`ui_screens_<key>.py` 에만 둔다.
- 빌드 assert: 화면 ID 누락·중복 0, PRD 추적·우선순위 = 화면 목록 정본, 기능 표 연계 누락 0, 콜아웃 수 = items 수, FR 전수 커버, IA 가 모든 그룹 포함, 흐름도 ≥1.
- 게이트 `check_ui_design.py` PASS 필수: 슬라이드 순서(앞부속·PART 1 9절·PART 2·부록 A~F) · 화면 슬라이드 밀도(도형 ≥25·콜아웃 ≥5) · 표준 빌더 표식 · `build_ui.py` 가 템플릿과 동일.
  FAIL 이면 완료 보고하지 않는다. 렌더된 모든 쪽을 열어 겹침·넘침·콜아웃 위치를 확인.

### 12. 자산 정리 (`--keep-assets` 면 생략)
10·11단계 게이트 PASS 후: `python3 $KIT/prune_assets.py "$OUT/<Brand>_assets"` · `python3 $KIT/prune_assets.py "$OUT/<Brand>_UI_assets"`(각각 `--dry-run` 먼저).
venv·와이어프레임/그림 PNG·캐시를 지우고 템플릿 사본 코드·research/·inputs/·requirements.txt·ASSETS.md 만 남긴다. 기초 보고서(deep)의 `_assets/` 는 건드리지 않는다.

### 13. 보고
경로(docx·pdf·pptx·pdf) · 입력 종류별 수 · RQ 수(추적 대상/매핑) · 단위 수 · FR 수(P0/P1/P2) · 화면 수 · 실측 저장소/스타 교차 수 · 게이트 결과 · 자산 정리(확보 용량) · 주요 결정·입력 간 충돌 5줄 · [미확인] 개수.

## 규칙
- 각 FR 은 입력 내용(도식·요구사항 문서·시안)에 충실하고 그대로 구현 가능한 수준(하는 일 + 구현 요지(라이브러리·API·알고리즘·설정 키) + 우선순위 + 참고 OSS + 근거(RQ·IN·도식 요소)).
- 참고 사이트는 접근일과 URL 을 남기고 기능·구조·패턴만 참고한다. 로그인·유료 영역은 사용자가 준 캡처로만 다룬다.
- **출처·라이선스·참고 이미지 항상 명시**(2장·부록 B·E, 표의 ★·SPDX, 그림 캡션 출처). AGPL/SSPL/BUSL/ELv2/비상업 라이선스는 경고하고 결합방식 A/L/X 로.
- **형식 참고용 이전 PRD·화면설계서는 출처에 넣지 않는다**(check_report `--forbid`).
- 가상 데이터만(실존 개인정보 금지). 공통 규칙은 references/kit.md §3.
