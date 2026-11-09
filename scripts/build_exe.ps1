<#
.SYNOPSIS
  Gera o ILoveFMTLY.exe com PyInstaller.

.DESCRIPTION
  Usa o .venv do projeto. Instala o PyInstaller se faltar, roda os testes
  e empacota. Resultado padrão: dist\ILoveFMTLY\ILoveFMTLY.exe (copie a
  pasta inteira). Com -OneFile: dist\ILoveFMTLY.exe sozinho, mas abre mais
  devagar.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
  powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1 -OneFile
  powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1 -SkipTests
#>
param([switch]$OneFile, [switch]$SkipTests)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root '.venv\Scripts\python.exe'
Set-Location $Root

if (-not (Test-Path $Py)) {
    throw "Não achei $Py. Crie o ambiente antes: python -m venv .venv; .venv\Scripts\python -m pip install -r requirements.txt"
}

& $Py -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Instalando PyInstaller...'
    & $Py -m pip install 'pyinstaller>=6.10'
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar o PyInstaller.' }
}

if (-not $SkipTests) {
    Write-Host 'Rodando testes...'
    & $Py -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw 'Testes falharam. Nada foi empacotado.' }
}

if ($OneFile) { $env:ILOVEFMTLY_ONEFILE = '1' } else { Remove-Item Env:ILOVEFMTLY_ONEFILE -ErrorAction SilentlyContinue }

# O PyInstaller apaga dist\ILoveFMTLY; o config.json (cadastro e preferências) mora lá.
$Config = 'dist\ILoveFMTLY\config.json'
$Backup = Join-Path $env:TEMP 'ILoveFMTLY-config.json'
if (Test-Path $Config) { Copy-Item $Config $Backup -Force }

Write-Host 'Empacotando...'
& $Py -m PyInstaller --noconfirm --clean ILoveFMTLY.spec
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller falhou.' }
if (Test-Path $Backup) { Move-Item $Backup $Config -Force; Write-Host 'config.json preservado.' }

$Exe = if ($OneFile) { 'dist\ILoveFMTLY.exe' } else { 'dist\ILoveFMTLY\ILoveFMTLY.exe' }
if (-not (Test-Path $Exe)) { throw "O PyInstaller terminou, mas $Exe não existe." }

$Size = if ($OneFile) { (Get-Item $Exe).Length } else { (Get-ChildItem 'dist\ILoveFMTLY' -Recurse | Measure-Object Length -Sum).Sum }
Write-Host ("Pronto: {0} ({1:N0} MB)" -f (Resolve-Path $Exe), ($Size / 1MB))
