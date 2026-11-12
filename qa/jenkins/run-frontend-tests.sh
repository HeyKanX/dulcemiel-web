#!/usr/bin/env bash
set -uo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
coverage_dir="$repo_root/frontend/coverage"
mkdir -p "$coverage_dir"
cd "$repo_root/frontend"
npm ci

set +e
CHROME_BIN="$repo_root/qa/jenkins/chrome-headless" \
  npm run test:coverage -- --browsers=ChromeHeadless 2>&1 | tee "$coverage_dir/frontend-tests.log"
test_status=${PIPESTATUS[0]}
set -e
exit "$test_status"
