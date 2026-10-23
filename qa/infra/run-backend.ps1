$ErrorActionPreference = 'Stop'
$qaRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$repoRoot = (Resolve-Path (Join-Path $qaRoot '..')).Path
$connectionFile = Join-Path $qaRoot '.local/connection.json'
if (-not (Test-Path -LiteralPath $connectionFile)) { throw 'Ejecuta primero qa/infra/bootstrap.ps1' }
$config = Get-Content -LiteralPath $connectionFile -Raw | ConvertFrom-Json
if ($config.container -ne 'dulce-miel-qa-c5' -or $config.port -ne 14333) { throw 'Configuración QA inesperada.' }
if (-not (docker ps --format '{{.Names}}' | Where-Object { $_ -eq $config.container })) { throw 'El SQL aislado no está activo.' }
$listener = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($listener) {
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
    $expectedJar = Join-Path $repoRoot 'backend/target/backend-0.0.1-SNAPSHOT.jar'
    if ($process.Name -eq 'java.exe' -and $process.CommandLine -and $process.CommandLine.Contains($expectedJar)) {
        try {
            $health = Invoke-RestMethod -Uri 'http://127.0.0.1:5000/api/health' -TimeoutSec 5
            if ($health.success) {
                Write-Output "El backend de QA ya está activo en http://127.0.0.1:5000 (PID $($listener.OwningProcess)). Continúa con las pruebas; no hace falta iniciarlo de nuevo."
                return
            }
        } catch { }
    }
    throw "El puerto 5000 está ocupado por $($process.Name) (PID $($listener.OwningProcess)). Revisa ese proceso antes de iniciar el backend de QA."
}
$env:PORT = '5000'
$env:MSSQL_JDBC_URL = 'jdbc:sqlserver://127.0.0.1:14333;databaseName=DulceMielBD;encrypt=true;trustServerCertificate=true'
$env:DB_USER = 'sa'
$env:DB_PASSWORD = $config.password
$env:FRONTEND_URL = 'http://127.0.0.1:4200'
$env:JWT_SECRET = 'clave-local-auditoria-' + $config.password
Push-Location (Join-Path $repoRoot 'backend')
try {
    & .\mvnw.cmd package -DskipTests
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo empaquetar el backend.' }
    & java -jar (Join-Path (Get-Location) 'target/backend-0.0.1-SNAPSHOT.jar')
} finally { Pop-Location }
