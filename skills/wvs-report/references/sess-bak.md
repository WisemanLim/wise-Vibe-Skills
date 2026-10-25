# mode `sess-bak` — Claude Code 프로젝트별 세션 히스토리 증분 백업


> 인수 규칙·경로 변수(`SKILL_DIR`·`KIT`)는 `wvs-report` SKILL.md 를 따른다. `KIT` = `SKILL_DIR/scripts`.

## 요청 원형과 자동화 규칙
> claude 에 저장된 project 별 대화내용(세션 히스토리)을 각 프로젝트별 개별파일로 저장.
> 예) `-Users-wise-Downloads---Developer-backup-wise-vibe-plugin` → `wise-vibe-plugin.md`. 누락되는 프로젝트가 없도록 저장.
> 기존 프로젝트 파일이 있으면 세션 히스토리 누락 없이 업데이트. 중복 내용은 증분 처리해 백업본 최소화.

- 원본: `~/.claude/projects/<인코딩된 경로>/` — `<sessionId>.jsonl`(대화), `<sessionId>/**/*.jsonl`(서브에이전트), `memory/*.md`.
- 출력: `OUT/<name>.md` (프로젝트 1개 = 파일 1개) + `OUT/INDEX.md`. OUT 기본 `~/.claude/session-history`.
- 이름: 디렉터리명 앞의 홈 경로 접두사(`-Users-<u>-Downloads---Developer-backup-` · `-Users-<u>-Developer-` · `-private-tmp-claude-501-` · `-Users-<u>-`) 제거, 연속 `-` 축약. `claude` → `claude-home`(대소문자 무시 FS 에서 CLAUDE.md 충돌 방지), 중복 이름은 `-2` …. **이미 만든 파일은 md 안의 `원본 디렉터리` 로 이름을 고정**해 다시 바뀌지 않는다.

## 인수
| 인수 | 기본값 | 의미 |
|---|---|---|
| `[OUT]` | `~/.claude/session-history` | 출력 폴더 |
| `--src <dir>` | `~/.claude/projects` | 원본 프로젝트 폴더 |
| `--install-hook` | — | `~/.claude/settings.json` 에 SessionEnd 훅 등록 → 세션이 끝날 때마다 백그라운드 자동 실행(종료 지연 없음, 로그 `OUT/.export.log`). 기존 `export_history.py` 훅은 교체, 다른 훅은 유지 |
| `--uninstall-hook` | — | 위 훅만 제거 |

## 증분 규칙 (백업본 최소화)
- 새 세션·메시지만 병합. 내용이 같은 파일은 다시 쓰지 않는다. 쓰기는 `.tmp` → 원자적 교체, **별도 백업 사본을 만들지 않는다**.
- 원본 jsonl 이 지워진 세션·서브에이전트, 지워진 `memory/` 는 기존 md 의 블록을 그대로 보존(INDEX `보존` 열).
- 세션 블록은 줄어들지 않는다 — 원본이 compact 등으로 짧아지면 기존 블록 유지.
- 기존 세션이 하나라도 빠질 상황이면 `ABORT <name>.md: would lose sessions …` 로 중단(쓰지 않음).
- 원본 디렉터리가 사라진 md 파일도 지우지 않고 INDEX 에 `(원본 디렉터리 삭제됨 — 기존 파일 보존)` 으로 남긴다.
- 동시 실행 방지: `OUT/.export.lock` (이미 실행 중이면 `another export is running` 으로 종료).

## 내용 형식
세션별 `## 세션 N: \`<sessionId>\`` — 기간·cwd·branch·제목, 사용자/어시스턴트 메시지(시스템 리마인더 제거, 슬래시 커맨드 축약), 도구 호출 한 줄 요약(`- 🔧 \`Tool\` — 인자`), compact 요약, 서브에이전트(첫 프롬프트·최종 응답 `<details>`), 마지막에 `## 프로젝트 메모리 (memory/)`.

## 절차
1. 실행: `python3 -I $KIT/export_history.py [OUT]` — 표준출력 = 프로젝트별 `이름·원본·세션·서브에이전트·메모리·크기·보존`, stderr = `# files updated: N`.
2. 검증(필수, 보고 전에):
   ```bash
   cd ~/.claude/projects
   for f in ./*/*.jsonl; do id=${f##*/}; id=${id%.jsonl}; grep -q "^## 세션 [0-9]*: \`$id\`" OUT/*.md || echo MISSING $f; done   # 세션 누락 0
   for d in ./*/; do d=${d%/}; d=${d#./}; grep -q "원본 디렉터리: \`.*/$d\`" OUT/*.md || echo NOPROJ $d; done              # 프로젝트 누락 0
   ```
   실행 전후 세션 ID 목록 비교는 파일별로 저장한 뒤 `LC_ALL=C sort` · `LC_ALL=C comm` 으로 한다(로케일 정렬 차이로 오탐). 같은 세션이 두 프로젝트에 있을 수 있어 파일별 합계 ≥ 고유 ID 수.
3. 자동 실행이 필요하면 `python3 $KIT/export_history.py --install-hook`(OUT·--src 를 함께 주면 그 값으로 등록).
4. 최종 보고: 프로젝트 수 · 새로 만든/갱신한 파일 · 원본 세션 수와 누락 0 · 기존 세션 보존 · OUT 용량.
