# 공통 툴킷 — scripts/ (구 wise-report-kit)


모드 repos · deep · prd 가 공통으로 쓰는 스크립트 모음이다. 단독으로도 쓸 수 있다.
경로: `SKILL_DIR/scripts/` (= `KIT`). 템플릿 빌드 스크립트는 `$WVS_KIT` → `~/.claude/skills` → `~/.agents/skills` → `~/.gemini/config/skills` → 프로젝트 `.claude/skills`·`.agents/skills` 의 `wvs-report/scripts` 순으로 KIT 를 찾는다.

## 0. 환경 준비 (처음 1회, 보고서마다 venv 하나)
```bash
KIT=<wvs-report>/scripts
bash $KIT/setup_env.sh <assets_dir>          # → <assets_dir>/.venv (python-docx · python-pptx · matplotlib · pymupdf), 마지막 줄 = venv python
gh auth status                               # 저장소 실측(gh api) — 미인증이면 익명 API(시간당 60회)로 폴백
command -v soffice || ls /Applications/LibreOffice.app   # PDF 변환
```
글꼴: macOS = Apple SD Gothic Neo(본문)·Menlo(코드), 그 외 = Noto Sans CJK KR (`WVS_FONT` 로 변경). 작성일 = 오늘(`WVS_DOC_DATE` 로 고정 가능).

## 1. 스크립트
| 스크립트 | 용도 | 사용 |
|---|---|---|
| `docx_lib.py` | 문서 템플릿 엔진 — `COVER` `H` `CH`/`SEC`(자동 장·절 번호) `P` `B` `N` `T` `W`(열 폭 비율) `KV` `CODE` `FIG`(자동 그림 번호 + 출처) `FIG_TABLE` `SAVE(out, pdf=True)` | 빌드 스크립트에서 `import docx_lib as r` |
| `md2docx.py` | 조사 원문(`research/r*.md`, `# KEY 제목` 블록 · `### 소제목`) → docx 렌더 (`load_all` `render` `subsections` `repos`) | `M.render(r, body, sub_level=3)` |
| `docx2pdf.sh` | docx/pptx → 같은 이름 .pdf (soffice headless, 특수문자 파일명 안전) | `bash docx2pdf.sh "A+B.docx"` |
| `gh_probe.py` | 저장소 실측 TSV(★·포크·SPDX·언어·아카이브·push·생성·브랜치·최신 릴리스·설명, 이전 감지) | `gh_probe.py list.txt -o repos.tsv [--col 3]` |
| `pkg_probe.py` | PyPI·npm·crates 최신 버전·업로드일·런타임 요구·라이선스 | `pkg_probe.py pkg_map.tsv -o packages.tsv` |
| `verify_sources.py` | research 의 REPOS·arXiv ID 실존 검증 → `measured.json`·`stats.py` | `verify_sources.py --assets <dir>` |
| `clone_repos.sh` | 매핑표대로 `<root>/<분류>/<도구>/` shallow clone(병렬·재실행 안전) + 크기 | `clone_repos.sh map.tsv <root> 6` |
| `make_trees.py` | 저장소별 compact 디렉토리 트리(깊이 2) → `trees.json` | `make_trees.py map.tsv <root> -o trees.json` |
| `out_dir.py` | 출력 폴더 결정 규칙 정본 — deep: `<root>/Miscellaneous-Data`, prd: `<root>/Need-to-be-organized-into-PRD` 가 있으면 그곳, 없으면 `<root>`, `--out-dir` 우선 | `OUT=$(out_dir.py deep --root <root>)` |
| `prd_intake.py` | PRD 입력 수집·분류(보고서·요구사항 문서·이미지·GitHub/사이트 URL·요청문) → `inputs/`·`inputs.json`·`_INPUTS.md`·`req_items.tsv`(RQ 추출) | `prd_intake.py req.md mock.png https://… --assets <dir> --prompt "…"` |
| `github_user_lists.py` | 사용자 Stars·Repositories 전수 → `stars_all.tsv`·`user_repos.tsv` | `github_user_lists.py WisemanLim -o research/` |
| `wire_lib.py` | PRD 와이어프레임 PNG(matplotlib) — `configure(brand, nav, …)` `frame()` 위젯·차트 `save()` | PRD 15.5 |
| `ui_lib.py` | 화면설계서 pptx(python-pptx) — `configure(system, nav, …)` `screen_slide(spec)` `Wire.shell()` | `<Brand>_UI_Design.pptx` |
| `check_research.py` | 조사 깊이 게이트(호스트 무관) — `_SPEC.md` 필수 절·사전 웹 확인 URL·판정 후보·조사 단위 표, 블록 분량·필수 소제목·소제목 분량·구현 코드·판정 표·출처 수, final: measured·그림·`sample/` 실행 결과 | `check_research.py --assets <A> [--stage spec\|research\|final] [--unit rN_x.md]` |
| `check_report.py` | 산출물 검사 — 장·표·그림 수, 금지 문자열(형식 참고 문서명), 필수 ID, PDF 빈 쪽, 쪽 PNG 렌더, `--min-pages`·`--min-tables` 분량 하한 | 빌드 후 반드시 |
| `check_ui_design.py` | 화면설계서 양식 게이트 — 슬라이드 순서(앞부속·PART 1 9절·PART 2·부록 A~F)·화면 밀도·콜아웃·표준 빌더 표식·`build_ui.py` 템플릿 동일성, PDF 빈 쪽·렌더 | `templates/prd/ui/pptx/build_ui.py` 가 자동 실행 |

