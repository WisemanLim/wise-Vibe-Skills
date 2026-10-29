---
name: wvs-tools
description: "개발 유틸리티 통합 스킬 — 단일 CLI `scripts/wvs task` 로 실행: pdf(Markdown+Mermaid → PDF, docx/pptx → PDF, 구 convert-to-pdf) · archive(tar.gz 분할 압축) · clean(.DS_Store 등 OS 임시 파일 정리) · bookmarks(Chrome 북마크 중복 제거) · deploy ios|android(TestFlight·Google Play 업로드) · dist(표준 서비스 배포 부트스트랩 TUI/CLI) · doctor. 구 ref-sh 스크립트 모음. Unified dev utility CLI. Use for 'PDF 변환', '압축', '임시 파일 정리', '북마크 중복 제거', 'TestFlight/Play 배포', '서비스 배포 부트스트랩'."
---

# wvs-tools — 개발 유틸리티 통합 CLI

Arguments: $ARGUMENTS
> 호스트가 `$ARGUMENTS` 를 치환하지 않는 에이전트에서는 사용자 요청문에서 작업(task)과 인수를 추출한다.

진입점: `SKILL_DIR/scripts/wvs <task> [args…]` (`SKILL_DIR` = 이 SKILL.md 디렉토리). 스크립트 원본은 `scripts/lib/`.
설치기 `--bin-dir ~/.local/bin` 옵션을 쓰면 터미널에서 `wvs` 로 바로 실행된다.

## 1. 작업
| task | 하는 일 | 대표 사용 | 상세 |
|---|---|---|---|
| `pdf` | `.md`(Mermaid 렌더 → pandoc+xelatex, Noto Sans CJK KR) / `.docx`·`.pptx`(LibreOffice) → 같은 이름 PDF | `wvs pdf REPORT.md -C` · `wvs pdf "A+B.docx"` | `references/pdf.md` |
| `archive` | tar.gz 아카이브 — 제외 규칙(.git·node_modules·빌드 산출물), `--split 2048m`, `--remove`, `--dry-run` | `wvs archive -F out.tar.gz ./src` | `references/scripts.md` |
| `clean` | `.DS_Store`·`__pycache__`·`Thumbs.db` 등 정리, `-D/-F/-E` 패턴, `--dry-run`, `-y` | `wvs clean . --dry-run` | 〃 |
| `bookmarks` | Chrome 북마크 중복 제거(폴더/전역, url/url-title, 정규화, `--in-place` 시 .bak) | `wvs bookmarks -i Bookmarks --dry-run` | 〃 |
| `deploy ios` | Xcode archive → TestFlight 업로드, 빌드 번호 +1, API Key 1회 설정(`.deploy-ios.env`) | `wvs deploy ios ./app` | 〃 |
| `deploy android` | Gradle → Google Play(fastlane), versionCode +1, 기본 트랙 internal | `wvs deploy android ./app` | 〃 |
| `dist` | 표준 서비스 배포 부트스트랩 — 저장소 동기화·Docker·compose·Makefile. TUI(기본) / `--cli` / `--no-run`, 구 CLI 판은 `--classic` | `wvs dist -I "<url1> <url2>" --cli` | `references/dist.md` |
| `doctor` · `list` · `help <task>` | 도구 점검 · 작업→스크립트 표 · 스크립트 도움말 | `wvs doctor` | — |

## 2. 실행 규칙
1. 처음 쓰는 작업은 `wvs help <task>` 로 옵션을 확인하고, 필요한 도구는 `wvs doctor` 로 점검한다. `pdf` 툴체인이 없으면 `references/pdf.md` 의 점검·안내 설치 절차를 따른다(설치는 도구별로 사용자 확인 후).
2. 삭제·덮어쓰기·업로드는 대상과 변경 내용을 확인하고 사용자가 승인한 범위에서 실행한다. `clean`·`archive`·`bookmarks`는 `--dry-run`으로 확인한다. `deploy`는 dry-run을 지원하지 않으므로 배포 설정·대상·버전 변경을 검토한다. `dist --no-run`도 저장소 동기화·파일 생성을 수행할 수 있어 무변경 미리보기로 취급하지 않는다. `bookmarks`는 `-o`가 없으면 기본 동작도 원본을 교체한다.
3. 자격증명 파일(`.deploy-ios.env`, `.deploy-android.env`, `*.p8`, 서비스 계정 JSON)은 git 에 커밋하지 않도록 `.gitignore` 를 확인한다.
4. 출력·오류는 그대로 인용하고, 종료 코드를 보고한다(pdf: 0 성공 · 1 인수 오류 · 2 의존성 누락 · 3 파이프라인 실패).

## 3. 구 커맨드 대응
| 구 커맨드·스크립트 | 새 호출 |
|---|---|
| `/convert-to-pdf -I X.md` · `convert2pdf.sh -I X.md` | `wvs pdf X.md` |
| `archive-tgz.sh` · `cleanup-meta.sh` · `chrome-bookmarks-dedup.sh` | `wvs archive` · `wvs clean` · `wvs bookmarks` |
| `deploy-ios-testflight.sh` · `deploy-android-play.sh` | `wvs deploy ios` · `wvs deploy android` |
| `dist-ss-tui.sh` · `dist-standard-service.sh` | `wvs dist` · `wvs dist --classic` |
| wvs-report 의 `docx2pdf.sh` | `wvs pdf X.docx` (같은 스크립트) |
