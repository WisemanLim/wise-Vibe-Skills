---
name: wvs-report
description: "보고서·PRD 생성 통합 스킬 — 모드 3종: repos(첨부 인포그래픽의 오픈소스를 GitHub 매핑·분류별 clone·디렉토리 구조·사용법·활용분야 요약 Summary-Repos.docx, 구 oss-clone-analysis) · deep(첨부 이미지·파일(md 등)·사이트의 패키지/개념별 정의·소스 repo·설치·사용·동작·활용·확장 상세 분석 + 논문·저장소 검증, <제목>.docx — Miscellaneous-Data 폴더가 있으면 그 안, 없으면 루트, 구 attachment-deep-analysis) · prd(분석 보고서·요구사항/개발방향 문서(md)·첨부 이미지·참고 사이트/GitHub 링크·요청문을 함께 받아 요구 항목(RQ) 추적·마이크로 에이전트·UI/UX·스택·유사 시스템·패키징/릴리스 PRD + 화면설계서 pptx, 구 requirement-based-prd). 모두 이전 보고서 양식 docx → PDF. Report/PRD generator. Use for 'Summary-Repos', '첨부 이미지 상세 분석 보고서', '보고서·요구사항 문서 기반 PRD'."
---

# wvs-report — 보고서·PRD 생성 (repos · deep · prd)

Arguments: $ARGUMENTS
> 호스트가 `$ARGUMENTS` 를 치환하지 않는 에이전트에서는 사용자 요청문에서 모드·인수를 추출한다. 첨부 이미지는 대화의 이미지·경로·URL 모두 허용.

## 1. 모드 선택
`wvs-report <mode> [입력…] [옵션]` — 모드가 없으면 아래 신호로 고르고, 고른 모드를 한 줄로 알린다.

| 모드 | 입력 | 산출물 | 고르는 신호 | 절차(먼저 읽기) |
|---|---|---|---|---|
| `repos` | 인포그래픽 이미지·링크(도구 목록) | `<root>/<Project>/NN-분류/도구/`(clone) + `Summary-Repos.docx/.pdf` | "clone", "Summary-Repos", 도구 로고 목록 | `references/repos.md` |
| `deep` | 첨부 이미지(인포그래픽·도식) · 첨부 파일(md 등) · 첨부 사이트 URL (하나 이상, 섞어서) | `OUT/<제목>.docx/.pdf` + `<제목>_assets/` — OUT = `<root>/Miscellaneous-Data`(있으면) 또는 `<root>` | "상세 분석", "보고서", 범주·패키지 비교 도식 | `references/deep.md` |
| `prd` | 다중 입력 — 분석 보고서 docx/pdf(+ `_assets/`) · 요구사항/개발방향 문서 md · 첨부 이미지(도식·UI 시안·캡처) · 참고 사이트·GitHub URL · 요청문 (하나 이상, 섞어서) | `OUT/<Brand>_<Phrase>_PRD.docx/.pdf` + `<Brand>_UI_Design.pptx/.pdf` — OUT = `<root>/Need-to-be-organized-into-PRD`(있으면) 또는 `<root>` | "PRD", 요구사항 md·보고서 파일 지정 | `references/prd.md` |

흐름 연결: `deep` 결과(보고서 + `_assets/research`) → `prd` 의 입력. `repos` 결과도 `prd` 기초 자료로 쓸 수 있다.
`prd` 는 입력을 먼저 `scripts/prd_intake.py` 로 분류·보존하고 요구사항 문서에서 RQ 를 뽑는다 — 분석 보고서 없이 요구사항 md·이미지·링크만으로도 동작한다.

## 2. 공통 인수
| 인수 | 기본값 | 의미 |
|---|---|---|
| `--root <dir>` | 현재 작업 디렉토리 | 작업 루트(예: wise-Analysis-Repos) |
| `--template <docx>` | 루트의 최근 같은 유형 문서 | 형식 참고(출처에 넣지 않음) |
| `--no-pdf` | false | PDF 변환 생략 |
| `--plan-only` | false | 전사·조사 사양(_SPEC.md)·카탈로그까지만 만들고 정지 |
| `--out-dir <dir>` | 자동 | deep·prd 출력 폴더. 기본 폴더(`Miscellaneous-Data` · `Need-to-be-organized-into-PRD`)가 `<root>` 에 **있으면 그 안**, **없으면 `<root>` 바로 아래**에 만든다(기본 폴더를 새로 만들지 않음). 결정은 `python3 $KIT/out_dir.py deep|prd --root <root>` |
모드별 옵션(`--project`·`--categories` / `--title`·`--axes`·`--experiment` / `--req`·`--image`·`--url`·`--links`·`--name`·`--github-user`·`--similar`·`--extra`·`--ui-pptx`)은 각 reference 의 인수 표.

## 3. `{ }` 와 `[ ]` — 자동 추출·도출 규칙
- `{ }` = 첨부 이미지·링크·기초 보고서에서 **자동 추출**: 제목·프로젝트명·문서명·범주·항목·원저작자. 사용자가 값을 주면 그 값이 우선.
- `[ ]` = 첨부·요청문에서 **자동 도출**해 분류·분석 축·장 구성·FR·화면으로 반영하는 세부 요구.
- 추출 결과(제목 · 범주 수 · 항목 수 · 출력 경로)를 시작 시 한 줄로 알리고 진행한다(`--plan-only` 면 정지).

