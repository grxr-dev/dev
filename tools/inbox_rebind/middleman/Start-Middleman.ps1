# Windows PowerShell 5.1 compatible. Uses the installed Muse lifecycle; no task submission.
[CmdletBinding()]
param(
    [switch]$StatusOnly,
    [string]$BridgeRoot = (Join-Path $env:USERPROFILE 'Documents\Codex\Muse\bridge')
)
$ErrorActionPreference = 'Stop'
$script:rows = [ordered]@{}
$script:notes = New-Object 'System.Collections.Generic.List[string]'
$script:log = $null
$script:blocked = $false
$script:degraded = $false
$mutex = $null
$held = $false

function Row([string]$Name, [string]$State, [string]$Detail) {
    $script:rows[$Name] = ('{0,-23} {1} - {2}' -f $Name,$State,$Detail)
}
function Note([string]$Value) { $script:notes.Add(('{0:HH:mm:ss} {1}' -f (Get-Date),$Value)) }
function Block([string]$Value) { $script:blocked=$true; Note $Value }
function Quote-Arg([string]$Value) {
    '"' + [regex]::Replace([regex]::Replace($Value,'(\\*)"','$1$1\"'),'(\\+)$','$1$1') + '"'
}
function Probe([string]$Exe, [string[]]$Arguments, [int]$Seconds=12, [string]$InputText='') {
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName=$Exe
    $info.Arguments=($Arguments | ForEach-Object { Quote-Arg $_ }) -join ' '
    $info.UseShellExecute=$false; $info.CreateNoWindow=$true
    $info.RedirectStandardOutput=$true; $info.RedirectStandardError=$true; $info.RedirectStandardInput=$true
    # Match the bridge's credential-store-only gh behavior; never print stderr or raw responses.
    if ([IO.Path]::GetFileName($Exe) -eq 'gh.exe') {
        foreach($key in @('GH_DEBUG','GH_HOST','GH_TOKEN','GITHUB_TOKEN','GH_ENTERPRISE_TOKEN','GITHUB_ENTERPRISE_TOKEN')) {
            $info.EnvironmentVariables.Remove($key)
        }
        $info.EnvironmentVariables['GH_PROMPT_DISABLED']='1'
    }
    $p=New-Object System.Diagnostics.Process
    $p.StartInfo=$info
    try {
        [void]$p.Start()
        $stdout=$p.StandardOutput.ReadToEndAsync(); $stderr=$p.StandardError.ReadToEndAsync()
        if ($InputText) { $p.StandardInput.Write($InputText) }
        $p.StandardInput.Close()
        if (-not $p.WaitForExit($Seconds*1000)) {
            # Only this disposable diagnostic child, never a relay/App Server process.
            $p.Kill(); [void]$p.WaitForExit(2000)
            return [pscustomobject]@{Code=124;Text=''}
        }
        [pscustomobject]@{Code=$p.ExitCode;Text=$stdout.GetAwaiter().GetResult()}
    } catch { [pscustomobject]@{Code=125;Text=''} }
    finally { $p.Dispose() }
}
function Read-Local([string]$Url) {
    $req=[Net.HttpWebRequest]::Create($Url)
    $req.Proxy=$null; $req.Timeout=2000; $req.ReadWriteTimeout=2000
    $response=$null; $reader=$null
    try {
        $response=$req.GetResponse()
        $reader=New-Object IO.StreamReader($response.GetResponseStream())
        $reader.ReadToEnd() | ConvertFrom-Json
    } catch { return $null }
    finally { if($reader){$reader.Dispose()}; if($response){$response.Dispose()} }
}
function Owners {
    @(Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and ($_.CommandLine.IndexOf((Join-Path $BridgeRoot 'Tray-Controller.ps1'),[StringComparison]::OrdinalIgnoreCase) -ge 0 -or
        $_.CommandLine.IndexOf((Join-Path $BridgeRoot 'bridge.py'),[StringComparison]::OrdinalIgnoreCase) -ge 0)
    } | Where-Object { $_.Name -match '^(powershell|pwsh|python|pythonw)\.exe$' })
}
function Listeners {
    @(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -in 8766,8767,18741 })
}
function Identity($Health) {
    if (-not $Health -or -not $Health.bridge_healthy -or $Health.workspace -ne $script:workspace) { return $false }
    $bridgeProcess=Get-CimInstance Win32_Process -Filter ('ProcessId={0}' -f [int]$Health.bridge_pid)
    if (-not $bridgeProcess -or $bridgeProcess.Name -notmatch '^python(w)?\.exe$' -or
        $bridgeProcess.CommandLine.IndexOf((Join-Path $BridgeRoot 'bridge.py'),[StringComparison]::OrdinalIgnoreCase) -lt 0) { return $false }
    $listener=@(Listeners | Where-Object { $_.LocalPort -eq 8766 })
    if ($listener.Count -ne 1 -or $listener[0].OwningProcess -ne $Health.bridge_pid -or $listener[0].LocalAddress -ne '127.0.0.1') { return $false }
    $parent=Get-CimInstance Win32_Process -Filter ('ProcessId={0}' -f $bridgeProcess.ParentProcessId)
    if (-not $parent -or $parent.Name -ne 'powershell.exe' -or
        $parent.CommandLine.IndexOf((Join-Path $BridgeRoot 'Tray-Controller.ps1'),[StringComparison]::OrdinalIgnoreCase) -lt 0) { return $false }
    $script:trayPid=$parent.ProcessId
    return $true
}

