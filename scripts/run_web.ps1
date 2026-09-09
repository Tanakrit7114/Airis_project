$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root
$python = Join-Path $root '.venv/Scripts/python.exe'
if (!(Test-Path $python)) { $python = 'python' }
& $python -m uvicorn app.server.main:app --host 127.0.0.1 --port 8001
