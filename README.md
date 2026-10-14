# wise-Vibe-Skills

**코딩 에이전트용 Skill set — 3개 스킬, 1개 CLI.**
저장소 리뷰(레벨 실행) · 보고서/PRD 생성(모드 실행) · 개발 유틸리티(`wvs` CLI)를 표준 `SKILL.md` 폴더로 제공한다.
Claude Code, Claude Desktop, Codex, Cursor, Gemini CLI, Windsurf, Devin, OpenCode, Antigravity, GitHub Copilot CLI, Command Code, Grok Build, OMP, VS Code 에 설치된다.

[English README](README.en.md)

| 스킬 | 한 줄 요약 | 호출 예 (Claude Code) |
|---|---|---|
| **`wvs-review`** | 저장소 리뷰를 **레벨**로 — L1 구조 분석 · L2 +상용화(라이선스·보안·ISO 5230) · L3 +주니어/구현 가이드 · L4 +라인 단위 코드 리뷰, 스타 목록 일괄 분석 | `/wvs-review ./proj --level 2` |
| **`wvs-report`** | 보고서·PRD를 **모드**로 — `repos`(클론+Summary-Repos) · `deep`(첨부 도식 상세 분석) · `prd`(보고서 기반 PRD + 화면설계서) → docx/pdf | `/wvs-report deep` (이미지 첨부) |
| **`wvs-tools`** | 유틸리티 **단일 CLI** `wvs` — pdf · archive · clean · bookmarks · deploy ios/android · dist · doctor | `wvs pdf REPORT.md` |

---

