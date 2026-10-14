#!/usr/bin/env bash
#
# deploy-ios-testflight.sh
# 가장 쉬운 iOS TestFlight 배포. 프로젝트 root 하나만 주면 나머지는 자동 감지.
#
#   ./deploy-ios-testflight.sh [프로젝트_root]      # 기본: 현재 디렉토리
#   ./deploy-ios-testflight.sh /path/to/app
#   ./deploy-ios-testflight.sh /path/to/app --reconfigure   # 계정 정보 다시 입력
#
# 자동 감지: .xcworkspace/.xcodeproj, scheme, bundle id, 버전, 빌드번호(+1 자동).
# 계정 연동: 최초 1회만 App Store Connect API Key 입력 -> <root>/.deploy-ios.env 저장.
#            이후 실행은 입력 없이 바로 배포.

set -euo pipefail
trap 'echo; echo "ERROR: 라인 ${LINENO} 실패 (exit=$?)."; exit 1' ERR

# ---- 인자 ----
ROOT="."
RECONFIGURE=0
REUSE_ARCHIVE=0
for a in "$@"; do
  case "$a" in
    --reconfigure) RECONFIGURE=1 ;;
    --reuse-archive) REUSE_ARCHIVE=1 ;;   # 기존 .xcarchive 재사용(재컴파일 생략). 서명/업로드만 재시도할 때.
    *) ROOT="$a" ;;
  esac
done
ROOT="$(cd "$ROOT" && pwd)"
CONFIG="${ROOT}/.deploy-ios.env"
LOG_DIR="${ROOT}/build/logs"; mkdir -p "$LOG_DIR"

echo "======================================"
echo " iOS TestFlight 자동 배포"
echo " 프로젝트: ${ROOT}"
echo "======================================"

# ---- 사전 점검 ----
command -v xcodebuild >/dev/null 2>&1 || { echo "ERROR: Xcode(xcodebuild) 필요."; exit 1; }

