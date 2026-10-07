$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try { & (Join-Path $PSScriptRoot '.venv\Scripts\python.exe') -m companion stop }
finally { Pop-Location }
