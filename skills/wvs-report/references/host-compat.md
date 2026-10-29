# 호스트 무관 실행 규약 — 어떤 에이전트에서든 같은 품질

> Claude Code · Claude Desktop · Codex · Cursor · Gemini CLI · Windsurf · Devin · OpenCode · Antigravity · GitHub Copilot CLI · Command Code · Grok Build · OMP · VS Code 공통.
> 보고서 품질은 모델 성실도가 아니라 **게이트 스크립트**로 보장한다. 이 문서는 `deep` 모드 기준이며 `repos`·`prd` 조사 단계에도 같은 원칙을 쓴다.

이 규약은 호스트별 실행 지침이며 모든 실제 에이전트에서의 검증 완료를 뜻하지 않는다. 설치 경로, 로컬 스크립트, 실제 호스트 도구 호출을 구분해 검증한다. `sess-bak`는 이 문서가 아니라 `references/sess-bak.md`의 에이전트별 지원 표를 따른다.

## 1. 왜 호스트마다 품질이 달라지는가 (실측)
같은 입력(AWS Well-Architected Agent · Azure Data Engineering 인포그래픽)을 두 호스트로 만든 결과:

| 지표 | 저품질 결과 | 양호 결과 |
|---|---|---|
| `_SPEC.md` | 5~8줄(템플릿을 요약) | 75~95줄(템플릿 전체 + 도식별 판정 후보) |
| 조사 원문 합계 | 453줄 | 1,836~2,025줄 |
| 항목 블록 분량 | 19줄, 소제목마다 1줄 | 77~119줄, 소제목 3~51줄 |
| 구현 코드·실측 표 | 없음 | 블록마다 1~3개 |
| 파일당 참고문헌 | 2~3건 | 9~45건 |
| 웹 확인 | 생략 — 실존 제품을 `[미확인]` 처리 | 공식 문서·릴리스 노트로 출시일·한도·API 확인 |
| `sample/` 참조 구현 | 없음 | 실행 코드 + `sample/out/` 결과 |
| 보고서 | 26~27쪽 · 표 26~27개 | 64~69쪽 · 표 89~114개 |

원인: ① 템플릿을 압축 요약, ② 서브에이전트 없이 한 컨텍스트에서 전 단위를 몰아 작성, ③ 웹 조사 생략, ④ 분량 규칙이 권고문이라 검증되지 않음.
대응: 아래 규약 + `scripts/check_research.py`(조사 깊이 게이트) + `check_report.py --min-pages --min-tables`(분량 게이트). **게이트 PASS 전에는 다음 단계로 가지 않는다.**

## 2. 시작 시 능력 점검 (한 줄로 보고)
작업 전에 아래 3가지를 확인하고 `호스트 능력: 서브에이전트 O/X · 웹 검색 O/X · 셸 O/X` 로 알린다.

| 능력 | 있으면 | 없으면(대체) |
|---|---|---|
| 서브에이전트(병렬 작업 위임) | 조사 단위마다 1개, 병렬 | **순차 모드**(§3) — 단위 하나씩, 단위마다 게이트 |
| 웹 검색·가져오기 | 공식 문서·릴리스 노트·가격·논문 검색 | 셸 `curl -sL <공식 URL>`, `gh api`, `gh search repos`, arXiv `curl https://export.arxiv.org/api/query?search_query=…` |
| 셸(Python·gh·soffice) | 스크립트·게이트·빌드 실행 | 실행 가능한 환경으로 옮겨 실행하도록 사용자에게 알린다. 게이트를 건너뛰고 "완료"라 하지 않는다 |

호스트별 대표 도구(이름은 버전마다 다를 수 있음 — 없으면 대체 열을 쓴다):