# Read-only SQLite inspection avoids importing/initializing the bridge or its stores.
# Only hashes, counts and fixed reason codes leave this diagnostic process.
$stateProbe=@'
import hashlib, json, pathlib, sqlite3, sys
root=pathlib.Path(sys.argv[1]); runtime=root/'.runtime'
try:
    db=sqlite3.connect((runtime/'completions.sqlite3').as_uri()+'?mode=ro',uri=True,timeout=3)
    db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
    tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    hashes={}
    for name in tables:
        rows=[]
        sql='SELECT source_ref,code FROM relay_v2_errors' if name=='relay_v2_errors' else 'SELECT * FROM "'+name.replace('"','""')+'"'
        for row in db.execute(sql):
            rows.append(json.dumps([{'bytes':v.hex()} if isinstance(v,bytes) else v for v in row],ensure_ascii=True,separators=(',',':')))
        hashes[name]=hashlib.sha256('\n'.join(sorted(rows)).encode()).hexdigest()
    reasons=[]
    if db.execute('SELECT count(*) FROM pending').fetchone()[0]: reasons.append('pending_turn_requires_review')
    if db.execute("SELECT count(*) FROM requests WHERE state='DISPATCHING' OR (state IN ('APP_SERVER_LOST','TRANSPORT_LOST') AND reconciliation IS NULL)").fetchone()[0]: reasons.append('startup_reconciliation_requires_review')
    if db.execute("SELECT count(*) FROM github_outbox WHERE state!='CLOSED'").fetchone()[0]: reasons.append('unsent_github_results_require_review')
    if db.execute("SELECT count(*) FROM github_inbox WHERE state='QUEUED'").fetchone()[0]: reasons.append('queued_github_work_requires_review')
    qpath=runtime/'inbox_queue.json'; qbytes=qpath.read_bytes(); q=json.loads(qbytes.decode('utf-8-sig'))
    counts={}
    for e in q['entries'].values(): counts[e['state']]=counts.get(e['state'],0)+1
    if counts.get('DELIVERING',0): reasons.append('unresolved_inbox_delivery_requires_review')
    if (q.get('recovery_once') or {}).get('status') in ('PREPARED','ARMED','CLAIMED'): reasons.append('armed_inbox_recovery_requires_review')
    hashes['inbox_queue.json']=hashlib.sha256(qbytes).hexdigest()
    for p in sorted(runtime.glob('thread*.json')): hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    for name in ('relay-v2.json','inbox-v1.json','inbox_native_recovery.json'):
        p=runtime/name
        if p.exists(): hashes[name]=hashlib.sha256(p.read_bytes()).hexdigest()
    remote='not_checked'
    if sys.argv[2]=='guard':
        sys.path.insert(0,str(root))
        from github_bus import GHClient,parse_issue
        config=json.loads((runtime/'relay-v2.json').read_text(encoding='utf-8-sig'))
        if config['browser']['enabled']: reasons.append('historical_browser_binding_enabled_requires_review')
        if config['github']['enabled']:
            client=GHClient(config['github']['repo'])
            try:
                client.private()
                actor=client.call('user')['login']
                issues=client.pages('issues?state=open&sort=created&direction=asc')
                remote='checked'
            except Exception:
                issues=[]; actor=None; remote='not_verified_network_or_login'
            if actor and actor!=config['github']['expected_author']: reasons.append('github_actor_requires_review')
            for issue in issues:
                if not str(issue.get('title','')).startswith('[CODEX RELAY]'): continue
                try:
                    req=parse_issue(issue,config['github']['expected_author'],{'sol-high','sol-medium','sol-light','astra-medium','astra-medium-new'})
                except ValueError as exc:
                    old_error=db.execute('SELECT code FROM relay_v2_errors WHERE source_ref=?',(config['github']['repo']+'#'+str(issue['number']),)).fetchone()
                    if old_error!=(str(exc),): reasons.append('new_invalid_github_envelope_requires_review')
                    continue
                old=db.execute('SELECT prompt_sha256,route_id,source_ref FROM requests WHERE request_id=?',(req['request_id'],)).fetchone()
                expected=(hashlib.sha256(req['message'].encode()).hexdigest(),req['route_id'],config['github']['repo']+'#'+str(issue['number']))
                if old!=expected: reasons.append('unreviewed_or_changed_github_work')
    fingerprint=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
    print(json.dumps({'ok':True,'reasons':sorted(set(reasons)),'fingerprint':fingerprint,'hashes':hashes,'inbox_counts':counts,'github_preflight':remote}))
    db.close()
