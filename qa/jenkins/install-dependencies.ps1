$ErrorActionPreference = 'Stop'
$qaRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$repoRoot = (Resolve-Path (Join-Path $qaRoot '..')).Path
$localRoot = Join-Path $qaRoot '.local'
New-Item -ItemType Directory -Force -Path $localRoot | Out-Null
$ready = Join-Path $localRoot 'jenkins-deps-ready.flag'
Remove-Item -LiteralPath $ready -Force -ErrorAction SilentlyContinue

Push-Location $repoRoot
try {
    npm ci --prefix qa
    if ($LASTEXITCODE -ne 0) { throw 'No se instalaron las dependencias Node de QA.' }
    py -3 -m venv qa\.venv
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno virtual Python de QA.' }
    & qa\.venv\Scripts\python.exe -m pip install --disable-pip-version-check -r qa\requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'No se instalaron las dependencias Python de QA.' }
    & qa\.venv\Scripts\python.exe -m playwright install chromium firefox webkit
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar los navegadores de Playwright.' }
    if (-not (Get-Command k6 -ErrorAction SilentlyContinue) -and -not (Test-Path 'C:\Program Files\k6\k6.exe')) {
        throw 'k6 no está instalado o no está en PATH.'
    }
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw 'Node.js no está disponible.' }
    Set-Content -LiteralPath $ready -Value 'ready' -Encoding utf8
    Write-Output 'Dependencias QA listas: Newman, Python, Selenium, Playwright y navegadores.'
} finally { Pop-Location }
