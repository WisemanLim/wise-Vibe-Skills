---
name: wvs-review
description: "저장소·소스 리뷰 통합 스킬 — 레벨로 깊이를 고른다. L1 구조 분석(구 analysis-source) · L2 +상용화 심층 분석(라이선스·보안·ISO 5230·위험 등급, 구 in-depth-review) · L3 +주니어/구현 가이드(한·영, 구 create-guide4junior) · L4 +독자 레벨(R0~R4) 라인 단위 코드 리뷰(구 code-review-by-levels), --stars 로 스타 목록 일괄 분석(구 totally-analysis-based-on-star). 결과는 .review/ 에 저장. Unified repository review with depth levels. Use for '소스 분석', '상용화 검토', '라이선스 감사', '주니어 가이드', '코드 리뷰', 'analyze/review this repo'."
---

# wvs-review — 저장소 리뷰 통합 (레벨 실행)

Arguments: $ARGUMENTS
> 호스트가 `$ARGUMENTS` 를 치환하지 않는 에이전트(Codex·Cursor·Gemini CLI 등)에서는 사용자 요청문에서 스킬 이름 뒤 텍스트를 인수로 쓴다.
> 레벨·파트가 없고 요청문이 특정 작업("라이선스만", "코드 리뷰", "가이드")을 말하면 그에 맞는 `--only` 를 고른다.

## 1. 레벨과 파트

| 레벨 | 실행 파트(누적) | 산출물 (`<target>/.review/`) | 상세 절차 |
|---|---|---|---|
| `--level 1` | structure | `REVIEW.md` — 목적·구조·스택·아키텍처·테스트·보안·문서·성숙도 8단계 | `references/structure.md` |
| `--level 2` **(기본)** | structure + commercial | + `REVIEW-InDepth.md` — 라이선스 감사·보안·커뮤니티·상용 아키텍처·법적/ISO 5230·5단계 위험 등급 | `references/commercial.md` |
| `--level 3` | + guide | + `GUIDE4Junior.md` · `GUIDE4ImpMethod.md` (한·영 병기) | `references/guide.md` |
| `--level 4` | + code | + `CODE-REVIEW-Lv<n>/` (n = `--reader`) (INDEX.md · 디렉토리 Abstract · 파일별 라인 리뷰) | `references/code.md` |

- `--only <parts>` — 누적하지 않고 지정 파트만: `structure`, `commercial`, `guide`, `code` (쉼표로 여러 개). 예: `--only commercial` = 구 in-depth-review 단독.
- `--stars <file.md>` — **일괄 모드**: pub-star-classifier MD 의 모든 저장소에 레벨 1~3 파트를 카테고리·랭크 버킷으로 생성(`references/bulk-stars.md`). 레벨 기본값 3.
- 파트 순서는 항상 structure → commercial → guide → code. **앞 파트에서 읽은 인벤토리(트리·매니페스트·LICENSE·README)는 뒤 파트에서 재사용**하고 다시 탐색하지 않는다.
- 각 파트는 해당 reference 파일을 **그 파트를 시작할 때 읽고** 그 절차·보고서 구조를 그대로 따른다.

## 2. 통합 인수

| 인수 | 기본값 | 의미 |
|---|---|---|
| 위치 인수 | 현재 디렉토리 | 대상 경로(여러 개 가능) |
| `--level <1-4>` | `2` | 깊이(누적) |
| `--only <parts>` | — | 지정 파트만 실행 |
| `-O`, `--overall` | false | 다중 대상 집계 — 첫 대상 `.review/<name>/` 아래 대상별 하위 폴더 + 종합 비교 |
| `--pdf` (`--pdf true`) | false | 각 산출 MD → PDF (`wvs-tools` 의 `wvs pdf` 우선, 없으면 pandoc) |
| `--name <base>` (`--review-result`) | 파트별 기본 | 단일 파트 실행 시 출력 파일·폴더 이름 |
| `--out-dir <dir>` | `.review` | 출력 폴더(대상 기준) |
| `--reader <0-4>` | `2` | code 파트 독자 레벨 R0(비전공)~R4(아키텍트). 구 code-review-by-levels 의 `--level` |
| `--include` · `--exclude` · `--max-files` · `--max-lines-per-file` · `--entry-only` | code.md 참조 | code 파트 범위 |
| `--previous` · `--out` · `--bucket-thresholds` · `--depth` · `--deep-top-per-cat` · `--workers` · `--force` · `--no-summary` · `--dry-run` | bulk-stars.md 참조 | `--stars` 일괄 모드 |

구 커맨드의 옵션 이름(`--review-result`, `--pdf true|false`, `-O`)은 모두 그대로 받는다.

## 3. 실행
1. 인수 해석 → 대상·파트 목록·출력 경로를 한 줄로 알린다(예: `대상 2 · L2(structure, commercial) · .review/`).
2. 대상마다 파트를 순서대로 실행. 파트 하나가 끝날 때마다 파일을 저장한다(중단 시 앞 파트 결과 보존).
3. `-O` 이면 대상별 결과를 모은 뒤 파트별 종합(공통점·차이·교차 위험·통합 판정)을 쓴다.
4. `--pdf` 이면 생성된 MD 마다 같은 이름의 PDF 를 만든다(Mermaid 포함 시 `wvs pdf` 가 렌더).
5. 끝에 출력 파일 전체 경로, 파트별 핵심 판정(L2 위험 등급, L4 상위 위험 3개)을 요약한다.

## 4. 공통 규칙
- 모든 주장은 실제로 읽은 파일 근거. 파일이 없으면 "확인 불가 — 파일 부재 / Not found". 추측 금지, 과장·마케팅 문구·불필요한 이모지 금지.
- 결과는 한국어 우선, 가능하면 영어 병기(guide 파트는 섹션마다 한·영 필수).
- 기존 `.review/` 의 다른 결과는 보존하고, 같은 이름 파일만 덮어쓴다.

## 5. 예시
```text
/wvs-review                                   # 현재 폴더 L2 (구 analysis-source + in-depth-review)
/wvs-review ./proj --level 1 --pdf            # 구조 분석만 + PDF
/wvs-review ./proj --only commercial          # 구 in-depth-review 단독
/wvs-review ./proj --level 3                  # + 주니어·구현 가이드
/wvs-review ./src --only code --reader 0      # 비전공자용 라인 리뷰
/wvs-review ./a ./b -O --level 2              # 두 프로젝트 비교 집계
/wvs-review --stars stars-20261014.md --previous stars-20260901.md --depth hybrid
```

## 6. 구 커맨드 대응
| 구 커맨드 | 새 호출 |
|---|---|
| `/analysis-source <p>` | `/wvs-review <p> --level 1` |
| `/in-depth-review <p>` | `/wvs-review <p> --only commercial` |
| `/create-guide4junior <p>` | `/wvs-review <p> --only guide` |
| `/code-review-by-levels <p> --level N` | `/wvs-review <p> --only code --reader N` |
| `/totally-analysis-based-on-star --input f.md` | `/wvs-review --stars f.md` |