# 입력 경로 정규화: ~확장, 둘러싼 따옴표 제거, (필요시) drag&drop 백슬래시 이스케이프 해제.
# 터미널에 붙여넣은 '...' "..." 또는 끌어다 놓은 /a\ b/\(c\) 형태를 모두 처리.
normalize_path() {
  local p="$1"
  p="${p#"${p%%[![:space:]]*}"}"; p="${p%"${p##*[![:space:]]}"}"   # 앞뒤 공백 trim
  p="${p/#\~/$HOME}"                                                # ~ 확장
  [[ "$p" == \'*\' ]] && p="${p:1:${#p}-2}"                         # 둘러싼 ' 제거
  [[ "$p" == \"*\" ]] && p="${p:1:${#p}-2}"                         # 둘러싼 " 제거
  if [[ ! -e "$p" && "$p" == *\\* ]]; then                         # 없고 백슬래시 있으면 이스케이프 해제
    local u="${p//\\/}"
    [[ -e "$u" ]] && p="$u"
  fi
  printf '%s' "$p"
}

# ---- 계정 연동 (최초 1회) ----
if [[ -f "$CONFIG" && "$RECONFIGURE" -eq 0 ]]; then
  # shellcheck disable=SC1090
  source "$CONFIG"
  echo "계정 정보 로드됨: ${CONFIG}"
else
  echo
  echo "[계정 연동] App Store Connect API Key 정보를 1회 입력합니다."
  echo "  (App Store Connect > Users and Access > Integrations > App Store Connect API)"

  # .p8 경로: 비어있거나 파일이 없으면 다시 입력 (빈 Enter 로 잘못 저장되는 것 방지)
  while :; do
    read -rp "  .p8 키 파일 경로(따옴표/드래그 모두 가능): " AUTH_KEY_PATH
    AUTH_KEY_PATH="$(normalize_path "$AUTH_KEY_PATH")"
    [[ -z "$AUTH_KEY_PATH" ]] && { echo "    -> 경로가 비었습니다. 다시 입력 (취소: Ctrl+C)."; continue; }
    [[ -f "$AUTH_KEY_PATH" ]] || { echo "    -> 파일 없음: $AUTH_KEY_PATH"; continue; }
    AUTH_KEY_PATH="$(cd "$(dirname "$AUTH_KEY_PATH")" && pwd)/$(basename "$AUTH_KEY_PATH")"
    break
  done
  # Key ID: .p8 파일명 AuthKey_XXXX.p8 의 XXXX 와 동일. 비어있으면 파일명에서 추정.
  GUESS_KID="$(basename "$AUTH_KEY_PATH" | sed -nE 's/^AuthKey_(.+)\.p8$/\1/p')"
  while :; do
    read -rp "  Key ID${GUESS_KID:+ [$GUESS_KID]}: " AUTH_KEY_ID
    AUTH_KEY_ID="${AUTH_KEY_ID:-$GUESS_KID}"
    [[ -n "$AUTH_KEY_ID" ]] && break; echo "    -> 비었습니다."
  done
  # Issuer ID: UUID 형식(8-4-4-4-12). 이름/계정명 잘못 입력 방지.
  while :; do
    read -rp "  Issuer ID (UUID 형식): " AUTH_ISSUER_ID
    [[ -z "$AUTH_ISSUER_ID" ]] && { echo "    -> 비었습니다."; continue; }
    if [[ ! "$AUTH_ISSUER_ID" =~ ^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$ ]]; then
      echo "    -> UUID 형식이 아닙니다 (예: 69a6de7e-1234-..). App Store Connect > Integrations 페이지 상단의 'Issuer ID' 복사."
      continue
    fi
    break
  done

  cat > "$CONFIG" <<EOF
# iOS 배포 계정 정보 (자동 생성). git 에 커밋하지 마세요.
AUTH_KEY_PATH="${AUTH_KEY_PATH}"
AUTH_KEY_ID="${AUTH_KEY_ID}"
AUTH_ISSUER_ID="${AUTH_ISSUER_ID}"
EOF
  chmod 600 "$CONFIG"
  echo "  저장됨: ${CONFIG} (다음부터 자동 사용)"
fi
[[ -f "$AUTH_KEY_PATH" ]] || { echo "ERROR: .p8 키 없음: ${AUTH_KEY_PATH} (--reconfigure 로 재설정)"; exit 1; }

# ---- 프로젝트 자동 감지 ----
echo
echo "[1/5] 프로젝트 자동 감지."
cd "$ROOT"

WORKSPACE="$(find . -maxdepth 2 -name '*.xcworkspace' -not -path '*/.*' -not -path '*.xcodeproj/*' | head -n 1 || true)"
if [[ -n "$WORKSPACE" ]]; then
  CONTAINER_FLAG=(-workspace "$WORKSPACE")
  echo "  workspace: $WORKSPACE"
else
  PROJ="$(find . -maxdepth 2 -name '*.xcodeproj' -not -path '*/.*' | head -n 1 || true)"
  [[ -n "$PROJ" ]] || { echo "ERROR: .xcworkspace/.xcodeproj 를 못 찾음."; exit 1; }
  CONTAINER_FLAG=(-project "$PROJ")
  echo "  project: $PROJ"
fi

# scheme 자동 감지.
# 1순위: 앱 .xcodeproj(=Pods.xcodeproj 제외)의 공유 스킴. CocoaPods/SPM 의존성 스킴(boost, React-* 등)을 자연히 배제.
# 2순위: workspace -list 전체에서 -Package 제외 첫 스킴 (공유 스킴 없을 때 폴백).
APP_PROJ="$(find . -maxdepth 2 -name '*.xcodeproj' -not -name 'Pods.xcodeproj' -not -path '*/.*' | head -n 1 || true)"
SCHEME=""
if [[ -n "$APP_PROJ" && -d "$APP_PROJ/xcshareddata/xcschemes" ]]; then
  SHARED="$(ls "$APP_PROJ/xcshareddata/xcschemes/" 2>/dev/null | sed -n 's/\.xcscheme$//p')"
  PROJ_NAME="$(basename "$APP_PROJ" .xcodeproj)"
  # 프로젝트명과 같은 스킴 우선, 없으면 첫 공유 스킴
  SCHEME="$(echo "$SHARED" | grep -xF "$PROJ_NAME" | head -n 1)"
  [[ -n "$SCHEME" ]] || SCHEME="$(echo "$SHARED" | head -n 1)"
fi
if [[ -z "$SCHEME" ]]; then
  SCHEMES="$(xcodebuild "${CONTAINER_FLAG[@]}" -list 2>/dev/null \
    | awk '/Schemes:/{f=1;next} f&&NF{gsub(/^[ \t]+/,"");print} f&&!NF{exit}')"
  SCHEME="$(echo "$SCHEMES" | grep -vE -- '-Package$' | head -n 1)"
  [[ -n "$SCHEME" ]] || SCHEME="$(echo "$SCHEMES" | head -n 1)"
fi
[[ -n "$SCHEME" ]] || { echo "ERROR: scheme 자동 감지 실패."; exit 1; }
echo "  scheme: $SCHEME"

# build settings 에서 번들/버전 추출
SETTINGS="$(xcodebuild "${CONTAINER_FLAG[@]}" -scheme "$SCHEME" -configuration Release -showBuildSettings 2>/dev/null || true)"
BUNDLE_ID="$(echo "$SETTINGS" | awk -F' = ' '/ PRODUCT_BUNDLE_IDENTIFIER =/{print $2; exit}')"
APP_VERSION="$(echo "$SETTINGS" | awk -F' = ' '/ MARKETING_VERSION =/{print $2; exit}')"
echo "  bundle id: ${BUNDLE_ID:-?}   version: ${APP_VERSION:-?}"

# ---- 빌드 번호 자동 증가 (archive 재사용 시 생략) ----
echo
echo "[2/5] 빌드 번호 자동 증가."
if [[ "$REUSE_ARCHIVE" -eq 1 ]]; then
  echo "  --reuse-archive: 기존 archive 사용 → 빌드번호 증가 생략."
elif command -v agvtool >/dev/null 2>&1; then
  # agvtool 은 프로젝트 디렉토리에서 동작
  pushd "$(dirname "${WORKSPACE:-$PROJ}")" >/dev/null
  agvtool next-version -all >/dev/null 2>&1 && echo "  agvtool: 빌드번호 +1" || echo "  WARN: agvtool 증가 실패, 기존 값 사용"
  NEW_BUILD="$(agvtool what-version -terse 2>/dev/null || echo '?')"
  popd >/dev/null
  echo "  build: ${NEW_BUILD}"
else
  echo "  WARN: agvtool 없음. 빌드번호 수동 관리 필요."
fi

# ---- 산출물 경로 / ExportOptions 자동 생성 ----
ARCHIVE_PATH="${ROOT}/build/${SCHEME}.xcarchive"
EXPORT_PATH="${ROOT}/build/export"
EXPORT_OPTIONS="${ROOT}/build/ExportOptions.plist"
mkdir -p "$EXPORT_PATH"
cat > "$EXPORT_OPTIONS" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key><string>app-store</string>
    <key>signingStyle</key><string>automatic</string>
    <key>uploadSymbols</key><true/>
    <key>uploadBitcode</key><false/>
</dict>
</plist>
PLIST

# ---- archive ----
echo
if [[ "$REUSE_ARCHIVE" -eq 1 && -d "$ARCHIVE_PATH" ]]; then
  echo "[3/5] archive 재사용: ${ARCHIVE_PATH} (재컴파일 생략)."
else
  [[ "$REUSE_ARCHIVE" -eq 1 ]] && echo "  WARN: 재사용할 archive 없음 → 새로 생성."
  echo "[3/5] archive 생성 (시간이 걸립니다)."
  xcodebuild "${CONTAINER_FLAG[@]}" \
    -scheme "$SCHEME" -configuration Release \
    -destination "generic/platform=iOS" \
    -archivePath "$ARCHIVE_PATH" \
    -allowProvisioningUpdates \
    -authenticationKeyPath "$AUTH_KEY_PATH" \
    -authenticationKeyID "$AUTH_KEY_ID" \
    -authenticationKeyIssuerID "$AUTH_ISSUER_ID" \
    clean archive 2>&1 | tee "${LOG_DIR}/ios-archive.log"
fi

# ---- export ----
# 서명/배포 인증서 생성은 Xcode 에 로그인된 Apple 계정으로 처리(-allowProvisioningUpdates).
# API Key 는 보통 cloud signing 권한이 없어(Developer 역할) export 에 쓰지 않음. 업로드에만 사용.
echo
echo "[4/5] ipa export (Xcode 계정으로 서명)."
xcodebuild -exportArchive \
  -archivePath "$ARCHIVE_PATH" \
  -exportPath "$EXPORT_PATH" \
  -exportOptionsPlist "$EXPORT_OPTIONS" \
  -allowProvisioningUpdates 2>&1 | tee "${LOG_DIR}/ios-export.log" || true

IPA_PATH="$(find "$EXPORT_PATH" -maxdepth 1 -name '*.ipa' | head -n 1 || true)"
if [[ -z "$IPA_PATH" ]]; then
  echo "ERROR: ipa 생성 실패."
  if grep -q "Cloud signing permission error\|No signing certificate" "${LOG_DIR}/ios-export.log" 2>/dev/null; then
    echo
    echo "원인: App Store Connect API Key 권한 부족(클라우드 서명 불가)."
    echo "  현재 키 역할이 Developer 로 추정됩니다. 배포용(iOS Distribution) 인증서 자동 생성은"
    echo "  Admin 또는 App Manager 역할 키가 필요합니다."
    echo
    echo "해결 방법 (택1):"
    echo "  A) App Store Connect > Users and Access > Integrations 에서"
    echo "     Admin(또는 App Manager) 역할로 새 API Key 생성 후:"
    echo "       ./$(basename "$0") \"$ROOT\" --reconfigure"
    echo "  B) Xcode > Settings > Accounts > (Apple ID) > Manage Certificates >"
    echo "     + > Apple Distribution 으로 배포 인증서를 1회 생성(키체인 설치) 후 재실행."
  fi
  exit 1
fi

# ---- upload ----
# altool 의 --apiKey 는 경로를 받지 않고 AuthKey_<KeyID>.p8 를 정해진 폴더에서 찾는다.
# 따라서 .p8 를 ~/.appstoreconnect/private_keys/ 로 복사해 둔다.
echo
echo "[5/5] TestFlight 업로드."
PRIVATE_KEYS_DIR="${HOME}/.appstoreconnect/private_keys"
mkdir -p "$PRIVATE_KEYS_DIR"
cp -f "$AUTH_KEY_PATH" "${PRIVATE_KEYS_DIR}/AuthKey_${AUTH_KEY_ID}.p8"
chmod 600 "${PRIVATE_KEYS_DIR}/AuthKey_${AUTH_KEY_ID}.p8"
xcrun altool --upload-app -f "$IPA_PATH" -t ios \
  --apiKey "$AUTH_KEY_ID" --apiIssuer "$AUTH_ISSUER_ID" \
  --output-format xml 2>&1 | tee "${LOG_DIR}/ios-upload.log" || true

if grep -q "Cannot determine the Apple ID\|No suitable application records" "${LOG_DIR}/ios-upload.log" 2>/dev/null; then
  echo
  echo "ERROR: App Store Connect 에 '${BUNDLE_ID}' 앱 레코드가 없습니다."
  echo "  해결: App Store Connect > Apps > + > New App 에서"
  echo "        Platform=iOS, Bundle ID=${BUNDLE_ID} 로 앱을 1회 생성 후 재실행."
  echo "        (생성 직후 반영까지 잠깐 걸릴 수 있음)"
  exit 1
fi
if grep -qiE "error" "${LOG_DIR}/ios-upload.log" 2>/dev/null && ! grep -q "No errors uploading" "${LOG_DIR}/ios-upload.log" 2>/dev/null; then
  echo
  echo "ERROR: 업로드 실패. 위 altool 메시지를 확인하세요. (로그: ${LOG_DIR}/ios-upload.log)"
  exit 1
fi

echo
echo "완료. App Store Connect > TestFlight 에서 processing 확인."
echo "  ${BUNDLE_ID:-app}  v${APP_VERSION:-?} (build ${NEW_BUILD:-?})"
