# Claude launcher installer for Windows (ASCII only: safe for "irm | iex" on PowerShell 5.1)
# Usage (PowerShell):
#   irm https://raw.githubusercontent.com/ljg719-afk/-/claude/relaxed-hamilton-cdii2m/tools/claude-launcher/install-windows.ps1 | iex

$ErrorActionPreference = 'Stop'
$base = 'https://raw.githubusercontent.com/ljg719-afk/-/claude/relaxed-hamilton-cdii2m/tools/claude-launcher'
$dest = Join-Path $env:USERPROFILE 'claude-launcher'

$lib = Join-Path $dest 'lib'
New-Item -ItemType Directory -Force -Path $lib | Out-Null
# PowerShell resolves "claude-launcher" to a .ps1 before a .cmd in the same PATH folder,
# and the .ps1 is then blocked by the execution policy. Keep the .ps1 out of the PATH folder.
Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $dest 'claude-launcher.ps1')
# -OutFile keeps the file bytes (UTF-8 BOM) so Korean text displays correctly
Invoke-WebRequest -UseBasicParsing -Uri "$base/claude-launcher.ps1?t=$([DateTime]::UtcNow.Ticks)" -OutFile (Join-Path $lib 'claude-launcher.ps1')
$cmd = "@echo off`r`npowershell -NoProfile -ExecutionPolicy Bypass -File `"%~dp0lib\claude-launcher.ps1`"`r`n"
[System.IO.File]::WriteAllText((Join-Path $dest 'claude-launcher.cmd'), $cmd, (New-Object System.Text.ASCIIEncoding))

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if (-not $userPath) { $userPath = '' }
if (($userPath -split ';') -notcontains $dest) {
    [Environment]::SetEnvironmentVariable('Path', ($userPath.TrimEnd(';') + ';' + $dest).TrimStart(';'), 'User')
}
if (($env:Path -split ';') -notcontains $dest) { $env:Path = "$env:Path;$dest" }

Write-Host ''
Write-Host "Installed: $dest" -ForegroundColor Green
Write-Host 'Run "claude-launcher" in any folder. (New windows pick up PATH automatically.)'
