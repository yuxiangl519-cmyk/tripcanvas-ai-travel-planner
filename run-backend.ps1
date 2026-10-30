$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$env:DEBUG = 'false'
Push-Location (Join-Path $PSScriptRoot 'backend')
try {
    if (-not (Test-Path '.venv/Scripts/python.exe')) {
        throw 'Create backend/.venv and install requirements.txt first; see QUICKSTART.md.'
    }
    $env:PATH = "$(Join-Path $PWD '.venv/Scripts');$env:PATH"
    & ./.venv/Scripts/python.exe run.py
    if ($LASTEXITCODE -ne 0) { throw "Backend exited with code $LASTEXITCODE" }
} finally {
    Pop-Location
}