except Exception:
    print(json.dumps({'ok':False,'reasons':['read_only_preflight_unavailable']}))
    sys.exit(1)
'@
function State([string]$Mode='snapshot') {
    $p=Probe $script:python @('-B','-',$BridgeRoot,$Mode) 50 $stateProbe
    if($p.Code -ne 0){ return $null }
    try { $p.Text | ConvertFrom-Json } catch { return $null }
}

try {
    $BridgeRoot=[IO.Path]::GetFullPath($BridgeRoot).TrimEnd('\')
    $script:workspace=Split-Path -Parent $BridgeRoot
    if(-not $StatusOnly) {
        $logDir=Join-Path $PSScriptRoot 'logs'
        [void](New-Item -ItemType Directory -Path $logDir -Force)
        $script:log=Join-Path $logDir ('Middleman-{0:yyyyMMdd-HHmmss-fff}Z-{1}.log' -f [DateTime]::UtcNow,$PID)
        # Retain only launcher-owned logs, never relay files.
        @(Get-ChildItem -LiteralPath $logDir -Filter 'Middleman-*.log' -File | Sort-Object LastWriteTimeUtc -Descending | Select-Object -Skip 19) |
            ForEach-Object { Remove-Item -LiteralPath $_.FullName }
        $mutex=New-Object Threading.Mutex($false,'Local\MiddlemanStartup_8766')
        try { $held=$mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $held=$true }
        if(-not $held){ throw 'Another Middleman startup is in progress; check again shortly.' }
    }
    foreach($name in @('workspace.json','Tray-Controller.ps1','TrayController.cs','bridge.py','relay_v2.py','github_bus.py')) {
        if(-not (Test-Path -LiteralPath (Join-Path $BridgeRoot $name) -PathType Leaf)){ throw "Required installation file missing: $name" }
    }
    $configPath=Join-Path $BridgeRoot 'workspace.json'
    $rawConfig=[IO.File]::ReadAllText($configPath)
    $config=$rawConfig | ConvertFrom-Json
    if($config.workspace -ne $workspace){throw 'Fixed workspace differs from the installation folder; review relocation manually.'}
    $script:python=(Get-Command python.exe -ErrorAction Stop).Source
    $codex=[string]$config.codex_executable
    $health=Read-Local 'http://127.0.0.1:8766/health'
    $known=@(Owners)
    $ports=@(Listeners)
    $owned=Identity $health
    $before=$null
    if(-not $owned -and -not $StatusOnly -and -not $known.Count -and -not $ports.Count) {
        Write-Host 'Checking saved state and GitHub read-only before starting the existing tray...'
        $before=State 'guard'
        if(-not $before -or -not $before.ok){throw 'Read-only startup safety check unavailable; saved state left untouched.'}
        if(@($before.reasons).Count){throw ('Startup requires review: '+($before.reasons -join ', '))}
        if($before.github_preflight -ne 'checked'){Note 'GitHub backlog not verified; network/login unavailable. Local startup can continue.'}
    }
    if(-not (Test-Path -LiteralPath $codex -PathType Leaf)) {
        if($StatusOnly -or $known.Count -or $ports.Count){throw 'Configured Codex executable is missing; no live process/configuration was changed.'}
        $candidates=@()
        $bin=Join-Path $env:LOCALAPPDATA 'OpenAI\Codex\bin'
        if(Test-Path -LiteralPath $bin){$candidates+=@(Get-ChildItem -LiteralPath $bin -Filter codex.exe -Recurse -File | Sort-Object LastWriteTime -Descending | ForEach-Object {$_.FullName})}
        $candidate=Join-Path $env:LOCALAPPDATA 'Programs\OpenAI\Codex\bin\codex.exe'
        if(Test-Path -LiteralPath $candidate){$candidates=@($candidate)+$candidates}
        $replacement=$null
        foreach($candidate in $candidates) {
            $v=Probe $candidate @('--version')
            if($v.Code -eq 0 -and $v.Text -match '^codex-cli [0-9]'){$replacement=$candidate;break}
        }
        if(-not $replacement){throw 'Codex executable missing; install/update Codex or correct its existing workspace configuration.'}
        $backup=$configPath+('.before-middleman-{0:yyyyMMdd-HHmmss-fff}.bak' -f (Get-Date))
        Copy-Item -LiteralPath $configPath -Destination $backup
        # Replace just the one JSON string, preserving all other settings and formatting.
        $encoded=ConvertTo-Json -InputObject $replacement -Compress
        $pattern='("codex_executable"\s*:\s*)"(?:\\.|[^"\\])*"'
        if([regex]::Matches($rawConfig,$pattern).Count -ne 1){throw 'Codex configuration key is ambiguous; backup made, original retained.'}
        $changed=[regex]::Replace($rawConfig,$pattern,[Text.RegularExpressions.MatchEvaluator]{param($m) $m.Groups[1].Value+$encoded})
        [IO.File]::WriteAllText($configPath,$changed,(New-Object Text.UTF8Encoding($false)))
        $codex=$replacement
        Note ('Repaired only stale codex_executable; dated backup: '+$backup)
    }
    if(-not $StatusOnly) {
        $version=Probe $codex @('--version')
        if($version.Code -ne 0 -or $version.Text -notmatch '^codex-cli [0-9]'){throw 'Configured Codex failed the bounded --version check.'}
    }
    Row 'Codex executable' 'READY' ([IO.Path]::GetFileName($codex)+' exists'+$(if($StatusOnly){''}else{' and --version passed'}))

    if($health -and -not $owned){throw 'Port 8766 health/process ownership mismatch; existing processes retained for review.'}
    if(-not $owned -and -not $StatusOnly) {
        if($ports.Count -and -not $known.Count){throw 'A required port is owned by another process; no process was stopped.'}
        if($known.Count) {
            Note 'Existing controller/bridge found; waiting for live health without starting another.'
        } else {
            $launcher=Join-Path $workspace 'Start-MuseRelay.ps1'
            if(-not (Test-Path -LiteralPath $launcher)){throw 'Supported Start-MuseRelay.ps1 launcher is missing.'}
            # ShellExecute leaves the supported detached tray outside this console/tool's job.
            # The existing launcher creates its own hidden tray/controller and child ownership job.
            $startInfo=New-Object Diagnostics.ProcessStartInfo
            $startInfo.FileName=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
            $startInfo.Arguments='-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File '+(Quote-Arg $launcher)
            $startInfo.UseShellExecute=$true; $startInfo.WindowStyle='Hidden'; $startInfo.WorkingDirectory=$workspace
            $launchProcess=[Diagnostics.Process]::Start($startInfo)
            $launchProcess.Dispose()
            Note 'Invoked the existing Start-MuseRelay.ps1; no task/message/approval endpoint called.'
        }
        $deadline=[DateTime]::UtcNow.AddSeconds(100)
        do {
            Start-Sleep -Milliseconds 1000
            $health=Read-Local 'http://127.0.0.1:8766/health'
            if($health -and (Identity $health)){$owned=$true;break}
        } while([DateTime]::UtcNow -lt $deadline)
        if(-not $owned){throw 'Existing lifecycle did not produce owned bridge health within 100 seconds; no restart/kill attempted.'}
        if($before) {
            $after=State
            if(-not $after -or $after.fingerprint -ne $before.fingerprint){Block 'Saved relay state changed during lifecycle startup; inspect before sending work.'}
            else {Note ('Queue/history tables, Inbox records and saved thread/config files unchanged; fingerprint '+$after.fingerprint);Note 'Existing worker health/error timestamps may refresh; no message/delivery state changed.'}
        }
    } elseif($owned) { Note ('Reused live tray PID '+$trayPid+' and bridge PID '+$health.bridge_pid+'; no launch.') }

    if(-not $owned) { Block 'Windows bridge is stopped or has unverified ownership.'; Row 'Windows bridge' 'BLOCKED' 'not running; double-click Start Middleman.cmd' }
    else {
        Row 'Windows bridge' 'READY' ('127.0.0.1:8766; PID '+$health.bridge_pid+'; tray PID '+$trayPid)
        $rpc=$null
        if($health.rpc_process_alive -and $health.rpc_process_id){$rpc=Get-CimInstance Win32_Process -Filter ('ProcessId={0}' -f [int]$health.rpc_process_id)}
        if($rpc -and $rpc.ParentProcessId -eq $health.bridge_pid -and $rpc.ExecutablePath -eq $codex -and $rpc.CommandLine -match 'app-server') {
            Row 'Codex App Server' 'READY' ('owned PID '+$rpc.ProcessId+'; '+$health.codex_version)
        } else {Block 'Private App Server process/ownership could not be verified.'; Row 'Codex App Server' 'BLOCKED' 'private process not verified'}
        if($health.relay_ready -and $health.model_catalog_status -eq 'resolved' -and -not $health.human_review_required) {
            Row 'Local relay readiness' 'READY' ('catalog resolved; turn active: '+[bool]$health.turn_active)
        } else {Block 'Local bridge needs Codex login, approval or model/thread review; see tray/monitor.'; Row 'Local relay readiness' 'BLOCKED' 'inspect tray or http://127.0.0.1:8767/monitor'}
        $monitor=Read-Local 'http://127.0.0.1:8767/monitor/status'
        $monitorOwner=@(Listeners | Where-Object {$_.LocalPort -eq 8767 -and $_.OwningProcess -eq $health.bridge_pid})
        if($monitor -and $monitorOwner.Count -eq 1){Row 'Local monitor' 'READY' 'http://127.0.0.1:8767/monitor'}
        else {$script:degraded=$true;Row 'Local monitor' 'DEGRADED' 'optional monitor unavailable'}
        $inbox=Read-Local 'http://127.0.0.1:18741/local/inbox/capabilities'
        # Capability requires a narrow local header. This route never claims a delivery.
        if(-not $inbox) {
            $req=[Net.HttpWebRequest]::Create('http://127.0.0.1:18741/local/inbox/capabilities');$req.Proxy=$null;$req.Timeout=2000;$req.ReadWriteTimeout=2000;$req.Headers.Add('X-Jarvis-Local','1')
            $res=$null;$reader=$null
            try {$res=$req.GetResponse();$reader=New-Object IO.StreamReader($res.GetResponseStream());$inbox=$reader.ReadToEnd() | ConvertFrom-Json} catch {} finally {if($reader){$reader.Dispose()};if($res){$res.Dispose()}}
        }
        if($inbox -and $inbox.pid -eq $health.bridge_pid){Row 'Local Inbox transport' 'READY' 'capabilities checked on 18741; no next/ack request'}
        else {$script:degraded=$true;Row 'Local Inbox transport' 'DEGRADED' 'optional local capability unavailable'}
    }

    $gh=Get-Command gh.exe -ErrorAction SilentlyContinue
    $githubReady=$false
    if($gh) {
        $repo=Probe $gh.Source @('api','--hostname','github.com','--method','GET','repos/grxr-dev/codex-relay')
        $issue=Probe $gh.Source @('api','--hostname','github.com','--method','GET','repos/grxr-dev/codex-relay/issues/45')
        try {
            $r=$repo.Text | ConvertFrom-Json; $i=$issue.Text | ConvertFrom-Json
            $githubReady=$repo.Code -eq 0 -and $issue.Code -eq 0 -and $r.full_name -eq 'grxr-dev/codex-relay' -and $r.private -and $i.number -eq 45
        } catch {}
    }
    if($githubReady){Row 'GitHub continuity' 'READY' 'private repository and issue #45 readable; GET only'}
    else {$script:degraded=$true;Row 'GitHub continuity' 'NOT VERIFIED' 'check network or existing gh auth login in a terminal'}
    Row 'Jarvis remote watcher' 'NOT VERIFIED' 'REMOTE NOT VERIFIED; remote jobs were not started'
    $tailscale=Join-Path $env:ProgramFiles 'Tailscale\tailscale.exe'
    $tsReady=$false
    if(Test-Path -LiteralPath $tailscale) {
        $ts=Probe $tailscale @('status','--json') 8
        try {$t=$ts.Text | ConvertFrom-Json;$tsReady=$ts.Code -eq 0 -and $t.BackendState -eq 'Running' -and $t.Self.Online} catch {}
    }
    if($tsReady){Row 'Tailscale / VM path' 'READY / NOT VERIFIED' 'local daemon online; VM delivery not tested'}
    else {$script:degraded=$true;Row 'Tailscale / VM path' 'DEGRADED' 'check/start configured Tailscale service or sign in; PIA untouched'}
    if(-not $StatusOnly) {
        $noSend=Probe $script:python @((Join-Path $BridgeRoot 'inbox-v1\binding.py'),'request-readiness') 8
        if($noSend.Code -eq 0){Note 'Requested exact-binding no-send readiness only; native host answers after manual extension load. No queue claim/ACK.'}
        else {Note 'No-send probe unavailable; saved/loaded binding remains unverified.'}
    }
    $bindingProbe=Probe $script:python @((Join-Path $BridgeRoot 'inbox-v1\middleman_status.py')) 8
    $bindingStatus=$null
    try {if($bindingProbe.Code -eq 0){$bindingStatus=$bindingProbe.Text | ConvertFrom-Json}} catch {}
    if($bindingStatus -and $bindingStatus.binding.delivery_policy -eq 'HOLD') {
        Row 'Saved Inbox binding' 'CONFIGURED / HOLD' ($bindingStatus.binding.conversation_id+'; generation '+$bindingStatus.binding.generation+'; epoch '+$bindingStatus.binding.epoch)
        Row 'Browser Inbox' $bindingStatus.browser_native ($bindingStatus.loaded_binding+'; '+$bindingStatus.readiness_reason)
        Row 'Current ChatGPT thread' $bindingStatus.browser_native $bindingStatus.url
        Row 'Recovery validator' $bindingStatus.validator ('loaded build: '+$bindingStatus.validator_build+'; HOLD never authorizes recovery')
        Note ('Firefox Load Temporary Add-on: '+$bindingStatus.manifest)
        if($bindingStatus.browser_native -eq 'READY') {
            Note 'Fresh NEW browser/native no-send handshake verified. No browser action currently required; manual temporary load is needed after Firefox restarts.'
        } else {
            Note 'If absent, manually load the manifest and refresh the NEW tab; Start requests a no-send probe, then Check reports the receipt. No message relay needed.'
        }
    } else {
        Block 'Saved recipient configuration failed validation; HOLD retained; no browser or delivery operation attempted.'
        Row 'Saved Inbox binding' 'BLOCKED' 'invalid/unavailable; inspect source/config coherency'
    }
    # Whole-relay status stays DEGRADED until the separate end-to-end handshake.
    $script:degraded=$true
} catch {
    $script:blocked=$true
    # Only our fixed diagnostics are safe for logs; never dump provider errors or task bodies.
    if($_.Exception -is [System.Management.Automation.RuntimeException]) {
        $safe=$_.Exception.Message
        if($_.CategoryInfo.Category -ne 'OperationStopped'){$safe='Startup diagnostic failed ('+$_.Exception.GetType().Name+'); check installation and access in a normal Windows session.'}
    } else {$safe='Startup diagnostic failed ('+$_.Exception.GetType().Name+'); check installation and access in a normal Windows session.'}
    Block $safe
    if(-not $script:rows.Contains('Windows bridge')){Row 'Windows bridge' 'BLOCKED' $safe}
} finally {
    if($held){$mutex.ReleaseMutex()}
    if($mutex){$mutex.Dispose()}
}
foreach($name in @('Codex App Server','Local monitor','GitHub continuity','Jarvis remote watcher','Tailscale / VM path','Browser Inbox','Current ChatGPT thread')) {
    if(-not $script:rows.Contains($name)){Row $name 'NOT VERIFIED' 'preflight did not complete; no action taken'}
}
$status=if($script:blocked){'BLOCKED'}elseif($script:degraded){'DEGRADED'}else{'READY'}
$exitCode=if($script:blocked){2}elseif($script:degraded){1}else{0}
$lines=@(('MIDDLEMAN STARTUP - '+$status), ('Checked: {0:yyyy-MM-dd HH:mm:ss zzz}' -f (Get-Date)), '')+@($script:rows.Values)+@('', 'Local readiness is separate from end-to-end delivery. Production delivery remains HOLD.', '')+@($script:notes)+@('', 'No manual message relay is required. Jarvis coordination uses GitHub issue #45.', 'If validator activation is pending: only after the current Codex turn has ended and the monitor is idle, use tray > Restart Bridge, then Check Middleman again.', '')
if($StatusOnly){$lines+='Read-only status: no launch, repair, log write, queue operation, or message sent.'}
elseif($script:log) {
    try { $lines | Set-Content -LiteralPath $script:log -Encoding UTF8; $lines+=('Log: '+$script:log) }
    catch { $lines+='Log could not be written; use the visible report.'; $exitCode=2 }
}
$lines | ForEach-Object { Write-Host $_ }
exit $exitCode