## 2. 문서 양식(이전 보고서와 동일)
US Letter · 여백 2.0cm · Normal 10pt · H1 16pt 1F3864(새 쪽) · H2 13pt 2E74B5 · H3 11.5pt 404040 · 표 헤더 1F3864 흰 글씨 · 키-값 표 첫 열 DEEAF6 ·
코드 F5F5F5 Menlo 8pt · 그림 중앙 + "그림 N. 캡션 (출처)" 8.5pt 666666 · 표지(제목 28 / 부제 16 / 태그라인 11 / 작성일·출처·저장 위치) → 목차(H1·H2 자동, 하위 3개 이상은 한 줄로 묶음).
기존 문서를 템플릿으로 지정받으면 `pandoc <old>.docx -t gfm` 으로 장 구성만 확인하고 **출처에는 넣지 않는다**.

## 3. 공통 규칙 (repos · deep · prd 공통)
- **출처·라이선스·참고 이미지 항상 명시**: 원본 첨부 이미지는 그림 캡션 출처에 "원저작자 · 사용자 첨부 이미지, 분석 목적 인용", 저장소는 ★·SPDX 병기, 부록에 출처 총람·그림 출처(FIG_TABLE).
- **형식(템플릿) 참고용 이전 문서는 출처에서 제외** — `check_report.py --forbid "<이전 문서명>"` 으로 확인.
- 확인 못 한 사실 `[미확인]`, 업계 일반 가정 `[도메인]`. 존재 확인 안 된 저장소·논문은 쓰지 않는다(`verify_sources.py`).
- 한국어 본문, 고유명사·코드·명령·표준 용어는 원문 병기. 과장·홍보 문구·이모지 금지.
- 조사 서브에이전트는 블록(절) 하나 끝낼 때마다 파일에 저장 — 몰아 쓰다 중단되면 소실.
- 완료 전: `check_report.py <docx> --pdf <pdf> --render <dir>` → PASS + 렌더된 쪽을 직접 열어 겹침·넘침·빈 쪽 확인. `deep` 은 `check_research.py` 게이트도 PASS(`references/host-compat.md`).
- 서브에이전트가 없는 호스트는 순차 모드 — 조사 단위 하나씩 쓰고 단위 게이트 후 다음으로. 템플릿 요약·압축 금지.
