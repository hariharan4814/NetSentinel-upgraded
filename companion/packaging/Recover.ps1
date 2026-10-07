$ErrorActionPreference = 'Stop'
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { throw 'Recovery requires an explicitly opened administrator PowerShell window.' }
Push-Location $PSScriptRoot
try { & (Join-Path $PSScriptRoot '.venv\Scripts\python.exe') -m companion recover; if ($LASTEXITCODE -ne 0) { throw 'Owned-rule cleanup is unconfirmed. Inspect Windows Firewall before uninstalling.' } }
finally { Pop-Location }
