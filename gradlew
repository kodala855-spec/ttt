#!/usr/bin/env bash
set -euo pipefail

GRADLE_VERSION="8.7"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="${GRADLE_USER_HOME:-$HOME/.gradle}/cto-wrapper"
DIST_DIR="$CACHE_DIR/gradle-$GRADLE_VERSION"

if [ ! -x "$DIST_DIR/bin/gradle" ]; then
  mkdir -p "$CACHE_DIR"
  ZIP_PATH="$CACHE_DIR/gradle-$GRADLE_VERSION-bin.zip"

  if [ ! -f "$ZIP_PATH" ]; then
    echo "Downloading Gradle $GRADLE_VERSION..." >&2
    if command -v curl >/dev/null 2>&1; then
      curl -fsSL -o "$ZIP_PATH" "https://services.gradle.org/distributions/gradle-$GRADLE_VERSION-bin.zip"
    elif command -v wget >/dev/null 2>&1; then
      wget -O "$ZIP_PATH" "https://services.gradle.org/distributions/gradle-$GRADLE_VERSION-bin.zip"
    else
      echo "Neither curl nor wget is available to download Gradle." >&2
      exit 1
    fi
  fi

  rm -rf "$DIST_DIR"
  unzip -q "$ZIP_PATH" -d "$CACHE_DIR"
fi

exec "$DIST_DIR/bin/gradle" -p "$PROJECT_DIR" "$@"
