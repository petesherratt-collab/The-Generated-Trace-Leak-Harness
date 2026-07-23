[CmdletBinding()]
param(
    [ValidateSet('CheckModels', 'DryRun', 'WiringCheck', 'Run', 'Analyse')]
    [string]$Mode = 'DryRun',

    [ValidateSet('minimax', 'glm', 'kimi')]
    [string]$Judge = 'minimax',

    [ValidateSet('deepinfra', 'inceptron', 'parasail', 'venice', 'moonshotai', 'together')]
    [string]$KimiProvider = 'deepinfra',

    [ValidateSet('bounded', 'native')]
    [string]$KimiMode = 'bounded',

    [string]$Python = 'python',

    [string]$EnvFile = 'C:\Users\Admin\Downloads\injection-defence-eval\.env',

    [ValidateRange(1, 4)]
    [int]$Workers = 2,

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
        Slug = 'minimax_official_permissive_reasoning_off'
        PrimaryTokens = 128
        RetryTokens = 256
        ReasoningMaxTokens = 0
        ReasoningEffort = 'none'
        RequireParameters = $false
        ReasoningUsageCeiling = 0
        TransportRetries = 2
        ScoreAcceptance = 'strict'
    }
    glm = @{
        Model = 'z-ai/glm-5.2'
        Provider = 'together'
        Slug = 'glm_together_serial_reasoning_off'
        PrimaryTokens = 128
        RetryTokens = 256
        ReasoningMaxTokens = 0
        ReasoningEffort = 'none'
        RequireParameters = $false
        ReasoningUsageCeiling = 0
        TransportRetries = 3
        ScoreAcceptance = 'strict'
    }
    kimi = @{
        Model = 'moonshotai/kimi-k2.7-code'
        Provider = $KimiProvider
        Slug = "kimi_$($KimiProvider)_permissive_headroom"
        PrimaryTokens = 4096
        RetryTokens = 8192
        ReasoningMaxTokens = 2048
        ReasoningEffort = ''
        RequireParameters = $false
        ReasoningUsageCeiling = 2048
        TransportRetries = 2
        ScoreAcceptance = 'strict'
    }
}

if ($Judge -eq 'kimi' -and $KimiMode -eq 'native') {
    $Panel.kimi = @{
        Model = 'moonshotai/kimi-k2.7-code'
        Provider = 'together'
        Slug = 'kimi_together_native_reasoning_v1'
        PrimaryTokens = 16384
        RetryTokens = 32768
        ReasoningMaxTokens = 0
        ReasoningEffort = ''
        RequireParameters = $false
        ReasoningUsageCeiling = -1
        TransportRetries = 3
        ScoreAcceptance = 'terminal'
    }
}

$Selected = $Panel[$Judge]
$Model = [string]$Selected.Model
$Provider = [string]$Selected.Provider
$Slug = [string]$Selected.Slug
$PrimaryTokens = [int]$Selected.PrimaryTokens
$RetryTokens = [int]$Selected.RetryTokens
$ReasoningMaxTokens = [int]$Selected.ReasoningMaxTokens
$ReasoningEffort = [string]$Selected.ReasoningEffort
$RequireParameters = [bool]$Selected.RequireParameters
$ReasoningUsageCeiling = [int]$Selected.ReasoningUsageCeiling
$TransportRetries = [int]$Selected.TransportRetries
$ScoreAcceptance = [string]$Selected.ScoreAcceptance
$Seed = 824663051
$Study = if ($Judge -eq 'kimi' -and $KimiMode -eq 'native') { 'openweight_kimi_native_compatibility_pilot_v1' } else { 'openweight_compatibility_pilot_v2' }
$Namespace = if ($Judge -eq 'kimi' -and $KimiMode -eq 'native') { 'ccc_openrouter_kimi_native_pilot_v1' } else { 'ccc_openrouter_pilot_v2' }
$RunId = "$($Namespace)_$($Slug)_$Seed"
$OutputPrefix = "$($Namespace)_$Slug"
$EvidenceDir = Join-Path $PSScriptRoot "results\$Namespace"
$Runner = Join-Path $PSScriptRoot 'run_ccc_frontier.py'
$LogStamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$ConsoleLog = Join-Path $EvidenceDir "$($OutputPrefix)_$($Mode.ToLowerInvariant())_console_$LogStamp.log"
$TempConsoleLog = Join-Path ([IO.Path]::GetTempPath()) "ccc_openrouter_pilot_$PID`_$LogStamp.log"
$PersistConsole = $Mode -in @('Run', 'Analyse')
$UsesApi = $Mode -in @('CheckModels', 'Run')

