# 화면 스펙 파일 작성 지침 (ui_screens_<key>.py) — 서브에이전트용

## 목적
`<Brand>_UI_Design.pptx`(화면설계서)를 **표준 양식 빌더 `build_ui.py`** 로 만든다. 화면 하나 = 슬라이드 하나:
상단 메타표 + 설명 + 좌측 와이어프레임(편집 가능한 도형, ①②③ 콜아웃) + 우측 기능 설명 표 + 하단 관련 FR + 발표자 노트.
기준 문서는 PRD `<FILE_STEM>.docx`. 구현팀은 PRD 와 화면설계서만 보고 구현하므로 **화면의 FR 이 하나라도 빠지면 안 된다.**

## 절대 규칙
- `build_ui.py` · `ui_lib.py` · `ui_design_data.py` · `ui_spec.py` · 다른 담당 파일은 **수정하지 않는다**. 새 빌더·새 양식을 만들지 않는다.
- 담당 키 `<key>` 의 화면(`ui_ids.FILES[<key>]` 그룹)을 **전부, ui_design_data.SCREENS 순서대로** 만든다. ID·이름·경로·권한·우선순위·fr 은 정본 값 그대로.
- 형식은 `ui_screens_example.py` 를 따른다(헬퍼 `panel · lines · checks · co · note · kpi · spark` 와 위젯은 `from ui_lib import *` 로 사용).

## 먼저 읽을 파일
1. `ui_screens_example.py` — 위저드(frame+stepper)·페이지(shell+KPI+탭+표+패널)·모달(dialog) 작성 예.
2. `<툴킷>/ui_lib.py` 의 `Wire` — `shell(nav=, crumb=, title=, tabs=, active_tab=)`(콘텐츠 x 14.5..99, y 16..95 / 탭 있으면 21..95),
   `frame(title, os_name=)`(x 2..98, y 9..98), `terminal(title, lines)`, `dialog(title, w, h)`(반환 = 내용 영역), 위젯 `box t btn input select toggle check radio badge dot bar tbl code tabs stepper card chat health empty`.
3. `../ui_design_data.py` — SCREENS·GROUPS·USERS·COMPONENTS(CMP)·STATES(ST)·MESSAGES(MSG). FR 정본은 `FR[id]` = (ID, 이름, 하는 일, 구현 요지, P, OSS, 근거, 단위).
4. `../ui_spec.py` — 내비(NAV)·셸 가상 데이터(SHELL)·그룹→nav 키(GROUP_NAV).
5. PRD 의 해당 장(FR 표, 15장 UI/UX, 입력 이미지·UI 시안 `<Brand>_assets/inputs/IN-NN.*` — 시안이 있으면 그 배치를 따른다).

## 화면 스펙
```python
S(id="S020", name="개요", path="/home", kind="페이지", section="HOM. 홈·개요", perm="전체", prio="P0",
  desc="목적·핵심 동작 2~3문장(PRD FR 요지).",
  fr=["FR-…", …],                      # 정본 PRD 추적 열 그대로(전부, 같은 순서)
  items=[(1, "구성요소", "유형", "기능 설명/동작 — 검증·상태·전이·예외·안전 규칙(40~90자)", "연계: FR·S…·MSG·ST·CMP"), …],   # 5~9행
  wire=w_s020,
  notes="상태(ST)·메시지(MSG)·권한별 차이·예외 흐름·API·이벤트·단축키")
```
- **fr 의 모든 ID 가 items 연계 열에 최소 한 번** — FR 이 많으면 한 행에 2~3개를 묶는다(빌드 assert).
- **콜아웃 수 = items 수**, 위치 = 해당 요소 좌상단(`co(w, [(x, y), …])`, 빌드 assert).
- kind: 페이지 · 모달 · 위저드(N단계 중 k) · 탭·드로어 · 공통 규약. 위저드는 `frame()+stepper()`, 모달은 `dialog()`.

## 와이어프레임 품질 기준 (이전 화면설계서와 같은 밀도)
- 실제 운영 화면처럼 **가상 데이터로 채운다**: KPI 카드·탭·필터·표(4~6행, 실제 같은 값)·패널·상태 점·배지·버튼·안내 배너·차트(spark).
- 금지: 빈 박스, FR ID 나열 박스, "(설명)" 자리표시, 화면 대부분이 비어 있는 배치.
- 글자 4.4~7(라벨 4.4~5.2, 제목 6~8.5). 한 줄 폭 ≥ 글자 수 × 1.1(%). 표 6행 이하, 넘치면 "… 외 N건". 같은 텍스트에 `$` 두 개 금지.
- 색은 의미로만(배지·점에는 텍스트 병기). 실존 개인정보 금지(가상 기업·사람·값).
- 안전 규칙 반영: 비가역 동작은 확인/승인 모달(MSG-002·HITL), 권한 없음은 비활성+사유(ST-04), 키·비밀은 1회 표시, 로그 PII 마스킹.

## 검사 (화면 3~4개마다 저장 후 실행)
```bash
cd <Brand>_UI_assets/pptx
<venv>/bin/python build_ui.py --stub          # 아직 없는 파일은 스텁으로 — 구조·assert 확인
<venv>/bin/python <툴킷>/check_ui_design.py ../stub_<Brand>_UI_Design.pptx --pdf --render /tmp/ui_<key>
```
렌더된 **담당 화면 모든 쪽을 직접 열어** 텍스트 겹침·표 넘침·콜아웃 위치·빈 영역을 확인하고 고친다.
최종 보고(15줄 이내): 화면 수 · assert 결과 · 확인한 쪽 · 남은 문제.
