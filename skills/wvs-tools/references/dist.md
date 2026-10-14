> **wvs 대응**: 아래 원본 사용 예의 `./<script>.sh` 는 `scripts/wvs <task>` 로 실행한다 — archive-tgz.sh→`wvs archive` · cleanup-meta.sh→`wvs clean` · chrome-bookmarks-dedup.sh→`wvs bookmarks` · convert2pdf.sh→`wvs pdf` · deploy-ios-testflight.sh→`wvs deploy ios` · deploy-android-play.sh→`wvs deploy android` · dist-ss-tui.sh→`wvs dist` · dist-standard-service.sh→`wvs dist --classic`. 스크립트 파일은 `scripts/lib/` 에 있다.

# Dist-Standard-Service 시리즈 — 상세 문서

범용 저장소 + Docker Compose 배포 부트스트랩.  
동일한 배포 파이프라인을 **CLI(대화형)** 과 **REPL 인터랙티브 셸** 두 가지 인터페이스로 제공합니다.

| | `dist-standard-service.sh` | `dist-ss-tui.sh` |
|---|---|---|
| 인터페이스 | CLI 대화형 (번호 메뉴) | REPL 커맨드 셸 (자동완성) |
| 저장소 지정 | `-I` 필수 | `/repo` 명령 또는 `-I` 사전 지정 |
| 저장소 관리 | 단순 URL 입력 | CRUD + 순서 변경 |
| 인증 | gh auth 전용 | gh / PAT / 없음 선택 |
| 커맨드 히스토리 | ✗ | ✓ (↑↓ 방향키) |
| 자동완성 | ✗ | ✓ (`/` 입력 시 메뉴) |
| CLI 모드 | ✗ | ✓ (`--cli` 플래그) |
| 종료 | Ctrl+C | `/exit` 또는 Ctrl+C×2 |
| 상태 저장 | `.dist-standard.conf` | `.dist-standard.conf` |

---

## dist-standard-service.sh — CLI 버전

### 사용법

```bash
# 기본
./dist-standard-service.sh -I "https://github.com/org/svc-a https://github.com/org/svc-b"

# 모든 옵션 지정
./dist-standard-service.sh \
  --input "git@github.com:org/ops.git git@github.com:org/api.git" \
  --workspace ~/work \
  --ops ops

# ops 저장소만 단독 클론
./dist-standard-service.sh -I git@github.com:org/ops.git --no-run
```

### 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `-I, --input <repos>` | 공백 구분 git 저장소 URL **(필수)** | — |
| `-w, --workspace <dir>` | clone 대상 디렉터리 | 실행 중 대화형 선택 |
| `-o, --ops <name>` | Makefile/compose 보유 저장소 이름 | compose 파일이 있는 첫 번째 저장소 |
| `--no-run` | compose 실행 메뉴 건너뜀 | — |
| `-h, --help` | 도움말 출력 | — |

### 실행 흐름

```
1. 인수 파싱 → workspace 결정
      ├─ -w 지정 시: 즉시 사용
      └─ 생략 시: 대화형 선택
             1) 현재 디렉터리 [기본값]
             2) 상위 디렉터리
             3) 사용자 지정 경로

2. OS 감지 → 도구 설치
      git / gh / docker / make / node / python3 없으면 자동 설치

3. gh auth 확인
      이미 로그인: 유지 / 재로그인 / 계정 전환 선택
      미로그인: gh auth login 실행

4. 저장소 clone / pull (INPUT_REPOS 순서대로)
      기존 .git 디렉터리 → fetch + pull --ff-only
      없음 → git clone

5. ops 디렉터리 결정 (-o 또는 자동)
      compose 파일 보유 저장소 우선, 없으면 첫 번째

6. Makefile 없으면 자동 생성 (docker-compose*.yml 기반)

7. Pre-run 커맨드 루프
      예: cp .env.example .env
      빈 Enter → 다음 단계

8. make 타겟 선택 및 실행
      up-* 타겟 우선 표시, 없으면 전체 타겟
      c) 커스텀 타겟 직접 입력
      마지막 선택 .dist-standard.conf 에 저장

9. docker group 활성화 (Linux 신규 설치 시)
      1) sg docker 서브셸 실행 (권장)
      2) 활성화 방법 안내
      3) 건너뜀
```

---

## dist-ss-tui.sh v3.0 — REPL 인터랙티브 버전

커맨드 입력 방식의 인터랙티브 셸. 자동완성·히스토리·저장소 매니저 내장.

### 사용법

```bash
# REPL 모드 (기본)
./dist-ss-tui.sh

# 저장소 사전 지정 (나머지는 REPL에서 설정)
./dist-ss-tui.sh -I "https://github.com/org/svc-a https://github.com/org/svc-b"

# 주요 설정 사전 지정
./dist-ss-tui.sh -I "git@github.com:org/ops.git" -w ~/work -o ops

# 비대화형 CLI 모드
./dist-ss-tui.sh -I "git@github.com:org/ops.git" --cli

# CLI dry-run (배포 없이 저장소 동기화만)
./dist-ss-tui.sh -I url --no-run
```

