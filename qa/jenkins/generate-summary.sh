#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"
state_file=qa/.local/jenkins-run.json
run_id='no-qa-stack'
if [[ -f "$state_file" ]]; then
  run_id="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8"))["runId"])' "$state_file")"
fi
python3 qa/testlink/generate_current_run.py --run-dir "qa/artifacts/$run_id" --build "${BUILD_TAG:-Jenkins}"
