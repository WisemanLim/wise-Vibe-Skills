# 스킬 기능 검증 결과

검증일: 2026-10-29. 환경: macOS / Darwin arm64, Python 3.14.8, Node.js 22.23.1.
범위: 현재 저장소 소스. 설치된 사용자 스킬 복사본을 갱신하거나 배포하지 않았다.

## 판정

`npm test` 전체 PASS. 신규 unittest 33개(세션 24·도구 7·호스트 2), 호스트 테스트 내부에서 14개 클라이언트 × user/project 28개 경로 조합을 Bash/Node 설치기로 비교했다. 스킬 3개의 공식 `quick_validate.py` 검사와 `git diff --check`도 PASS.

이는 **모든 에이전트의 실제 실행·대화 품질을 검증했다는 뜻이 아니다**. 아래에서 자동 검증, 로컬 로그 표본 검증, 미실행 항목을 구분한다. 기존 테스트는 통과했지만 세션 백업 회귀 테스트는 없었다.

## 기능별 검증표

| 대상 | 수행한 검증 | 결과와 한계 |
|---|---|---|
| 스킬 3개 메타데이터·참조 파일 | 설명 길이·이름·금지 문자, SKILL과 하위 Markdown의 구체적인 번들 경로 | PASS. 실제 호스트의 자연어 지침 준수는 별도 |
| 설치기 14개 클라이언트 | 각 user/project 경로 비교, 환경 변수·공백·한글 경로, dry-run 무설치 | PASS. 클라이언트 앱이 그 경로를 실제 발견하는지는 미검증 |
| 설치·제거·레거시 정리 | 임시 환경에 복사·bin 링크·마커 소유권 확인·제거 | PASS. 사용자 설치본은 변경하지 않음 |
| Claude Desktop ZIP | CRC 무결성, exporter와 어댑터 포함 | PASS. Desktop 업로드/샌드박스 실행은 미검증 |
| `sess-bak`: Claude Code | 본문·도구 결과·중첩 서브에이전트·메모리, 옛 MD 전환 | PASS. 실제 로컬 로그 1개도 임시 복사본으로 검증(정규화 이벤트 3개) |
| `sess-bak`: Codex | active/archive, cwd 그룹화, event/response 중복, event-only·혼합 로그·compact | PASS. 실제 메시지 포함 로그 1개 검증(이벤트 72개); 메타데이터 전용 로그도 처리 확인 |
| `sess-bak`: Gemini CLI | JSON·JSONL·중첩 서브에이전트·patch·rewind·checkpoint | PASS. 로컬 JSON 표본 1개 검증(이벤트 1개). 최신 JSONL은 공식 타입 기반 합성 입력 검증 |
| `sess-bak` 증분 보존 | 세션 삭제·동일 개수 내용 수정·응답 확장·메모리 일부 삭제/수정, 동일 내용 재실행 | PASS. 기존 블록 보존, 프로젝트 MD와 INDEX의 바이트/mtime 동일성 확인 |
| `sess-bak` 경계 조건 | 비UUID ID, 대소문자·예약 이름·기존 파일 충돌, 손상 JSONL·변조 MD·본문 속 마커 | PASS. 오류 시 기존 백업 유지, 미지원 호스트에 Claude fallback 없음 |
| 훅 | Claude 설정 루트, 등록 재실행·제거, 같은 그룹의 타 훅 보존, 셸 특수문자 인용 | 합성 설정 PASS. 실제 세션 종료 이벤트는 미실행. 다른 에이전트 자동 등록은 미지원 |
| 동시 실행 | POSIX 잠금 보유 상태에서 두 번째 프로세스 거부 | PASS. Windows msvcrt 분기는 구현했으나 실제 Windows 실행 미검증 |
| 보고서 도구·deep·PRD·UI | 기존 smoke_kit/deep/research/prd/ui: 문서·슬라이드·PDF 생성, 품질 게이트, 입력/요구사항 추적, 자산 정리 | PASS. 실제 외부 조사부터 최종 장문 문서까지의 호스트별 품질 검증은 아님 |
| `repos` | 공통 문서/소스 처리 도구·참조/문법 검사 | 원격 저장소 수집·clone부터 Summary-Repos까지 전체 흐름은 미실행 |
| `wvs-review` L1~L4·stars | 메타데이터·모든 번들 reference 경로 | 실제 호스트별 리뷰 산출물·내용 품질은 미검증(독립 실행 엔진 없음) |
| `wvs-tools pdf` | MD 입력 인수 전달, 공백·한글·`--input=`, 기존 office PDF smoke | PASS. 이번 추가 테스트의 MD converter는 스텁; pandoc/TeX/Mermaid 전체 체인 신규 E2E는 미실행 |
| `wvs-tools clean` | dry-run 무삭제, 실제 삭제 대상과 보존 파일 | 임시 파일로 PASS |
| `wvs-tools bookmarks` | dry-run, folder/global 차이, 별도 출력 시 원본 보존 | 합성 Bookmarks로 PASS. 브라우저 프로필은 변경하지 않음 |
| `wvs-tools archive` | dry-run, 실제 압축 내용·제외 규칙·원본 보존, GNU tar가 `tar`라는 이름인 환경 | PASS. 분할 대용량·원본 삭제 옵션은 미실행 |
| `deploy ios/android`, `dist` | 문법·CLI 분기·잘못된 배포 대상 오류, 옵션 구현 대조 | 스토어 업로드·버전 증가·원격 동기화·컨테이너 실행은 미실행 |

