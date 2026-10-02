param([string]$PythonPath = '', [string]$InstallRoot = (Join-Path $env:LOCALAPPDATA 'NetSentinel\app'))
$ErrorActionPreference = 'Stop'
$source = [IO.Path]::GetFullPath($PSScriptRoot)
$destination = [IO.Path]::GetFullPath($InstallRoot)
$expectedRoot = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'NetSentinel'))
if (-not $destination.StartsWith($expectedRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'InstallRoot must be a child of your LocalAppData\NetSentinel directory.' }
if ($source -eq $destination) { throw 'Extract the release ZIP to a separate folder before installation.' }
if (-not $PythonPath) {
  $candidate = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe'
  if (Test-Path -LiteralPath $candidate -PathType Leaf) { $PythonPath = $candidate }
  else { throw 'Install Python 3.11 (64-bit) from python.org, then pass -PythonPath with its absolute python.exe path.' }
}
$PythonPath = [IO.Path]::GetFullPath($PythonPath)
if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) { throw 'Python executable is missing.' }
& $PythonPath -c 'import sys, struct; assert sys.version_info[:2] == (3,11) and struct.calcsize("P")==8, "Python 3.11 64-bit required"'
if ($LASTEXITCODE -ne 0) { throw 'Python prerequisite check failed.' }
if (Test-Path -LiteralPath (Join-Path $destination 'VERSION')) { throw 'An installation already exists. Stop it, back up private state, and follow UPGRADE.md. This installer will not overwrite it.' }
New-Item -ItemType Directory -Path $destination -Force | Out-Null
# Explicit distribution allowlist; never copy a source checkout, env file or data.
foreach ($entry in @('companion','sensor','requirements-companion.txt','requirements-companion.lock','THIRD_PARTY_NOTICES.txt','README.md','UPGRADE.md','VERSION','Start.ps1','Stop.ps1','Start-Broker.ps1','Recover.ps1','Uninstall.ps1','Show-Access-Key.ps1')) {
  Copy-Item -LiteralPath (Join-Path $source $entry) -Destination $destination -Recurse
}
& $PythonPath -m venv (Join-Path $destination '.venv')
if ($LASTEXITCODE -ne 0) { throw 'Environment creation failed. No driver or security setting was changed.' }
$runtime = Join-Path $destination '.venv\Scripts\python.exe'
& $runtime -m pip install --require-hashes --only-binary=:all: -r (Join-Path $destination 'requirements-companion.lock')
if ($LASTEXITCODE -ne 0) { throw 'Dependency install failed. Retain this output and remove only the new app folder before retrying.' }
Push-Location $destination
try { & $runtime -m companion init; if ($LASTEXITCODE -ne 0) { throw 'Private state provisioning failed.' } }
finally { Pop-Location }
Write-Host 'NetSentinel installed. Run Start.ps1 without administrator privileges.'
Write-Host 'Npcap is not bundled or installed. Follow README.md for its manual prerequisite and license.'
Write-Host 'The source distribution and scripts are unsigned. No startup task or service was added.'
