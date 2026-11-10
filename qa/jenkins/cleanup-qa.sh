#!/usr/bin/env bash
set -uo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"
local_dir=qa/.local
state_file="$local_dir/jenkins-run.json"
[[ -f "$state_file" ]] || { echo 'No hay recursos QA registrados.'; exit 0; }
project="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8"))["project"])' "$state_file")"
[[ "$project" =~ ^dmqa-[a-z0-9_-]+$ ]] || { echo 'ID Compose inválido; no se eliminaron contenedores.' >&2; exit 1; }
if [[ -f "$local_dir/compose.env" ]]; then
  docker compose --project-name "$project" --env-file "$local_dir/compose.env" -f compose.qa.yaml down --volumes --remove-orphans
else
  docker compose --project-name "$project" -f compose.qa.yaml down --volumes --remove-orphans
fi
rm -f "$local_dir/compose.env" "$local_dir/jenkins-ready.flag" "$local_dir/jenkins-run.json"
echo 'Se limpiaron solo los recursos efímeros de esta corrida.'
