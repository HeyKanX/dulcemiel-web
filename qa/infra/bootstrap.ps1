$ErrorActionPreference = 'Stop'
$qaRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$repoRoot = (Resolve-Path (Join-Path $qaRoot '..')).Path
$localDir = Join-Path $qaRoot '.local'
$connectionFile = Join-Path $localDir 'connection.json'
$container = 'dulce-miel-qa-c5'

if (Test-Path -LiteralPath $connectionFile) { throw 'La instancia QA ya fue preparada. No se restablece automáticamente.' }
if (docker ps -a --format '{{.Names}}' | Where-Object { $_ -eq $container }) { throw "Ya existe el contenedor $container. Revisa su estado antes de continuar." }
if (Get-NetTCPConnection -LocalPort 14333 -State Listen -ErrorAction SilentlyContinue) { throw 'El puerto local 14333 ya está ocupado.' }

New-Item -ItemType Directory -Force -Path $localDir | Out-Null
$alphabet = 'abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#%'
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$bytes = New-Object byte[] 32
$rng.GetBytes($bytes)
$password = 'Qa!' + (-join ($bytes | ForEach-Object { $alphabet[$_ % $alphabet.Length] }))
$connection = @{ container = $container; port = 14333; password = $password; database = 'DulceMielBD' }
$connection | ConvertTo-Json | Set-Content -LiteralPath $connectionFile -Encoding utf8

docker run -d --name $container -p '127.0.0.1:14333:1433' -e 'ACCEPT_EULA=Y' -e "MSSQL_SA_PASSWORD=$password" 'mcr.microsoft.com/mssql/server:2022-latest' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'No se pudo iniciar el SQL aislado.' }

$ready = $false
for ($attempt = 0; $attempt -lt 45; $attempt++) {
    docker exec -e "SQLCMDPASSWORD=$password" $container /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -C -Q 'SELECT 1' -b *> $null
    if ($LASTEXITCODE -eq 0) { $ready = $true; break }
    Start-Sleep -Seconds 2
}
if (-not $ready) { throw 'SQL no respondió; revisa docker logs dulce-miel-qa-c5.' }

docker cp (Join-Path $repoRoot 'backend/database/schema.sql') "${container}:/tmp/schema.sql"
if ($LASTEXITCODE -ne 0) { throw 'No se copió el esquema.' }
docker cp (Join-Path $PSScriptRoot 'seed.sql') "${container}:/tmp/seed.sql"
if ($LASTEXITCODE -ne 0) { throw 'No se copiaron los datos sintéticos.' }
docker exec -e "SQLCMDPASSWORD=$password" $container /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -C -i /tmp/schema.sql -b
if ($LASTEXITCODE -ne 0) { throw 'Falló el esquema. La instancia sigue aislada para inspección.' }
docker exec -e "SQLCMDPASSWORD=$password" $container /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -C -i /tmp/seed.sql -b
if ($LASTEXITCODE -ne 0) { throw 'Falló el dato sintético.' }
Write-Output "SQL aislado listo en localhost:14333. Configuración local: $connectionFile"
