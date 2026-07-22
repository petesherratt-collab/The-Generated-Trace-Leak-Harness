[CmdletBinding()]
param(
    [ValidateSet('CheckModels', 'DryRun', 'WiringCheck', 'Run', 'Resume', 'Analyse')]
    [string]$Mode = 'DryRun',

    [string]$Python = 'python',

    [string]$EnvFile = 'C:\Users\Admin\Downloads\injection-defence-eval\.env',

    [ValidateRange(1, 16)]
    [int]$Workers = 4,

    [switch]$ApproveApiCalls
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Models = @(
    'openai/gpt-5.6-sol',
    '~anthropic/claude-fable-latest',
    'google/gemini-3.1-pro-preview',
    'x-ai/grok-4.5'
)
$ModelCsv = $Models -join ','
$Seed = 305774821
$RunId = 'ccc_frontier_v3_305774821'
$OutputPrefix = 'ccc_frontier_v3'
$EvidenceDir = Join-Path $PSScriptRoot 'results\ccc_frontier_v3'
$Runner = Join-Path $PSScriptRoot 'run_ccc_frontier.py'
$LogStamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$ConsoleLog = Join-Path $EvidenceDir "ccc_frontier_v3_$($Mode.ToLowerInvariant())_console_$LogStamp.log"
$TempConsoleLog = Join-Path ([IO.Path]::GetTempPath()) "ccc_frontier_v3_$PID`_$LogStamp.log"
$PersistConsole = $Mode -in @('Run', 'Resume', 'Analyse')

$ApiModes = @('CheckModels', 'Run', 'Resume')
$UsesApi = $Mode -in $ApiModes
if ($UsesApi -and -not $ApproveApiCalls) {
    throw 'No API call made. Re-run with -ApproveApiCalls only after reviewing the frozen v3 panel, budgets, paths, and cost.'
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
    throw "CCC release gates require CPython 3.10-3.13; $Python resolved to $PythonVersion. Pass -Python with a supported interpreter."
}

$RunnerArgs = @(
    $Runner,
    '--models', $ModelCsv,
    '--domains', 'arith,code,sql',
    '--protocols', 'score_only',
    '--study', 'frontier_v3',
    '--run-id', $RunId,
    '--evidence-dir', $EvidenceDir,
    '--output-prefix', $OutputPrefix,
    '--seed', "$Seed",
    '--score-max-tokens', '1024',
    '--score-retry-tokens', '2048',
    '--balance-gap', '0.05',
    '--workers', "$Workers"
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

Write-Host "CCC frontier v3 mode : $Mode"
Write-Host "Python               : $PythonVersion ($Python)"
Write-Host "Models               : $ModelCsv"
Write-Host "Seed / run ID        : $Seed / $RunId"
Write-Host "Evidence             : $EvidenceDir"
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
    throw "CCC frontier v3 runner exited with code $ExitCode.$LogHint"
}

if ($PersistConsole) {
    New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null
    Move-Item -LiteralPath $TempConsoleLog -Destination $ConsoleLog
    Write-Host "Completed successfully. Console record: $ConsoleLog"
} else {
    Write-Host 'Completed successfully.'
}
