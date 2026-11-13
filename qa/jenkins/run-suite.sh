#!/usr/bin/env bash
set -euo pipefail
suite="${1:-}"
case "$suite" in
  Newman|Behave|Compatibility|Axe|PendingPlaywright|K6Smoke|K6Baseline|K6Moderate|K6Stress|K6Spike|K6Sustained) ;;
  *) echo "Suite desconocida: $suite" >&2; exit 2 ;;
esac
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
qa_root="$repo_root/qa"
state_file="$qa_root/.local/jenkins-run.json"
[[ -f "$state_file" ]] || { echo 'No existe el estado QA de esta corrida.' >&2; exit 1; }
eval "$(python3 - "$state_file" <<'PY'
import json, shlex, sys
with open(sys.argv[1], encoding='utf-8') as stream:
    s = json.load(stream)
for key in ('runId', 'ready'):
    print(f'{key.upper()}={shlex.quote(str(s[key]))}')
PY
)"
[[ "$READY" == 'True' || "$READY" == 'true' ]] || { echo 'El stack QA no está listo.' >&2; exit 1; }

export QA_ISOLATED_DB=1
export QA_RUN_ID="$RUNID"
export QA_API_URL='http://backend:5000/api'
export QA_WEB_URL='http://frontend:4200'
export QA_ARTIFACTS="$qa_root/artifacts/$RUNID"
export QA_HEADLESS=1
artifact_root="$QA_ARTIFACTS"
mkdir -p "$artifact_root"
cd "$qa_root"
python="$qa_root/.venv/bin/python"

case "$suite" in
  Newman)
    out="$artifact_root/api"; mkdir -p "$out"
    ./node_modules/.bin/newman run ./tests/functional/api/dulcemiel.postman_collection.json \
      --env-var "baseUrl=$QA_API_URL" --reporters cli,junit,json \
      --reporter-junit-export "$out/newman.xml" --reporter-json-export "$out/newman.json"
    ;;
  Behave)
    out="$artifact_root/ui-behave"; mkdir -p "$out"
    "$python" -m behave ./tests/functional/features --lang en --junit --junit-directory "$out" -f progress
    ;;
  Compatibility)
    out="$artifact_root/compatibility"; mkdir -p "$out"
    export QA_BROWSERS='chromium,firefox,webkit'
    set +e
    "$python" ./tests/non-functional/compatibility/playwright_compatibility.py 2>&1 | tee "$out/playwright.log"
    status=${PIPESTATUS[0]}
    set -e
    python3 - "$status" "$out/playwright.log" "$out/result.json" <<'PY'
import json, re, sys
code, log_path, path = int(sys.argv[1]), sys.argv[2], sys.argv[3]
try:
    text = open(log_path, encoding='utf-8', errors='replace').read()
except OSError:
    text = ''
results = re.findall(r"\(engine='[^']+',\s*width=\d+\)\s+\.\.\.\s+(ok|FAIL|ERROR)", text)
total = len(results) or 1
failed = sum(result != 'ok' for result in results) if results else (1 if code else 0)
with open(path, 'w', encoding='utf-8') as stream:
    json.dump({'case_id':'TC-NF-COM-001','tool':'Playwright','status':'p' if code == 0 else 'f',
               'tests_total':total,'tests_passed':total-failed,'tests_failed':failed,
               'detail':f'Prueba de compatibilidad ejecutada; código de salida {code}.',
               'evidence':'compatibility/playwright.log'}, stream, ensure_ascii=False, indent=2)
PY
    (( status == 0 )) || exit "$status"
    ;;
  Axe)
    out="$artifact_root/accessibility-axe"; mkdir -p "$out"
    "$python" ./tests/non-functional/accessibility/axe_core_scan.py --base-url "$QA_WEB_URL" --output "$out" --fail-on-violations
    ;;
  PendingPlaywright)
    out="$artifact_root/pending-playwright"; mkdir -p "$out"
    QA_ARTIFACTS="$out" "$python" ./tests/non-functional/accessibility/pending_playwright_cases.py
    ;;
  K6*)
    profile="${suite#K6}"; profile="${profile,,}"
    out="$artifact_root/k6-$profile"; mkdir -p "$out"
    set +e
    k6 run -e "QA_API_URL=$QA_API_URL" -e "QA_WEB_URL=$QA_WEB_URL" \
      -e "QA_LOAD_PROFILE=$profile" -e "QA_K6_SUMMARY=$out/summary.json" \
      ./tests/non-functional/performance/k6/catalogo.js 2>&1 | tee "$out/k6.log"
    status=${PIPESTATUS[0]}
    set -e
    if [[ "$suite" == 'K6Spike' ]]; then sleep 30; fi
    (( status == 0 )) || exit "$status"
    ;;
esac
