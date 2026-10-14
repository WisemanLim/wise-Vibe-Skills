#!/usr/bin/env bash
#
# deploy-android-play.sh
# 가장 쉬운 Android Google Play 배포. 프로젝트 root 하나만 주면 나머지는 자동 감지.
#
#   ./deploy-android-play.sh [프로젝트_root]        # 기본: 현재 디렉토리
#   ./deploy-android-play.sh /path/to/app
#   ./deploy-android-play.sh /path/to/app --reconfigure   # 계정 정보 다시 입력
#
# 자동 감지: 앱 모듈, applicationId, versionCode(+1 자동), AAB 산출물.
# 계정 연동: 최초 1회만 서비스 계정 JSON 키 경로 입력 -> <root>/.deploy-android.env 저장.
#            이후 실행은 입력 없이 바로 배포. 기본 트랙 internal.

set -euo pipefail
trap 'echo; echo "ERROR: 라인 ${LINENO} 실패 (exit=$?)."; exit 1' ERR

# ---- 인자 ----
ROOT="."
RECONFIGURE=0
for a in "$@"; do
  case "$a" in
    --reconfigure) RECONFIGURE=1 ;;
    *) ROOT="$a" ;;
  esac
done
ROOT="$(cd "$ROOT" && pwd)"
CONFIG="${ROOT}/.deploy-android.env"
LOG_DIR="${ROOT}/build/logs"; mkdir -p "$LOG_DIR"

echo "======================================"
echo " Android Google Play 자동 배포"
echo " 프로젝트: ${ROOT}"
echo "======================================"

