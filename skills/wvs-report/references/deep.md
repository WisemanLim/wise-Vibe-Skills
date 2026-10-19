# mode `deep` — 첨부 자료 상세 분석 보고서 (구 attachment-deep-analysis, 요청 유형 --2)


> 인수 규칙·경로 변수(`SKILL_DIR`·`KIT`)는 `wvs-report` SKILL.md 를 따른다. `KIT` = `SKILL_DIR/scripts`.
> **호스트 무관 품질**: 어떤 에이전트(Claude Code·Cursor·Codex·Gemini CLI …)에서 실행하든 `references/host-compat.md` 규약과 게이트 4개(`check_research.py` spec·unit·final, `check_report.py --min-pages 40 --min-tables 50`)를 따른다. **게이트 PASS 전에는 다음 단계로 가지 않는다.**

## 요청 원형과 자동화 규칙
> 첨부이미지는 **{OCR+PDF Extractors}** 관련 문서로 **[Native PDF, OCR Engines, Document Parsers, VLM+Specialists 의 구성 및 세부 구성을 패키지(또는 라이브러리)를 비교하면서 상세한 내용]** 을 포함하여 도식화한 자료.
> 관련 내용을 상세화하고 **[각 패키지의 정의, 소스repo, 설치/환경설정, 사용방법 및 동작방식 등까지 조사하여 사용 및 활용용도, 확장방안 등에 대응까지도 포함]** 한 분석 보고서를 작성.
> 첨부이미지상의 자세한 도식화 자료를 기반으로 분석하며, 필요시 인터넷 검색으로 관련 논문·백서 등을 포함. 구현 관점은 github.com repo 를 확인해 참고.
> 보고서는 'Miscellaneous-Data/OCR+PDF Extractors.docx' 로 생성하고 pdf 로 변환. 형식은 이전 보고서를 참고하되 출처 명시 시 형식 참고용은 제외.

출력 위치 규칙: `<root>/Miscellaneous-Data` 가 있으면 그 안, 없으면 `<root>/<제목>.docx/.pdf` (`--out-dir` 우선, `scripts/out_dir.py deep`).
> 요청문의 "'Miscellaneous-Data/<제목>.docx' 로 생성" 은 **이 규칙을 뜻한다 — 폴더가 없으면 만들지 않고 `<root>/<제목>.docx` 로 쓴다.** 출력 폴더는 항상 `out_dir.py` 결과만 쓰고 `mkdir` 로 기본 폴더를 만들지 않는다(`setup_env.sh` 는 출력 폴더가 없으면 중단).

- `{ }` = **첨부에서 자동 추출**: 주제/대제목(→ 보고서 제목·파일명), 부제·원저작자·웹 주소, 범주 라벨과 순서.
- `[ ]` = **첨부·요청에서 도출**: ① 구성 축 — 범주 → 세부 항목(패키지·라이브러리·개념 카드) 목록과 비교 관점(도식 푸터·말풍선이 말하는 차원 포함)
  ② 분석 축 — 항목별 필수 소제목(정의·소스 저장소·설치·환경설정·사용방법·동작방식·성능·활용용도·확장방안·도식 판정). 요청문에 다른 축이 있으면 그것을 따른다.

