$ErrorActionPreference = 'Stop'
$qaRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$repoRoot = (Resolve-Path (Join-Path $qaRoot '..')).Path
$statePath = Join-Path $qaRoot '.local/jenkins-run.json'
$runId = 'no-qa-stack'
if (Test-Path -LiteralPath $statePath) {
    $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    $runId = $state.runId
}
$runDir = Join-Path $qaRoot "artifacts/$runId"
Push-Location $repoRoot
try {
    & py -3 qa\testlink\generate_current_run.py --run-dir $runDir --build $env:BUILD_TAG
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo generar el resumen actual para TestLink.' }
} finally { Pop-Location }
