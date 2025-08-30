param([int]$Port=8080)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Always run from project root (handles being launched from /scripts)
$ROOT = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ROOT

function Get-PythonCmd {
  if (Get-Command py -ErrorAction SilentlyContinue) {
    return @("py","-3")
  }
  if (Get-Command python -ErrorAction SilentlyContinue) {
    return @("python")
  }
  Write-Host "Python not found. Attempting to install via winget..." -ForegroundColor Yellow
  try {
    winget install --id Python.Python.3 --exact --source winget --accept-source-agreements --accept-package-agreements
  } catch {
    Write-Host "winget install failed. Please install Python 3 from https://www.python.org/downloads/ then re-run." -ForegroundColor Red
    exit 1
  }
  if (Get-Command py -ErrorAction SilentlyContinue) { return @("py","-3") }
  if (Get-Command python -ErrorAction SilentlyContinue) { return @("python") }
  Write-Host "Could not find Python after installation. Please restart PowerShell and run again." -ForegroundColor Red
  exit 1
}

$py = Get-PythonCmd

# Create venv if missing
$venvPy = Join-Path $ROOT ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
  Write-Host "Creating virtual environment..." -ForegroundColor Cyan
  if ($py.Length -gt 1) {
    & $py[0] $py[1] -m venv .venv
  } else {
    & $py[0] -m venv .venv
  }
  $venvPy = Join-Path $ROOT ".venv\Scripts\python.exe"
}

# Install deps with venv python (no activation needed)
& $venvPy -m pip install --upgrade pip
& $venvPy -m pip install -r requirements.txt

# Run app
$env:PORT=$Port
& $venvPy -m app.main