### 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `-I, --input <repos>` | 공백 구분 git 저장소 URL | REPL에서 `/repo` 로 입력 |
| `-w, --workspace <dir>` | clone 대상 디렉터리 | REPL에서 `/workspace` 로 선택 |
| `-o, --ops <name>` | ops 저장소 이름 | 자동 감지 |
| `-c, --cli` | 비대화형 CLI 모드 강제 | — |
| `--no-run` | 배포 실행 건너뜀 (CLI 모드) | — |
| `-h, --help` | 도움말 출력 | — |

### REPL 커맨드

| 커맨드 | 단축키 | 설명 |
|--------|--------|------|
| `/repo [url...]` | `/R` | 저장소 관리 (추가/삭제/순서변경) 또는 URL 직접 지정 |
| `/workspace [path]` | `/W` | clone 디렉터리 설정 또는 메뉴 선택 |
| `/auth [gh\|pat\|none]` | `/A` | 인증 방식 설정 또는 메뉴 선택 |
| `/bootstrap` | `/B` | 도구 설치 + 저장소 동기화 |
| `/status` | `/S` | 현재 설정 상태 표시 |
| `/dist-run` | `/D` | 검증 → 타겟 선택 → 배포 실행 |
| `/help` | `/H` | 도움말 표시 |
| `/exit` | `/E` | 종료 + 캐시 삭제 |
| `! <command>` | — | 셸 명령 실행 후 결과 출력 |

### REPL 키 조작

| 키 | 동작 |
|----|------|
| `↑` / `↓` | 커맨드 히스토리 탐색 |
| `←` / `→` | 커서 이동 |
| `Delete` | 커서 앞 문자 삭제 |
| `/` 로 시작 입력 | 자동완성 메뉴 (↑↓ 탐색, Enter 선택) |
| `ESC` | 자동완성 닫기 |
| `↑` / `↓` (자동완성 중) | 자동완성 항목 탐색 |

### 일반적인 사용 순서

```
1. ./dist-ss-tui.sh 실행

2. /repo                     # 저장소 추가
   > Add Repository
   > Enter Repo URL: https://github.com/org/ops.git
   > Save & Exit

3. /workspace                # clone 위치 선택
   > Current dir  →  /home/user/project

4. /auth                     # 인증 방식 선택
   > gh auth login — GitHub CLI (권장)

5. /dist-run                 # 자동 bootstrap → 타겟 선택 → 배포
   > (Bootstrap 자동 실행)
   > Make Target: up
   > Pre-run 명령어: (빈 Enter 2회 → 건너뜀)
   > Deploy? ▶ Run Now
```

`/dist-run` 은 bootstrap 미완료 시 자동으로 실행합니다.  
각 단계를 수동 제어하려면 `/bootstrap` → `/dist-run` 순서로 실행하세요.

### /repo — 저장소 매니저

```
━━ Repository Manager ━━
  1) https://github.com/org/ops.git
  2) https://github.com/org/api.git

  Actions
  ▶ Add Repository
    Delete Repository
    Clear All
    Change Order (Reorder)
    Save & Exit
    Cancel & Discard
```

- **Add**: URL 입력 (최대 8개)
- **Delete**: 목록에서 선택 삭제
- **Clear All**: 전체 삭제 (확인 후)
- **Change Order**: ↑↓ 드래그로 순서 변경

#### 직접 지정 (인수 전달)

```bash
# 명령줄 인수
./dist-ss-tui.sh -I "url1 url2"

# REPL 내 인수 전달
/repo https://github.com/org/ops.git https://github.com/org/api.git
```

### /status — 설정 상태

```
━━ dist-ss-tui Configuration Status ━━
  Workspace : /home/user/project          ← 설정됨 (녹색)
  Repos     : [NOT SET]                   ← 미설정 (빨강)
  Auth      : gh                          ← 설정됨
  Ops Repo  : [NOT SET]                   ← /bootstrap 시 자동 감지
  Bootstrap : [PENDING]                   ← 미완료 (노랑)
```

### /auth — 인증 방식

#### gh auth login

- `gh` 없으면 `/bootstrap` 시 자동 설치
- 이미 로그인 시: 유지 / 재로그인 / 계정 전환 선택

#### Access Token (PAT)

- 마스킹 입력 (`read -s`)
- SSH URL → HTTPS 자동 변환 (`git@github.com:org/repo` → `https://github.com/org/repo`)
- `mktemp` 임시 credential 파일 생성 (`chmod 600`)
- `git -c credential.helper=store --file=<tmpfile>` 로 주입
- EXIT 트랩에서 자동 삭제
- PAT 발급: GitHub → Settings → Developer settings → Personal access tokens  
  최소 권한: **Contents → Read-only**

#### No auth

공개 저장소 전용. gh 설치·로그인 불필요.

### 세션 캐시

경로: `/tmp/.dist-ss-tui-<UID>.cache`  
히스토리: `/tmp/.dist-ss-tui_history`

- 각 커맨드 실행 후 자동 저장 (저장소·workspace·인증방식·타겟·bootstrap상태)
- 다음 실행 시 자동 로드
- **삭제 조건**: 정상 완료(`/dist-run` 성공) / Ctrl+C×2 / `/exit`

