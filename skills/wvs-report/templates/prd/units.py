# -*- coding: utf-8 -*-
"""단위 에이전트 카탈로그 정본 — 원본 도식의 세부 항목 1개 = 마이크로 에이전트 1개.
(단위 ID, 도메인, 레이어, 에이전트명, 원본 도식 요소(원문), 책임, A2A skill id, 기본 배포 이미지)

작성 규칙
- 구조 원천 = 도식 이미지가 있으면 그 레이어 띠 → 레이어(L1·L2·L3 …), 번호 카드 → 도메인(2~4자 대문자), 카드 속 흐름 단계·아이콘 타일·불릿 → 단위(DOMAIN-ITEM).
  도식이 없고 요구사항 문서만 있으면 문서의 장(Epic) → 도메인, 기능 묶음(Feature) → 단위. UI 시안 이미지는 화면 구성의 원천으로 쓴다.
- '원본 도식 요소' 열에 카드 문구·타일 이름(또는 `IN-02 §3 RQ-002…` 처럼 입력 ID·절·RQ)을 원문 그대로 적는다(21장 추적표가 이 열을 쓴다). 도식에 없는 보완 단위는 '(도식 누락 — 보완)'.
- 에이전트형 시스템이면 단위 = 마이크로 에이전트(A2A skill), 아니면 단위 = 독립 배포 모듈·서비스(A2A skill 열은 "-").
- 플랫폼(PLT-*)과 공통(X-*)은 요청 6항·5항에서 온다. 단위 ID 는 FR ID(FR-<단위ID>-NN) 접두로 그대로 쓰인다.
"""
BRAND_SLUG = "{brand}"      # 이미지 이름 접두(예: atlas)

UNITS = [
    # L1 · 01 {개념 A}
    ("AL-PLAN", "AL", "L1", "Planner", "PLAN (클립보드 아이콘) — '{카드 문구}'", "목표를 단계 계획으로 분해하고 재계획", "loop.plan", f"{BRAND_SLUG}/agent-al-plan"),
    ("AL-ACT", "AL", "L1", "Actor", "ACT (▶ 아이콘)", "선택된 행동을 도구 호출·위임으로 실행", "loop.act", f"{BRAND_SLUG}/agent-al-act"),
    # … 도식의 모든 세부 항목
    # 하단 띠
    ("MAT", "MAT", "띠", "Maturity Assessor", "{하단 흐름 띠 원문}", "성숙도 점수·진단·로드맵", "mat.assess", f"{BRAND_SLUG}/agent-mat"),
    # 플랫폼 (요청 6항)
    ("PLT-MGR", "PLT", "P", "Agent Manager", "(요구 6항) 에이전트 관리", "등록·수정·삭제·검색·의존성·버전 카탈로그", "plt.manager", f"{BRAND_SLUG}/manager"),
    ("PLT-DEP", "PLT", "P", "Deploy Controller", "(요구 6항) 배포", "로컬·compose·Kubernetes 배포, 카나리·롤백·스케일·헬스", "plt.deploy", f"{BRAND_SLUG}/manager (모듈)"),
    ("PLT-TEN", "PLT", "P", "Tenant Manager", "(요구) 기업관리", "기업·프로젝트·환경·쿼터·정책 상속", "plt.tenant", f"{BRAND_SLUG}/manager (모듈)"),
    ("PLT-IAM", "PLT", "P", "IAM", "(요구) 사용자·권한", "OIDC SSO·SCIM·RBAC/ABAC·서비스 계정·감사", "plt.iam", f"{BRAND_SLUG}/manager (모듈)"),
    ("PLT-SEC", "PLT", "P", "Secrets", "(요구) 키 관리", "비밀 보관·주입·회전", "plt.secrets", f"{BRAND_SLUG}/manager (모듈)"),
    ("PLT-PKG", "PLT", "P", "Packaging", "(요구 6항) 설치 패키지", "멀티플랫폼 설치 패키지·설치 마법사·오프라인 번들", "-", "빌드 파이프라인"),
    ("PLT-REL", "PLT", "P", "Release", "(요구 6항) 릴리스 방법", "SemVer·채널·서명·SBOM·provenance·자동 업데이트", "-", "빌드 파이프라인"),
    ("PLT-CON", "PLT", "P", "Console", "(요구 2항) UI/UX", "웹·데스크톱 콘솔 셸, 도식형 개요 맵, CLI", "-", f"{BRAND_SLUG}/console · desktop"),
    # 공통 (요청 5항 — 유사 시스템 공통 기능, 4장 판정으로 확정)
    ("X-WSP", "X", "X", "Workspace & Home", "(유사 시스템 공통)", "홈·즐겨찾기·검색·작업공간", "-", f"{BRAND_SLUG}/manager (모듈)"),
    ("X-HITL", "X", "X", "Approval Inbox", "(도식 누락 — 보완)", "비가역 행동·정책 예외 승인함", "x.hitl", f"{BRAND_SLUG}/manager (모듈)"),
    ("X-NTF", "X", "X", "Notifications", "(유사 시스템 공통)", "알림 규칙·채널", "-", f"{BRAND_SLUG}/manager (모듈)"),
]

# 도메인(도식 카드) 정의 — (도메인 ID, 레이어, 이름(도식 표기), 요지(카드 흐름/타일 원문), [단위 ID…]) — 도식 순서
_DOM_META = [
    ("AL", "L1", "01 {개념 A}", "{카드 흐름 원문}"),
    ("MAT", "띠", "{하단 띠}", "{띠 원문}"),
    ("PLT", "P", "플랫폼", "Agent Manager · 배포 · 기업/테넌트 · IAM · 비밀 · 패키지 · 릴리스 · 콘솔"),
    ("X", "X", "공통 기능", "유사 시스템 공통 기능"),
]
DOMAINS = [(d, l, n, s, [u[0] for u in UNITS if u[1] == d]) for d, l, n, s in _DOM_META]
UNIT = {u[0]: u for u in UNITS}
AGENT_UNITS = [u for u in UNITS if u[1] not in ("PLT", "X")]
assert len(UNITS) == len(UNIT), "단위 ID 중복"
assert all(u[1] in {d[0] for d in _DOM_META} for u in UNITS), "도메인 미정의 단위"
