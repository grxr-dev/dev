using System;
using System.Collections.Generic;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows.Forms;
using System.Web.Script.Serialization;

namespace MuseRelay {
// Separate jobs ensure terminating our stack cannot affect unrelated Desktop/tunnels.
public sealed class OwnedChild : IDisposable {
 [StructLayout(LayoutKind.Sequential)] struct Limits { public long a,b; public uint flags; public UIntPtr c,d; public uint e; public UIntPtr f; public uint g; }
 [StructLayout(LayoutKind.Sequential)] struct IO { public ulong a,b,c,d,e,f; }
 [StructLayout(LayoutKind.Sequential)] struct Extended { public Limits basic; public IO io; public UIntPtr a,b,c,d; }
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode)] static extern IntPtr CreateJobObject(IntPtr a,string b);
 [DllImport("kernel32.dll")] static extern bool SetInformationJobObject(IntPtr j,int c,ref Extended e,uint n);
 [DllImport("kernel32.dll")] static extern bool AssignProcessToJobObject(IntPtr j,IntPtr p);
 [DllImport("kernel32.dll")] static extern bool TerminateJobObject(IntPtr j,uint code);
 [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
 public Process Process; IntPtr job;
 public OwnedChild(ProcessStartInfo info, Action<string> log) {
  job=CreateJobObject(IntPtr.Zero,null); var limit=new Extended(); limit.basic.flags=0x2000;
  if(job==IntPtr.Zero || !SetInformationJobObject(job,9,ref limit,(uint)Marshal.SizeOf(limit))) throw new Exception("Cannot establish owned-process job");
  Process=new Process(); Process.StartInfo=info;
  Process.OutputDataReceived+=(s,e)=>{if(e.Data!=null)log(e.Data);};
  Process.ErrorDataReceived+=(s,e)=>{if(e.Data!=null)log(e.Data);};
  try { Process.Start(); if(!AssignProcessToJobObject(job,Process.Handle)) { Process.Kill(); throw new Exception("Cannot assign owned child to job"); }
   Process.BeginOutputReadLine(); Process.BeginErrorReadLine();
  } catch { Dispose(); throw; }
 }
 public static bool ExitConfirmed(Process process,int timeout) { return process.WaitForExit(timeout); }
 public bool Alive { get { try{return Process!=null && !Process.HasExited;}catch{return false;} } }
 public void Dispose() { if(job!=IntPtr.Zero){TerminateJobObject(job,0);CloseHandle(job);job=IntPtr.Zero;} if(Process!=null)Process.Dispose(); }
}
// Pure recovery decisions share the production state machine with deterministic tests.
public sealed class HealthSample {
 public bool Ready,Active,ProcessDead,Recoverable,HumanReview,Known,ApprovalPending;
 public string Reason="local_health_unreachable",Message="Local health unavailable";
}
public sealed class RecoveryGate {
 public int Attempts {get;private set;}
 DateTime? degraded,stable;
 public void Reset(){Attempts=0;degraded=null;stable=null;}
 public void Attempt(){Attempts++;degraded=null;stable=null;}
 public string Decide(HealthSample h,DateTime now,bool startupWaiting){
  if(h.HumanReview)return "Manual";
  if(h.ApprovalPending&&!h.ProcessDead)return "Approval Required";
  if(h.Ready){degraded=null;if(!stable.HasValue)stable=now;if((now-stable.Value).TotalSeconds>=300)Attempts=0;return h.Active?"Working":"Ready";}
  stable=null;
  // A secondary poll is never permission to kill a live/unknown active turn.
  if(h.Active&&!h.ProcessDead)return "Degraded";
  if(h.Known&&!h.Recoverable)return "Manual";
  if(startupWaiting&&!h.Known)return "Starting";
  if(!degraded.HasValue)degraded=now;
  if(!h.ProcessDead&&(now-degraded.Value).TotalSeconds<3)return "Degraded";
  return Attempts>=3?"Exhausted":"Recover";
 }
}
public sealed class Tray : ApplicationContext {
 public const string RelayUrl="https://desktop-eklergf.tail870ad5.ts.net/";
 readonly string root,python;readonly NotifyIcon icon;readonly System.Windows.Forms.Timer timer;
 readonly ConcurrentQueue<Action> pending=new ConcurrentQueue<Action>();readonly Queue<string> logs=new Queue<string>();
 readonly ToolStripMenuItem statusItem,tokenItem,monitorItem,publicItem,approvalItem;readonly Mutex singleton;
 readonly ManualResetEvent stopAck=new ManualResetEvent(false);string acknowledgement;
 readonly RecoveryGate gate=new RecoveryGate();
 Dictionary<string,string> expectedModules;
 OwnedChild bridge;string token,state="Starting",publicStatus="Unchecked",lastFault;bool ready,polling,publicPolling,closing,suspended;
 DateTime startupDeadline,nextStart;bool restartScheduled;string notifiedApproval;int shutdownDeferrals;HealthSample last=new HealthSample();
 internal bool SimulateCatalogFailure;
 public string State {get{return state;}}public int BridgePid {get{return bridge==null?0:bridge.Process.Id;}}
 public int RecoveryAttempts {get{return gate.Attempts;}}public string PublicStatus {get{return publicStatus;}}public bool IconVisible {get{return icon.Visible;}}
 public bool HasToken {get{return token!=null&&token.Length>=64;}}internal string TokenForTest(){return token;}
 public string LogsForTest(){return String.Join("\n",logs.ToArray());}
 public Tray(string workspace,string py){
  root=workspace;python=py;bool first;singleton=new Mutex(true,"Local\\MuseCodexRelay_8766",out first);if(!first)throw new Exception("Muse Codex Relay is already running");
  using(var rng=RandomNumberGenerator.Create()){byte[] bytes=new byte[48];rng.GetBytes(bytes);token=Convert.ToBase64String(bytes).TrimEnd('=').Replace('+','-').Replace('/','_');}
  var menu=new ContextMenuStrip();statusItem=new ToolStripMenuItem("Status: Starting"){Enabled=false};menu.Items.Add(statusItem);
  menu.Items.Add(new ToolStripMenuItem("Public Relay: "+RelayUrl){Enabled=false});
  Add(menu,"Copy Relay URL",()=>Clipboard.SetText(RelayUrl));Add(menu,"Check Public Relay",CheckPublicRelay);
  publicItem=new ToolStripMenuItem("Public ingress: Unchecked"){Enabled=false};menu.Items.Add(publicItem);
  menu.Items.Add(new ToolStripSeparator());monitorItem=Add(menu,"Open Live Monitor",()=>Open("http://127.0.0.1:8767/monitor"));
  approvalItem=Add(menu,"Review Approval",()=>Open("http://127.0.0.1:8767/monitor"));approvalItem.Enabled=false;
  Add(menu,"Open Muse Workspace",()=>Open(root));tokenItem=Add(menu,"Copy Bearer Token",()=>Clipboard.SetText(token));
  Add(menu,"Restart Bridge",RestartBridge);Add(menu,"Open Logs",ShowLogs);Add(menu,"Stop Bridge & Exit",Stop);
  icon=new NotifyIcon(){Icon=SystemIcons.Application,Text="Muse Codex Relay: Starting",ContextMenuStrip=menu,Visible=true};
  icon.BalloonTipClicked+=(s,e)=>{if(last.ApprovalPending)Open("http://127.0.0.1:8767/monitor");};
  icon.DoubleClick+=(s,e)=>{if(ready)Open("http://127.0.0.1:8767/monitor");};
  timer=new System.Windows.Forms.Timer(){Interval=1000};timer.Tick+=(s,e)=>Tick();timer.Start();pending.Enqueue(()=>StartBridge(false));Update("Starting");
 }
 ToolStripMenuItem Add(ContextMenuStrip menu,string text,Action action){var item=new ToolStripMenuItem(text);item.Click+=(s,e)=>{try{action();}catch(Exception ex){Fail(ex.Message);}};menu.Items.Add(item);return item;}
 void Open(string target){Process.Start(new ProcessStartInfo(target){UseShellExecute=true});}
 void Update(string value){state=value;statusItem.Text="Status: "+value;icon.Text="Muse Codex Relay: "+value;tokenItem.Enabled=HasToken;monitorItem.Enabled=bridge!=null&&bridge.Alive;approvalItem.Enabled=last.ApprovalPending&&monitorItem.Enabled;
  try{var directory=Path.Combine(root,"bridge",".runtime");Directory.CreateDirectory(directory);
   File.WriteAllText(Path.Combine(directory,"tray.json"),new JavaScriptSerializer().Serialize(new {pid=Process.GetCurrentProcess().Id,status=state,relay_url=RelayUrl,public_ingress=publicStatus,bridge_pid=BridgePid,recovery_attempts=gate.Attempts,last_fault=lastFault,monitor_url="http://127.0.0.1:8767/monitor"}));}catch{}
 }
 void Log(string line){if(token!=null)line=line.Replace(token,"[redacted]");line=Regex.Replace(line,@"(?i)Bearer\s+\S+","Bearer [redacted]");logs.Enqueue(DateTime.Now.ToString("HH:mm:ss ")+line);while(logs.Count>300)logs.Dequeue();}
 void Fail(string reason){if(closing)return;suspended=true;lastFault=reason;Log(reason);Update("Failed");icon.ShowBalloonTip(6000,"Muse Codex Relay",reason,ToolTipIcon.Error);}
 ProcessStartInfo Info(){return new ProcessStartInfo(python,"-B -u \""+Path.Combine(root,"bridge","bridge.py")+"\" --port 8766 --monitor-port 8767 --managed"){WorkingDirectory=root,UseShellExecute=false,CreateNoWindow=true,WindowStyle=ProcessWindowStyle.Hidden,RedirectStandardInput=true,RedirectStandardOutput=true,RedirectStandardError=true};}
 void StartBridge(bool recovery){
  try{if(String.IsNullOrEmpty(python)||!File.Exists(python))throw new Exception("Python installation not found");
   expectedModules=new Dictionary<string,string>();
   foreach(string name in new[]{"bridge.py","reliability.py","relay_v2.py","relay_state.py","github_bus.py","completions.py","inbox_local.py","inbox_queue.py","inbox_supersession.py"}){
    using(var hash=SHA256.Create())expectedModules[name]=BitConverter.ToString(hash.ComputeHash(File.ReadAllBytes(Path.Combine(root,"bridge",name)))).Replace("-","").ToLowerInvariant();
   }
   var info=Info();info.EnvironmentVariables["MUSE_BRIDGE_TOKEN"]=token;
   bridge=new OwnedChild(info,line=>{
    if(line.StartsWith("CONTROL ")){acknowledgement=line.Contains("accepted")?"accepted":"busy";stopAck.Set();}
    else pending.Enqueue(()=>Log("Bridge: "+line));
   });
   ready=false;startupDeadline=DateTime.UtcNow.AddSeconds(90);Update(recovery?"Recovering":"Starting");Log("Started private bridge PID "+BridgePid+"; same in-memory token and workspace");
  }catch(Exception ex){Fail(ex.Message);}
 }
 void Tick(){
  if(closing)return;Action action;while(pending.TryDequeue(out action))action();
  if(suspended)return;
  if(restartScheduled){if(DateTime.UtcNow>=nextStart){restartScheduled=false;StartBridge(true);}return;}
  if(polling)return;polling=true;var expected=bridge;bool childDead=bridge==null||!bridge.Alive;
  ThreadPool.QueueUserWorkItem(unused=>{
   HealthSample sample=new HealthSample(){Active=last.Active,ProcessDead=childDead};string diagnostic=null,task="IDLE",approvalId=null;
   try{
    var health=Read("http://127.0.0.1:8766/health");sample=Parse(health,root);
    if(expected==null||!expected.Alive||Convert.ToInt32(health["bridge_pid"])!=expected.Process.Id){sample.Ready=false;sample.HumanReview=true;sample.Reason="stale_bridge_pid";sample.Message="Listener is not the owned bridge; no automatic kill/restart";}
    object rawCapability;var capability=health.TryGetValue("capabilities",out rawCapability)?rawCapability as Dictionary<string,object>:null;
    object rawModules;var modules=capability!=null&&capability.TryGetValue("loaded_modules",out rawModules)?rawModules as Dictionary<string,object>:null;
    bool activated=modules!=null&&expectedModules!=null&&modules.Count==expectedModules.Count;
    if(activated)foreach(var module in expectedModules){object value;if(!modules.TryGetValue(module.Key,out value)||Convert.ToString(value)!=module.Value){activated=false;break;}}
    if(!activated){sample.Ready=false;sample.HumanReview=true;sample.Reason="build_activation_mismatch";sample.Message="Owned process has not loaded intended module bundle; review idle activation, never kill active work";}
    if(SimulateCatalogFailure){sample.Ready=false;sample.Recoverable=true;sample.Reason="catalog_refresh_failed";sample.Message="Simulated model/list transport failure";}
    if(!sample.Ready){try{diagnostic=new JavaScriptSerializer().Serialize(Read("http://127.0.0.1:8767/monitor/diagnostics"));}catch{}}
    // Monitor availability has no bearing on backend recovery.
    try{var monitor=Read("http://127.0.0.1:8767/monitor/status");task=Convert.ToString(monitor["status"]);
     object raw;if(monitor.TryGetValue("approvals",out raw)&&raw is System.Collections.IEnumerable){foreach(object value in (System.Collections.IEnumerable)raw){var row=value as Dictionary<string,object>;if(row!=null&&Convert.ToString(row["state"])=="pending"){approvalId=Convert.ToString(row["approval_id"]);break;}}}
    }catch{}
   }catch(Exception ex){sample.Message="Local health request failed: "+ex.GetType().Name+": "+ex.Message;}
   pending.Enqueue(()=>{polling=false;if(closing||bridge!=expected||suspended)return;Apply(sample,task,diagnostic,approvalId);});
  });
 }
 public static HealthSample Parse(Dictionary<string,object> health,string workspace){
  var h=new HealthSample(){Known=true,Active=Bool(health,"turn_active"),ProcessDead=health.ContainsKey("rpc_process_alive")&&!Bool(health,"rpc_process_alive"),HumanReview=Bool(health,"human_review_required"),ApprovalPending=Bool(health,"approval_pending")};
  object raw;if(health.TryGetValue("recovery",out raw)&&raw is Dictionary<string,object>){var r=(Dictionary<string,object>)raw;h.Recoverable=Bool(r,"recoverable");h.Reason=Convert.ToString(r["reason"]);h.Message=Convert.ToString(r["message"]);}
  bool identity=String.Equals(Convert.ToString(health["workspace"]),workspace,StringComparison.OrdinalIgnoreCase)&&Convert.ToString(health["default_route"])=="sol-high";
  if(!identity){h.Recoverable=false;h.HumanReview=true;h.Reason="workspace_or_route_mismatch";h.Message="Expected fixed Muse workspace and sol-high default";}
  h.Ready=identity&&Bool(health,"relay_ready")&&Convert.ToString(health["model_catalog_status"])=="resolved";
  return h;
 }
 static bool Bool(Dictionary<string,object> d,string key){object value;return d.TryGetValue(key,out value)&&value is bool&&(bool)value;}
 void Apply(HealthSample sample,string task,string diagnostic,string approvalId){
  last=sample;var decision=gate.Decide(sample,DateTime.UtcNow,!ready&&DateTime.UtcNow<startupDeadline);
  if(decision=="Approval Required"){
   ready=true;Update("Approval Required");
   if(approvalId!=null&&approvalId!=notifiedApproval){notifiedApproval=approvalId;icon.ShowBalloonTip(10000,"Muse Codex Relay — Approval Required","Codex is waiting for Graham. Review the exact operation in the local monitor.",ToolTipIcon.Warning);}
   return;
  }
  if(!sample.ApprovalPending)notifiedApproval=null;
  if(!sample.Ready){string fault=sample.Reason+": "+sample.Message;if(fault!=lastFault){lastFault=fault;Log(fault);if(diagnostic!=null)Log("Local lifecycle diagnostic: "+diagnostic);}}
  if(decision=="Ready"||decision=="Working"){ready=true;Update(task=="BLOCKED"?"Blocked":task=="FAILED"?"Failed":decision);return;}
  if(decision=="Manual"){Fail(sample.Reason+": "+sample.Message+". Manual Restart Bridge after review; no request replay.");return;}
  if(decision=="Exhausted"){Fail("Automatic recovery exhausted after 3 attempts: "+lastFault);return;}
  if(decision=="Recover"){Recover(sample);return;}
  Update(decision);
 }
 void Recover(HealthSample sample){
  Log("Recovery reason: "+sample.Reason+": "+sample.Message);
  if(sample.Active&&sample.ProcessDead)Log("Active turn genuinely lost: private process dead. Request will NOT be replayed.");
  Update("Recovering");
  if(!StopBridge(sample.ProcessDead)){shutdownDeferrals++;Update("Degraded");Log("Recovery deferred: active work or unconfirmed shutdown; keeping owned process intact");if(shutdownDeferrals>=3)Fail("Cannot confirm idle shutdown after 3 checks; automatic recovery stopped, owned process retained for review");return;}
  shutdownDeferrals=0;
  gate.Attempt();int seconds=(int)Math.Pow(2,gate.Attempts);Log("Automatic recovery attempt "+gate.Attempts+"/3; backoff "+seconds+" seconds; no relay replay");
  restartScheduled=true;nextStart=DateTime.UtcNow.AddSeconds(seconds);ready=false;Update("Recovering");
 }
 public static Dictionary<string,object> Read(string uri,int timeout=2000){var req=(HttpWebRequest)WebRequest.Create(uri);req.Proxy=null;req.Timeout=timeout;req.ReadWriteTimeout=timeout;using(var response=req.GetResponse())using(var reader=new StreamReader(response.GetResponseStream()))return new JavaScriptSerializer(){MaxJsonLength=4000000}.Deserialize<Dictionary<string,object>>(reader.ReadToEnd());}
 bool StopBridge(bool force){
  ready=false;if(bridge==null)return true;
  if(bridge.Alive){
   try{acknowledgement=null;stopAck.Reset();bridge.Process.StandardInput.WriteLine(force?"{\"op\":\"shutdown\"}":"{\"op\":\"shutdown\",\"if_idle\":true}");bridge.Process.StandardInput.Flush();
    if(!force){if(!stopAck.WaitOne(2500)||acknowledgement!="accepted")return false;}
    if(!OwnedChild.ExitConfirmed(bridge.Process,5000))return false;
   }catch{if(!force&&bridge.Alive)return false;}
  }
  if(bridge.Alive)return false;
  bridge.Dispose();bridge=null;return true; // Token stays in the controller across every bridge restart.
 }
 public void RestartBridge(){
  if(last.Active&&!last.ProcessDead){Log("Manual restart deferred: live active turn protected");Update("Degraded");icon.ShowBalloonTip(4000,"Muse Codex Relay","Active turn protected. Retry Restart Bridge after it completes.",ToolTipIcon.Info);return;}
  if(!StopBridge(false)){Log("Manual restart deferred: bridge reports busy or cannot confirm idle shutdown");Update("Degraded");return;}
  gate.Reset();shutdownDeferrals=0;suspended=false;restartScheduled=false;lastFault=null;last=new HealthSample();StartBridge(false);
 }
 public void CheckPublicRelay(){
  if(publicPolling)return;publicPolling=true;
  ThreadPool.QueueUserWorkItem(unused=>{bool reachable=false;string detail;
   try{var h=Read(RelayUrl+"health",10000);reachable=Convert.ToString(h["workspace"])==root;detail=reachable?"PUBLIC INGRESS REACHABLE; bridge "+(Bool(h,"relay_ready")?"READY":"NOT READY"):"PUBLIC INGRESS UNREACHABLE: unexpected health identity";}
   catch(Exception ex){detail="PUBLIC INGRESS UNREACHABLE: "+ex.GetType().Name;}
   pending.Enqueue(()=>{publicPolling=false;if(closing)return;ReportPublic(reachable,detail);});
  });
 }
 void ReportPublic(bool reachable,string detail){publicStatus=reachable?"Reachable":"PUBLIC INGRESS UNREACHABLE";publicItem.Text="Public ingress: "+publicStatus;Log(detail);Update(state);icon.ShowBalloonTip(5000,"Muse Codex Relay",detail,reachable?ToolTipIcon.Info:ToolTipIcon.Warning);}
 internal void PublicFailureForTest(){ReportPublic(false,"PUBLIC INGRESS UNREACHABLE: simulated internet failure");}
 void ShowLogs(){string diagnostic="";try{diagnostic=File.ReadAllText(Path.Combine(root,"bridge",".runtime","diagnostics.json"));}catch{}
  var form=new Form(){Text="Muse Codex Relay â€” Logs",Width=900,Height=550,ShowInTaskbar=false,StartPosition=FormStartPosition.CenterScreen};
  form.Controls.Add(new RichTextBox(){ReadOnly=true,Dock=DockStyle.Fill,Text=String.Join(Environment.NewLine,logs.ToArray())+"\n\nBounded local lifecycle metadata:\n"+diagnostic});form.ShowDialog();form.Dispose();
 }
 public void Stop(){if(closing)return;closing=true;timer.Stop();StopBridge(true);icon.Visible=false;icon.Dispose();timer.Dispose();stopAck.Dispose();singleton.ReleaseMutex();singleton.Dispose();token=null;try{File.Delete(Path.Combine(root,"bridge",".runtime","tray.json"));}catch{}ExitThread();}
 protected override void Dispose(bool disposing){if(disposing&&!closing)Stop();base.Dispose(disposing);}
}
public static class Entry {
 public static void Run(string root,string python){Application.EnableVisualStyles();try{using(var tray=new Tray(root,python))Application.Run(tray);}catch(Exception ex){MessageBox.Show(ex.Message,"Muse Codex Relay",MessageBoxButtons.OK,MessageBoxIcon.Error);}}
 static void Assert(bool value,string message){if(!value)throw new Exception(message);}
 public static string PolicyTests(){
  Assert(!OwnedChild.ExitConfirmed(Process.GetCurrentProcess(),1),"live old PID cannot be disposed or replaced");
  var g=new RecoveryGate();var t=DateTime.UtcNow;var healthy=new HealthSample(){Ready=true,Known=true};
  Assert(g.Decide(healthy,t,false)=="Ready","healthy");
  var working=new HealthSample(){Ready=false,Active=true,Recoverable=true,Known=true};Assert(g.Decide(working,t,false)=="Degraded","protect active");Assert(g.Decide(working,t.AddMinutes(20),false)=="Degraded","long active protection");
  var unknown=new HealthSample(){Active=true};Assert(g.Decide(unknown,t.AddMinutes(40),false)=="Degraded","unknown poll never kills work");
  var approval=new HealthSample(){HumanReview=true,ProcessDead=true,Known=true};Assert(g.Decide(approval,t,false)=="Manual","approval cannot recover automatically");
  var pendingApproval=new HealthSample(){ApprovalPending=true,Active=true,Known=true};
  int beforeApproval=g.Attempts;Assert(g.Decide(pendingApproval,t,false)=="Approval Required","live approval waits locally");
  Assert(g.Decide(pendingApproval,t.AddHours(1),false)=="Approval Required"&&g.Attempts==beforeApproval,"approval never spends recovery budget");
  var dead=new HealthSample(){ProcessDead=true,Active=true,Recoverable=true,Known=true};
  Assert(g.Decide(new HealthSample(){ApprovalPending=true,ProcessDead=true,Recoverable=true,Known=true},t,false)=="Recover","real RPC death during approval is recoverable");
  for(int i=0;i<3;i++){Assert(g.Decide(dead,t,false)=="Recover","bounded attempt "+i);g.Attempt();g.Decide(healthy,t.AddSeconds(1),false);}
  Assert(g.Decide(dead,t.AddSeconds(2),false)=="Exhausted","stop after three including short successful restarts");
  Assert(g.Decide(dead,t.AddHours(1),false)=="Exhausted","no infinite loop");
  g.Decide(healthy,t.AddHours(2),false);g.Decide(healthy,t.AddHours(2).AddSeconds(301),false);Assert(g.Attempts==0,"reset only after sustained health");
  var catalog=new HealthSample(){Known=true,Recoverable=true,Reason="catalog_refresh_failed"};Assert(g.Decide(catalog,t,false)=="Degraded","short grace");Assert(g.Decide(catalog,t.AddSeconds(4),false)=="Recover","catalog recover");
  Assert(g.Decide(new HealthSample(){Known=true,Recoverable=false},t,false)=="Manual","policy unavailability blocks");
  return "recovery policy: grace, active-turn protection, approval block, 3-attempt cap, sustained-health reset PASS";
 }
 public static string Test(string root,string python){
  var results=new List<string>();results.Add(PolicyTests());using(var tray=new Tray(root,python)){
   Wait(tray,"Ready",100);Assert(tray.IconVisible&&tray.HasToken,"tray/token");Assert(Hidden(tray.BridgePid),"hidden bridge");
   string token=tray.TokenForTest(),sol=SolId();int bridge=tray.BridgePid;Echo(token);results.Add("startup, stable URL, icon, hidden bridge, authenticated echo PASS");
   tray.RestartBridge();Wait(tray,"Ready",100);Assert(tray.TokenForTest()==token&&SolId()==sol,"manual restart token/thread");Echo(token);results.Add("manual bridge restart preserves token and Sol thread PASS");
   var health=Tray.Read("http://127.0.0.1:8766/health");int app=Convert.ToInt32(health["rpc_process_id"]);Assert(app>0,"owned app-server ID");Process.GetProcessById(app).Kill();
   WaitNewReady(tray,tray.BridgePid,100);Assert(tray.TokenForTest()==token&&SolId()==sol,"automatic restart token/thread");Echo(token);Assert(tray.LogsForTest().Contains("rpc_transport_unavailable"),"precise death reason");results.Add("real App Server death, recovery, token/thread preservation, diagnostic reason PASS");
   bridge=tray.BridgePid;tray.SimulateCatalogFailure=true;Wait(tray,"Recovering",20);tray.SimulateCatalogFailure=false;WaitNewReady(tray,bridge,100);
   Assert(tray.LogsForTest().Contains("Simulated model/list transport failure"),"catalog diagnostic reason");Assert(tray.TokenForTest()==token&&SolId()==sol,"catalog restart identity");results.Add("simulated catalog failure triggers recovery with exact reason PASS");
   int before=tray.BridgePid,attempts=tray.RecoveryAttempts;tray.PublicFailureForTest();Pump(3000);Assert(tray.BridgePid==before&&tray.RecoveryAttempts==attempts,"public outage must not restart bridge");results.Add("public ingress failure separate from recovery PASS");
   tray.SimulateCatalogFailure=true;Wait(tray,"Failed",50);Assert(tray.RecoveryAttempts==3,"native retry limit");int failedPid=tray.BridgePid;Pump(4000);Assert(tray.BridgePid==failedPid&&tray.RecoveryAttempts==3,"native recovery stopped");
   tray.SimulateCatalogFailure=false;tray.RestartBridge();Wait(tray,"Ready",100);Assert(tray.TokenForTest()==token&&SolId()==sol,"bounded recovery preserves token/thread");Echo(token);results.Add("native 3-restart limit, no infinite loop, manual recovery PASS");
   tray.CheckPublicRelay();Pump(12000);Assert(tray.PublicStatus=="Reachable","real public /health check");results.Add("real public health action (no inference) PASS");
   int b=tray.BridgePid;int a=Convert.ToInt32(Tray.Read("http://127.0.0.1:8766/health")["rpc_process_id"]);tray.Stop();Thread.Sleep(1000);Assert(!Alive(b)&&!Alive(a),"owned shutdown");results.Add("owned bridge/App Server shutdown PASS");
  }return String.Join("\n",results.ToArray());
 }
 static void Echo(string token){var req=(HttpWebRequest)WebRequest.Create("http://127.0.0.1:8766/echo");req.Proxy=null;req.Method="POST";req.ContentType="application/json";req.Headers["Authorization"]="Bearer "+token;var bytes=System.Text.Encoding.UTF8.GetBytes("{\"message\":\"no-inference supervisor test\"}");req.ContentLength=bytes.Length;using(var stream=req.GetRequestStream())stream.Write(bytes,0,bytes.Length);using(var response=req.GetResponse())using(var reader=new StreamReader(response.GetResponseStream()))Assert(reader.ReadToEnd().Contains("no-inference supervisor test"),"echo");}
 static string SolId(){var h=Tray.Read("http://127.0.0.1:8766/health");return Convert.ToString(((Dictionary<string,object>)((Dictionary<string,object>)h["threads"])["main"])["id"]);}
 delegate bool WindowCallback(IntPtr window,IntPtr data);
 [DllImport("user32.dll")] static extern bool EnumWindows(WindowCallback callback,IntPtr data);
 [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr window);
 [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr window,out uint pid);
 static bool Hidden(int pid){bool hidden=true;EnumWindows((w,d)=>{uint owner;GetWindowThreadProcessId(w,out owner);if(owner==pid&&IsWindowVisible(w))hidden=false;return true;},IntPtr.Zero);return hidden;}
 static bool Alive(int pid){try{return !Process.GetProcessById(pid).HasExited;}catch{return false;}}
 static void Pump(int milliseconds){var until=DateTime.UtcNow.AddMilliseconds(milliseconds);while(DateTime.UtcNow<until){Application.DoEvents();Thread.Sleep(50);}}
 static void Wait(Tray tray,string wanted,int seconds){var until=DateTime.UtcNow.AddSeconds(seconds);while(DateTime.UtcNow<until){Application.DoEvents();if(tray.State==wanted)return;Thread.Sleep(100);}throw new Exception("Timed out waiting for "+wanted+" ("+tray.State+")\n"+tray.LogsForTest());}
 static void WaitNewReady(Tray tray,int old,int seconds){var until=DateTime.UtcNow.AddSeconds(seconds);while(DateTime.UtcNow<until){Application.DoEvents();if(tray.State=="Ready"&&tray.BridgePid!=old)return;Thread.Sleep(100);}throw new Exception("New ready bridge timeout\n"+tray.LogsForTest());}
}
}
