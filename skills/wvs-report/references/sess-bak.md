# mode `sess-bak` — 에이전트별 세션 히스토리 증분 백업

`KIT` = 이 스킬의 `scripts` 디렉터리. Python 3.9+ 표준 라이브러리만 필요하다.
보고서용 venv·docx/PDF 빌드·조사 게이트·자산 정리는 적용하지 않는다.

## 호스트 선택과 지원 범위

**스킬을 실행하는 에이전트 이름을 `--agent`로 명시한다.** 사용자가 백업 대상을 지정하면 그 값이 우선이다. 스킬 설치 경로(`.agents/skills`)만으로 실행 호스트를 추정하지 않는다.

| `--agent` | 기본 원본 | 기본 출력 | 읽는 형식 |
|---|---|---|---|
| `claude-code` | `${CLAUDE_CONFIG_DIR:-~/.claude}/projects` | 같은 설정 루트의 `session-history` | 프로젝트 JSONL·중첩 서브에이전트 JSONL·`memory/**/*.md` |
| `codex` | `${CODEX_HOME:-~/.codex}` | 같은 루트의 `session-history` | `sessions/**/*.jsonl` + `archived_sessions/**/*.jsonl`, `session_meta.payload.cwd`별 그룹화 |
| `gemini-cli` | `${GEMINI_CLI_HOME:-~}/.gemini/tmp` | `${GEMINI_CLI_HOME:-~}/.gemini/session-history` | `<project>/chats/`의 JSON·JSONL 및 중첩 서브에이전트, `projectHash`별 그룹화 |

- `auto`는 명확한 실행 환경 변수 또는 명시한 `--src`의 형식만 판별한다. 다중 후보·불명확한 경우 오류로 중단한다. 설치된 폴더가 있다는 이유로 Claude 백업을 실행하지 않는다.
- **미지원**: Cursor, Windsurf, Devin, OpenCode, Antigravity, Copilot CLI, Command Code, Grok Build, OMP, VS Code 자체 대화 저장소. 해당 이름으로 실행하면 실패하며 Claude 경로로 대체하지 않는다. 지원되는 형식의 내보내기 파일을 별도 확보한 경우에만 해당 `--agent`·`--src`를 지정한다.
- Claude Desktop의 일반 채팅은 Claude Code 로그가 아니다. Code 탭에서 실제 Claude Code 프로젝트 로그를 사용하는 경우만 `claude-code`로 처리한다. 원격/컨테이너 호스트는 원본 로그가 보이는 환경에서 실행해야 한다.
- Codex의 `.jsonl.zst`는 현재 직접 읽지 않는다. 발견하면 오류로 중단하므로 압축을 푼 복사본을 `--src`로 지정한다.
- 설치기에서 14개 클라이언트를 지원한다는 뜻과 세션 포맷을 지원한다는 뜻은 다르다. 전체 검증 범위는 저장소의 `tests/VALIDATION.md`에 기록한다.

## 인수와 실행

| 인수 | 의미 |
|---|---|
| `[OUT]` | 출력 디렉터리. 생략하면 위 에이전트별 기본값 |
| `--agent <name>` | 기본 `auto`. 스킬 실행 시에는 호스트 이름을 명시 |
| `--src <dir>` | 위 표의 원본 루트 재정의. Codex는 별도의 sessions 또는 archived_sessions 디렉터리도 허용 |
| `--list-agents` | 지원 포맷·실제 환경 변수 반영 경로·훅 지원 여부 출력, 백업하지 않음 |
| `--install-hook` / `--uninstall-hook` | Claude Code의 POSIX 환경에서만 SessionEnd 등록/제거. 다른 에이전트는 설정 변경 없이 오류. 두 옵션 동시 사용 불가 |

```bash
python3 -I "$KIT/export_history.py" --agent codex
python3 -I "$KIT/export_history.py" --agent claude-code
python3 -I "$KIT/export_history.py" --agent gemini-cli
python3 -I "$KIT/export_history.py" ./history --agent codex --src ./copied-codex-home
python3 -I "$KIT/export_history.py" --agent claude-code --install-hook
```

OUT은 원본 세션 트리 밖에 둔다. Codex 홈을 원본으로 지정한 경우에는 `sessions`·`archived_sessions` 밖의 `session-history`를 허용한다. 기존 백업을 다른 OUT으로 옮길 때에는 프로젝트 MD와 INDEX를 함께 옮긴다.

## 보존·내용 규칙

