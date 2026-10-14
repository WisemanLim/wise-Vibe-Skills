# 멀티플랫폼 설치 패키지 · 독립 배포 · 릴리스 기준 (요청 6항 대응)

요청 6항: "설치용 패키지는 멀티플랫폼을 지원하며 릴리스 방법을 포함. 에이전트는 개별·독립 구동 및 배포 가능,
에이전트를 관리(등록·수정·삭제·배포)하는 매니징(오케스트레이터 포함 Multi-Agent Systems)도 구동·배포 가능."
PRD 11장(플랫폼)·14장(아키텍처)·18장(패키지·릴리스)과 PLT-* FR 이 아래를 빠짐없이 다뤄야 한다. 기술 선택은 조사(r6_platform)에서 실측 근거로 확정한다.

## 1. 독립 실행 규격 (Agent Spec) — 모든 단위 에이전트 공통
| 요소 | 요구 |
|---|---|
| manifest | `<brand>-agent.yaml` (apiVersion · kind: Agent · metadata(id·unit·layer·version SemVer·owner) · spec(a2a skills·card 경로, config schema, secrets 참조, resources, events pub/sub, health)) |
| 엔드포인트 | A2A 서버(`/.well-known/agent-card.json`, message/send · stream · tasks/get), `/healthz` `/readyz` `/metrics`(Prometheus), OTel trace export |
| 설정·비밀 | 환경변수 > 파일 > Manager push 우선순위, 비밀은 참조만(Vault/OpenBao/SOPS/KMS), 마지막 정상 설정으로 계속 동작(fail-static) |
| 단독 실행 | `docker run …`, `pip install <brand>-agent-<id> && <brand>-agent-<id>`, 단일 바이너리 — **Manager 없이** 동작 |
| 외부 에이전트 | 규격을 만족하는 다른 프레임워크의 A2A 에이전트도 등록 가능 |

## 2. 배포 단위와 실행 모드
| 배포 단위 | 단독 배포 형태 |
|---|---|
| 단위 에이전트 | OCI 이미지(linux/amd64·arm64) · wheel/npm · 단일 바이너리 · Helm 서브차트 · compose 서비스 |
| 에이전트 세트(레이어 번들) | compose profile · Helm umbrella values on/off |
| Multi-Agent System(오케스트레이터 + 팀 + 구성 버전) | System manifest · CRD(AgentSystem) |
| Manager(컨트롤 플레인: 레지스트리·배포·테넌트·IAM·비밀·콘솔 서빙) | 단일 바이너리(SQLite 단일 노드) · OCI · Helm(+Operator) · systemd/launchd/Windows Service |
| 콘솔 | 웹 SPA(Manager 내장) · 데스크톱(Tauri 2 권장 — dmg · MSI/NSIS · AppImage/deb/rpm) |
| CLI | tar.gz/zip · Homebrew · winget · Scoop · deb/rpm · `curl … | sh` 설치 스크립트 |

실행 모드 4종(같은 manifest): `local`(프로세스) · `compose` · `kubernetes`(Helm/Operator) · `edge/airgap`(번들).

## 3. 설치 패키지 매트릭스 (OS × arch × 형식)
| OS | arch | 형식 | 서명 |
|---|---|---|---|
| macOS 13+ | arm64 · amd64(universal) | dmg(앱) · pkg · Homebrew tap · tar.gz | Apple Developer ID + notarization |
| Windows 10/11 | amd64 · arm64 | MSI/NSIS(앱) · winget · Scoop · zip | Authenticode(EV 권장) |
| Linux(glibc·musl) | amd64 · arm64 | deb · rpm · AppImage · tar.gz · OCI | GPG(repo) · cosign |
| Kubernetes 1.29+ | amd64 · arm64 | Helm OCI 차트 · Operator(OLM 선택) | cosign · SLSA provenance |

## 4. 릴리스 방법
- 버전: SemVer 2.0, 구성요소별 독립 버전(release-please manifest 또는 changesets), 번들 별칭 YYYY.MM.patch
- 파이프라인: Conventional Commits → 릴리스 PR → 매트릭스 빌드(GoReleaser/cibuildwheel/tauri-action/docker buildx) → **SBOM(Syft, SPDX/CycloneDX)** → 취약점 스캔(Grype/Trivy) → **provenance(SLSA L3, GitHub attestations)** → **서명(cosign keyless + Rekor)** → 채널 게시 → 패키지 매니저 매니페스트 갱신
- 채널: nightly → beta → stable(+LTS). 같은 digest 재태깅으로 승격
- 호환성: Manager N 은 에이전트 N-2 지원, apiVersion 변환 웹훅, DB expand/contract 마이그레이션
- 업데이트: 데스크톱 updater(서명 필수), CLI self-update(서명 검증), K8s 는 알림 + 운영자 승인
- 에어갭: 이미지·차트·SBOM·서명·CLI 단일 번들, 오프라인 레지스트리 적재
- 배포 게이트: 서명·SBOM·provenance 미검증 산출물 배포 차단, eval 점수 게이트(해당 시), 카나리 + 자동 롤백

## 5. 관리면(Agent Manager + Orchestrator) 기능 체크리스트 (PLT-* FR 후보)
등록(manifest 업로드·레지스트리 가져오기·서명 검증) · 수정(설정 버전·diff·승인) · 삭제(의존성 검사·soft delete·보존) · 검색·태그 ·
배포(대상 환경·모드·카나리·롤백·스케일·헬스) · 버전 카탈로그 · Multi-Agent System 구성(오케스트레이터·팀·라우팅 정책) ·
테넌트(기업·프로젝트·환경·쿼터·리전) · IAM(OIDC SSO·SCIM·RBAC/ABAC·서비스 계정·감사) · 비밀 · 알림 · 감사 로그 · 백업/복구 · 지원 번들