## 4. 경로와 도구
- `SKILL_DIR` = 이 SKILL.md 디렉토리, `KIT` = `SKILL_DIR/scripts` (docx 엔진·PDF 변환·GitHub/레지스트리/arXiv 검증·클론·트리·와이어프레임·pptx·산출물 검사). 상세: `references/kit.md`.
- 템플릿: `SKILL_DIR/templates/{repos,deep,prd}/` — 보고서 `_assets/` 로 복사해 채운 뒤 빌드. 화면설계서는 `templates/prd/ui/` → `<Brand>_UI_assets/`(빌더 `build_ui.py` 수정·재작성 금지). 빌드 스크립트는 `$WVS_KIT`·자산 폴더 `.wvs_kit`·설치된 `wvs-report/scripts` 순으로 툴킷을 찾는다.
- 출력 폴더는 항상 `out_dir.py` 결과. 요청문의 "Miscellaneous-Data/…로 생성"·"Need-to-be-organized-into-PRD 이하에 작성" 은 이 규칙(있으면 그 안, 없으면 `<root>`)이며 폴더를 만들라는 뜻이 아니다.
- 준비: `bash $KIT/setup_env.sh <assets>`(venv: python-docx·python-pptx·matplotlib·pymupdf), `gh auth status`, LibreOffice(`soffice`).

## 5. 품질 게이트 — 호스트 무관 (반드시)
어느 에이전트(Claude Code·Claude Desktop·Codex·Cursor·Gemini CLI·Windsurf·Devin·OpenCode·Antigravity·Copilot CLI·Command Code·Grok Build·OMP·VS Code)에서든 같은 품질을 내도록, 품질은 스크립트 게이트로 판정한다. 규약: `references/host-compat.md`.
- 시작 시 `호스트 능력: 서브에이전트 O/X · 웹 검색 O/X · 셸 O/X → 병렬|순차 모드` 한 줄 보고. 서브에이전트가 없으면 **순차 모드**(조사 단위 하나씩 작성 → 단위 게이트 → 다음).
- 템플릿(`_SPEC.md` 등)은 **복사해 채운다 — 요약·압축 금지**. 조사 전에 **사전 웹 확인**(제목·제품 실존·현행 상태, 1차 출처 URL 3건+). 웹 도구가 없으면 `curl`·`gh api`.
- `deep` 게이트: `scripts/check_research.py --assets <A> --stage spec` → 단위마다 `--unit rN_x.md` → `--stage research` → `--stage final` → `check_report.py … --min-pages 40 --min-tables 50`. **PASS 전에는 다음 단계로 가지 않는다.** 근거가 없어 못 채운 FAIL 은 지어내지 말고 사유와 함께 보고.

## 6. 공통 규칙 (세 모드 공통)
- **출처·라이선스·참고 이미지 항상 명시** — 원본 첨부 이미지 캡션 출처 "원저작자 · 사용자 첨부 이미지, 분석 목적 인용", 저장소는 ★·SPDX 병기, 부록에 출처 총람·그림 출처.
- **형식(템플릿) 참고용 이전 문서는 출처에서 제외** — `check_report.py --forbid "<이전 문서명>"` 로 확인.
- 1차 출처 우선, 확인 못 한 사실 `[미확인]`, 업계 일반 가정 `[도메인]`. 실존 확인 안 된 저장소·논문은 쓰지 않는다(`verify_sources.py`, `gh_probe.py`).
- 조사는 서브에이전트 병렬(없으면 순차), 블록·절 하나 끝낼 때마다 파일 저장.
- 완료 전 `check_report.py <docx> --pdf <pdf> --render <dir>` PASS(화면설계서는 `check_ui_design.py <pptx> --pdf --render <dir>` PASS) + 렌더 쪽 육안 확인. 최종 보고: 경로·장/쪽 수·검증 수·핵심 판정 5줄.

## 7. 예시
```text
/wvs-report repos --root ~/wise-Analysis-Repos                       (인포그래픽 첨부)
/wvs-report repos --categories "Model & Data Security, Data Visualization"
/wvs-report deep --root ~/wise-Analysis-Repos --title "OCR+PDF Extractors"   (도식 첨부)
/wvs-report prd "9AI-Concepts-That-Put-You-Ahead-of-99%-in-2026" --github-user WisemanLim
/wvs-report prd docs/requirements.md ui-mock-1.png ui-mock-2.png https://www.bizinfo.go.kr https://github.com/langgenius/dify
/wvs-report prd direction.md --links refs.txt --name GovScout                (보고서 없이 요구사항 문서 + 참고 링크)
```

## 8. 구 커맨드 대응
| 구 커맨드 | 새 호출 |
|---|---|
| `/oss-clone-analysis` | `/wvs-report repos` |
| `/attachment-deep-analysis` | `/wvs-report deep` |
| `/requirement-based-prd` | `/wvs-report prd` |
| wise-report-kit 스크립트 | `wvs-report/scripts/*` (`references/kit.md`) |