# 입력 경로 정규화: ~확장, 둘러싼 따옴표 제거, (필요시) drag&drop 백슬래시 이스케이프 해제.
normalize_path() {
  local p="$1"
  p="${p#"${p%%[![:space:]]*}"}"; p="${p%"${p##*[![:space:]]}"}"
  p="${p/#\~/$HOME}"
  [[ "$p" == \'*\' ]] && p="${p:1:${#p}-2}"
  [[ "$p" == \"*\" ]] && p="${p:1:${#p}-2}"
  if [[ ! -e "$p" && "$p" == *\\* ]]; then
    local u="${p//\\/}"
    [[ -e "$u" ]] && p="$u"
  fi
  printf '%s' "$p"
}

cd "$ROOT"
[[ -f ./gradlew ]] || { echo "ERROR: ./gradlew 없음. Android 프로젝트 root 가 맞는지 확인."; exit 1; }

# ---- 도구 점검 ----
command -v java >/dev/null 2>&1 || { echo "ERROR: java 미설치."; exit 1; }
if ! command -v fastlane >/dev/null 2>&1; then
  echo "fastlane 미설치 -> 설치 시도."
  command -v gem >/dev/null 2>&1 || { echo "ERROR: ruby/gem 필요(fastlane 설치용)."; exit 1; }
  gem install fastlane -NV
fi

# ---- 계정 연동 (최초 1회) ----
if [[ -f "$CONFIG" && "$RECONFIGURE" -eq 0 ]]; then
  # shellcheck disable=SC1090
  source "$CONFIG"
  echo "계정 정보 로드됨: ${CONFIG}"
else
  echo
  echo "[계정 연동] Google Play 서비스 계정 JSON 키를 1회 입력합니다."
  echo "  (Play Console > 사용자 및 권한 / Google Cloud 서비스 계정 JSON)"
  while :; do
    read -rp "  서비스 계정 JSON 키 경로(따옴표/드래그 모두 가능): " JSON_KEY_PATH
    JSON_KEY_PATH="$(normalize_path "$JSON_KEY_PATH")"
    [[ -z "$JSON_KEY_PATH" ]] && { echo "    -> 경로가 비었습니다. 다시 입력 (취소: Ctrl+C)."; continue; }
    [[ -f "$JSON_KEY_PATH" ]] || { echo "    -> 파일 없음: $JSON_KEY_PATH"; continue; }
    JSON_KEY_PATH="$(cd "$(dirname "$JSON_KEY_PATH")" && pwd)/$(basename "$JSON_KEY_PATH")"
    break
  done
  read -rp "  배포 트랙 (internal/alpha/beta/production) [internal]: " TRACK
  TRACK="${TRACK:-internal}"
  cat > "$CONFIG" <<EOF
# Android 배포 계정 정보 (자동 생성). git 에 커밋하지 마세요.
JSON_KEY_PATH="${JSON_KEY_PATH}"
TRACK="${TRACK}"
EOF
  chmod 600 "$CONFIG"
  echo "  저장됨: ${CONFIG} (다음부터 자동 사용)"
fi
TRACK="${TRACK:-internal}"
[[ -f "$JSON_KEY_PATH" ]] || { echo "ERROR: JSON 키 없음: ${JSON_KEY_PATH} (--reconfigure 로 재설정)"; exit 1; }

# ---- 앱 모듈 자동 감지 ----
echo
echo "[1/6] 앱 모듈 / 패키지 자동 감지."
APP_MODULE=""
for m in app mobile android; do
  if [[ -f "${m}/build.gradle" || -f "${m}/build.gradle.kts" ]]; then APP_MODULE="$m"; break; fi
done
if [[ -z "$APP_MODULE" ]]; then
  # com.android.application 플러그인 가진 모듈 탐색
  APP_MODULE="$(grep -rlE "com\.android\.application" --include="build.gradle*" . 2>/dev/null \
    | head -n 1 | xargs -I{} dirname {} | sed "s|^\./||" || true)"
fi
[[ -n "$APP_MODULE" ]] || { echo "ERROR: 앱 모듈 자동 감지 실패."; exit 1; }
echo "  모듈: ${APP_MODULE}"

BUILD_FILE="${APP_MODULE}/build.gradle.kts"
[[ -f "$BUILD_FILE" ]] || BUILD_FILE="${APP_MODULE}/build.gradle"

PACKAGE_NAME="$(grep -E "applicationId" "$BUILD_FILE" | head -n 1 | sed -E 's/.*applicationId[ =]*"([^"]+)".*/\1/' || true)"
[[ -n "$PACKAGE_NAME" ]] || { echo "ERROR: applicationId 자동 감지 실패 ($BUILD_FILE)."; exit 1; }
echo "  패키지: ${PACKAGE_NAME}"

# ---- versionCode 자동 증가 ----
echo
echo "[2/6] versionCode 자동 증가."
CUR_VC="$(grep -E "versionCode" "$BUILD_FILE" | head -n 1 | grep -oE "[0-9]+" | head -n 1 || true)"
if [[ -n "$CUR_VC" ]]; then
  NEW_VC=$((CUR_VC + 1))
  cp "$BUILD_FILE" "${BUILD_FILE}.bak"
  # kts: versionCode = N / groovy: versionCode N
  perl -0pi -e "s/versionCode(\\s*=\\s*|\\s+)[0-9]+/versionCode\${1}${NEW_VC}/" "$BUILD_FILE"
  echo "  versionCode: ${CUR_VC} -> ${NEW_VC} (백업: ${BUILD_FILE}.bak)"
else
  echo "  WARN: versionCode 자동 감지 실패. 기존 값 사용."
fi

# ---- release AAB 빌드 ----
echo
echo "[3/6] release AAB 빌드 (시간이 걸립니다)."
chmod +x ./gradlew
./gradlew clean "${APP_MODULE}:bundleRelease" 2>&1 | tee "${LOG_DIR}/android-build.log"

# ---- AAB 탐색 ----
echo
echo "[4/6] AAB 산출물 탐색."
AAB_PATH="$(find "${APP_MODULE}/build/outputs/bundle" -type f -name '*.aab' | sort | tail -n 1 || true)"
[[ -n "$AAB_PATH" ]] || { echo "ERROR: .aab 못 찾음. release 서명 설정 확인."; exit 1; }
echo "  AAB: ${AAB_PATH}"

# ---- 키 검증 ----
echo
echo "[5/6] 서비스 계정 키 검증."
fastlane run validate_play_store_json_key json_key:"${JSON_KEY_PATH}"

# ---- 업로드 ----
echo
echo "[6/6] Google Play 업로드 (track=${TRACK})."
fastlane supply \
  --aab "${AAB_PATH}" \
  --json_key "${JSON_KEY_PATH}" \
  --package_name "${PACKAGE_NAME}" \
  --track "${TRACK}" \
  --skip_upload_apk true \
  --skip_upload_images true \
  --skip_upload_screenshots true \
  --skip_upload_metadata true 2>&1 | tee "${LOG_DIR}/android-upload.log"

echo
echo "완료. Play Console > 테스트(${TRACK}) 트랙에서 릴리스 확인."
echo "  ${PACKAGE_NAME}  versionCode ${NEW_VC:-$CUR_VC}"