## 인수
| 인수 | 기본값 | 의미 |
|---|---|---|
| 위치 인수 | (대화의 첨부) | 첨부 이미지(경로·URL) · 첨부 파일(md/txt/docx/pdf) · 첨부 사이트(URL) — 하나 이상, 섞어서. 여러 개면 같은 주제로 합쳐 전사 |
| `--root <dir>` | 현재 작업 디렉토리 | 작업 루트(예: wise-Analysis-Repos) |
| `--out-dir <dir>` | 자동 | 출력 폴더(`OUT`). 기본: `<root>/Miscellaneous-Data` 가 **있으면** 그곳, **없으면** `<root>` 바로 아래(폴더를 새로 만들지 않음) — `scripts/out_dir.py deep`. 지정하면 그 폴더(상대 경로는 `<root>` 기준) |
| `--title <name>` | {첨부 대제목} | 보고서 제목 = 파일명(확장자 제외). 파일명 금지 문자 `/:` 만 치환 |
| `--axes "<a, b, …>"` | [요청문에서 도출] | 항목별 분석 축을 명시적으로 지정 |
| `--experiment` | false | 실측 실험 장 추가(도구를 격리 환경에 설치해 같은 입력으로 측정) |
| `--no-sample` | false | `sample/` 참조 구현 생략(실행 불가 환경 — 사유를 최종 보고에 기재) |
| `--template <docx>` | `OUT` 의 최근 보고서 | 형식 참고(출처에 넣지 않음) |
| `--no-pdf` · `--plan-only` | false | PDF 생략 · 전사와 조사 사양(_SPEC.md)까지만 |

## 산출물
```
OUT = <root>/Miscellaneous-Data (있을 때) | <root> (없을 때) | --out-dir
OUT/<Title>.docx / .pdf
OUT/<Title>_assets/
├── source_infographic.png      ← 원본 첨부
├── research/ _SPEC.md r1_*.md … rN_*.md   ← 조사 원문(블록 = 절)
├── measured.json stats.py      ← 저장소·논문 검증(verify_sources.py)
├── fig_*.png figs.py           ← 재구성·원리·비교 그림(자체 작성)
├── sample/                     ← 참조 구현(실행 결과를 보고서에 인용)
├── exp/                        ← (--experiment) 실측 실험 코드·결과
├── report_config.py build_report.py p_*.py .venv/
```

## 절차
`SKILL_DIR` = wvs-report 스킬 디렉토리, `KIT` = `SKILL_DIR/scripts`.
**출력 폴더 먼저 결정**: `OUT=$(python3 $KIT/out_dir.py deep --root <root> [--out-dir <dir>])` — 이하 `<Title>_assets` 는 모두 `$OUT/<Title>_assets` 이고, 보고서는 `$OUT/<Title>.docx/.pdf` 로 저장된다(빌드 템플릿이 자산 폴더의 상위를 출력 폴더로 쓴다).

### 0. 호스트 능력 점검
서브에이전트·웹 검색·셸 유무를 확인해 `호스트 능력: 서브에이전트 O/X · 웹 검색 O/X · 셸 O/X → 병렬|순차 모드` 한 줄로 알린다(`references/host-compat.md` §2).

### 1. 입력 확보와 전사 ({ } 자동 추출)
1. 입력 보존: `python3 $KIT/prd_intake.py <이미지…> <파일.md…> <URL…> --assets "$OUT/<Title>_assets" --root <root>` → `inputs/IN-NN.*` · `research/inputs.json`(보고서 2장 입력 표로 자동 수록).
   대표 이미지는 `<Title>_assets/source_infographic.png` 로도 복사(여러 장이면 `report_config.py` 의 `SOURCE_IMAGES`). URL·게시물은 이미지 추출, 실패 시 사용자에게 파일 요청.
   **이미지가 없어도 진행한다**(md·사이트만 입력) — 원본 그림 없이 입력 표와 전사로 2장을 채운다.
2. 입력을 직접 보고 **빠짐없이** 전사: 이미지는 대제목·부제·작성자·웹 주소·푸터·말풍선·장식·크기(px), 범주(라벨 색·순서) → 항목(이름 — 주소/카드 문구/흐름/타일/불릿).
   md 등 파일은 제목·절 구조·항목 목록, 사이트는 `inputs/IN-NN.txt` 발췌(접속 실패 시 WebFetch/브라우저)에서 같은 범주 → 항목 구조로 뽑는다.
3. 도식 유형 판정: **A 목록형**(패키지·도구 이름 + 주소) / **B 개념·아키텍처형**(레이어·카드·흐름도). 유형에 맞는 분석 축을 고른다(references/deep-research-spec.md).
✅ 전사 항목 수 = 이미지 항목 수. 제목·범주·항목 수를 한 줄로 알리고 계속.

