$ErrorActionPreference = 'Stop'
# Explicitly chosen by the local user. Never log or upload this file.
$keyFile = Join-Path $env:LOCALAPPDATA 'NetSentinel\state\access.token'
Write-Host 'Private local access key. Enter it only at http://127.0.0.1:8765. Do not share it.'
Get-Content -LiteralPath $keyFile