## 목차
1. [빠른 시작](#1-빠른-시작)
2. [설치](#2-설치)
3. [사용법 — wvs-review](#3-사용법--wvs-review)
4. [사용법 — wvs-report](#4-사용법--wvs-report)
5. [사용법 — wvs-tools (`wvs` CLI)](#5-사용법--wvs-tools-wvs-cli)
6. [기본 제공 기능과 비교 · 대체 가능성](#6-기본-제공-기능과-비교--대체-가능성)
7. [구 버전(v0.1) 커맨드 대응](#7-구-버전v01-커맨드-대응)
8. [문제 해결 · FAQ](#8-문제-해결--faq)
9. [저장소 구조 · 개발 · 릴리스](#9-저장소-구조--개발--릴리스)
10. [참고 · 출처 · 라이선스](#10-참고--출처--라이선스)

---

## 1. 빠른 시작

```bash
# 1) 설치 — 감지된 에이전트 전부 + 터미널용 wvs CLI 링크  (저장소가 비공개면 2.1 의 gh api 명령 사용)
curl -fsSL https://raw.githubusercontent.com/WisemanLim/wise-Vibe-Skills/main/install.sh | bash -s -- --bin-dir ~/.local/bin

# 2) 실행 중인 에이전트를 새 세션으로 다시 시작

# 3) 사용 (Claude Code 예)
/wvs-review ./my-repo                     # 구조 분석 + 상용화 심층 분석 (기본 L2)
/wvs-report deep                          # 첨부 인포그래픽 → 상세 분석 보고서 docx/pdf
wvs pdf docs/REPORT.md                    # 터미널: Mermaid 포함 Markdown → PDF
```

다른 에이전트(Codex · Cursor · Gemini CLI 등)에서는 "**wvs-review 스킬로 ./my-repo 를 레벨 2로 분석해줘**"처럼 스킬 이름과 요청을 함께 말한다.
에이전트는 각 스킬의 `description` 을 보고 스킬을 고르며, `$ARGUMENTS` 를 치환하지 않는 에이전트에서도 요청문에서 인수를 읽도록 작성되어 있다.

---

## 2. 설치

### 2.1 방법 비교
| 방법 | 명령 | 언제 |
|---|---|---|
| **설치 스크립트** (권장) | `curl -fsSL https://raw.githubusercontent.com/WisemanLim/wise-Vibe-Skills/main/install.sh \| bash` | macOS · Linux · Windows(Git Bash/WSL). Node 불필요 |
| **npx** | `npx github:WisemanLim/wise-Vibe-Skills install` (npm 배포 후 `npx wise-vibe-skills@latest install`) | Node 18+ · Windows 기본 셸 포함 |
| **Claude Code 플러그인** | `/plugin marketplace add WisemanLim/wise-Vibe-Skills` → `/plugin install wise-vibe-skills@wise-vibe-skills` | Claude Code 만. 스킬 이름이 `/wise-vibe-skills:wvs-review` 로 네임스페이스됨 |
| **skills.sh** | `npx skills add WisemanLim/wise-Vibe-Skills` | skills CLI 사용자 |
| **Claude Desktop(채팅)** | `npx wise-vibe-skills zip` 또는 `install.sh --desktop-zip` → Settings › Capabilities › Skills 에서 `<skill>.zip` 업로드 | Desktop 채팅. 코드 실행 기능 활성화 필요 |
| **수동** | `git clone` 후 `skills/<name>/` 폴더를 에이전트 스킬 폴더로 복사 | 오프라인·사내망 |

**저장소가 비공개(private)이면** `raw.githubusercontent.com` 이 토큰 없는 `curl` 에 404 를 돌려준다(`gh auth login` 은 curl 에 적용되지 않음). 이때는 GitHub CLI 로 설치 스크립트를 받는다 — 스크립트가 본체도 `gh api` 로 내려받는다:

```bash
gh auth login        # 저장소 접근 권한이 있는 계정
gh api -H "Accept: application/vnd.github.raw" repos/WisemanLim/wise-Vibe-Skills/contents/install.sh | bash -s -- --bin-dir ~/.local/bin
# 또는
gh repo clone WisemanLim/wise-Vibe-Skills && cd wise-Vibe-Skills && ./install.sh --bin-dir ~/.local/bin
```

비공개 상태의 npx 는 git 이 인증될 때만 동작한다(`gh auth setup-git` 후 `npx github:WisemanLim/wise-Vibe-Skills install`). 모든 사용자가 `curl … | bash` 한 줄로 설치하게 하려면 저장소를 공개(public)로 전환한다.

### 2.2 설치 스크립트 옵션 (npx 도 동일)
| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--client <ids>` | `detected` | 쉼표 목록 · `all` · `detected`(감지된 에이전트, 없으면 Claude Code + 공유 폴더) |
| `--scope user\|project` | `user` | `project` = 현재 폴더의 `.claude/skills` · `.agents/skills` 에 설치(팀 저장소 공유용) |
| `--dir <path>` | — | 임의 스킬 폴더에 설치 |
| `--skills <list>` | 전체 | `wvs-review,wvs-report,wvs-tools` 중 선택 |
| `--bin-dir <dir>` | — | `wvs` CLI 심볼릭 링크 생성(예: `~/.local/bin`) |
| `--desktop-zip [dir]` | `~/Downloads/wise-vibe-skills-desktop` | Claude Desktop 업로드용 zip 생성(Claude Desktop 선택 시 자동) |
| `--ref <tag>` | `main` | 설치할 브랜치·태그(예: `v0.2.0`) |
| `--link` · `--source <path>` | — | 로컬 체크아웃에서 심볼릭 링크/복사(개발용) |
| `--force` | — | 이 설치기가 만들지 않은 같은 이름 폴더도 덮어쓰기 |
| `--dry-run` · `--list` · `--uninstall` · `-y` | — | 계획만 · 목록/감지 상태 · 제거 · 질문 없이 진행 |

```bash
curl -fsSL https://raw.githubusercontent.com/WisemanLim/wise-Vibe-Skills/main/install.sh | bash -s -- --list
curl -fsSL https://raw.githubusercontent.com/WisemanLim/wise-Vibe-Skills/main/install.sh | bash -s -- --client claude-code,codex,cursor -y
curl -fsSL https://raw.githubusercontent.com/WisemanLim/wise-Vibe-Skills/main/install.sh | bash -s -- --scope project --skills wvs-review
npx wise-vibe-skills doctor          # 에이전트 감지·설치 현황·필요 도구 점검
```

### 2.3 에이전트별 설치 위치
클라이언트별 개인 스킬 경로는 REA 설치기의 클라이언트 레지스트리(`morluto/rea` · `SupportedClients.ts`)를 따른다. 같은 경로는 한 번만 설치한다.

| `--client` | 에이전트 | user 범위 | project 범위 |
|---|---|---|---|
| `claude-code` | Claude Code | `${CLAUDE_CONFIG_DIR:-~/.claude}/skills` | `./.claude/skills` |
| `claude-desktop` | Claude Desktop | zip 업로드 + `~/.claude/skills`(Code 탭) | — |
| `antigravity` | Antigravity | `~/.gemini/config/skills` | `./.agents/skills` |
| `gemini-cli` | Gemini CLI | `${GEMINI_CLI_HOME:-~}/.agents/skills` | `./.agents/skills` |
| `codex` `cursor` `windsurf` `devin` `opencode` `copilot-cli` `commandcode` `grok-build` `omp` `vscode` | Codex · Cursor · Windsurf · Devin · OpenCode · GitHub Copilot CLI · Command Code · Grok Build · OMP · VS Code | `~/.agents/skills` (공유) | `./.agents/skills` |

목록에 없는 에이전트는 `--dir <그 에이전트의 스킬 폴더>` 로 설치한다.

### 2.4 업데이트 · 제거
```bash
# 업데이트 = 같은 명령 재실행(이전 설치본을 교체). 특정 버전: --ref v0.2.0
curl -fsSL https://raw.githubusercontent.com/WisemanLim/wise-Vibe-Skills/main/install.sh | bash -s -- -y
# 제거 (wvs CLI 링크까지)
curl -fsSL https://raw.githubusercontent.com/WisemanLim/wise-Vibe-Skills/main/install.sh | bash -s -- --uninstall --bin-dir ~/.local/bin -y
```
- 설치기는 각 스킬 폴더에 `.wise-vibe-skills` 표식을 남긴다. **표식이 있는 폴더만** 교체·삭제하고, 사용자가 만든 같은 이름 폴더는 건드리지 않는다(`--force` 로 강제).
- v0.1 스킬(구 11종)은 표식이 있으면 설치 시 자동으로 정리된다. `~/.claude/commands/` 의 구 슬래시 커맨드 파일은 경고만 하고 지우지 않는다.

### 2.5 요구 환경
| 기능 | 필요 도구 | 확인 |
|---|---|---|
| wvs-review | 없음(에이전트만). `--pdf` 시 wvs-tools pdf 툴체인 | — |
| wvs-report | `python3`(빌드 시 `<assets>/.venv` 에 python-docx · python-pptx · matplotlib · pymupdf 자동 설치), `git`, `gh`(`gh auth login` 권장 — 미인증 시 익명 API 시간당 60회), LibreOffice(`soffice`) | `npx wise-vibe-skills doctor` |
| wvs-tools pdf | md: `pandoc` · `xelatex`(BasicTeX/TeX Live) · `mmdc`(`npm i -g @mermaid-js/mermaid-cli`) · Noto Sans CJK KR / docx·pptx: LibreOffice | `wvs doctor` |
| wvs-tools 기타 | archive: GNU tar(`gtar`) · bookmarks: python3 · deploy ios: Xcode · deploy android: JDK + fastlane · dist: git · gh · Docker | `wvs doctor` |

---

## 3. 사용법 — wvs-review

저장소·소스 리뷰를 하나로 통합하고 **레벨로 깊이**를 고른다. 레벨은 누적이며 결과는 대상의 `.review/` 에 저장된다.

| 레벨 | 실행 파트 | 산출물 (`<target>/.review/`) |
|---|---|---|
| `--level 1` | structure — 목적·구조·스택·아키텍처·테스트·보안·문서·성숙도 8단계 | `REVIEW.md` |
| `--level 2` **(기본)** | + commercial — 라이선스 감사(AGPL·BUSL·GPL 전파), 보안, 커뮤니티, 상용 아키텍처, 법적·ISO 5230/OpenChain, 5단계 위험 등급 | + `REVIEW-InDepth.md` |
| `--level 3` | + guide — 한·영 병기 주니어 가이드·구현 가이드 | + `GUIDE4Junior.md` · `GUIDE4ImpMethod.md` |
| `--level 4` | + code — 독자 레벨 R0(비전공)~R4(아키텍트) 라인/블록 단위 코드 리뷰 | + `CODE-REVIEW-Lv<n>/` (INDEX · 디렉토리 요약 · 파일별 리뷰) |

| 옵션 | 설명 |
|---|---|
| `--only structure,commercial,guide,code` | 누적 없이 지정 파트만 |
| `--reader 0-4` | code 파트 독자 레벨(기본 2 = 3년 차 주니어 인수인계 수준) |
| `-O` / `--overall` | 다중 대상 집계 — 첫 대상 `.review/<name>/` 아래 대상별 폴더 + 종합 비교 |
| `--pdf` | 산출 MD → PDF |
| `--name` · `--out-dir` | 출력 이름 · 폴더 |
| `--include` · `--exclude` · `--max-files` · `--max-lines-per-file` · `--entry-only` | code 파트 범위 |
| `--stars <md> [--previous <md>] [--depth mass\|deep\|hybrid]` | 스타 목록 일괄 분석 — 카테고리·랭크 버킷, 증분 실행 |

```text
/wvs-review                                   현재 폴더 L2
/wvs-review ./proj --level 1 --pdf            구조 분석 + PDF
/wvs-review ./proj --only commercial          상용화(라이선스) 검토만
/wvs-review ./proj --level 3                  + 주니어·구현 가이드
/wvs-review ./src --only code --reader 0      비전공자용 라인 해설
/wvs-review ./a ./b -O                        두 프로젝트 비교
/wvs-review --stars stars.md --previous stars-old.md --depth hybrid
```

---

## 4. 사용법 — wvs-report

첨부 이미지·링크·보고서에서 docx(이전 보고서 양식: US Letter · Apple SD Gothic Neo/Noto CJK · 표지·자동 목차·표/그림 규격)와 PDF를 만든다.

### 4.1 모드
| 모드 | 입력 | 산출물 | 핵심 단계 |
|---|---|---|---|
| `repos` | 도구 목록 인포그래픽(이미지·링크) | `<root>/<Project>/NN-분류/도구/`(shallow clone) + `Summary-Repos.docx/.pdf` | 전사 → GitHub 매핑(이전 저장소 추적) → 실측(★·SPDX·릴리스·레지스트리) → 클론·트리 → 저장소별 조사 → 비교·선택 가이드·인포그래픽 검증 |
| `deep` | 범주·패키지·개념 도식 | `<root>/Miscellaneous-Data/<제목>.docx/.pdf` + `<제목>_assets/` | 전사 → 조사 사양 → 병렬 조사(정의·소스 repo·설치·사용·동작·성능·활용·확장) → 저장소·arXiv 검증 → (선택 실측 실험) → 도식 판정 종합 |
| `prd` | 분석 보고서 docx/pdf(+`_assets/`) | `<root>/Need-to-be-organized-into-PRD/<Brand>_<Phrase>_PRD.docx/.pdf` + `<Brand>_UI_Design.pptx/.pdf` | 도식 세부 항목 = 독립 배포 마이크로 에이전트 → FR(`FR-<단위>-NN`) → 유사 시스템 → GitHub stars/repos 교차 → UI/UX 와이어프레임 → 패키징·릴리스·Agent Manager → 누락 게이트 |

### 4.2 `{ }` 와 `[ ]`
요청문에서 `{ }` 는 **첨부에서 자동 추출**되는 값(제목·프로젝트명·문서명·범주), `[ ]` 는 **첨부에서 자동 도출**되어 분류·분석 축·장 구성·FR·화면을 이루는 세부 요구다. 직접 값을 주면 그 값이 우선한다.

```text
/wvs-report repos --root ~/wise-Analysis-Repos
  첨부이미지를 참고하여 {Python-Tools-for-AI-Projects} 프로젝트에 {각 분류의 세부 프로젝트}를 clone 하고
  디렉토리 구조·사용방법·활용분야/범위 요약 보고서 Summary-Repos.docx 를 작성 후 pdf 변환
  (일부 분류만: --categories "Model & Data Security, Data Visualization")

/wvs-report deep --root ~/wise-Analysis-Repos
  첨부이미지는 {OCR+PDF Extractors} 관련 문서로 [Native PDF·OCR Engines·Document Parsers·VLM+Specialists 구성 비교]를 …
  [각 패키지의 정의·소스repo·설치/환경설정·사용방법·동작방식·활용용도·확장방안] 을 포함한 분석 보고서 (+ --experiment 로 실측 장)

/wvs-report prd "9AI-Concepts-That-Put-You-Ahead-of-99%-in-2026" --github-user WisemanLim
  {분석 보고서} 기반 요구사항·개발방향 → {'The map behind production AI Systems'} 를 반영한 문서명의 PRD (+ 화면설계서, --ui-pptx false 로 끔)
```

### 4.3 공통 규칙
- 출처·라이선스·참고 이미지를 항상 명시한다(그림 캡션 출처, 저장소 ★·SPDX, 부록 출처 총람·그림 출처).
- **형식(템플릿) 참고용 이전 문서는 출처에서 제외**한다 — 빌드 후 `check_report.py --forbid` 로 검사.
- 확인 못 한 사실은 `[미확인]`, 실존 확인 안 된 저장소·논문은 싣지 않는다(`gh_probe.py`, `verify_sources.py`).
- 완료 전 산출물 검사(빈 쪽·필수 ID·금지 문자열)와 쪽 렌더 확인을 한다. 흐름: `deep` 결과를 `prd` 입력으로 쓴다.

---

## 5. 사용법 — wvs-tools (`wvs` CLI)

에이전트에서는 `/wvs-tools <작업>` 으로, 터미널에서는 `wvs <작업>` 으로 쓴다(`--bin-dir` 로 링크했거나 `<스킬폴더>/wvs-tools/scripts/wvs` 직접 실행).

| 작업 | 설명 | 예 |
|---|---|---|
| `pdf` | `.md`(Mermaid → PNG 렌더, pandoc + xelatex, 한글 글꼴) / `.docx`·`.pptx`(LibreOffice) → 같은 이름 PDF | `wvs pdf REPORT.md -C` · `wvs pdf "A+B.docx"` |
| `archive` | tar.gz 생성 — 기본 제외 규칙, `--split 2048m`, `--remove`, `--dry-run` | `wvs archive -o out.tar.gz ./src ./docs` |
| `clean` | `.DS_Store`·`__pycache__`·`Thumbs.db` 등 정리, 사용자 패턴 `-D/-F/-E` | `wvs clean . --dry-run` |
| `bookmarks` | Chrome 북마크 중복 제거(폴더/전역, URL 정규화, `--in-place` 시 .bak) | `wvs bookmarks -i Bookmarks --dry-run` |
| `deploy ios` | Xcode archive → TestFlight 업로드, 빌드 번호 자동 +1 | `wvs deploy ios ./app` |
| `deploy android` | Gradle → Google Play(fastlane), versionCode +1 | `wvs deploy android ./app` |
| `dist` | 표준 서비스 배포 부트스트랩(저장소 동기화·Docker·compose·Makefile) — TUI, `--cli`, `--no-run`, 구 판 `--classic` | `wvs dist -I "<url1> <url2>" --cli` |
| `doctor` · `list` · `help <작업>` | 도구 점검 · 작업↔스크립트 · 원본 스크립트 도움말 | `wvs help archive` |

삭제·업로드·덮어쓰기 작업은 스킬이 먼저 `--dry-run` 결과를 보여 주고 확인을 받는다. 자격증명(`.deploy-*.env`, `*.p8`, 서비스 계정 JSON)은 `.gitignore` 로 커밋을 막는다.

---

## 6. 기본 제공 기능과 비교 · 대체 가능성

에이전트·서비스에 이미 비슷한 기본 기능이 있으면 그것을 써도 된다. 아래 표로 **무엇이 대체되고 무엇이 이 Skill set 에만 있는지** 보고 고른다.
(2026-10 기준. 기본 기능은 버전마다 바뀌므로 각 에이전트의 `/help` 로 확인한다.)

| 이 Skill set | 기본 제공 대안 | 대체 가능성 | 선택 기준 |
|---|---|---|---|
| `wvs-tools pdf` (md → PDF) | Claude: Anthropic **`pdf` 스킬**(PDF 생성·병합·분할·추출·양식, Claude.ai/Desktop 기본 제공, Claude Code 는 `/plugin marketplace add anthropics/skills`) · Gemini CLI · Codex · Copilot CLI: 전용 명령 없음(에이전트가 pandoc 등 직접 실행) | **부분** | 일반 PDF 생성·편집은 `pdf` 스킬로 충분. **Mermaid 다이어그램 렌더 + 한글(CJK) 글꼴 + xelatex 출판 품질 + 툴체인 점검·안내 설치**가 필요하면 `wvs pdf` |
| `wvs-tools pdf` (docx/pptx → PDF) | Anthropic **`docx`·`pptx` 스킬**(문서 생성·편집) · LibreOffice `soffice --convert-to pdf` | **대체 가능** | 변환만이면 어느 쪽이든 같다. `wvs pdf` 는 특수문자 파일명·격리 프로필 처리를 해 준다 |
| `wvs-review` L1 structure | Claude Code `/init`(CLAUDE.md) · Codex `/init`(AGENTS.md) · Gemini CLI `/init`(GEMINI.md) | **부분** | `/init` 은 에이전트용 **컨텍스트 파일**. 사람이 읽는 8단계 분석 **보고서**(다중 비교·PDF)가 필요하면 L1 |
| `wvs-review` L2 commercial | Claude Code `/security-review` · Gemini CLI security 확장(`/security:analyze`) · Copilot 앱 `/security-review` | **부분(보안 항목만)** | 기본 기능은 **취약점** 위주. **라이선스 감사·GPL/AGPL 전파·ISO 5230·상용화 위험 등급**은 L2 에만 있다 |
| `wvs-review` L3 guide | `/init` 류 컨텍스트 파일 | **부분** | 사람용 **한·영 온보딩·구현 가이드**가 필요하면 L3 |
| `wvs-review` L4 code | Claude Code `/review`·`code-review` 스킬 · Codex `/review` · Copilot CLI `/review` · Cursor `/review`(Bugbot, 3.7+) · Gemini CLI code-review 확장 · GitHub PR 리뷰 | **부분** | 기본 기능은 **변경분(diff) 결함 탐지**. **전체 코드를 독자 레벨(R0~R4)로 해설하는 교육·인수인계 문서**는 L4. PR 게이트에는 기본 기능 권장 |
| `wvs-review --stars` | 없음 | **불가** | 스타 수백~수천 개 일괄 분석·증분 처리 |
| `wvs-report repos` / `deep` | Claude **Research** · Gemini **Deep Research** 등 웹 조사 보고서 | **부분(조사 단계)** | 조사 요약만이면 대체 가능. **저장소 클론·디렉토리 트리·GitHub/레지스트리/arXiv 실측 검증·도식 판정·기존 양식 docx/pdf**는 wvs-report 에만 있다 |
| `wvs-report prd` | PRD 템플릿 스킬·플러그인 · Anthropic `docx`/`pptx` 스킬(문서 형식) | **부분** | 일반 PRD 초안이면 대체 가능. **도식 → 마이크로 에이전트 분해, FR↔화면 100% 추적 게이트, stars/repos 교차, 화면설계서 pptx**는 wvs-report prd |
| `wvs-tools archive` · `clean` | `tar` · `find … -delete` | **대체 가능** | 제외 규칙·분할·dry-run 을 한 번에 원하면 `wvs` |
| `wvs-tools bookmarks` | 브라우저 확장·수동 정리 | **대체 가능** | 폴더 구조 유지·백업·dry-run 이 필요하면 `wvs` |
| `wvs-tools deploy` | fastlane(`pilot`·`supply`) · Xcode Cloud · Gradle Play Publisher | **대체 가능** | 이미 CI/CD 가 있으면 기존 도구. 로컬에서 한 줄 업로드면 `wvs deploy` |
| `wvs-tools dist` | `gh repo clone` + `docker compose` 직접 실행 | **대체 가능** | 다수 저장소 동기화·compose 선택·Makefile 생성을 대화형으로 하려면 `wvs dist` |

---

## 7. 구 버전(v0.1) 커맨드 대응

| 구 커맨드 | 새 호출 |
|---|---|
| `/analysis-source <p>` | `/wvs-review <p> --level 1` |
| `/in-depth-review <p>` | `/wvs-review <p> --only commercial` (구조 분석과 함께: `--level 2`) |
| `/create-guide4junior <p>` | `/wvs-review <p> --only guide` |
| `/code-review-by-levels <p> --level N` | `/wvs-review <p> --only code --reader N` |
| `/totally-analysis-based-on-star --input f.md` | `/wvs-review --stars f.md` |
| `/convert-to-pdf -I X.md` | `/wvs-tools pdf X.md` · `wvs pdf X.md` |
| `ref-sh` 스크립트 8종 | `wvs archive · clean · bookmarks · pdf · deploy ios/android · dist [--classic]` |
| `/oss-clone-analysis` · `/attachment-deep-analysis` · `/requirement-based-prd` | `/wvs-report repos` · `/wvs-report deep` · `/wvs-report prd` |
| `wise-report-kit` | `wvs-report/scripts/` (스킬 내부 툴킷) |

구 옵션 이름(`--review-result`, `--pdf true|false`, `-O`)은 그대로 받는다.

---

## 8. 문제 해결 · FAQ

| 증상 | 해결 |
|---|---|
| 스킬이 목록에 안 보임 | 에이전트를 **새 세션**으로 재시작. `npx wise-vibe-skills doctor` 로 설치 위치 확인. 목록에 없는 에이전트는 `--dir` |
| `curl … install.sh` 404 | 저장소가 비공개(또는 미배포). curl 은 gh 인증을 쓰지 않는다 → 2.1 의 `gh api … install.sh \| bash` 또는 `gh repo clone` 후 `./install.sh` |
| `/analysis-source` 등 구 커맨드가 중복 표시 | `~/.claude/commands/<구 이름>.md` 를 직접 삭제(설치기는 경고만 함) |
| `wvs-report/scripts 를 찾을 수 없습니다` | 빌드 스크립트가 툴킷을 못 찾음 → `export WVS_KIT=<스킬폴더>/wvs-report/scripts` |
| GitHub 실측이 느리거나 실패 | `gh auth login`(인증 시 시간당 5,000회). 미인증 익명 API 는 시간당 60회 |
| PDF 변환 실패(docx) | LibreOffice 설치: macOS `brew install --cask libreoffice` · Debian `sudo apt-get install -y libreoffice-writer libreoffice-impress` |
| PDF 한글 깨짐 | Noto Sans CJK KR 설치 또는 `WVS_FONT="<글꼴명>"` |
| Windows 에서 `wvs` | Git Bash/WSL 에서 `bash <스킬폴더>/wvs-tools/scripts/wvs …` |

---

## 9. 저장소 구조 · 개발 · 릴리스

```
install.sh                       curl | bash 설치기 (bash 3.2 호환, 잘림 방지 가드)
bin/wise-vibe-skills.mjs         npx 설치기 (install · uninstall · list · doctor · zip), 의존성 없음
.claude-plugin/                  Claude Code 플러그인·마켓플레이스 매니페스트
skills/
├── wvs-review/   SKILL.md · references/{structure,commercial,guide,code,bulk-stars}.md
├── wvs-report/   SKILL.md · references/{repos,deep,prd,kit,…}.md · scripts/(docx 엔진·검증·클론·와이어프레임·pptx·검사) · templates/{repos,deep,prd}/
└── wvs-tools/    SKILL.md · references/{pdf,scripts,dist}.md · scripts/wvs · scripts/lib/*.sh
tests/                           run.sh · validate_skills.py · smoke_kit.py
```

- **설계**: `SKILL.md` 는 짧은 라우터(레벨·모드·작업 선택)이고, 세부 절차는 해당 파트를 실행할 때만 `references/` 에서 읽는다(필요한 만큼만 컨텍스트 사용).
- **테스트**: `bash tests/run.sh` — 메타데이터·문법·shellcheck·설치기 bash/npx 경로 동일성·설치/구 버전 정리/제거·bin 링크·zip·`wvs` 디스패치·보고서 툴킷 스모크 빌드(docx/pptx/pdf). `WVS_TEST_PY=<venv python>` 으로 venv 재사용.
- **업로드 제외**: `.gitignore` 가 OS 파일(.DS_Store·Thumbs.db), 개인 개발 환경(.vscode·.idea·*.code-workspace·.env·.venv), 에이전트 세션·대화 기록(.claude/·.codex/·.gemini/·.cursor/·.omc/·*.jsonl·sessions/), 리뷰/보고서 산출물(.review/), 서명·자격증명(*.p8·*.keystore·서비스 계정 JSON)을 제외한다. `.gitattributes` 로 셸 스크립트 LF 를 고정한다.
- **릴리스**: `VERSION` · `package.json` · `.claude-plugin/*.json` · `wvs` 의 `VERSION` 을 함께 올림 → `bash tests/run.sh` → 커밋 → `git tag vX.Y.Z && git push --tags` → (선택) `npm publish`.

---

## 10. 참고 · 출처 · 라이선스
- 설치 방식 참고: [REA — Get started](https://rea.tools/get-started/), [morluto/rea](https://github.com/morluto/rea) (`install.sh`, `docs/installation.md`, `src/application/SupportedClients.ts`)
- 기존 스킬 원본: [WisemanLim/expired-wise-skills](https://github.com/WisemanLim/expired-wise-skills) `commands/`
- 기본 기능 비교 근거: [Claude Code slash commands](https://code.claude.com/docs/en/commands) · [anthropics/skills](https://github.com/anthropics/skills) · [Codex CLI slash commands](https://developers.openai.com/codex/cli/slash-commands) · [Gemini CLI commands](https://geminicli.com/docs/reference/commands) · [Gemini CLI code review·security 확장 codelab](https://codelabs.developers.google.com/gemini-cli-code-analysis) · [GitHub Copilot CLI command reference](https://docs.github.com/en/copilot/reference/cli-command-reference) · [Cursor Bugbot](https://docs.cursor.com/bugbot)
- 라이선스: 아직 지정하지 않았다. 공개 배포 전에 `LICENSE` 파일을 추가한다. `wvs-tools/scripts/lib/` 의 스크립트와 템플릿이 생성하는 문서의 출처 표기 규칙은 각 스킬 문서를 따른다.
