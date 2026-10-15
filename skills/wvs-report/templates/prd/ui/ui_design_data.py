# -*- coding: utf-8 -*-
"""화면설계서 정본 데이터 — <Brand>_UI_assets/ui_design_data.py (wvs-report prd 템플릿).
화면 목록·그룹은 PRD 와 **같은 정본**(<Brand>_assets/ui_data.py)을 그대로 쓴다 — 화면 ID 가 PRD 15.4 화면 목록과 1:1.
FR 은 PRD 의 data_fr.py 에서 import. 여기서는 화면설계서에만 필요한 데이터(사용자 유형·그룹 설명·컴포넌트·상태·메시지)를 채운다.

SCREENS 튜플(PRD ui_data 와 동일): (화면 ID, 화면명, 라우트, 권한, PRD 추적(FR 공백 구분), 우선순위, 유형 P/M/W/T/C, 목적(영역별 구성 — 상호작용), 그룹 코드)
유형: P 페이지 · M 모달 · W 위저드 · T 탭·드로어·패널 · C 공통 규약
"""
import glob, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
_PRD = next((d for d in sorted(glob.glob(os.path.join(os.path.dirname(HERE), "*_assets")))
             if not d.endswith("_UI_assets") and os.path.exists(os.path.join(d, "data_fr.py"))), None)
assert _PRD, "PRD 자산 폴더(<Brand>_assets/data_fr.py)를 찾지 못했습니다 — 화면설계서는 PRD 와 같은 출력 폴더에 둔다"
sys.path.insert(0, _PRD)
from data import SYSTEM, FILE_STEM, VERSION as PRD_VER                         # noqa: E402
import datetime as _dt
PRD_DATE = os.environ.get("WVS_DOC_DATE") or _dt.date.fromtimestamp(os.path.getmtime(os.path.join(_PRD, "data.py"))).isoformat()
from data_fr import ITEMS, FR, DOMAINS                                         # noqa: E402
import ui_data as _PU                                                          # noqa: E402  (PRD 화면 정본)

PRD_FILE = FILE_STEM + ".docx"
FR_TOTAL = len(FR)
SCREENS = list(_PU.SCREENS)
# 그룹: (코드, 이름, 설명, 주 사용자) — 이름은 PRD 정본, 설명·사용자는 여기서 채운다
_DESC = {
    # "INS": ("설치 마법사·사전 점검·구성 요소·완료", "설치자"),
}
GROUPS = [(c, n, _DESC.get(c, ("", ""))[0], _DESC.get(c, ("", ""))[1]) for c, n, *_ in _PU.GROUPS]

# 사용자 유형: (ID, 이름, 역할(RBAC), 목표) — PRD 5.2 사용자와 역할
USERS = [
    ("U1", "{운영자}", "Operator", "{목표}"),
    ("U2", "{관리자}", "Admin", "{목표}"),
]

# 공통 컴포넌트: (ID, 이름, 용도, 상태·변형, 규칙)
COMPONENTS = [
    ("CMP-01", "버튼", "주 동작·보조·위험", "기본·hover·disabled·loading", "위험 동작은 확인 대화상자(MSG-002)"),
    ("CMP-02", "검색·필터 바", "목록 필터", "기본·적용됨·초기화", "필터 상태는 URL 쿼리에 유지"),
    ("CMP-03", "데이터 표", "목록", "로딩·빈·오류·선택", "가상 스크롤·열 정렬·CSV 내보내기"),
]
# 상태: (ID, 이름, 발생, 화면 표현)
STATES = [
    ("ST-01", "로딩", "조회·저장 중", "스켈레톤 · 300ms 이후 표시"),
    ("ST-02", "빈 상태", "데이터 없음", "안내 문구 + 첫 동작 버튼"),
    ("ST-03", "오류", "요청 실패", "오류 배너 + 재시도 · 상세 펼치기"),
    ("ST-04", "권한 없음", "역할 부족", "동작 비활성 + 사유 툴팁(숨기지 않음)"),
]
# 메시지: (ID, 상황, 종류, 문구 ko, 문구 en) — {변수} 는 런타임 치환
MESSAGES = [
    ("MSG-001", "저장 성공", "토스트", "저장했습니다.", "Saved."),
    ("MSG-002", "삭제 확인", "확인", "{name} 을(를) 삭제할까요? 되돌릴 수 없습니다.", "Delete {name}? This cannot be undone."),
    ("MSG-003", "권한 없음", "안내", "이 작업은 {role} 권한이 필요합니다.", "This action requires the {role} role."),
    ("MSG-004", "입력 오류", "인라인", "{field} 형식이 올바르지 않습니다.", "{field} is invalid."),
]

# ---- 정합성 검사
_ids = [s[0] for s in SCREENS]
assert len(_ids) == len(set(_ids)), "화면 ID 중복"
_cov = {f for s in SCREENS for f in s[4].split()}
assert not (_cov - set(FR)), ("PRD 에 없는 FR", sorted(_cov - set(FR))[:10])
assert set(FR) <= _cov, ("화면에 매핑 안 된 FR", sorted(set(FR) - _cov)[:10])
assert {s[8] for s in SCREENS} <= {g[0] for g in GROUPS}, "GROUPS 에 없는 그룹 코드"
