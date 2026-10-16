# -*- coding: utf-8 -*-
"""보고서 구성 — wvs-report deep. 값은 전부 첨부 자료 전사(research/_SPEC.md)와 조사 결과로 채운다.
{ } 표기 = 첨부에서 자동 추출되는 값(제목·원저자·범주 등), [ ] 표기 = 첨부에서 도출된 세부 분석 축(장·절 구성)."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
# 출력 폴더 = 이 자산 폴더(<Title>_assets)의 상위. 규칙(scripts/out_dir.py): <root>/Miscellaneous-Data 가 있으면 그곳, 없으면 <root>
OUT_DIR = os.path.dirname(HERE)
ROOT = os.path.dirname(OUT_DIR) if os.path.basename(OUT_DIR) == "Miscellaneous-Data" else OUT_DIR
TITLE_FILE = "{OCR+PDF Extractors}"                     # 보고서 제목 = 파일명(확장자 제외)

CFG = dict(
    TITLE="{OCR + PDF Extractors}",                                   # 도식 대제목 그대로(파일명과 같게)
    SUBTITLE="{The document parsing landscape} — {4}개 범주 · {18}개 오픈소스 도구 상세 분석 보고서",
    TAGLINE="[범주(도구 …) 나열] 를 [정의 · 소스 저장소 · 설치·환경설정 · 사용방법 · 동작방식] 으로 상세화하고, …까지 정리한 분석 문서",
    SOURCE="{인포그래픽 'OCR + PDF EXTRACTORS — Open-source tools worth knowing for AI engineers' — 작성자 (도식 표기)}",
    EXTRA_SOURCES="",                                                  # 예: 'ISO 32000 · OmniDocBench, 본 보고서 실측 실험(Apple M5 Max)'
    OUT=os.path.join(OUT_DIR, TITLE_FILE + ".docx"),
    OUT_LABEL=os.path.normpath(os.path.join(os.path.basename(ROOT), os.path.relpath(OUT_DIR, ROOT), TITLE_FILE + ".docx")) + " (+ .pdf)",
    PURPOSE=[
        "분석 대상은 인포그래픽 **'{제목}'** … 도식의 범주·항목·핵심 주장 요약(원문 인용).",
        "본 보고서의 목적은 … ① 전사·현행 대조 ② [항목별 상세화 축] ③ … ④ 도식 누락 보완 ⑤ 활용·구현·확장.",
    ],
    METHOD=[  # (방법, 설명) — 저장소 실측·논문 검증·판정·제외 행은 빌더가 자동 추가
        ("원문 전사", "도식 이미지를 범주 라벨 · 항목명 · 주소 · 푸터 · 말풍선 단위로 전사 (2장)"),
        ("범주별 조사", "r1~rN 조사 단위로 병렬 조사. 공식 저장소 README · 코드 · 릴리스 노트 · 문서 · 논문 1차 출처 우선"),
    ],
    TOC_TABLE=[["1~2", "-", "개요, 원문 도식 전수 정리"], ["3", "{범주 1}", "…"]],
    SOURCE_DESC="원본 인포그래픽(가로×세로 px)은 … 배치를 설명한다. 아래는 원본이며, 그다음은 본 보고서가 다시 그린 재구성도다.",
    # 입력 = 첨부 이미지 · 첨부 파일(md 등) · 첨부 사이트. 입력 표는 research/inputs.json(prd_intake.py)에서 자동 생성.
    # 이미지가 여러 장이면 SOURCE_IMAGES=[(파일, 캡션, 출처)…], 이미지가 없으면(md·사이트만) 그림 없이 진행한다.
    SOURCE_IMAGE="source_infographic.png",
    SOURCE_CAPTION="원본 인포그래픽 '{제목}'",
    SOURCE_CREDIT="{원저작자} · 사용자 첨부 이미지, 분석 목적 인용",
    RECON_FIGS=[("fig_landscape.png", "{N} 범주 × {M} 항목 재구성 (본 보고서 정리)", 16.5)],
    TRANSCRIPTION=[("범주별 전사와 저장소 현행 대조", "| 범주 | 항목 | 도식 주소 | 현행 저장소 | ★ | 라이선스 | 상세 |\n|---|---|---|---|---|---|---|\n| … |")],
    # 조사 장: blocks = [(파일태그, 블록KEY, [그림(앞)], [그림(뒤)])] — 그림 = (파일, 캡션, 폭cm, 출처)
    CHAPTERS=[
        dict(title="{범주 1} — {한 줄 설명}", intro="도식 첫 범주 … 를 다룬다.",
             blocks=[("r1", "FND_X", [("fig_x.png", "원리 그림 (본 보고서 정리)")]), ("r1", "TOOL_A"), ("r1", "CMP_X")]),
        dict(title="도식 누락 보완", intro="도식에 없지만 빠질 수 없는 요소 …", blocks=[("r5", "GAP_TOOLS")]),
        dict(title="벤치마크와 통합 비교", intro="", blocks=[("r6", "VAL_COMPARE")]),
        dict(title="사용 및 활용용도", intro="", blocks=[("r6", "VAL_USE")]),
        dict(title="통합 구현 가이드 — 참조 아키텍처와 참조 구현", intro="", blocks=[("r6", "VAL_ARCH")], module=None),  # module="p_impl" 로 실행 결과 장 추가
        dict(title="확장방안 — 성숙도 로드맵 · 운영", intro="", blocks=[("r6", "VAL_ROADMAP")]),
        dict(title="라이선스 · 보안 · 거버넌스", intro="", blocks=[("r6", "VAL_GOV")]),
    ],
    EXTRA_VERDICTS=[],          # [["2장", "도식 항목", "누락", "근거"]] — 조사 블록 밖 판정(전사·실측)
    VERDICT_SUMMARY=["총평 — 도식의 뼈대가 근거와 부합하는지, 누락·해석주의의 성격, 사용 시 보정할 점."],
    CONCLUSION=["결론 문단 …"],
    RECOMMEND=["권고 1 …", "권고 2 …"],
    APPENDIX_FIGS=[("fig_stars.png", "항목별 GitHub ★ 와 라이선스(SPDX)", 15.5)],
    PRIMARY_SOURCES=[
        "{원본 인포그래픽 제목} — {원저작자} ({웹 주소}, 도식 표기). 게시 플랫폼·게시일 [미확인]. 도식 속 제품명은 각 소유자의 상표. 2장에 분석 목적으로 인용",
        "본 보고서의 재구성 그림(fig_*.png)은 원본 도식 · 조사 자료 · 실측 결과를 바탕으로 본 보고서가 matplotlib 으로 새로 그린 것",
    ],
)
