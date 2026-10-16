$ErrorActionPreference = 'Stop'
throw 'Force-stop helper disabled: use tray Restart Bridge at an idle boundary; active turns must never be killed by process-tree cleanup.'
$recordPath = Join-Path $PSScriptRoot '.runtime\process.json'
if (!(Test-Path -LiteralPath $recordPath)) { Write-Host 'No bridge process record.'; return }
$record = Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
$expectedScript = Join-Path $PSScriptRoot 'bridge.py'
if ($record.script -ne $expectedScript) { throw 'Process record does not match this bridge.' }
$bridgeProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$($record.pid)"
if (!$bridgeProcess) { Remove-Item -LiteralPath $recordPath; Write-Host 'Bridge already stopped.'; return }
$created = ([DateTimeOffset]$bridgeProcess.CreationDate).ToUnixTimeSeconds()
if ($bridgeProcess.Name -notmatch '^python(3|313)?\.exe$' -or !$bridgeProcess.CommandLine.Contains($expectedScript) -or [Math]::Abs($created - $record.started_at) -gt 5) {
    throw 'PID identity mismatch; refusing to stop an unrelated process.'
}
# Snapshot descendants rooted in this verified bridge PID, never kill by executable name.
$all = @(Get-CimInstance Win32_Process)
$owned = @($bridgeProcess)
$frontier = @([uint32]$record.pid)
while ($frontier.Count -gt 0) {
    $next = @($all | Where-Object { $frontier -contains $_.ParentProcessId -and $_.CreationDate -ge $bridgeProcess.CreationDate })
    $owned += $next
    $frontier = @($next | ForEach-Object { $_.ProcessId })
}
[array]::Reverse($owned)
foreach ($entry in $owned) {
    $current = Get-CimInstance Win32_Process -Filter "ProcessId=$($entry.ProcessId)"
    if ($current -and $current.CreationDate -eq $entry.CreationDate -and $current.ParentProcessId -eq $entry.ParentProcessId) {
        Stop-Process -Id $entry.ProcessId -Force -ErrorAction SilentlyContinue
    }
}
Remove-Item -LiteralPath $recordPath -ErrorAction SilentlyContinue
Write-Host 'Stopped only this bridge and its verified descendants.'