- 프로젝트별 `<name>.md` + `INDEX.md`. 기존 파일명은 프로젝트 식별자로 고정한다. Codex는 cwd의 마지막 경로명, Gemini는 복원 불가능한 원본 경로를 추측하지 않고 projectHash를 쓴다.
- 프로젝트 식별자에는 에이전트를 포함한다. 같은 이름·대소문자 충돌은 숫자 접미사로 구분하며 `INDEX`, `AGENTS`, `CLAUDE`, `GEMINI` 등은 출력 이름으로 사용하지 않는다. 무관한 기존 MD는 덮어쓰지 않는다.
- 세션 ID와 메시지 ID·내용 해시로 병합한다. 동일 기록 재실행은 중복 추가하지 않으며 내용이 같은 프로젝트 MD와 INDEX는 다시 쓰지 않는다.
- 원본 세션/프로젝트 삭제, compact/rewind, 메시지 수정, 메모리 일부 삭제 후에도 이미 백업된 기록을 보존한다. 수정 전후 내용은 각각 남는다. 메모리 수정 전 내용은 `파일명@해시`로 보존한다.
- **기존 Claude 전용 MD 최초 전환**: 메시지 식별자가 없는 옛 블록은 `legacy snapshot`으로 한 번 보존한다. 원본에서 읽은 기록과 일부 겹칠 수 있으며 이후 실행은 중복을 추가하지 않는다. 이미 옛 백업에서 생략된 내용을 원본 없이 복원할 수는 없다.
- 본문은 사용자/어시스턴트 대화, 도구 입출력, compact 요약, 서브에이전트 대화를 포함한다. 시스템/개발자 지침·내부 추론·사용량 통계는 대상이 아니며 이미지 바이너리는 원본 위치에 남기고 표식만 기록한다. 인증 파일이나 DB를 복제하는 **에이전트 환경 복구용 원시 백업은 아니다**. 대화나 도구 출력에 포함된 민감정보를 자동 제거하지는 않는다.
- 대화 본문은 인용 블록으로 격리하여 대화 안의 제목/마커가 세션 경계로 오인되지 않게 한다. HTML 주석의 `wvs:*` 마커를 제거하지 않는다. 저장된 메시지 본문 해시가 다르면 중단한다.
- 손상된 JSON/JSONL은 조용히 건너뛰지 않는다. 전체 입력을 읽은 뒤 쓰기 시작하므로 파싱 오류 시 기존 백업은 바뀌지 않는다. 실행 중 세션의 마지막 줄이 미완성이면 기록 완료 후 재실행한다.
- 파일별 원자적 교체와 출력 디렉터리 잠금(POSIX flock / Windows msvcrt)을 사용한다. 여러 파일을 한꺼번에 교체하는 트랜잭션은 아니므로 중간 I/O 실패 시 오류를 확인한 뒤 재실행한다.

## 훅과 완료 검증

Claude 훅은 `${CLAUDE_CONFIG_DIR:-~/.claude}/settings.json`에 등록한다. 백그라운드 실행, 로그 `OUT/.export.log`, 경로는 셸 인용 처리한다. 기존 wvs 훅만 교체하며 같은 그룹의 다른 훅과 다른 설정은 유지한다. 다른 에이전트의 훅이 존재하지 않는다는 뜻이 아니라 **이 도구의 자동 등록이 Claude에만 구현되어 있다는 뜻**이다.

성공 시 JSON 결과의 `agent`, `source`, `out`, `projects`, `source_sessions`, `files_updated`, `missing`, `preserved_projects`를 보고한다. 저장된 MD를 다시 읽어 현재 원본의 세션 ID·메시지 키 누락을 검사하며 `missing: 0`이어야 한다. 원본 세션 수가 0이면 빈 원본이라고 명시하고 대화 백업이 완료됐다고 표현하지 않는다. 보존된 과거 기록 때문에 출력의 세션 수는 현재 원본보다 클 수 있다.

## 형식 확인에 사용한 1차 근거

- [Claude Code hooks: transcript_path·SessionEnd](https://code.claude.com/docs/en/hooks)
- [Codex 환경 변수: CODEX_HOME](https://learn.chatgpt.com/docs/config-file/environment-variables)
- [Gemini CLI 세션 관리와 저장 위치](https://geminicli.com/docs/cli/session-management/)
- [Gemini CLI 기록 구현](https://github.com/google-gemini/gemini-cli/blob/main/packages/core/src/services/chatRecordingService.ts) · [기록 타입](https://github.com/google-gemini/gemini-cli/blob/main/packages/core/src/services/chatRecordingTypes.ts)

확인일: 2026-10-29. 원본 포맷 변경 시 어댑터와 회귀 테스트를 함께 갱신한다.
