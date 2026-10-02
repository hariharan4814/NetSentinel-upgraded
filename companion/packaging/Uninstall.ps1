param([switch]$DeletePrivateHistory)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($PSScriptRoot)
$expected = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'NetSentinel\app'))
if ($root -ne $expected) { throw 'This removal script operates only on LocalAppData\NetSentinel\app. For custom installs, use the documented manual procedure.' }
& (Join-Path $root 'Stop.ps1')
& (Join-Path $root 'Recover.ps1')
# Native failures above stop removal; never lose the recovery tool first.
$state = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'NetSentinel\state'))
if ($DeletePrivateHistory) {
  $parent = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'NetSentinel'))
  if (-not $state.StartsWith($parent + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe private-data target.' }
  Remove-Item -LiteralPath $state -Recurse -Force
}
Set-Location $env:TEMP
Remove-Item -LiteralPath $root -Recurse -Force
Write-Host 'NetSentinel app removed. Private history is retained unless -DeletePrivateHistory was explicitly selected. Npcap was not removed.'