로컬 표본은 원본 해시 불변, 내보내기 누락 0, 2회 실행 결과 동일성을 확인했다. 표본과 생성 대화 파일은 임시 디렉터리에서 처리 후 제거했으며 저장소에 넣지 않았다. `missing: 0`은 지원 어댑터가 읽은 세션·메시지·메모리와 출력 간 비교 결과이며, 제외되는 내부 추론·이미지 원본까지의 원시 백업을 뜻하지 않는다.

## 재현된 결함과 수정

1. Claude 전용 기본 경로 → 에이전트별 어댑터와 `--agent`, 환경 변수 반영, 미지원/불명확한 대상의 명시적 오류.
2. 메시지 수 비교만으로 compact 이후 신규 대화 또는 같은 개수의 교체 내용 누락 → 식별자/내용 해시 기반 누적 보존.
3. 메모리 일부 삭제 시 백업에서도 누락, 서브에이전트 첫/끝 발췌 → 개별 파일 보존·수정 전 내용 보존, 대화/도구 입출력 전체 처리.
4. UUID 정규식·프로젝트 basename만의 식별·INDEX/대소문자 충돌 → 포맷 마커·에이전트/프로젝트 식별자·예약 이름 처리.
5. JSON 오류 조용한 무시·INDEX 매번 덮어쓰기 → 파싱 오류 중단, 파일별 원자적 교체, 내용 동일 시 쓰기 생략.
6. 훅 그룹 전체 제거·경로 셸 인용 문제 → 해당 훅만 제거하고 형제 훅 보존, `shlex.quote`, 설정 루트 반영.
7. `wvs pdf --input=...` 입력 탐색 실패 → 옵션 정규화. 회귀 테스트에서 수정 전 실패/수정 후 통과 확인.
8. Linux의 GNU `tar`를 인식하지 못해 불필요한 설치 경로 진입 → `tar --version`으로 GNU tar 재사용.
9. 잘못된 `archive -o` 예시 → 실제 지원하는 `-F`와 단일 대상 예시로 수정. deploy의 존재하지 않는 dry-run·dist의 무변경 미리보기 오인 안내 수정.
10. 공식 스킬 검증기의 description 꺾쇠 금지 위반 → 메타데이터 수정, 저장소 검증기에 같은 검사 추가.

## 재실행

```bash
npm test
# 외부 Python 패키지 설치 없이 실행하는 신규 회귀 테스트
python3 -B tests/test_history.py
python3 -B tests/test_tools.py
python3 -B tests/test_hosts.py
python3 tests/validate_skills.py
```

전체 smoke는 Python 문서 패키지와 LibreOffice를 사용한다. `WVS_TEST_PY`로 기존 테스트 venv를 재사용할 수 있다. GNU tar가 없으면 실제 압축 테스트는 명시적으로 SKIP하며, 테스트가 시스템 패키지를 설치하지 않는다. 이번 실행에는 GNU tar와 LibreOffice가 있어 해당 검증을 수행했다.

## 남은 검증 우선순위

1. 실제 Claude SessionEnd·Codex·Gemini 호스트에서 스킬 호출→대상 선택→백업 결과 안내까지 실행. 다른 호스트는 버전과 원본 포맷/공식 export를 확보한 뒤 어댑터를 추가한다.
2. 동일한 작은 저장소·요구사항 입력으로 호스트별 wvs-review와 repos/deep/prd 산출물 비교. 도구 유무·네트워크·권한 차이를 별도로 기록한다.
3. Linux·Windows CI에서 경로·잠금·셸·문서 변환 실행. 지원 최소 Python 버전(3.9)의 별도 검증.
4. 격리된 배포 프로젝트와 테스트 계정에서 ios/android/dist 확인. 실제 계정 업로드 성공을 문법 검사 결과로 대체하지 않는다.

## 근거

- 코드: [export_history.py](../skills/wvs-report/scripts/export_history.py), [history_sources.py](../skills/wvs-report/scripts/history_sources.py), [wvs](../skills/wvs-tools/scripts/wvs), [archive-tgz.sh](../skills/wvs-tools/scripts/lib/archive-tgz.sh).
- 재현/검증: [test_history.py](test_history.py), [test_tools.py](test_tools.py), [test_hosts.py](test_hosts.py), [run.sh](run.sh).
- 공식 포맷: [Claude hooks](https://code.claude.com/docs/en/hooks), [Codex CODEX_HOME](https://learn.chatgpt.com/docs/config-file/environment-variables), [Gemini 세션 관리](https://geminicli.com/docs/cli/session-management/), [Gemini 기록 타입](https://github.com/google-gemini/gemini-cli/blob/main/packages/core/src/services/chatRecordingTypes.ts).