### 종료 방법

| 상황 | 종료 방법 | 캐시 |
|------|-----------|------|
| REPL 프롬프트 | `/exit` 또는 `/E` | 삭제 |
| 메뉴 중 | `q` 또는 `ESC` | 유지 |
| 어디서든 강제 | Ctrl+C × 2 (2초 이내) | 삭제 |
| 배포 완료 후 | 자동 | 삭제 |

---

## 공통 내부 동작

### OS 감지 및 패키지 매니저

| OS | 감지 조건 | 패키지 매니저 |
|----|-----------|---------------|
| macOS | `uname -s == Darwin` | Homebrew (`brew`) |
| Debian/Ubuntu | `/etc/os-release` ID_LIKE=debian | `apt-get update && apt-get install -y` |
| Fedora/RHEL/Rocky/AlmaLinux | ID_LIKE=fedora/rhel/centos | `dnf` 또는 `yum` |
| Arch | ID_LIKE=arch | `pacman` |

### Docker 설치

배포판 기본 패키지가 아닌 **Docker 공식 저장소**에서 설치합니다.

| 배포판 | 이유 |
|--------|------|
| Debian/Ubuntu | Ubuntu 기본 repo에 `docker-compose-plugin` 없음 |
| RHEL 계열 | `dnf install docker` 는 `podman-docker` 심만 설치 (compose v2 없음) |

- Debian: `/etc/apt/keyrings/docker.gpg` 키링 등록 후 설치
- RHEL: `podman-docker` 제거 후 `docker-ce.repo` 등록
- Arch: `pacman -S docker docker-compose`
- macOS: `brew install --cask docker` 후 Docker.app 자동 실행 대기

#### docker group 처리 (Linux)

```
/etc/group 에 사용자 추가 (usermod -aG docker)
  ↓
현재 셸 보조 그룹 확인 (id -nG)
  ├─ 그룹 활성화됨 → 직접 docker 호출
  └─ 미활성화 → DAEMON_NEEDS_SG=1
       → 모든 docker/make 호출을 sg docker -c "..." 로 래핑
```

### Makefile 자동 생성

`OPS_DIR/Makefile` 없고 `docker-compose*.yml` 발견 시 자동 생성.

```makefile
# 생성 규칙
up:      docker compose -f <base> up -d
down:    docker compose -f <base> down
ps:      docker compose -f <base> ps
logs:    docker compose -f <base> logs -f --tail=200
build:   docker compose -f <base> build
clean:   docker compose -f <base> down -v --remove-orphans

# base 외 compose 파일은 경로+파일명에서 태그 추출
up-<tag>:   docker compose -f <base> -f <extra> up -d
down-<tag>: docker compose -f <base> -f <extra> down
```

- base 선택: `docker-compose.yml` / `compose.yml` 중 가장 얕은 경로
- 태그: 파일명에서 확장자·공통 prefix 제거, 서브디렉터리는 `-` 구분자로 경로 포함

### 실패 시 로그 수집

make 타겟 실패 시 비정상 컨테이너 로그 자동 출력.

```
조건: Up + (healthy) → 스킵
조건: 그 외 (unhealthy, Exited, Restarting 등) → docker logs 출력
  DSS (CLI)  : --tail=80
  TUI (REPL) : --tail=40
```

### 상태 파일

`<OPS_DIR>/.dist-standard.conf`

```bash
LAST_TARGET='up'
LAST_RUN='2026-06-13T10:30:00Z'
```

다음 실행 시 자동 로드 → 마지막 타겟을 기본값으로 표시.

---

## 비교 요약

| 기능 | DSS (CLI) | DSS-Tui v3 (REPL) |
|------|-----------|-------------------|
| 저장소 입력 | `-I` 필수 | `/repo` CRUD 또는 `-I` |
| 저장소 순서 변경 | ✗ | ✓ (드래그) |
| Workspace 선택 | 번호 메뉴 (1/2/3) | `/workspace` 메뉴 |
| 인증 | gh auth 전용 | gh / PAT / no-auth |
| PAT 지원 | ✗ | ✓ (임시 credential, 자동 삭제) |
| SSH→HTTPS 변환 | ✗ | ✓ (PAT 모드) |
| 커맨드 자동완성 | ✗ | ✓ (`/` 입력 시) |
| 커맨드 히스토리 | ✗ | ✓ (↑↓ 방향키) |
| 커서 이동 | ✗ | ✓ (←→ 방향키) |
| 상태 확인 | ✗ | ✓ (`/status`) |
| Bootstrap 상태 추적 | ✗ | ✓ (`BOOTSTRAP_DONE`) |
| make 타겟 선택 | 번호 메뉴 | 방향키 메뉴 |
| 비대화형 CLI 모드 | ✗ | ✓ (`--cli` 플래그) |
| Node.js 설치 | ✓ | ✓ |
| Python3 설치 | ✓ | ✗ |
| 셸 명령 실행 | ✗ | `! <cmd>` (언제든) |
| 강제 종료 | Ctrl+C | Ctrl+C×2 (2초 이내) |
