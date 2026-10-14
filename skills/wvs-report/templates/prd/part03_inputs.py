# -*- coding: utf-8 -*-
# 3장 입력 분석·세부 항목 상세화 — research/_INPUTS.md(입력별 전사·요약, 입력 간 충돌·결정) + req_items.tsv(RQ) + units.py.
H("3. 입력 분석·세부 항목 상세화", 1)
_INP_MD = os.path.join(RES, "_INPUTS.md")
_parts = M.subsections(open(_INP_MD, encoding="utf-8").read()) if os.path.exists(_INP_MD) else []
H("3.1 입력별 전사·요약", 2)
P("각 입력(IN-NN)을 직접 읽고 전사·요약했다 — 도식은 레이어·카드·흐름·타일 원문, UI 시안은 화면·영역·컴포넌트, 참고 사이트는 기능·정보 구조·UI 패턴, 요구사항 문서는 목표·범위.")
for title, body in _parts:
    if title.startswith("입력별"):
        M.render(r, body, size=8.8, sub_level=3)
H("3.2 요구사항 문서 정리 (RQ)", 2)
P("요구사항·개발방향 문서와 요청문에서 추출해 검토한 요구 항목이다. 기능·UI·비기능·제약 항목은 모두 FR·NFR·장으로 이어진다(미매핑이면 빌드 게이트 실패).")
req_table()
H("3.3 단위 카탈로그", 2)
T(["단위 ID", "레이어", "이름", "원천 요소(원문·입력·RQ)", "책임"],
  [[u[0], u[2], u[3], u[4], u[5]] for u in UNITS], widths=W([1.8, 1.0, 2.8, 5.6, 6.4]), font=6.6)
H("3.4 입력 간 충돌·결정", 2)
for title, body in _parts:
    if title.startswith("입력 간 충돌"):
        M.render(r, body, size=8.8, sub_level=3)