| 호스트 | 서브에이전트 | 웹 검색 | 비고 |
|---|---|---|---|
| Claude Code · Claude Desktop(Code 탭) | Agent(Task) 도구 | WebSearch · WebFetch | 병렬 모드 기본 |
| Codex | 호스트 설정에 따름 | 웹 검색(활성화 시) | 없으면 순차 + curl |
| Cursor · Windsurf · VS Code(Copilot Chat) | 호스트 설정에 따름 | 웹 검색 도구(@Web 등) | 상위 추론 모델·긴 컨텍스트 모드 권장, 순차 모드 기본 |
| Gemini CLI · Antigravity | 호스트 설정에 따름 | google_web_search · web_fetch | |
| Devin · OpenCode · Copilot CLI · Command Code · Grok Build · OMP | 호스트 설정에 따름 | 호스트 제공 도구 | 없으면 curl·gh |
| Claude Desktop(채팅 업로드 스킬) | 없음 | 호스트 설정에 따름 | 네트워크·셸 제한 시 조사·게이트를 Code 탭/CLI 에서 실행 |

## 3. 조사 실행 규약 (병렬·순차 공통)
1. **템플릿을 압축하지 않는다.** `references/deep-research-spec.md` 의 `~~~markdown` 블록을 그대로 복사해 `{ }` 만 채운다. 품질 규칙·파일 형식 절을 지우거나 요약하면 게이트 FAIL.
2. **사전 웹 확인을 먼저 한다.** 대제목·제품명·핵심 용어를 검색해 실존 여부·출시일·현행 이름·상태(GA/preview/폐기)를 1차 출처 URL 과 함께 `_SPEC.md` `## 사전 웹 확인` 표에 적는다(3건+). 이 단계를 건너뛰고 `[미확인]` 으로 처리하지 않는다.
3. `check_research.py --assets <A> --stage spec` PASS.
4. 조사 단위 실행
   - 병렬 모드: 단위마다 서브에이전트 1개, 지시문은 §4 그대로.
   - **순차 모드**: 단위 하나 = 한 작업 묶음. 단위 파일을 블록 단위로 append 저장 → `check_research.py --assets <A> --unit rN_x.md` → FAIL 항목 보강 → PASS 후 다음 단위. 여러 단위를 한 번에 쓰지 않는다(컨텍스트가 커질수록 블록이 짧아진다).
5. 모든 단위 후 `--stage research` PASS → 검증(`verify_sources.py`) → `sample/` 참조 구현 실행 → `--stage final` PASS → 빌드 → `check_report.py … --min-pages 40 --min-tables 50` PASS.
6. 게이트가 FAIL 인데 보강할 근거가 없으면(실제로 자료가 없는 주제) 숫자를 채우려 지어내지 않는다. 남은 FAIL 과 사유를 최종 보고에 그대로 적는다.

## 4. 조사 지시문 (서브에이전트·순차 공통 — 그대로 사용)
```text
너는 "<Title>" 보고서의 조사 담당이다. 담당 파일: research/<rN_x.md>, 블록 KEY: <KEY…>.
1) research/_SPEC.md 를 처음부터 끝까지 읽는다(원본 이미지 ../source_infographic.png 도 본다).
2) 블록마다 웹 검색으로 1차 출처(공식 문서 페이지·릴리스 노트·가격·GitHub README/코드·논문)를 3건 이상 실제로 열어 확인한다.
   저장소는 gh api 로 ★·SPDX·push·릴리스를 직접 조회한다. 확인 못 한 것만 [미확인].
3) 항목 블록은 _SPEC 의 필수 소제목을 순서대로 모두 쓴다. 블록 70줄 이상, 소제목 3줄 이상, 구현/사용방법은 실제 API·CLI 코드(40줄 이하) + 옵션 표, 도식 판정 표 3행 이상.
   원리·비교·누락·통합 블록은 35줄 이상, 소제목 3개 이상.
4) 블록 하나를 끝낼 때마다 파일에 append 저장한다. 파일 끝에 # PAPERS(블록당 3건+, STD 는 URL 포함) · # REPOS.
5) 끝나면 python3 <KIT>/check_research.py --assets <A> --unit <rN_x.md> 를 실행해 PASS 까지 보강한다.
6) 형식 참고용 이전 보고서와 다른 보고서 폴더는 읽지도 인용하지도 않는다. 도구 설치·실행 금지(웹·gh·curl 만).
```

## 5. 최종 보고에 포함
호스트 능력 한 줄 · 모드(병렬/순차) · `check_research.py --stage final` 결과 · `check_report.py` 결과(쪽·표·그림) · 저장소/논문 검증 수 · 남은 FAIL·[미확인] 과 사유 · `prune_assets.py` 정리 결과(또는 `--keep-assets`).
