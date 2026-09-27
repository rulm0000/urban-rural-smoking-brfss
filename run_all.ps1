<#
.SYNOPSIS
    Runs the full analysis, from the raw CDC BRFSS files to every table and figure.

.DESCRIPTION
    Steps (see README.md for what each produces):
      1  Python  download and verify the BRFSS 2018-2025 files (skipped if already present)
      2  Python  build the pooled analytic file
      3  Python  descriptive tables (Table 1, S2 Table, S3 Table)
      4  SAS     import the analytic file
      5  SAS     state and nationwide survey logistic models (Models 1, 2, 3a, 3b)
      6  SAS     nationwide GEE models
      7  SAS     year-specification sensitivity analysis
      8  SAS     state quadratic-trend sensitivity analysis
      9  Python  model tables (Table 2, S1 Table, S4 Table)
      10 Python  Fig 1
      11 Python  S1 Fig
      12 Stata   Fig 2
      13 Python  Fig 2 TIFF

.PARAMETER RawDir
    Folder holding (or to receive) LLCP2018.XPT ... LLCP2025.XPT. Default: data\raw.

.PARAMETER UseArchivedData
    Skip the CDC download and unpack the analytic file kept in data\brfss_2018_2025_analytic.csv.xz.
    Gives the same results without the 8 GB of raw files.

.PARAMETER From
    First step to run (for resuming). Default: 1.

.PARAMETER To
    Last step to run. Default: 13.

.EXAMPLE
    .\run_all.ps1
.EXAMPLE
    .\run_all.ps1 -RawDir "D:\BRFSS"
.EXAMPLE
    .\run_all.ps1 -UseArchivedData
.EXAMPLE
    .\run_all.ps1 -From 9
#>
param(
    [string]$RawDir   = "",
    [switch]$UseArchivedData,
    [int]$From        = 1,
    [int]$To          = 13,
    [string]$Python   = "python",
    [string]$SasExe   = "",
    [string]$StataExe = ""
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location -LiteralPath $Root
$Code = Join-Path $Root "code"
$Logs = Join-Path $Root "output\logs"
foreach ($d in @("data\raw", "data\derived", "output\models", "output\tables", "output\figures", "output\logs")) {
    New-Item -ItemType Directory -Force -Path (Join-Path $Root $d) | Out-Null
}

if ($RawDir -ne "") { $env:BRFSS_RAW_DIR = (Resolve-Path -LiteralPath $RawDir).Path }

# ---- locate SAS and Stata (override with -SasExe / -StataExe) ----------------------------
if ($SasExe -eq "") {
    $SasExe = @("C:\Program Files\SASHome\SASFoundation\9.4\sas.exe",
                "C:\Program Files\SAS\SASFoundation\9.4\sas.exe") |
              Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if ($StataExe -eq "") {
    $StataExe = Get-ChildItem -Path "C:\Program Files\Stata*\Stata*-64.exe" -ErrorAction SilentlyContinue |
                Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
}

function Say($msg) { Write-Host ("[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $msg) -ForegroundColor Cyan }

function Run-Python($script, $extra = @()) {
    $log = Join-Path $Logs ($script -replace '\.py$', '.log')
    $ErrorActionPreference = "Continue"      # Python writes progress to stderr; that is not an error
    & $Python (Join-Path $Code $script) @extra 2>&1 |
        ForEach-Object { if ($_ -is [System.Management.Automation.ErrorRecord]) { $_.Exception.Message } else { $_ } } |
        Tee-Object -FilePath $log
    if ($LASTEXITCODE -ne 0) { throw "$script failed (see $log)" }
}

function Run-Sas($script) {
    if (-not $SasExe) { throw "SAS not found. Pass -SasExe <path to sas.exe>." }
    $log = Join-Path $Logs ($script -replace '\.sas$', '.log')
    $lst = Join-Path $Logs ($script -replace '\.sas$', '.lst')
    $sasArgs = @("-sysin", "`"$(Join-Path $Code $script)`"", "-log", "`"$log`"", "-print", "`"$lst`"",
              "-nosplash", "-noicon", "-batch")
    $p = Start-Process -FilePath $SasExe -ArgumentList $sasArgs -WorkingDirectory $Root -Wait -PassThru -WindowStyle Hidden
    if ($p.ExitCode -gt 1) { throw "$script ended with errors (exit code $($p.ExitCode)); see $log" }
}

function Run-Stata($script) {
    if (-not $StataExe) { throw "Stata not found. Pass -StataExe <path to Stata*-64.exe>." }
    $p = Start-Process -FilePath $StataExe -ArgumentList @("/e", "do", "`"$(Join-Path $Code $script)`"") `
                       -WorkingDirectory $Root -Wait -PassThru -WindowStyle Hidden
    $slog = Join-Path $Root ($script -replace '\.do$', '.log')
    $log = Join-Path $Logs ($script -replace '\.do$', '.log')
    if (Test-Path -LiteralPath $slog) { Move-Item -LiteralPath $slog -Destination $log -Force }
    if (-not (Test-Path -LiteralPath $log) -or (Select-String -LiteralPath $log -Pattern '^r\(\d+\);' -Quiet)) {
        throw "$script ended with errors; see $log"
    }
}

$steps = @(
    @(1,  "Download and verify BRFSS files",     { if ($UseArchivedData) { Write-Host "  skipped (-UseArchivedData)" } else { Run-Python "01_download_brfss.py" } }),
    @(2,  "Build analytic file",                 { if ($UseArchivedData) { Run-Python "02_build_analytic_file.py" @("--from-archive") } else { Run-Python "02_build_analytic_file.py" } }),
    @(3,  "Descriptive tables",                  { Run-Python "03_descriptives.py" }),
    @(4,  "SAS: import analytic file",           { Run-Sas "04_import_analytic_file.sas" }),
    @(5,  "SAS: state and nationwide models",    { Run-Sas "05_state_models.sas" }),
    @(6,  "SAS: nationwide GEE models",          { Run-Sas "06_nationwide_gee.sas" }),
    @(7,  "SAS: year-specification sensitivity", { Run-Sas "07_year_specification.sas" }),
    @(8,  "SAS: state quadratic sensitivity",    { Run-Sas "08_state_quadratic.sas" }),
    @(9,  "Model tables",                        { Run-Python "09_model_tables.py" }),
    @(10, "Fig 1",                               { Run-Python "10_fig1_tilegrid.py" }),
    @(11, "S1 Fig",                              { Run-Python "11_s1_fig_map.py" }),
    @(12, "Stata: Fig 2",                        { Run-Stata "12_fig2_panels.do" }),
    @(13, "Fig 2 TIFF",                          { Run-Python "13_fig2_tiff.py" })
)

$t0 = Get-Date
foreach ($step in $steps) {
    $k, $label, $action = $step
    if ($k -lt $From -or $k -gt $To) { continue }
    Say "Step $k/13: $label"
    $s = Get-Date
    & $action
    Say ("  done in {0:n1} min" -f ((Get-Date) - $s).TotalMinutes)
}
Say ("Finished in {0:n1} min. Tables: output\tables  Figures: output\figures  Logs: output\logs" -f ((Get-Date) - $t0).TotalMinutes)
