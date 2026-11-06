<#
.SYNOPSIS
  Instala (ou remove) a impressora virtual "ILoveFMTLY PDF".

.DESCRIPTION
  Usa o driver nativo "Microsoft Print To PDF" com uma porta local que grava
  em %LOCALAPPDATA%\ILoveFMTLY\spool\print.pdf. O ILoveFMTLY vigia essa
  pasta e abre cada impressão automaticamente. Nada sai da máquina.

  Precisa ser executado como administrador, uma única vez.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\setup_printer.ps1
  powershell -ExecutionPolicy Bypass -File scripts\setup_printer.ps1 -Remove
#>
param([switch]$Remove)

$ErrorActionPreference = 'Stop'
$PrinterName = 'ILoveFMTLY PDF'
$Driver = 'Microsoft Print To PDF'
$SpoolDir = Join-Path $env:LOCALAPPDATA 'ILoveFMTLY\spool'
$PortName = Join-Path $SpoolDir 'print.pdf'

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
           ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Error 'Execute este script como administrador.'
}

if ($Remove) {
    if (Get-Printer -Name $PrinterName -ErrorAction SilentlyContinue) {
        Remove-Printer -Name $PrinterName
    }
    if (Get-PrinterPort -Name $PortName -ErrorAction SilentlyContinue) {
        Remove-PrinterPort -Name $PortName
    }
    Write-Host "Impressora '$PrinterName' removida."
    return
}

New-Item -ItemType Directory -Force -Path $SpoolDir | Out-Null

if (-not (Get-PrinterDriver -Name $Driver -ErrorAction SilentlyContinue)) {
    Write-Host "Driver '$Driver' ausente. Ativando o recurso do Windows (local, sem download)..."
    Enable-WindowsOptionalFeature -Online -FeatureName 'Printing-PrintToPDFServices-Features' -All -NoRestart | Out-Null
    if (-not (Get-PrinterDriver -Name $Driver -ErrorAction SilentlyContinue)) {
        Write-Error "Driver '$Driver' continua indisponível. Reinicie o Windows e rode o script de novo."
    }
}
if (-not (Get-PrinterPort -Name $PortName -ErrorAction SilentlyContinue)) {
    Add-PrinterPort -Name $PortName
}
if (-not (Get-Printer -Name $PrinterName -ErrorAction SilentlyContinue)) {
    Add-Printer -Name $PrinterName -DriverName $Driver -PortName $PortName
}
Write-Host "Impressora '$PrinterName' pronta. Impressões vão para $SpoolDir"
