[CmdletBinding()]
param(
    [ValidateSet('CheckModels', 'DryRun', 'WiringCheck', 'Run', 'Resume', 'Analyse')]
    [string]$Mode = 'DryRun',

    [ValidateSet('minimax', 'qwen', 'glm', 'kimi')]
    [string]$Judge = 'minimax',

    [string]$Python = 'python',

    [string]$EnvFile = 'C:\Users\Admin\Downloads\injection-defence-eval\.env',

    [ValidateRange(1, 32)]
    [int]$Workers = 4,

    [ValidateRange(10, 3600)]
    [int]$ProgressSecs = 60,

    [switch]$ApproveApiCalls
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# The panel is frozen in PREREG_ccc_openrouter_panel.md. Runs are deliberately
# separate by judge: this prevents one provider failure from corrupting another
# model's metadata and lets the operator inspect cost/missingness between blocks
# without changing the already-frozen panel or decision rule.
$Panel = @{
    minimax = @{
        Model = 'minimax/minimax-m3'
        Provider = 'deepinfra'
        Slug = 'minimax_m3_structured'
        PrimaryTokens = 1024
        RetryTokens = 2048
        ReasoningMaxTokens = 2048
        ReasoningEffort = ''
        StructuredScoreOutput = $true
    }
    qwen = @{
        Model = 'qwen/qwen3.7-plus'
        Provider = 'alibaba'
        Slug = 'qwen37_plus_hosted_bounded'
        PrimaryTokens = 1024
        RetryTokens = 2048
        ReasoningMaxTokens = 2048
        ReasoningEffort = ''
        StructuredScoreOutput = $true
    }
    glm = @{
        Model = 'z-ai/glm-5.2'
        Provider = 'deepinfra'
        Slug = 'glm52_bounded'
        PrimaryTokens = 1024
        RetryTokens = 2048
        ReasoningMaxTokens = 0
        ReasoningEffort = 'high'
        StructuredScoreOutput = $true
    }
    kimi = @{
        Model = 'moonshotai/kimi-k2.7-code'
        Provider = 'together'
        Slug = 'kimi_k27_code_together_bounded'
        PrimaryTokens = 1024
        RetryTokens = 2048
        ReasoningMaxTokens = 2048
        ReasoningEffort = ''
        StructuredScoreOutput = $true
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
$StructuredScoreOutput = [bool]$Selected.StructuredScoreOutput
$Seed = 1496017540
$RunId = "ccc_openrouter_v1_$($Slug)_$Seed"
$OutputPrefix = "ccc_openrouter_v1_$Slug"
$EvidenceDir = Join-Path $PSScriptRoot 'results\ccc_openrouter_v1'
$Runner = Join-Path $PSScriptRoot 'run_ccc_frontier.py'
$LogStamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$ConsoleLog = Join-Path $EvidenceDir "$($OutputPrefix)_$($Mode.ToLowerInvariant())_console_$LogStamp.log"
$TempConsoleLog = Join-Path ([IO.Path]::GetTempPath()) "ccc_openrouter_$PID`_$LogStamp.log"
$PersistConsole = $Mode -in @('Run', 'Resume', 'Analyse')

$ApiModes = @('CheckModels', 'Run', 'Resume')
$UsesApi = $Mode -in $ApiModes
if ($UsesApi -and -not $ApproveApiCalls) {
    throw 'No API call made. Re-run with -ApproveApiCalls only after reviewing the judge, provider, budgets, evidence path, and cost.'
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
    '--models', $Model,
    '--domains', 'arith,code,sql',
    '--protocols', 'score_only',
    '--study', 'openrouter_ecosystem_v1',
    '--run-id', $RunId,
    '--evidence-dir', $EvidenceDir,
    '--output-prefix', $OutputPrefix,
    '--seed', "$Seed",
    '--provider', $Provider,
    '--score-max-tokens', "$PrimaryTokens",
    '--score-retry-tokens', "$RetryTokens",
    '--balance-gap', '0.05',
    '--workers', "$Workers",
    '--progress-secs', "$ProgressSecs"
)
if ($ReasoningMaxTokens -gt 0) {
    $RunnerArgs += @('--reasoning-max-tokens', "$ReasoningMaxTokens")
}
if ($ReasoningEffort) {
    $RunnerArgs += @('--reasoning-effort', $ReasoningEffort)
}
if ($StructuredScoreOutput) {
    $RunnerArgs += '--structured-score-output'
}

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

Write-Host "CCC OpenRouter mode : $Mode"
Write-Host "Judge               : $Judge"
Write-Host "Model               : $Model"
Write-Host "Provider            : $Provider (fallbacks disabled)"
Write-Host "Token budgets       : $PrimaryTokens / $RetryTokens"
Write-Host "Reasoning control   : $(if ($ReasoningMaxTokens -gt 0) { "max $ReasoningMaxTokens" } elseif ($ReasoningEffort) { "effort $ReasoningEffort" } else { 'provider default' })"
Write-Host "Structured output   : $StructuredScoreOutput"
Write-Host "Python              : $PythonVersion ($Python)"
Write-Host "Seed / run ID       : $Seed / $RunId"
Write-Host "Evidence            : $EvidenceDir"
Write-Host "Planned scored cells: 1,344 (384 arithmetic, 384 code, 576 SQL)"
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
    throw "CCC runner exited with code $ExitCode.$LogHint"
}

if ($PersistConsole) {
    New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null
    Move-Item -LiteralPath $TempConsoleLog -Destination $ConsoleLog
    Write-Host "Completed successfully. Console record: $ConsoleLog"
} else {
    Write-Host 'Completed successfully.'
}
