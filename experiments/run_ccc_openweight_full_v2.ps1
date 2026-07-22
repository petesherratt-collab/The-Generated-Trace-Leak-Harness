[CmdletBinding()]
param(
    [ValidateSet('CheckModels', 'DryRun', 'WiringCheck', 'Run', 'Resume', 'Analyse')]
    [string]$Mode = 'DryRun',

    [ValidateSet('minimax', 'glm')]
    [string]$Judge = 'minimax',

    [string]$Python = 'python',

    [string]$EnvFile = 'C:\Users\Admin\Downloads\injection-defence-eval\.env',

    [ValidateRange(10, 3600)]
    [int]$ProgressSecs = 60,

    [switch]$ApproveApiCalls
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Panel = @{
    minimax = @{
        Model = 'minimax/minimax-m3'
        Provider = 'minimax'
        Study = 'openweight_minimax_m3_v2'
        Prefix = 'ccc_openrouter_minimax_m3_v2'
        Workers = 2
        TransportRetries = 2
    }
    glm = @{
        Model = 'z-ai/glm-5.2'
        Provider = 'together'
        Study = 'openweight_glm52_v2'
        Prefix = 'ccc_openrouter_glm52_v2'
        Workers = 1
        TransportRetries = 3
    }
}

$Selected = $Panel[$Judge]
$Model = [string]$Selected.Model
$Provider = [string]$Selected.Provider
$Study = [string]$Selected.Study
$OutputPrefix = [string]$Selected.Prefix
$Workers = [int]$Selected.Workers
$TransportRetries = [int]$Selected.TransportRetries
$Seed = 1496017540
$RunId = "$($OutputPrefix)_$Seed"
$EvidenceDir = Join-Path $PSScriptRoot "results\$OutputPrefix"
$Runner = Join-Path $PSScriptRoot 'run_ccc_frontier.py'
$LogStamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$ConsoleLog = Join-Path $EvidenceDir "$($OutputPrefix)_$($Mode.ToLowerInvariant())_console_$LogStamp.log"
$TempConsoleLog = Join-Path ([IO.Path]::GetTempPath()) "ccc_openweight_full_v2_$PID`_$LogStamp.log"
$PersistConsole = $Mode -in @('Run', 'Resume', 'Analyse')
$UsesApi = $Mode -in @('CheckModels', 'Run', 'Resume')

if ($UsesApi -and -not $ApproveApiCalls) {
    throw 'No API call made. Re-run with -ApproveApiCalls after reviewing the frozen 1,344-cell arm.'
}
if ($UsesApi) {
    if (-not $EnvFile -or -not (Test-Path -LiteralPath $EnvFile -PathType Leaf)) {
        throw "The env file was not found: $EnvFile"
    }
    $env:OPENROUTER_ENV_FILE = (Resolve-Path -LiteralPath $EnvFile).Path
}

$PythonVersion = (& $Python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')").Trim()
if ($LASTEXITCODE -ne 0) { throw "Could not run the requested Python interpreter: $Python" }
$Version = [version]$PythonVersion
if ($Version.Major -ne 3 -or $Version.Minor -lt 10 -or $Version.Minor -gt 13) {
    throw "CCC release gates require CPython 3.10-3.13; $Python resolved to $PythonVersion."
}

$RunnerArgs = @(
    $Runner,
    '--models', $Model,
    '--domains', 'arith,code,sql',
    '--protocols', 'score_only',
    '--study', $Study,
    '--run-id', $RunId,
    '--evidence-dir', $EvidenceDir,
    '--output-prefix', $OutputPrefix,
    '--seed', "$Seed",
    '--provider', $Provider,
    '--score-max-tokens', '128',
    '--score-retry-tokens', '256',
    '--reasoning-effort', 'none',
    '--structured-score-output',
    '--score-acceptance', 'strict',
    '--allow-unadvertised-provider-parameters',
    '--balance-gap', '0.05',
    '--workers', "$Workers",
    '--progress-secs', "$ProgressSecs",
    '--transport-retries', "$TransportRetries"
)

switch ($Mode) {
    'CheckModels' { $RunnerArgs += '--check-models' }
    'DryRun'      { $RunnerArgs += '--dry-run' }
    'WiringCheck' { $RunnerArgs += '--wiring-check' }
    'Run'         { $RunnerArgs += '--run' }
    'Resume'      { $RunnerArgs += '--resume' }
    'Analyse'     { $RunnerArgs += '--analyse-only' }
}
if ($UsesApi) { $RunnerArgs += '--approve-api-calls' }

Write-Host "CCC open-weight v2  : $Mode"
Write-Host "Judge              : $Judge ($Model)"
Write-Host "Provider           : $Provider (fallbacks disabled)"
Write-Host 'Reasoning          : effort=none; observed usage must be zero'
Write-Host 'Output ceilings    : 128 / 256'
Write-Host 'Score acceptance   : exact JSON plus normal stop'
Write-Host "Workers / retries  : $Workers / $TransportRetries"
Write-Host "Python             : $PythonVersion ($Python)"
Write-Host "Seed / run ID      : $Seed / $RunId"
Write-Host "Evidence           : $EvidenceDir"
Write-Host 'Full cells         : 1,344'
Write-Host "API approved       : $($ApproveApiCalls.IsPresent)"

if ($PersistConsole) {
    & $Python @RunnerArgs 2>&1 | Tee-Object -FilePath $TempConsoleLog
    $ExitCode = $LASTEXITCODE
} else {
    & $Python @RunnerArgs
    $ExitCode = $LASTEXITCODE
}
if ($ExitCode -ne 0) {
    $LogHint = if ($PersistConsole) { " Temporary console record: $TempConsoleLog" } else { '' }
    throw "CCC open-weight v2 runner exited with code $ExitCode.$LogHint"
}

if ($PersistConsole) {
    New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null
    Move-Item -LiteralPath $TempConsoleLog -Destination $ConsoleLog
    Write-Host "Completed successfully. Console record: $ConsoleLog"
} else {
    Write-Host 'Completed successfully.'
}
