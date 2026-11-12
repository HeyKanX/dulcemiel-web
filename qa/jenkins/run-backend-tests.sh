#!/usr/bin/env bash
set -uo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root/backend"

set +e
bash ./mvnw -B -ntp test
test_status=$?
bash ./mvnw -B -ntp jacoco:report
coverage_status=$?
set -e

if (( test_status != 0 )); then
  echo "Las pruebas Maven fallaron (código $test_status); se conservó el intento de generar JaCoCo." >&2
  exit "$test_status"
fi
if (( coverage_status != 0 )); then
  echo "Las pruebas pasaron, pero JaCoCo no pudo generar su reporte (código $coverage_status)." >&2
  exit "$coverage_status"
fi
