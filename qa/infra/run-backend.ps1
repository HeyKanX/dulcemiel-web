$ErrorActionPreference = 'Stop'
$qaRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$repoRoot = (Resolve-Path (Join-Path $qaRoot '..')).Path
$connectionFile = Join-Path $qaRoot '.local/connection.json'
if (-not (Test-Path -LiteralPath $connectionFile)) { throw 'Ejecuta primero qa/infra/bootstrap.ps1' }
$config = Get-Content -LiteralPath $connectionFile -Raw | ConvertFrom-Json
if ($config.container -ne 'dulce-miel-qa-c5' -or $config.port -ne 14333) { throw 'Configuración QA inesperada.' }
if (-not (docker ps --format '{{.Names}}' | Where-Object { $_ -eq $config.container })) { throw 'El SQL aislado no está activo.' }
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
