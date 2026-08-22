#Requires -Version 5.1
<#
.SYNOPSIS
  Bootstrap and run video-unwatermark on Windows.

.EXAMPLE
  .\start.ps1
  .\start.ps1 -Cookies C:\path\to\cookies.txt
  .\start.ps1 -CookiesFromBrowser chrome
#>
[CmdletBinding()]
param(
  [string]$Cookies = "",
  [string]$CookiesFromBrowser = ""
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Find-Python {
  foreach ($runner in @(
      @{ Cmd = "py"; Args = @("-3") },
      @{ Cmd = "python"; Args = @() },
      @{ Cmd = "python3"; Args = @() }
    )) {
    if (-not (Get-Command $runner.Cmd -ErrorAction SilentlyContinue)) { continue }
    try {
      $ver = & $runner.Cmd @($runner.Args + @("-c", "import sys; print(sys.version_info[:2] >= (3,10))")) 2>$null
      if ("$ver".Trim() -eq "True") {
        return @{ Cmd = $runner.Cmd; Prefix = $runner.Args }
      }
    } catch { }
  }
  return $null
}

$py = Find-Python
if (-not $py) {
  Write-Error "Python 3.10+ not found. Install from https://www.python.org/downloads/ and re-run."
  exit 1
}

function Invoke-Py {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$PyArgs)
  & $py.Cmd @($py.Prefix + $PyArgs)
  return $LASTEXITCODE
}

if ($Cookies) {
  $env:UNWATERMARK_COOKIES = $Cookies
  Write-Host "[start] cookies file: $Cookies"
}
if ($CookiesFromBrowser) {
  $env:UNWATERMARK_COOKIES_FROM_BROWSER = $CookiesFromBrowser
  Write-Host "[start] cookies_from_browser: $CookiesFromBrowser"
}

$venvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
  Write-Host "[start] creating .venv ..."
  $code = Invoke-Py -m venv .venv
  if ($code -ne 0 -or -not (Test-Path $venvPython)) {
    Write-Error "Failed to create .venv"
    exit 1
  }
}

function Invoke-VenvPy {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$PyArgs)
  & $venvPython @PyArgs
  return $LASTEXITCODE
}

Write-Host "[start] pip install ..."
Invoke-VenvPy -m pip install -U pip | Out-Null
Invoke-VenvPy -m pip install -r requirements.txt
if ((Invoke-VenvPy -m pip install videofetch) -ne 0) { Write-Host "[start] skip videofetch" }
if ((Invoke-VenvPy -m pip install you-get) -ne 0) { Write-Host "[start] skip you-get" }

$hasPw = $false
& $venvPython -c "from playwright.sync_api import sync_playwright" 2>$null
if ($LASTEXITCODE -eq 0) { $hasPw = $true }
if (-not $hasPw) {
  if ((Invoke-VenvPy -m pip install playwright) -ne 0) {
    Write-Host "[start] skip playwright"
  } else {
    $hasPw = $true
  }
}

$chromeOk = $false
foreach ($p in @(
    "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "${env:LocalAppData}\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles}\Chromium\Application\chrome.exe"
  )) {
  if ($p -and (Test-Path $p)) { $chromeOk = $true; break }
}
if (-not $chromeOk -and $hasPw) {
  Write-Host "[start] installing Playwright Chromium ..."
  Invoke-VenvPy -m playwright install chromium
  if ($LASTEXITCODE -ne 0) { Write-Host "[start] skip playwright chromium" }
}

$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ffmpeg) {
  Write-Host "[start] ffmpeg not on PATH."
  Write-Host "        Install tip (pick one):"
  Write-Host "          winget install --id Gyan.FFmpeg -e"
  Write-Host "          choco install ffmpeg"
  Write-Host "          Or download from https://ffmpeg.org/download.html"
  Write-Host "        Admin rights may be required; this script will not elevate."
}

Write-Host "[start] ensuring lux for Windows..."
$luxCode = "from app.engines.lux import ensure_lux, resolve_lux_asset, lux_bin_path; n,u=resolve_lux_asset(); print('[start] lux asset:', n); print('[start] lux bin:', lux_bin_path()); print('[start] lux ok' if ensure_lux() else '[start] lux missing (engine will skip)')"
& $venvPython -c $luxCode
if ($LASTEXITCODE -ne 0) { Write-Host "[start] skip lux bootstrap" }

$env:PYTHONUNBUFFERED = "1"
Write-Host "[start] http://127.0.0.1:8787"
& $venvPython -m uvicorn app.main:app --host 0.0.0.0 --port 8787
exit $LASTEXITCODE
