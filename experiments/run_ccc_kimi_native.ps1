[CmdletBinding()]
param(
    [ValidateSet('CheckModels', 'DryRun', 'WiringCheck', 'Run', 'Resume', 'Analyse')]
    [string]$Mode = 'DryRun',

    [string]$Python = 'python',

    [string]$EnvFile = 'C:\Users\Admin\Downloads\injection-defence-eval\.env',

    [ValidateRange(10, 3600)]
    [int]$ProgressSecs = 60,

    [switch]$ApproveApiCalls
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Model = 'moonshotai/kimi-k2.7-code'
$Provider = 'together'
$Seed = 1496017540
$RunId = "ccc_openrouter_kimi_native_v1_$Seed"
$OutputPrefix = 'ccc_openrouter_kimi_native_v1'
$EvidenceDir = Join-Path $PSScriptRoot 'results\ccc_openrouter_kimi_native_v1'
$Runner = Join-Path $PSScriptRoot 'run_ccc_frontier.py'
$LogStamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$ConsoleLog = Join-Path $EvidenceDir "$($OutputPrefix)_$($Mode.ToLowerInvariant())_console_$LogStamp.log"
$TempConsoleLog = Join-Path ([IO.Path]::GetTempPath()) "ccc_kimi_native_$PID`_$LogStamp.log"
$PersistConsole = $Mode -in @('Run', 'Resume', 'Analyse')
$UsesApi = $Mode -in @('CheckModels', 'Run', 'Resume')

if ($UsesApi -and -not $ApproveApiCalls) {
    throw 'No API call made. Re-run with -ApproveApiCalls after reviewing the frozen 1,344-cell run.'
}
if ($UsesApi) {
    if (-not $EnvFile -or -not (Test-Path -LiteralPath $EnvFile -PathType Leaf)) {
        throw "The env file was not found: $EnvFile"
    }
    $env:OPENROUTER_ENV_FILE = (Resolve-Path -LiteralPath $EnvFile).Path
}

$PythonVersion = (& $Python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')").Trim()
if ($LASTEXITCODE -ne 0) {
    throw "Could not run the requested Python interpreter: $Python"
}
$Version = [version]$PythonVersion
if ($Version.Major -ne 3 -or $Version.Minor -lt 10 -or $Version.Minor -gt 13) {
    throw "CCC release gates require CPython 3.10-3.13; $Python resolved to $PythonVersion."
}

$RunnerArgs = @(
    $Runner,
    '--models', $Model,
    '--domains', 'arith,code,sql',
    '--protocols', 'score_only',
    '--study', 'openweight_kimi_native_v1',
    '--run-id', $RunId,
    '--evidence-dir', $EvidenceDir,
    '--output-prefix', $OutputPrefix,
    '--seed', "$Seed",
    '--provider', $Provider,
    '--score-max-tokens', '16384',
    '--score-retry-tokens', '32768',
    '--structured-score-output',
    '--score-acceptance', 'terminal',
    '--allow-unadvertised-provider-parameters',
    '--balance-gap', '0.05',
    '--workers', '1',
    '--progress-secs', "$ProgressSecs",
    '--transport-retries', '3'
)

switch ($Mode) {
    'CheckModels' { $RunnerArgs += '--check-models' }
    'DryRun'      { $RunnerArgs += '--dry-run' }
    'WiringCheck' { $RunnerArgs += '--wiring-check' }
    'Run'         { $RunnerArgs += '--run' }
    'Resume'      { $RunnerArgs += '--resume' }
    'Analyse'     { $RunnerArgs += '--analyse-only' }
}
if ($UsesApi) {
    $RunnerArgs += '--approve-api-calls'
}

Write-Host "CCC Kimi native mode : $Mode"
Write-Host "Model/provider       : $Model / $Provider (fallbacks disabled)"
Write-Host 'Reasoning            : provider default'
Write-Host 'Output ceilings      : 16384 / 32768'
Write-Host 'Score acceptance     : terminal JSON plus normal stop'
Write-Host "Python               : $PythonVersion ($Python)"
Write-Host "Seed / run ID        : $Seed / $RunId"
Write-Host "Evidence             : $EvidenceDir"
Write-Host 'Full cells           : 1,344 (56 items x 8 strata x 3 repetitions)'
Write-Host "API approved         : $($ApproveApiCalls.IsPresent)"

if ($PersistConsole) {
    & $Python @RunnerArgs 2>&1 | Tee-Object -FilePath $TempConsoleLog
    $ExitCode = $LASTEXITCODE
} else {
    & $Python @RunnerArgs
    $ExitCode = $LASTEXITCODE
}
if ($ExitCode -ne 0) {
    $LogHint = if ($PersistConsole) { " Temporary console record: $TempConsoleLog" } else { '' }
    throw "CCC Kimi native runner exited with code $ExitCode.$LogHint"
}

if ($PersistConsole) {
    New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null
    Move-Item -LiteralPath $TempConsoleLog -Destination $ConsoleLog
    Write-Host "Completed successfully. Console record: $ConsoleLog"
} else {
    Write-Host 'Completed successfully.'
}
