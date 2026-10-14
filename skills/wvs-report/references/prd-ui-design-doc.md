# 화면설계서(UI Design Document, pptx) 작성 기준 — PRD 15장 + `<Brand>_UI_Design.pptx`

## 1. 근거 — 사실상 표준 구조 (조사 요약, 출처는 §6)
- "화면설계서"는 ISO/IEEE 로 규격화된 문서가 아니다. 국내에서는 ① 공공 산출물 표준 **CBD D2 사용자 인터페이스 설계서**(구조도 → 목록(화면·출력물) → 화면 상세 설계)와
  ② 민간 **스토리보드(PPT)** 관행(표지 → 개정 이력 → 목차 → 개요 → IA → 화면 목록 → 흐름도 → 공통 정책·영역 → 화면별 설계(좌 와이어프레임 / 우 Description) → EOD)이 사실상 표준이다.
- 와이어프레임 주석은 **번호 콜아웃 ↔ 설명 표** 매핑이 국내외 공통 관행. 추적성은 CBD R3 요구사항 추적표(요구사항 ID → … → 화면 ID → … → 시험 ID)가 근거.
- 결론: CBD D2 를 뼈대로, 스토리보드의 번호 주석 Description 을 화면 상세 설계에 흡수하는 하이브리드.

## 2. 최소 필수 25항목 (빠지면 "표준 화면설계서"라 부르기 어려움)
[문서] ① 표지(시스템·문서명·단계·작성일·버전) ② 제·개정 이력(날짜/버전/작성자/승인자/내용) ③ 화면 ID 체계 정의
[공통] ④ IA(메뉴 구조도) ⑤ 공통 영역(레이아웃·GNB/LNB·페이징) ⑥ 권한·정보노출·기본 정책 ⑦ 화면 흐름도(복잡 흐름)
[목록] ⑧ 화면 목록(화면ID/화면명/관련 요구사항ID) ⑨ 출력물 목록(해당 시) ⑩ 화면 유형
[화면별] ⑪ 화면 ID ⑫ 화면명 ⑬ 화면 경로 ⑭ 화면 개요 ⑮ 관련 요구사항 ID ⑯ 와이어프레임 ⑰ 번호 주석 ↔ 설명
        ⑱ 입출력 항목(항목명/컨트롤/타입·길이/속성/Validation) ⑲ 처리 내용(이벤트별) ⑳ 화면 전이 ㉑ 유효성 규칙 ㉒ 오류·예외·메시지
[추적] ㉓ 요구사항 ↔ 화면 추적표 ㉔ 미커버 점검 ㉕ 개정 이력과 화면 목록 변경 표기 일치

## 3. pptx 슬라이드 구성 (ui_lib.py)
| 구간 | 슬라이드 |
|---|---|
| 앞부속 | 표지(NAVY 배경, 기준 PRD 파일명·FR 수·화면 수·버전) · 문서 정보·개정 이력 · 목차 |
| PART 1 개요·구조 | 1 시스템 개요 · 원본 도식 = 정보 구조 / 2 화면 ID 명명 규칙·슬라이드 구성 / 3~4 IA(내비 그룹 = 도식 레이어) / 5 화면 목록(페이지 분할) / 6 역할 × 화면 매트릭스 / 7 화면 흐름도 / 8 공통 UI 가이드(레이아웃·토큰·컴포넌트) / 9 상태·메시지·유효성·오류 처리(ST-xx·MSG-xxx) |
| PART 2 화면별 설계 | 그룹(section_slide)마다 화면 1개 = 슬라이드 1개(`screen_slide`): 상단 메타표 + 설명 + 좌 와이어프레임(①②③ 콜아웃) + 우 기능 설명 표(No·구성요소·유형·기능 설명/동작·연계) + 하단 관련 FR + 발표자 노트 |
| PART 3 부록 | A 위저드·모달 카탈로그 · B 메시지 정의(ko/en) · C 요구사항 추적표(RTM, FR ↔ 화면, 미커버 0) · D 비화면 요구의 표출 위치 · E PRD 화면 ↔ 설계서 화면 ID · F 참고 자료·한계 |

