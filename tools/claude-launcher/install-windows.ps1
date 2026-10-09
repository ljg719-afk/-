# Claude launcher installer for Windows (ASCII only: safe for "irm | iex" on PowerShell 5.1)
# Usage (PowerShell):
#   irm https://raw.githubusercontent.com/ljg719-afk/-/claude/relaxed-hamilton-cdii2m/tools/claude-launcher/install-windows.ps1 | iex

$ErrorActionPreference = 'Stop'
$base = 'https://raw.githubusercontent.com/ljg719-afk/-/claude/relaxed-hamilton-cdii2m/tools/claude-launcher'
$dest = Join-Path $env:USERPROFILE 'claude-launcher'

New-Item -ItemType Directory -Force -Path $dest | Out-Null
# -OutFile keeps the file bytes (UTF-8 BOM) so Korean text displays correctly
Invoke-WebRequest -UseBasicParsing -Uri "$base/claude-launcher.ps1" -OutFile (Join-Path $dest 'claude-launcher.ps1')
Invoke-WebRequest -UseBasicParsing -Uri "$base/claude-launcher.cmd" -OutFile (Join-Path $dest 'claude-launcher.cmd')

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if (-not $userPath) { $userPath = '' }
if (($userPath -split ';') -notcontains $dest) {
    [Environment]::SetEnvironmentVariable('Path', ($userPath.TrimEnd(';') + ';' + $dest).TrimStart(';'), 'User')
}
if (($env:Path -split ';') -notcontains $dest) { $env:Path = "$env:Path;$dest" }

Write-Host ''
Write-Host "Installed: $dest" -ForegroundColor Green
Write-Host 'Run "claude-launcher" in any folder. (New windows pick up PATH automatically.)'
