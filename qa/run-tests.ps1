param(
    [ValidateSet('setup', 'backend', 'frontend', 'ui', 'api', 'compat', 'k6', 'axe', 'all')]
    [string]$Suite = 'all',
    [ValidateSet('smoke', 'baseline', 'moderate')]
    [string]$Profile = 'smoke',
    [string]$Tag,
    [string]$Test,
    [string]$BaseUrl = 'https://jolly-smoke-017f42010.5.azurestaticapps.net',
    [switch]$Plan
)

$ErrorActionPreference = 'Stop'
$qaRoot = $PSScriptRoot
$repoRoot = (Resolve-Path (Join-Path $qaRoot '..')).Path
$auditRoot = (Resolve-Path (Join-Path $repoRoot '..')).Path
$evidenceRoot = Join-Path $auditRoot 'Evidencias'
$runId = Get-Date -Format 'yyyyMMdd-HHmmss'
$selected = if ($Suite -eq 'all') { @('backend', 'frontend', 'ui', 'api', 'compat', 'k6', 'axe') } else { @($Suite) }

if ($Tag -and $Suite -ne 'ui') { throw '-Tag solo se usa con -Suite ui.' }
if ($Test -and $Suite -ne 'backend') { throw '-Test solo se usa con -Suite backend.' }

if ($Plan) {
    Write-Output "Directorio: $repoRoot"
    Write-Output "Suites: $($selected -join ', ')"
    Write-Output "Corrida: $runId"
    if ('k6' -in $selected) { Write-Output "Perfil k6: $Profile" }
    if ('axe' -in $selected) { Write-Output "Origen axe-core: $BaseUrl" }
    return
}

function Require-Command([string]$name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        throw "Falta '$name' en PATH. Revisa los requisitos de qa/README.md."
    }
}

function Assert-App {
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:5000/api/health' -TimeoutSec 5
        if (-not $health.success) { throw 'La API no respondió success=true.' }
        $web = Invoke-WebRequest -Uri 'http://127.0.0.1:4200/productos' -Headers @{ Accept = 'text/html' } -UseBasicParsing -TimeoutSec 5
        if ($web.StatusCode -ne 200) { throw "El frontend respondió HTTP $($web.StatusCode)." }
    } catch {
        throw "Inicia backend y frontend antes de esta suite. Detalle: $($_.Exception.Message)"
    }
}

function Assert-IsolatedDb {
    $connection = Join-Path $qaRoot '.local/connection.json'
    if (-not (Test-Path -LiteralPath $connection)) { throw 'Falta la base QA aislada. Ejecuta .\qa\run-tests.ps1 -Suite setup.' }
    Require-Command 'docker'
    $config = Get-Content -LiteralPath $connection -Raw | ConvertFrom-Json
    $running = docker ps --format '{{.Names}}'
    if ($LASTEXITCODE -ne 0 -or $config.container -notin $running) {
        throw "El contenedor SQL de QA '$($config.container)' no está activo. Inícialo antes de ejecutar pruebas que escriben datos."
    }
}

function Assert-QABackend {
    $expectedJar = Join-Path $repoRoot 'backend/target/backend-0.0.1-SNAPSHOT.jar'
    $listener = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $listener) { throw 'El backend de QA no está activo en el puerto 5000.' }
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
    if (-not $process -or $process.Name -ne 'java.exe' -or
        -not $process.CommandLine -or -not $process.CommandLine.Contains($expectedJar)) {
        throw 'El puerto 5000 no pertenece al backend de esta copia de auditoría. Inícialo con .\qa\infra\run-backend.ps1.'
    }
    $products = Invoke-RestMethod -Uri 'http://127.0.0.1:5000/api/productos' -TimeoutSec 5
    if (-not $products.success -or 'Miel QA' -notin @($products.data | ForEach-Object { $_.nombre })) {
        throw 'El backend no presenta los datos sintéticos de la base QA aislada.'
    }
}

function Evidence-Dir([string]$relative) {
    $path = Join-Path $evidenceRoot (Join-Path $relative $runId)
    New-Item -ItemType Directory -Force -Path $path | Out-Null
    return $path
}

function Run-Command([string]$directory, [string]$log, [scriptblock]$action) {
    Push-Location $directory
    $started = $false
    try {
        Start-Transcript -LiteralPath $log -Force | Out-Null
        $started = $true
        $global:LASTEXITCODE = 0
        & $action | Out-Host
        return [int]$LASTEXITCODE
    } finally {
        if ($started) { Stop-Transcript | Out-Null }
        Pop-Location
    }
}

