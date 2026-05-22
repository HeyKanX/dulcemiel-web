$ErrorActionPreference = "Stop"

$tcpPath = "HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\MSSQL17.MSSQLSERVER\MSSQLServer\SuperSocketNetLib\Tcp"
$ipAllPath = Join-Path $tcpPath "IPAll"

Set-ItemProperty -Path $tcpPath -Name Enabled -Value 1
Set-ItemProperty -Path $ipAllPath -Name TcpPort -Value "1433"
Set-ItemProperty -Path $ipAllPath -Name TcpDynamicPorts -Value ""

Restart-Service MSSQLSERVER -Force
Start-Sleep -Seconds 5

Write-Host "SQL Server TCP/IP habilitado en HEYKAN:1433"
Get-Service MSSQLSERVER | Select-Object Name, Status, DisplayName
