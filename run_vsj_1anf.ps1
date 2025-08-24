# Arrenca el scraper (actualitza repo + venv) per VSJ 1ANF
param(
  [string]$RepoDir = "C:\Guillem\Temporada 25-26\Overlay\VSJ\1ANF\rfevb-classificacio-vsj-1anf"
)

$ErrorActionPreference = "SilentlyContinue"

if (Test-Path $RepoDir) {
  Set-Location $RepoDir
  git pull
} else {
  Write-Host "Repo no trobat a $RepoDir"
  exit 1
}

if (-not (Test-Path ".\.venv")) { py -m venv .venv }
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

New-Item -ItemType Directory -Force -Path "C:\Guillem\Temporada 25-26\Overlay\VSJ\1ANF" | Out-Null

.\.venv\Scripts\python.exe .\scrape_vsj_1anf.py
