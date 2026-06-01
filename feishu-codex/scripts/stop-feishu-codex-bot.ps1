#Requires -Version 5.1
<#
.SYNOPSIS
    Stop the Feishu Codex bot process.
#>

$ErrorActionPreference = "SilentlyContinue"

$procs = Get-CimInstance Win32_Process | Where-Object {
    ([string]$_.CommandLine).Contains("feishu_codex_bot.py")
}

if (-not $procs) {
    Write-Host "No running Feishu Codex bot found."
    exit 0
}

foreach ($proc in $procs) {
    Write-Host "Stopping bot (PID: $($proc.ProcessId))..."
    Stop-Process -Id $proc.ProcessId -Force
    Write-Host "Stopped."
}
