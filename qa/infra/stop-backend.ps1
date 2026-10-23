$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$expectedJar = Join-Path $repoRoot 'backend/target/backend-0.0.1-SNAPSHOT.jar'
$listener = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1

if (-not $listener) {
    Write-Output 'El backend de QA ya está detenido; el puerto 5000 está libre.'
    return
}

$process = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
if (-not $process) { throw 'El proceso del puerto 5000 cambió; vuelve a intentarlo.' }
$parent = Get-CimInstance Win32_Process -Filter "ProcessId=$($process.ParentProcessId)"
if ($process.Name -ne 'java.exe' -or
    -not $process.CommandLine -or
    -not $process.CommandLine.Contains($expectedJar) -or
    -not $parent.CommandLine -or
    $parent.CommandLine -notmatch 'run-backend\.ps1') {
    throw "El puerto 5000 está ocupado por un proceso distinto del backend de QA (PID $($listener.OwningProcess)); no se detuvo."
}

Stop-Process -Id $listener.OwningProcess
for ($attempt = 0; $attempt -lt 20; $attempt++) {
    if (-not (Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue)) {
        Write-Output 'Backend de QA detenido; puedes ejecutar Maven clean verify.'
        return
    }
    Start-Sleep -Milliseconds 250
}

throw 'El backend de QA no liberó el puerto 5000.'
