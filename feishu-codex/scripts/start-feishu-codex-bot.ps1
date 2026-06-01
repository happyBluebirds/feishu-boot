#Requires -Version 5.1
<#
.SYNOPSIS
    Start the Feishu Codex bot as a background process.

.DESCRIPTION
    Launches the Feishu Codex bot in a detached background process.
    The bot connects to Feishu via WebSocket and dispatches commands to Codex (Claude Code).

.PARAMETER ConfigPath
    Path to the bot configuration JSON file.
    Defaults to: integrations/feishu-codex/config/feishu_codex_bot.json

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File start-feishu-codex-bot.ps1
#>

param(
    [string]$ConfigPath = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$IntegrationRoot = Split-Path -Parent $ScriptDir
$BotScript = Join-Path $IntegrationRoot "app\feishu_codex_bot.py"

if (-not $ConfigPath) {
    $ConfigPath = Join-Path $IntegrationRoot "config\feishu_codex_bot.json"
}

if (-not (Test-Path $BotScript)) {
    Write-Error "Bot script not found: $BotScript"
    exit 1
}

if (-not (Test-Path $ConfigPath)) {
    Write-Error "Config not found: $ConfigPath"
    Write-Host "Create it from: $(Join-Path $IntegrationRoot 'config\feishu_codex_bot.example.json')"
    exit 1
}

# Check if already running
$botScriptForPs = $BotScript.Replace("'", "''")
$existingPid = Get-CimInstance Win32_Process | Where-Object {
    ([string]$_.CommandLine).Contains("feishu_codex_bot.py")
} | Select-Object -First 1 -ExpandProperty ProcessId

if ($existingPid) {
    Write-Host "Bot already running (PID: $existingPid)"
    exit 0
}

Write-Host "Starting Feishu Codex bot..."
Write-Host "  Config: $ConfigPath"
Write-Host "  Script: $BotScript"

# Start in background
$pythonPath = "python"
$process = Start-Process -FilePath $pythonPath -ArgumentList @(
    $BotScript,
    "--config", $ConfigPath
) -WindowStyle Hidden -PassThru

Write-Host "Bot started (PID: $($process.Id))"
Write-Host "Logs: D:\code\codex\outputs\feishu-codex\logs\feishu-codex-bot.log"
