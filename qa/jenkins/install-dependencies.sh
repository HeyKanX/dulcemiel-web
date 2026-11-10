#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"
mkdir -p qa/.local
rm -f qa/.local/jenkins-deps-ready.flag

command -v docker >/dev/null || { echo 'Falta Docker CLI en el agente.' >&2; exit 1; }
docker compose version >/dev/null
command -v java >/dev/null || { echo 'Falta Java en el agente.' >&2; exit 1; }
command -v node >/dev/null || { echo 'Falta Node.js en el agente.' >&2; exit 1; }
command -v python3 >/dev/null || { echo 'Falta Python 3 en el agente.' >&2; exit 1; }
command -v k6 >/dev/null || { echo 'Falta K6 en el agente.' >&2; exit 1; }
[[ -x /usr/bin/chromium ]] || { echo 'Falta Chromium en el agente.' >&2; exit 1; }
[[ -x /usr/bin/chromedriver ]] || { echo 'Falta ChromeDriver en el agente.' >&2; exit 1; }
docker info >/dev/null

npm ci --prefix qa
python3 -m venv qa/.venv
qa/.venv/bin/python -m pip install --disable-pip-version-check -r qa/requirements.txt
qa/.venv/bin/python -m playwright install chromium firefox webkit
touch qa/.local/jenkins-deps-ready.flag
echo 'Herramientas QA listas: Newman, Behave/Selenium, Playwright, axe-core y K6.'
