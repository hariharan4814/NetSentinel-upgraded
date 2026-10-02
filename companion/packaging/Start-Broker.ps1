$ErrorActionPreference = 'Stop'
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { throw 'Open a separate PowerShell window as administrator yourself, then run this script. Automatic elevation is disabled. Never run Next.js or Django as administrator.' }
Push-Location $PSScriptRoot
try { & (Join-Path $PSScriptRoot '.venv\Scripts\python.exe') -m companion broker }
finally { Pop-Location }
