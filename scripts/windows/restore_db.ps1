[CmdletBinding(DefaultParameterSetName = 'FromUrl')]
param(
    [Parameter(Mandatory = $true, ParameterSetName = 'FromUrl')]
    [string]$DumpUrl,

    [Parameter(Mandatory = $true, ParameterSetName = 'FromFile')]
    [string]$DumpFile,

    [string]$Database = 'marketplace_db',

    [string]$DbUser = 'odoo',
    [string]$DbPassword = $null,
    [string]$DbHost = $null,
    [string]$DbPort = $null,
    [string]$PgPath = $null,

    [switch]$Force,
    [switch]$Neutralize
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-RepoRoot {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    # scripts/windows/restore_db.ps1 -> repo root is two levels up
    return (Resolve-Path (Join-Path $scriptDir '..\..')).Path
}

$repoRoot = Get-RepoRoot
$odooBin = Join-Path $repoRoot 'odoo\odoo-bin'
if (-not (Test-Path $odooBin)) {
    throw "Impossible de trouver odoo-bin: $odooBin (vérifie que le submodule Odoo est bien initialisé)."
}

$venvPython = Join-Path $repoRoot 'venv\Scripts\python.exe'
if (Test-Path $venvPython) {
    $pythonExe = $venvPython
} else {
    $pythonExe = (Get-Command python -ErrorAction Stop).Source
}

$addonsPath = 'odoo/addons,odoo/odoo/addons,addons'

$tempDump = $null
try {
    if ($PSCmdlet.ParameterSetName -eq 'FromUrl') {
        $tempDump = Join-Path $env:TEMP ("AuraMarket_dump_{0}.zip" -f ([guid]::NewGuid().ToString('N')))
        Write-Host "Téléchargement du dump: $DumpUrl"
        Invoke-WebRequest -Uri $DumpUrl -OutFile $tempDump
        $DumpFile = $tempDump
    } else {
        $DumpFile = (Resolve-Path $DumpFile).Path
    }

    if (-not (Test-Path $DumpFile)) {
        throw "Dump introuvable: $DumpFile"
    }

    $odooArgs = @(
        $odooBin,
        'db',
        '--addons-path', $addonsPath
    )

    if ($DbUser) { $odooArgs += @('--db_user', $DbUser) }
    if ($DbPassword) { $odooArgs += @('--db_password', $DbPassword) }
    if ($DbHost) { $odooArgs += @('--db_host', $DbHost) }
    if ($DbPort) { $odooArgs += @('--db_port', $DbPort) }
    if ($PgPath) { $odooArgs += @('--pg_path', $PgPath) }

    $odooArgs += @('load')
    if ($Force) { $odooArgs += @('--force') }
    if ($Neutralize) { $odooArgs += @('--neutralize') }
    $odooArgs += @($Database, $DumpFile)

    Push-Location $repoRoot
    try {
        & $pythonExe @odooArgs
    } finally {
        Pop-Location
    }

    Write-Host "OK: base '$Database' restaurée."
} finally {
    if ($tempDump -and (Test-Path $tempDump)) {
        Remove-Item -Force $tempDump
    }
}