### 2. 조사 사양 `_SPEC.md`, 사전 웹 확인과 사전 실측
1. **사전 웹 확인**: 대제목·제품명·핵심 용어를 웹 검색(없으면 `curl -sL`)해 실존·현행 이름·출시일·상태(GA/preview/폐기)·수치 근거를 1차 출처 URL 3건 이상으로 확인한다. 도식이 실제 제품을 설명하는지 여기서 가린다 — 건너뛰고 `[미확인]` 처리 금지.
2. 도식의 GitHub 주소(또는 찾은 공식 저장소)를 목록으로 `gh_probe.py` 실행 → 사전 실측 표(이전·아카이브·NOASSERTION 표기).
3. `SKILL_DIR/references/deep-research-spec.md` 의 템플릿을 **그대로 복사해** `research/_SPEC.md` 작성(요약·압축 금지): 전사, 사전 웹 확인, 사전 실측, **도식 판정 후보(이 도식 특화 4개+)**, 항목별 필수 소제목([ ] 분석 축), 조사 단위 표(KEY = `PREFIX_NAME`), 품질 규칙, 파일 형식.
4. 게이트: `python3 $KIT/check_research.py --assets "$OUT/<Title>_assets" --stage spec` → PASS.
3. 조사 단위: 범주별 r1..r(K) + 원리 블록(FND_) + 비교 블록(CMP_), `r(K+1)_gap`(도식 누락 보완 — 최신 도구·상용 서비스·보조 도구), `r(K+2)_value`(벤치마크·통합 비교·사용 및 활용용도·참조 아키텍처·로드맵·거버넌스). 단위당 블록 4~8개.
✅ `--plan-only` 면 여기서 정지하고 _SPEC.md 경로를 보고.

### 3. 조사 (병렬: 서브에이전트 · 순차: 단위별)
- 지시문은 `references/host-compat.md` §4 를 **그대로** 쓴다(블록마다 웹 1차 출처 3건+, gh api 실측, 필수 소제목 전부, append 저장, 끝나면 단위 게이트).
- 병렬 모드: 조사 단위마다 서브에이전트 1개. **순차 모드**(서브에이전트 도구가 없을 때): 단위 하나씩 작성 → `check_research.py --assets <A> --unit rN_x.md` PASS → 다음 단위. 여러 단위를 한 번에 몰아 쓰지 않는다.
- 구현 관점: 저장소 디렉토리 구조(`gh api repos/O/R/contents/PATH`), 실제 API·클래스명·설정 키, 동작 가능한 코드(40줄 이하).
- 전 단위 후 게이트: `check_research.py --assets <A>`(stage research) → PASS. FAIL 블록은 해당 단위만 다시 보강(병렬이면 해당 에이전트에 FAIL 줄을 그대로 전달).

### 4. 검증
```bash
bash $KIT/setup_env.sh "<Title>_assets"
python3 $KIT/verify_sources.py --assets "<Title>_assets"      # repos missing · papers bad → 본문에서 삭제 또는 [미확인]
```
✅ `missing` = 0(또는 본문에서 제거), `bad_papers` = 0.

### 5. 참조 구현(필수) · 실측 실험(선택 `--experiment`)
- **참조 구현(기본 필수, `--no-sample` 로만 생략)**: 통합 구현 가이드용 `sample/` 코드를 작성하고 실제 실행해 결과를 `sample/out/` 에 저장, `p_<name>.py` 로 보고서 장에 출력까지 싣는다. 클라우드 자격 증명이 필요한 주제는 자격 증명 없이 돌아가는 부분(공개 가격 API 조회·IaC 정적 검사 `terraform validate`/`checkov`·설정 파일 생성·로컬 시뮬레이션)으로 구성한다.
- 실측 실험(`--experiment`): 정답을 먼저 정의한 소형 코퍼스로 도구별 **독립 가상환경**(uv)에서 실행, 지표·시간을 `exp/results.json` 으로 집계하고 보고서 수치는 이 파일에서만 읽는다. 하드웨어·버전 명시.
- 모델·대용량 다운로드 전 사용자에게 용량을 알린다.
- 게이트: `check_research.py --assets <A> --stage final [--no-sample]` → PASS(measured missing 0 · bad_papers 0 · 그림 3+ · sample 코드+결과).