## 4. 화면 명세 데이터 (ui_data.py · ui_screens_*.py)
- `SCREENS` 튜플: `(ID, 화면명, 라우트, 권한, PRD추적(공백 구분 FR ID), 우선순위, 유형 P/M/W, 목적(영역별 구성 — 상호작용), PRD 화면 S-ID)`
- 화면 스펙(dict): `id, name, path, kind(페이지/모달/위저드), section, perm, prio, desc, fr[list], items[(No, 구성요소, 유형, 기능 설명/동작(검증·상태·전이·예외, 40~80자), 연계(FR·SCR·MSG·ST·CMP))], wire=callable(Wire), notes`
- **fr 목록의 모든 ID 가 items 연계 열에 최소 한 번** 나와야 한다(빌드 assert). FR 이 많으면 한 행에 FR 2개를 묶는다.
- 그룹 A(설치)는 `frame()` + `stepper()` (시작·모드·사전 점검·구성 요소·저장소·관리자/TLS·진행·완료).
- 개념 개요 화면은 **원본 도식의 흐름도·타일을 그대로** 콘텐츠 중앙에 그리고 노드/타일에 상태·지표를 겹친다.
- 가상 데이터만(가상 기업·사용자, 실존 개인정보 금지). 금액 통화 명시.
- 안전·운영 규칙을 화면에 반영: 상위 정책 완화 불가, prod 변경 확인, 서명 미검증 배포 차단, 키 1회 표시, 비가역 행동 HITL, Manager 끊김 시 fail-static, AGPL/ELv2 구성요소 별도 컨테이너, 로그 PII 마스킹.

## 5. 와이어프레임 규칙
- PRD 15.5 용 PNG: `wire_lib.frame(title, screen_id, stage=…)` + 위젯(card·table·field·button·badge·charts) → `save()`
- pptx 용 도형: `ui_lib.Wire.shell(nav=…, crumb=…, title=…, tabs=…)` → 콘텐츠 x 14.5..99, y 16..95(탭 있으면 21..95)
- 글자 4.4~7pt(라벨 4.4~5.2, 제목 7~8.5). 한 줄 폭 = 글자 수 × 1.1(%) 이상. 표 6행 이하(넘치면 "… 외 N건").
- 색은 의미로만(주동작·정상·주의·오류·L3/외부·정보) + 배지에 텍스트 병기. 레이어 색 = 도식 레이어 색.
- 콜아웃 번호 수 = items 수, 위치 = 해당 요소 좌상단.
- 검사: 화면 3~4개마다 저장 → pptx → `docx2pdf.sh` → `check_report.py --render` 로 **모든 쪽 PNG 를 눈으로 확인**(겹침·넘침·콜아웃 위치).

## 6. 출처 (조사 확보분)
- CBD SW개발 표준 산출물 관리 가이드(2011.12) — https://www.cisp.or.kr/wp-content/uploads/2012/01/20160909_074634.pdf (D2 사용자 인터페이스 설계서, R3 요구사항 추적표)
- 디지털 정부서비스 UI/UX 가이드라인(KRDS, WCAG 2.1 AA) — https://www.krds.go.kr/html/site/utility/utility_07.html
- brunch @mojuns 「기획 산출물 #2 화면 설계서」 — https://brunch.co.kr/@mojuns/10 · john33fiao.dev 「화면정의서」 — https://john33fiao.dev/ux/user-interface-description
- velog @corone_hi 「화면 설계서(SB) 작성」 — https://velog.io/@corone_hi/화면-설계서-작성-방법 · 이랜서 「스토리보드/화면 설계서 작성법」 — https://www.elancer.co.kr/blog/detail/66
- NN/g 「Creating Design Specs for Development」 — https://www.nngroup.com/articles/creating-design-specs-for-development/
- Balsamiq 「How to use wireframe annotations」 — https://balsamiq.com/blog/wireframe-annotations/ · DECODE 「Wireframe annotations: A complete guide」 — https://decode.agency/article/wireframe-annotations/
(인용 시 조사 시점에 다시 접근해 확인. 접근 실패 시 [미확인].)
