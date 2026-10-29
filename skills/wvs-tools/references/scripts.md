> **wvs 대응**: 아래 원본 사용 예의 `./<script>.sh` 는 `scripts/wvs <task>` 로 실행한다 — archive-tgz.sh→`wvs archive` · cleanup-meta.sh→`wvs clean` · chrome-bookmarks-dedup.sh→`wvs bookmarks` · convert2pdf.sh→`wvs pdf` · deploy-ios-testflight.sh→`wvs deploy ios` · deploy-android-play.sh→`wvs deploy android` · dist-ss-tui.sh→`wvs dist` · dist-standard-service.sh→`wvs dist --classic`. 스크립트 파일은 `scripts/lib/` 에 있다.

# .ref-sh 쉘 스크립트 모음

범용 배포·빌드·유틸리티 스크립트 모음입니다.
macOS / Linux (Debian·Fedora/RHEL·Arch) 를 기본 지원합니다.

---

## 배포 부트스트랩

> 상세 문서: [README-dss.md](README-dss.md)

| 스크립트 | 방식 | 특징 |
|----------|------|------|
| `dist-standard-service.sh` | CLI (대화형) | `-I` 로 저장소 지정 필수, gh auth 통합 |
| `dist-ss-tui.sh` | 전체 화면 TUI | 방향키 메뉴, PAT/gh/no-auth 선택, 더블 Ctrl+C 강제종료 |

---

## 앱 배포

### deploy-ios-testflight.sh — iOS TestFlight 배포

```bash
./deploy-ios-testflight.sh /path/to/ios-project
./deploy-ios-testflight.sh /path/to/ios-project --reconfigure
./deploy-ios-testflight.sh /path/to/ios-project --reuse-archive
```

- 최초 1회: App Store Connect **API Key** 입력 (`.p8` 경로 / Key ID / Issuer ID)
  → `<root>/.deploy-ios.env` 저장, 이후 자동 재사용
- 빌드 번호 자동 +1 (`agvtool`)
- 빌드 설정(스킴·번들ID·버전) 자동 감지
- `--reuse-archive`: 재컴파일 없이 서명/업로드만 재시도
- 필요 환경: macOS + Xcode

> API Key 역할은 **Admin 또는 App Manager** 필요 (Developer 역할은 export 단계 오류)  
> 발급: App Store Connect → Users and Access → Integrations → App Store Connect API

### ExportOptions.plist

`deploy-ios-testflight.sh` 가 사용하는 Xcode archive export 설정 파일.  
`method: app-store`, `signingStyle: automatic` 기본값.

### deploy-android-play.sh — Android Google Play 배포

```bash
./deploy-android-play.sh /path/to/android-project
./deploy-android-play.sh /path/to/android-project --reconfigure
```

- 최초 1회: **서비스 계정 JSON 키** 경로 + 트랙 입력
  → `<root>/.deploy-android.env` 저장, 이후 자동 재사용
- `versionCode` 자동 +1
- 기본 트랙 `internal`
- 필요 환경: JDK, fastlane (없으면 자동 설치 시도), Play App Signing 등록된 앱

> 서비스 계정 키: Play Console → 사용자 및 권한 → Google Cloud 서비스 계정 JSON

**공통 주의사항**
- `.deploy-ios.env`, `.deploy-android.env` 는 자격증명 포함 → **git 커밋 금지** (`.gitignore` 추가 권장)
- 로그: `<root>/build/logs/`
- 외부 테스터 배포·심사는 업로드 후 콘솔에서 별도 진행

---

## 유틸리티

### archive-tgz.sh — tar.gz 아카이브 생성

```bash
./archive-tgz.sh [OPTIONS] <파일/디렉터리...>
./archive-tgz.sh -F output.tar.gz ./src
./archive-tgz.sh --split 2048m ./large-dir   # 2GB 단위 분할
./archive-tgz.sh --dry-run ./project          # 실제 압축 없이 목록만 확인
```

- GNU tar(`gtar`) 사용, macOS bash 3.2 호환
- `.DS_Store`, `node_modules`, `.git`, 빌드 아티팩트 등 자동 제외
- `--split <크기>`: 지정 크기 단위로 분할 아카이브 생성
- `--remove`: 아카이브 성공 후 원본 삭제
- `--dry-run`: 실행 없이 대상 목록만 출력

### chrome-bookmarks-dedup.sh — Chrome 북마크 중복 제거

```bash
./chrome-bookmarks-dedup.sh -i ~/Library/Application\ Support/Google/Chrome/Default/Bookmarks
./chrome-bookmarks-dedup.sh -i Bookmarks -o Bookmarks.clean --mode global
./chrome-bookmarks-dedup.sh -i Bookmarks --in-place --dry-run
```

- python3 기본 내장만 사용 (추가 설치 없음), macOS bash 3.2 호환
- 폴더 구조 유지, `type=url` 항목만 중복 검사
- `--mode folder`: 폴더 내 중복 제거 (기본) / `--mode global`: 전체 중복 제거
- `--key url-title`: URL + 제목 조합으로 중복 판단 (기본: URL만)
- `--normalize`: URL 정규화 후 비교 (trailing slash 등)
- `--in-place`: 원본 파일 덮어쓰기 (자동 `.bak` 백업)

### cleanup-meta.sh — OS 임시 파일/디렉터리 삭제

```bash
./cleanup-meta.sh [OPTIONS] [TARGET_DIR]
./cleanup-meta.sh ./project --dry-run
./cleanup-meta.sh . -y
```

- macOS bash 3.2 호환
- `.DS_Store`, `__pycache__`, `Thumbs.db` 등 OS 임시 파일 자동 포함
- `--dry-run`: 삭제 없이 대상 목록만 출력
- `-y, --yes`: 확인 없이 즉시 삭제

### convert2pdf.sh — Mermaid 포함 Markdown → PDF 변환

```bash
./convert2pdf.sh -I REPORT.md
./convert2pdf.sh --input docs/spec.md --cleanup
```

**파이프라인**

1. ` ```mermaid ``` ` 블록 추출 → `diagrams/dNN.mmd`
2. `@mermaid-js/mermaid-cli` (mmdc) 로 각 `.mmd` → `.png` 렌더링 (실패 시 원본 코드 폴백)
3. `<input>.rendered.md` 생성 (이미지 참조 포함)
4. `pandoc` + `xelatex` → PDF (Noto Sans CJK KR)
5. `--cleanup`: 중간 산출물 제거

필요 환경: Node.js + `@mermaid-js/mermaid-cli`, `pandoc`, `xelatex` (TeX Live/MacTeX)

| 종료 코드 | 의미 |
|-----------|------|
| 0 | 성공 |
| 1 | 사용자 오류 |
| 2 | 의존성 누락 |
| 3 | 파이프라인 실패 |
