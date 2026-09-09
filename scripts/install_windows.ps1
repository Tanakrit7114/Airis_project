$ErrorActionPreference='Stop'
$root=Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path); Set-Location $root
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -U pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
Write-Host 'JARVIS installed. Install Tesseract separately for OCR.'
