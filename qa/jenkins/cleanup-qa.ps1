$ErrorActionPreference = 'Continue'
$qaRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$repoRoot = (Resolve-Path (Join-Path $qaRoot '..')).Path
$localRoot = Join-Path $qaRoot '.local'
$statePath = Join-Path $localRoot 'jenkins-run.json'
if (-not (Test-Path -LiteralPath $statePath)) { Write-Output 'No hay recursos QA de Jenkins registrados para limpiar.'; exit 0 }
$state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json

Push-Location $repoRoot
try {
    if ($state.project -match '^dmqa-[a-z0-9_-]+$') {
        & docker compose --project-name $state.project --env-file (Join-Path $localRoot 'compose.env') -f compose.qa.yaml down --volumes --remove-orphans
    }
} finally { Pop-Location }

Remove-Item -LiteralPath (Join-Path $localRoot 'compose.env') -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $localRoot 'jenkins-ready.flag') -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $statePath -Force -ErrorAction SilentlyContinue
Write-Output 'Se limpiaron únicamente los recursos QA identificados para esta corrida.'
