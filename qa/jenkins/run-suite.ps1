param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Newman', 'Behave', 'Compatibility', 'Axe', 'K6Smoke', 'K6Baseline', 'K6Moderate', 'K6Stress', 'K6Spike', 'K6Sustained')]
    [string]$Suite
)
$ErrorActionPreference = 'Stop'
$qaRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$repoRoot = (Resolve-Path (Join-Path $qaRoot '..')).Path
$statePath = Join-Path $qaRoot '.local/jenkins-run.json'
if (-not (Test-Path $statePath)) { throw 'No existe el estado de QA de esta corrida.' }
$state = Get-Content $statePath -Raw | ConvertFrom-Json
if (-not $state.ready) { throw 'El entorno QA no quedó listo.' }

$env:QA_ISOLATED_DB = '1'
$env:QA_RUN_ID = $state.runId
$env:QA_API_URL = "http://127.0.0.1:$($state.apiPort)/api"
$env:QA_WEB_URL = "http://127.0.0.1:$($state.webPort)"
$artifactRoot = Join-Path $qaRoot "artifacts/$($state.runId)"
New-Item -ItemType Directory -Force -Path $artifactRoot | Out-Null
$env:QA_ARTIFACTS = $artifactRoot
$python = Join-Path $qaRoot '.venv/Scripts/python.exe'

Push-Location $qaRoot
try {
    switch ($Suite) {
        'Newman' {
            $out = Join-Path $artifactRoot 'api'
            New-Item -ItemType Directory -Force -Path $out | Out-Null
            & '.\node_modules\.bin\newman.cmd' run '.\tests\functional\api\dulcemiel.postman_collection.json' `
                --env-var "baseUrl=$($env:QA_API_URL)" `
                --reporters cli,junit,json `
                --reporter-junit-export (Join-Path $out 'newman.xml') `
                --reporter-json-export (Join-Path $out 'newman.json')
            if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        }
        'Behave' {
            $out = Join-Path $artifactRoot 'ui-behave'
            New-Item -ItemType Directory -Force -Path $out | Out-Null
            & $python -m behave '.\tests\functional\features' --lang en --junit --junit-directory $out -f progress
            if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        }
        'Compatibility' {
            $out = Join-Path $artifactRoot 'compatibility'
            New-Item -ItemType Directory -Force -Path $out | Out-Null
            $env:QA_BROWSERS = 'chromium,firefox,webkit'
            & $python '.\tests\non-functional\compatibility\playwright_compatibility.py' 2>&1 | Tee-Object -FilePath (Join-Path $out 'playwright.log')
            $code = $LASTEXITCODE
            @{ case_id = 'TC-NF-COM-001'; tool = 'Playwright'; status = $(if ($code -eq 0) { 'p' } else { 'f' }); detail = "Prueba de compatibilidad ejecutada; código de salida $code."; evidence = 'compatibility/playwright.log' } |
                ConvertTo-Json | Set-Content -LiteralPath (Join-Path $out 'result.json') -Encoding utf8
            if ($code -ne 0) { exit $code }
        }
        'Axe' {
            $out = Join-Path $artifactRoot 'accessibility-axe'
            & $python '.\tests\non-functional\accessibility\axe_core_scan.py' --base-url $env:QA_WEB_URL --output $out --fail-on-violations
            if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        }
        default {
            $out = Join-Path $artifactRoot "k6-$($Suite.Substring(2).ToLowerInvariant())"
            New-Item -ItemType Directory -Force -Path $out | Out-Null
            $profile = $Suite.Substring(2).ToLowerInvariant()
            $k6 = (Get-Command k6 -ErrorAction SilentlyContinue).Source
            if (-not $k6) { $k6 = 'C:\Program Files\k6\k6.exe' }
            & $k6 run `
                -e "QA_API_URL=$($env:QA_API_URL)" `
                -e "QA_WEB_URL=$($env:QA_WEB_URL)" `
                -e "QA_LOAD_PROFILE=$profile" `
                -e "QA_K6_SUMMARY=$(Join-Path $out 'summary.json')" `
                '.\tests\non-functional\performance\k6\catalogo.js' 2>&1 |
                Tee-Object -FilePath (Join-Path $out 'k6.log')
            $code = $LASTEXITCODE
            if ($Suite -eq 'K6Spike') { Start-Sleep -Seconds 30 }
            if ($code -ne 0) { exit $code }
        }
    }
} finally { Pop-Location }
