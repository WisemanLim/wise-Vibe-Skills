# -*- coding: utf-8 -*-
"""화면 목록 정본 — PRD 15.4 화면 목록 · 15.5 와이어프레임 · 화면설계서(pptx) 공통.
SCREENS 튜플: (화면 ID, 화면명, 라우트, 권한, PRD 추적(공백 구분 FR ID), 우선순위, 유형 P/M/W, 목적(영역별 구성 — 상호작용), 그룹 코드)
- 그룹 코드 = 내비 그룹(도식 레이어·카드 순서) — GROUPS 에 정의
- 모든 FR 이 최소 1개 화면의 PRD 추적 열에 있어야 한다(build_prd 게이트). 비화면 FR(백엔드·파이프라인)은 그 설정·상태를 보여주는 화면에 매핑.
- WIREFRAMES: PRD 15.5 에 와이어프레임 PNG 로 싣는 핵심 화면 ID (15~25개 — 개요 맵, 카드별 개요, 관리·배포·설치 위저드 등)
"""
GROUPS = [  # (그룹 코드, 그룹명, 내비 레이어 키)
    ("INS", "설치", "Platform"), ("AUT", "로그인·진입", "홈"), ("HOM", "홈·개요 맵", "홈"),
    ("AL", "01 {개념 A}", "L1"),
    ("MGR", "에이전트 관리·배포", "Platform"), ("TEN", "기업·사용자·권한", "Platform"), ("X", "공통", "공통"),
]
SCREENS = [
    ("S001", "설치 마법사 — 시작", "(installer)", "설치자", "FR-PLT-PKG-01", "P0", "W", "언어·라이선스 동의·설치 모드 선택 — 다음/취소", "INS"),
    ("S010", "개요 맵", "/p/{proj}/home", "전체", "FR-PLT-CON-01", "P0", "P", "원본 도식 레이아웃(레이어 띠·번호 카드) 위에 에이전트 상태·지표 겹침 — 카드 클릭 시 개념 화면", "HOM"),
]
WIREFRAMES = ["S010"]
SID = {s[0]: s for s in SCREENS}


def screens_of(fr_id):
    return [s[0] for s in SCREENS if fr_id in s[4].split()]