function Find-K6 {
    $command = Get-Command 'k6' -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    $installed = 'C:\Program Files\k6\k6.exe'
    if (Test-Path -LiteralPath $installed) { return $installed }
    throw 'No se encontró k6. Instálalo o añádelo a PATH.'
}

function Run-Suite([string]$name) {
    Write-Output "`n=== $name ==="
    switch ($name) {
        'setup' {
            Require-Command 'npm'
            Require-Command 'py'
            Require-Command 'docker'
            $setupLogs = Join-Path $qaRoot '.local/setup-logs'
            New-Item -ItemType Directory -Force -Path $setupLogs | Out-Null
            $code = Run-Command $qaRoot (Join-Path $setupLogs 'npm-qa.log') { npm ci }
            if ($code -ne 0) { throw 'Falló npm ci en qa.' }
            $code = Run-Command $repoRoot (Join-Path $setupLogs 'python.log') { py -m pip install -r (Join-Path $qaRoot 'requirements.txt') }
            if ($code -ne 0) { throw 'Falló la instalación de Python.' }
            $code = Run-Command $qaRoot (Join-Path $setupLogs 'playwright.log') { py -m playwright install chromium firefox webkit }
            if ($code -ne 0) { throw 'Falló la instalación de Playwright.' }
            $code = Run-Command (Join-Path $repoRoot 'frontend') (Join-Path $setupLogs 'npm-frontend.log') { npm ci }
            if ($code -ne 0) { throw 'Falló npm ci en frontend.' }
            if (-not (Test-Path -LiteralPath (Join-Path $qaRoot '.local/connection.json'))) {
                & (Join-Path $qaRoot 'infra/bootstrap.ps1')
            } else {
                $config = Get-Content -LiteralPath (Join-Path $qaRoot '.local/connection.json') -Raw | ConvertFrom-Json
                $existing = docker ps -a --format '{{.Names}}'
                if ($config.container -notin $existing) { throw "Falta el contenedor SQL '$($config.container)' indicado por la configuración QA." }
                $running = docker ps --format '{{.Names}}'
                if ($config.container -notin $running) {
                    docker start $config.container | Out-Host
                    if ($LASTEXITCODE -ne 0) { throw 'No se pudo iniciar el SQL aislado.' }
                }
                Write-Output 'La base QA existente está activa y conserva sus datos.'
            }
            Write-Output 'Preparación completa.'
            return
        }
        'backend' {
            Require-Command 'java'
            Require-Command 'docker'
            $dir = Evidence-Dir 'unitarias/java-junit-mockito'
            $backend = Join-Path $repoRoot 'backend'
            $mavenArgs = @('test', '-Djacoco.append=false')
            if ($Test) { $mavenArgs += "-Dtest=$Test" }
            $testStarted = (Get-Date).ToUniversalTime().AddSeconds(-3)
            $code = Run-Command $backend (Join-Path $dir 'maven.log') { & .\mvnw.cmd @mavenArgs }
            $reportCode = Run-Command $backend (Join-Path $dir 'jacoco.log') { & .\mvnw.cmd jacoco:report }
            $reports = Join-Path $backend 'target/surefire-reports'
            if (Test-Path -LiteralPath $reports) {
                $reportDir = Join-Path $dir 'surefire-reports'
                New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
                Get-ChildItem -LiteralPath $reports -File | Where-Object { $_.LastWriteTimeUtc -ge $testStarted } |
                    ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $reportDir -Force }
            }
            $coverage = Join-Path $backend 'target/site/jacoco'
            if (Test-Path -LiteralPath $coverage) {
                Copy-Item -LiteralPath $coverage -Destination (Join-Path $dir 'jacoco') -Recurse -Force
            }
            Write-Output "Evidencia: $dir"
            if ($code -ne 0 -or $reportCode -ne 0) { throw "Maven terminó con código $code; JaCoCo con $reportCode. Revisa los reportes." }
            return
        }
        'frontend' {
            Require-Command 'npm'
            $dir = Evidence-Dir 'unitarias/angular-jasmine-karma'
            $front = Join-Path $repoRoot 'frontend'
            $code = Run-Command $front (Join-Path $dir 'karma.log') { npm run test:coverage }
            $coverage = Join-Path $front 'coverage'
            if (Test-Path -LiteralPath $coverage) {
                Copy-Item -LiteralPath $coverage -Destination (Join-Path $dir 'coverage') -Recurse -Force
            }
            Write-Output "Evidencia: $dir"
            if ($code -ne 0) { throw "Karma terminó con código $code." }
            return
        }
        'ui' {
            Require-Command 'py'
            Assert-IsolatedDb
            Assert-App
            Assert-QABackend
            $dir = Evidence-Dir 'funcionales-ui/behave-selenium'
            $previousIsolated = $env:QA_ISOLATED_DB
            $previousRunId = $env:QA_RUN_ID
            $previousArtifacts = $env:QA_ARTIFACTS
            $env:QA_ISOLATED_DB = '1'
            $env:QA_RUN_ID = $runId
            $env:QA_ARTIFACTS = $dir
            $behaveArgs = @('-m', 'behave', 'tests/functional/features', '--lang', 'en', '--junit', '--junit-directory', $dir, '-f', 'progress')
            if ($Tag) { $behaveArgs += "--tags=$Tag" }
            try { $code = Run-Command $qaRoot (Join-Path $dir 'behave.log') { py @behaveArgs } }
            finally {
                $env:QA_ISOLATED_DB = $previousIsolated
                $env:QA_RUN_ID = $previousRunId
                $env:QA_ARTIFACTS = $previousArtifacts
            }
            Write-Output "Evidencia: $dir"
            if ($code -ne 0) { throw "Behave terminó con código $code." }
            return
        }
        'api' {
            Assert-IsolatedDb
            Assert-App
            Assert-QABackend
            $newman = Join-Path $qaRoot 'node_modules/.bin/newman.cmd'
            if (-not (Test-Path -LiteralPath $newman)) { throw 'Falta Newman. Ejecuta .\qa\run-tests.ps1 -Suite setup.' }
            $dir = Evidence-Dir 'funcionales-api/postman-newman'
            $collection = Join-Path $qaRoot 'tests/functional/api/dulcemiel.postman_collection.json'
            $code = Run-Command $qaRoot (Join-Path $dir 'newman.log') { & $newman run $collection -r cli,junit --reporter-junit-export (Join-Path $dir 'newman.xml') }
            Write-Output "Evidencia: $dir"
            if ($code -ne 0) { throw "Newman terminó con código $code." }
            return
        }
        'compat' {
            Require-Command 'py'
            Assert-App
            $dir = Evidence-Dir 'compatibilidad/playwright'
            $script = Join-Path $qaRoot 'tests/non-functional/compatibility/playwright_compatibility.py'
            $code = Run-Command $qaRoot (Join-Path $dir 'playwright.log') { py $script }
            Write-Output "Evidencia: $dir"
            if ($code -ne 0) { throw "Playwright terminó con código $code." }
            return
        }
        'k6' {
            Assert-App
            $k6 = Find-K6
            $dir = Evidence-Dir 'rendimiento/k6'
            $script = Join-Path $qaRoot 'tests/non-functional/performance/k6/catalogo.js'
            $summary = Join-Path $dir "k6-$Profile.json"
            $code = Run-Command $qaRoot (Join-Path $dir "k6-$Profile.log") { & $k6 run -e "QA_LOAD_PROFILE=$Profile" -e "QA_K6_SUMMARY=$summary" $script }
            Write-Output "Evidencia: $dir"
            if ($code -ne 0) { throw "k6 terminó con código $code." }
            return
        }
        'axe' {
            Require-Command 'py'
            $dir = Evidence-Dir 'accesibilidad/axe-core'
            $script = Join-Path $qaRoot 'tests/non-functional/accessibility/axe_core_scan.py'
            $code = Run-Command $qaRoot (Join-Path $dir 'axe-core.log') { py $script --base-url $BaseUrl --output $dir }
            Write-Output "Evidencia: $dir"
            if ($code -ne 0) { throw "axe-core terminó con código $code." }
            return
        }
    }
}

if ($Suite -eq 'all') {
    Assert-IsolatedDb
    Assert-App
    Assert-QABackend
}
$failed = @()
foreach ($name in $selected) {
    try { Run-Suite $name; Write-Output "✓ $name" }
    catch { Write-Warning "${name}: $($_.Exception.Message)"; $failed += $name }
}
if ($failed.Count) { throw "Suites con fallos: $($failed -join ', '). Las demás se ejecutaron y sus evidencias se conservaron." }
Write-Output "`nCorrida $runId finalizada. Evidencias en $evidenceRoot"
