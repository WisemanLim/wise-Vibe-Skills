# -*- coding: utf-8 -*-
"""Summary-Repos 보고서 고유 값 — <Project>/_assets/content/extra.py
{ } = 첨부 이미지/링크에서 자동 추출, [ ] = 첨부에서 도출한 세부 분류·분석 결과. 순수 파이썬(import 없음)."""
CFG = dict(
    PROJECT="{Python-Tools-for-AI-Projects}",                  # 프로젝트 디렉토리명(= 클론 루트)
    TITLE="{Python Tools for AI Projects}",                    # 표지 제목(인포그래픽 대제목 정리)
    SUBTITLE="{AI 프로젝트용 Python 도구 38종} 오픈소스 저장소 요약 보고서 (Summary-Repos)",
    INFOGRAPHIC="{Python Tools You Need for AI Projects}",     # 인포그래픽 원제
    AUTHOR="{Brij Kishore Pandey (@brijpandeyji)}",            # 원저작자(도식 표기) — 모르면 '[미확인]'
    SOURCE_URL="",                                             # 첨부가 링크면 URL
    INFOGRAPHIC_DESC="{10개 분류 박스가 중앙 로고에 연결되고 각 분류에서 3~4개 도구 로고가 뻗는 방사형 구성}",
    # 흐름(수명주기) 지도 — 분류를 업무 흐름 단계로 재배치. 단계 순서대로, 횡단(cross) 영역은 별도
    FLOW_TITLE="[AI 프로젝트 수명주기]",
    STAGES=[("S1 데이터", ["02-Data-Preprocessing-Management"]), ("S2 모델링", ["03-Machine-Learning-Frameworks"])],
    CROSS=[("횡단 — 보안·프라이버시", ["01-Model-Data-Security"])],
    FLOW_READING="**읽는 법.** … 단계별로 한 도구씩 고르면 최소 스택이 된다.",
    DISPLAY={"OpenMined-TenSEAL": "OpenMined (TenSEAL)"},     # 디렉토리명 → 인포그래픽 표기명(다를 때만)
    SELECTION_RULES="① 공식 저장소(조직 계정) ② 이전된 경우 현재 소유 저장소 ③ 조직·플랫폼·비공개 SDK 항목은 대표 저장소로 대체하고 사유를 해당 절에 명시",
    COMMON=["**공통 특징 1** — 실측 근거 문장", "…"],          # 1장 '공통 특징' 불릿(수치는 sr_data 실측과 일치시킬 것)
    FINDINGS=["**핵심 발견 1** — …"],                          # 인포그래픽 검증 장 '핵심 발견'
    ADOPTION_NOTES=["**버전 하한/상한** — …", "**보안 기본값** — …"],  # 라이선스 장 '도입 시 공통 유의'
    SCENARIOS=dict(header=["시나리오", "단계 A", "단계 B", "단계 C", "단계 D"],
                   rows=[["과제 유형 1", "도구 (대체)", "…", "…", "…"]],
                   notes=["**환경 분리 주의.** …"]),
)
