#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"
local_dir=qa/.local
state_path="$local_dir/jenkins-run.json"
ready_path="$local_dir/jenkins-ready.flag"
env_path="$local_dir/compose.env"
mkdir -p "$local_dir"
rm -f "$ready_path"

[[ -n "${BUILD_TAG:-}" ]] || { echo 'Este preparador requiere BUILD_TAG de Jenkins.' >&2; exit 1; }
[[ -f "$local_dir/jenkins-deps-ready.flag" ]] || { echo 'No se instalaron las dependencias QA.' >&2; exit 1; }
[[ ! -f "$state_path" ]] || { echo 'Quedó estado de otra ejecución QA; no se iniciará otra pila.' >&2; exit 1; }
docker network inspect jenkins_default >/dev/null 2>&1 || { echo 'Falta la red Docker privada jenkins_default.' >&2; exit 1; }

safe_tag="$(printf '%s' "$BUILD_TAG" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9_-]/-/g' | cut -c1-30)"
suffix="$(openssl rand -hex 4)"
project="dmqa-${safe_tag}-${suffix}"
run_id="build-${BUILD_NUMBER:-local}-${suffix}"
password="Qa!$(openssl rand -hex 24)"
jwt_secret="qa-${suffix}-$(openssl rand -hex 32)"
web_url='http://frontend:4200'
api_url='http://backend:5000/api'

cat > "$env_path" <<EOF
QA_SQL_PASSWORD='$password'
QA_JWT_SECRET='$jwt_secret'
QA_WEB_URL=$web_url
QA_API_URL=$api_url
QA_DOCKER_NETWORK=jenkins_default
EOF
python3 - "$state_path" "$BUILD_TAG" "$project" "$run_id" <<'PY'
import json, sys
path, owner, project, run_id = sys.argv[1:]
with open(path, 'w', encoding='utf-8') as stream:
    json.dump({'owner': owner, 'project': project, 'runId': run_id, 'ready': False}, stream)
PY

cleanup_on_error() {
  status=$?
  if (( status != 0 )); then
    docker compose --project-name "$project" --env-file "$env_path" -f compose.qa.yaml down --volumes --remove-orphans || true
  fi
  exit "$status"
}
trap cleanup_on_error EXIT

bash backend/mvnw -B -ntp -DskipTests package
docker compose --project-name "$project" --env-file "$env_path" -f compose.qa.yaml up -d --wait --wait-timeout 240 sql
docker compose --project-name "$project" --env-file "$env_path" -f compose.qa.yaml run --rm init
docker compose --project-name "$project" --env-file "$env_path" -f compose.qa.yaml up -d --build backend frontend

ready=0
for attempt in $(seq 1 90); do
  if curl --fail --silent http://backend:5000/api/health >/dev/null && curl --fail --silent http://frontend:4200/productos >/dev/null; then
    ready=1
    break
  fi
  sleep 2
done
if (( ready != 1 )); then
  docker compose --project-name "$project" --env-file "$env_path" -f compose.qa.yaml logs --no-color
  echo 'API o frontend QA no quedó disponible.' >&2
  exit 1
fi

python3 - "$state_path" <<'PY'
import json, sys
path = sys.argv[1]
with open(path, encoding='utf-8') as stream:
    data = json.load(stream)
data['ready'] = True
with open(path, 'w', encoding='utf-8') as stream:
    json.dump(data, stream, indent=2)
PY
touch "$ready_path"
trap - EXIT
echo 'Stack QA efímero disponible solo dentro de la red Docker privada.'
