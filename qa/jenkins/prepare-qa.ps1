$ErrorActionPreference = 'Stop'
$qaRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$repoRoot = (Resolve-Path (Join-Path $qaRoot '..')).Path
$localRoot = Join-Path $qaRoot '.local'
New-Item -ItemType Directory -Force -Path $localRoot | Out-Null

$buildTag = $env:BUILD_TAG
if (-not $buildTag) { throw 'Este preparador debe ejecutarse dentro de Jenkins (falta BUILD_TAG).' }
$safeTag = ($buildTag.ToLowerInvariant() -replace '[^a-z0-9_-]', '-')
$suffix = [Guid]::NewGuid().ToString('N').Substring(0, 8)
$projectName = "dmqa-$safeTag-$suffix"
$statePath = Join-Path $localRoot 'jenkins-run.json'
$readyPath = Join-Path $localRoot 'jenkins-ready.flag'
$envPath = Join-Path $localRoot 'compose.env'

if (Test-Path -LiteralPath $statePath) { throw 'Ya existe estado de una corrida QA; revisa el agente antes de iniciar otra.' }
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker CLI no está disponible en el agente Jenkins.' }
if (-not (Get-Command java -ErrorAction SilentlyContinue)) { throw 'Java no está disponible en el agente Jenkins.' }
if (-not (Get-Command k6 -ErrorAction SilentlyContinue) -and -not (Test-Path 'C:\Program Files\k6\k6.exe')) { throw 'k6 no está instalado o no está en PATH.' }
if (-not (Test-Path (Join-Path $qaRoot '.venv/Scripts/python.exe'))) { throw 'Falta instalar las dependencias Python de QA.' }
if (-not (Test-Path (Join-Path $qaRoot 'node_modules/.bin/newman.cmd'))) { throw 'Falta instalar Newman en qa/node_modules.' }

function Test-FreePort([int]$Port) {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
    try { $listener.Start(); return $true } catch { return $false } finally { $listener.Stop() }
}
function Find-FreePort([int]$Start, [int]$End) {
    foreach ($candidate in $Start..$End) { if (Test-FreePort $candidate) { return $candidate } }
    throw "No hay puerto libre entre $Start y $End. No se detuvo ningún proceso existente."
}

$apiPort = 5000
if (-not (Test-FreePort $apiPort)) { throw 'El puerto local 5000 está ocupado; no se detuvo ni reutilizó el servicio existente.' }
$webPort = Find-FreePort 4201 4299
$state = [ordered]@{
    owner = $buildTag; project = $projectName
    apiPort = $apiPort; webPort = $webPort
    runId = "build-$($env:BUILD_NUMBER)-$suffix"; ready = $false
}
$state | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding utf8

try {
    $alphabet = 'abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#%'
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $bytes = New-Object byte[] 32
    $rng.GetBytes($bytes)
    $sqlPassword = 'Qa!' + (-join ($bytes | ForEach-Object { $alphabet[$_ % $alphabet.Length] }))
    $jwtSecret = "qa-$sqlPassword-$suffix"
    @(
        "QA_API_PORT=$apiPort"
        "QA_WEB_PORT=$webPort"
        "QA_SQL_PASSWORD='$sqlPassword'"
        "QA_JWT_SECRET='$jwtSecret'"
        "QA_WEB_URL=http://127.0.0.1:$webPort"
    ) | Set-Content -LiteralPath $envPath -Encoding utf8

    Push-Location $repoRoot
    try {
        & .\backend\mvnw.cmd -B -ntp -DskipTests package
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo empaquetar el backend para QA.' }
        & docker compose --project-name $projectName --env-file $envPath -f compose.qa.yaml up -d --wait --wait-timeout 240 sql
        if ($LASTEXITCODE -ne 0) { throw 'SQL de QA no quedó saludable en Docker Compose.' }
        & docker compose --project-name $projectName --env-file $envPath -f compose.qa.yaml run --rm init
        if ($LASTEXITCODE -ne 0) { throw 'Falló la inicialización del esquema o los datos sintéticos de QA.' }
        & docker compose --project-name $projectName --env-file $envPath -f compose.qa.yaml up -d --build backend frontend
        if ($LASTEXITCODE -ne 0) { throw 'Docker Compose no pudo levantar el stack de QA.' }
    } finally { Pop-Location }

    $apiReady = $false
    $webReady = $false
    for ($attempt = 0; $attempt -lt 90; $attempt++) {
        if (-not $apiReady) {
            try { $apiReady = [bool](Invoke-RestMethod -Uri "http://127.0.0.1:$apiPort/api/health" -TimeoutSec 3).success } catch { }
        }
        if (-not $webReady) {
            try { $webReady = (Invoke-WebRequest -Uri "http://127.0.0.1:$webPort/productos" -UseBasicParsing -TimeoutSec 3).StatusCode -eq 200 } catch { }
        }
        if ($apiReady -and $webReady) { break }
        Start-Sleep -Seconds 2
    }
    if (-not $apiReady -or -not $webReady) {
        Push-Location $repoRoot
        try { & docker compose --project-name $projectName --env-file $envPath -f compose.qa.yaml logs --no-color } finally { Pop-Location }
        throw "QA no quedó disponible; API=$apiReady, web=$webReady."
    }

    $state.ready = $true
    $state | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding utf8
    Set-Content -LiteralPath $readyPath -Value 'ready' -Encoding utf8
    Write-Output "Stack QA aislado en Docker Compose disponible: API http://127.0.0.1:$apiPort, web http://127.0.0.1:$webPort."
} catch {
    Write-Error $_
    exit 1
}