### 6. 그림 (자체 작성, matplotlib)
그림 1 원본(출처: 원저작자 · 사용자 첨부 이미지, 분석 목적 인용) · 그림 2 재구성 지형도(범주 × 항목, 라이선스·특징, 도식 밖 보완 항목 점선) ·
범주별 원리/파이프라인 그림 · 항목별 ★·라이선스 막대 · (실험 시) 지표 그래프 · 성숙도 로드맵. 한글 글꼴 등록(AppleGothic/Noto CJK).

### 7. 빌드
```bash
cp $SKILL_DIR/templates/deep/{build_report.py,report_config.py} "<Title>_assets/"
# report_config.py 채우기: TITLE_FILE(=<Title>)·제목·부제·태그라인·원본 출처·목적·방법·문서 구성 표·전사 절·CHAPTERS(조사 블록 배치)·결론·권고·원자료
WVS_KIT=$KIT "<Title>_assets/.venv/bin/python" "<Title>_assets/build_report.py" --pdf
```
장 구성(이전 분석 보고서와 동일): 표지 → 목차 → 1 개요 및 분석 방법 → 2 원문 도식 전수 정리 → 3.. 범주별(원리 → 항목별 9개 소제목 → 비교) →
도식 누락 보완 → 벤치마크·통합 비교 → (실측 실험) → 사용 및 활용용도 → 통합 구현 가이드 → 확장방안 → 라이선스·보안·거버넌스 →
도식 검증 종합(각 절 '도식 판정' 자동 수집) → 결론 및 권고 → 부록 A 논문(arXiv 검증) · B 저장소 실측표 · C 출처 · D 그림·이미지 출처.
그림 파일·조사 블록이 빠져도 빌드는 멈추지 않는다 — 해당 자리에 `[미확인]` 표시 후 docx/pdf 를 만들고 끝에 `WARN:` 목록을 출력하므로, WARN 을 채워 다시 빌드한다.
특수 장(실험·참조 구현 결과)은 `p_<name>.py` 를 만들고 CHAPTERS 항목에 `module="p_<name>"` 로 연결.

### 8. 검사
```bash
"$OUT/<Title>_assets/.venv/bin/python" $KIT/check_report.py "$OUT/<Title>.docx" --pdf "<…>.pdf" --render /tmp/ada_pages \
   --forbid "<형식 참고 문서명>" --min-h1 10 --min-pages 40 --min-tables 50
```
✅ PASS·빈 쪽 0. 쪽·표 하한 FAIL 이면 `check_research.py` 로 얕은 블록을 찾아 보강 후 재빌드(분량을 채우려 지어내지 않는다). 렌더 쪽을 열어 표 넘침·코드 잘림·그림 겹침 확인.
최종 보고: 경로·장 수·쪽 수·표 수·저장소/논문 검증 수·주요 도식 판정 5줄 + 호스트 능력·모드 + 게이트 결과(남은 FAIL·[미확인] 과 사유).

## 규칙
- 1차 출처 우선, 수치는 출처 병기, 추측 금지. 저장소는 gh api 실측값, 논문은 arXiv 존재 확인된 것만.
- **출처 명시 시 형식 참고용 이전 보고서는 제외**(부록 C 에도 넣지 않음).
- 도식의 부정확·과장·오탈자·누락은 근거와 함께 '도식 판정' 표로 지적(일치/부분일치/표기오류/해석주의/누락/과장).
- 공통 규칙은 references/kit.md §3.