if ($UsesApi -and -not $ApproveApiCalls) {
    throw 'No API call made. Re-run with -ApproveApiCalls after reviewing the 48-cell pilot.'
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
    '--study', $Study,
    '--run-id', $RunId,
    '--evidence-dir', $EvidenceDir,
    '--output-prefix', $OutputPrefix,
    '--seed', "$Seed",
    '--provider', $Provider,
    '--score-max-tokens', "$PrimaryTokens",
    '--score-retry-tokens', "$RetryTokens",
    '--structured-score-output',
    '--score-acceptance', $ScoreAcceptance,
    '--balance-gap', '0.05',
    '--pilot-items-per-domain', '2',
    '--repetitions', '1',
    '--pilot-reasoning-ceiling', "$ReasoningUsageCeiling",
    '--workers', "$Workers",
    '--progress-secs', "$ProgressSecs",
    '--transport-retries', "$TransportRetries"
)
if ($ReasoningMaxTokens -gt 0) {
    $RunnerArgs += @('--reasoning-max-tokens', "$ReasoningMaxTokens")
}
if ($ReasoningEffort) {
    $RunnerArgs += @('--reasoning-effort', $ReasoningEffort)
}
if (-not $RequireParameters) {
    $RunnerArgs += '--allow-unadvertised-provider-parameters'
}

switch ($Mode) {
    'CheckModels' { $RunnerArgs += '--check-models' }
    'DryRun'      { $RunnerArgs += '--dry-run' }
    'WiringCheck' { $RunnerArgs += '--wiring-check' }
    'Run'         { $RunnerArgs += '--run' }
    'Analyse'     { $RunnerArgs += '--analyse-only' }
}
if ($UsesApi) {
    $RunnerArgs += '--approve-api-calls'
}

Write-Host "CCC pilot mode      : $Mode"
Write-Host "Judge               : $Judge ($Model)"
Write-Host "Provider            : $Provider (fallbacks disabled)"
Write-Host "Output ceilings      : $PrimaryTokens / $RetryTokens"
Write-Host "Reasoning control   : $(if ($ReasoningMaxTokens -gt 0) { "max $ReasoningMaxTokens" } elseif ($ReasoningEffort) { "effort $ReasoningEffort" } else { 'provider default' })"
Write-Host "Require parameters  : $RequireParameters"
Write-Host "Reasoning usage gate: $(if ($ReasoningUsageCeiling -lt 0) { 'record only; no ceiling' } else { "<= $ReasoningUsageCeiling tokens on every attempt" })"
Write-Host "Score acceptance    : $ScoreAcceptance"
Write-Host "Python              : $PythonVersion ($Python)"
Write-Host "Seed / run ID       : $Seed / $RunId"
Write-Host "Evidence            : $EvidenceDir"
Write-Host 'Pilot cells         : 48 (2 items x 3 domains x 4 conditions x 2 candidates)'
Write-Host "API approved        : $($ApproveApiCalls.IsPresent)"

if ($PersistConsole) {
    & $Python @RunnerArgs 2>&1 | Tee-Object -FilePath $TempConsoleLog
    $ExitCode = $LASTEXITCODE
} else {
    & $Python @RunnerArgs
    $ExitCode = $LASTEXITCODE
}
if ($ExitCode -ne 0) {
    $LogHint = if ($PersistConsole) { " Temporary console record: $TempConsoleLog" } else { '' }
    throw "CCC pilot runner exited with code $ExitCode.$LogHint"
}

if ($PersistConsole) {
    New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null
    Move-Item -LiteralPath $TempConsoleLog -Destination $ConsoleLog
    Write-Host "Completed successfully. Console record: $ConsoleLog"
} else {
    Write-Host 'Completed successfully.'
}
