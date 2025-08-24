# Instal·lació + Tasca programada per VSJ 1ANF
param(
  [string]$RepoURL    = "https://github.com/Detersolin/rfevb-classificacio-vsj-1anf.git",
  [string]$InstallDir = "C:\Guillem\Temporada 25-26\Overlay\VSJ\1ANF\rfevb-classificacio-vsj-1anf"
)

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ErrorActionPreference = "Stop"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Cal Git (git-scm.com)" }
if (-not (Get-Command py  -ErrorAction SilentlyContinue)) { throw "Cal Python (python.org) amb 'Add to PATH'." }

if (Test-Path $InstallDir) {
  Set-Location $InstallDir
  git pull
} else {
  git clone $RepoURL $InstallDir
  Set-Location $InstallDir
}

py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

New-Item -ItemType Directory -Force -Path "C:\Guillem\Temporada 25-26\Overlay\VSJ\1ANF" | Out-Null

$taskName = "VSJ_1ANF_Classificacio"
$ps1 = Join-Path $InstallDir "run_vsj_1anf.ps1"
$action = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$ps1`" -RepoDir `"$InstallDir`""
schtasks /Create /TN $taskName /TR $action /SC ONLOGON /RL HIGHEST /F

Write-Host "✔ VSJ 1ANF instal·lat. Reinicia sessió o executa ara: $action"
