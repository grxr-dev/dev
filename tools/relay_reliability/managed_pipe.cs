using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Web.Script.Serialization;

namespace MusePostTurn {
public static class ManagedPipe {
 [StructLayout(LayoutKind.Sequential)] struct HandleEntry {
  public IntPtr HandleValue, HandleCount, PointerCount;
  public uint GrantedAccess, ObjectTypeIndex, Attributes, Reserved;
 }
 [DllImport("kernel32.dll",SetLastError=true)] static extern IntPtr OpenProcess(uint access,bool inherit,int pid);
 [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool DuplicateHandle(IntPtr source,IntPtr handle,IntPtr target,out IntPtr duplicate,uint access,bool inherit,uint options);
 [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
 [DllImport("kernel32.dll")] static extern uint GetFileType(IntPtr handle);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool WriteFile(IntPtr handle,byte[] data,uint size,out uint written,IntPtr overlapped);
 [DllImport("ntdll.dll")] static extern int NtQueryInformationProcess(IntPtr process,int kind,IntPtr data,int length,out int required);

 sealed class Candidate : IDisposable {
  public long Original;
  public IntPtr Handle;
  public void Dispose(){if(Handle!=IntPtr.Zero){CloseHandle(Handle);Handle=IntPtr.Zero;}}
 }
 static string Hash(string text){using(var hash=SHA256.Create())return BitConverter.ToString(hash.ComputeHash(Encoding.UTF8.GetBytes(text))).Replace("-","").ToLowerInvariant();}
 static List<Candidate> Pipes(int pid,bool write){
  var process=OpenProcess(0x1440,false,pid);
  if(process==IntPtr.Zero)throw new InvalidOperationException("cannot_query_verified_process_handles");
  var candidates=new List<Candidate>();
  try{
   int capacity=65536;
   while(capacity<=8*1024*1024){
    var buffer=Marshal.AllocHGlobal(capacity);
    try{
     int required;int status=NtQueryInformationProcess(process,51,buffer,capacity,out required);
     if(status==unchecked((int)0xC0000004)){capacity=Math.Max(capacity*2,required);continue;}
     if(status!=0)throw new InvalidOperationException("process_handle_snapshot_failed");
     long count=Marshal.ReadIntPtr(buffer).ToInt64();int stride=Marshal.SizeOf(typeof(HandleEntry));
     if(count<0||count>100000||2L*IntPtr.Size+count*stride>capacity)throw new InvalidOperationException("invalid_handle_snapshot");
     for(long index=0;index<count;index++){
      var entry=(HandleEntry)Marshal.PtrToStructure(IntPtr.Add(buffer,checked(2*IntPtr.Size+(int)index*stride)),typeof(HandleEntry));
      bool readable=(entry.GrantedAccess&1)!=0;bool writable=(entry.GrantedAccess&2)!=0;
      if(write?(!writable||readable):(!readable||writable))continue;
      IntPtr duplicate;
      if(!DuplicateHandle(process,entry.HandleValue,GetCurrentProcess(),out duplicate,0,false,2))continue;
      bool keep=false;
      try{
       if(GetFileType(duplicate)!=3)continue;
       candidates.Add(new Candidate{Original=entry.HandleValue.ToInt64(),Handle=duplicate});keep=true;
      }finally{if(!keep)CloseHandle(duplicate);}
     }
     return candidates;
    }finally{Marshal.FreeHGlobal(buffer);}
   }
   throw new InvalidOperationException("handle_snapshot_bound_exceeded");
  }catch{foreach(var candidate in candidates)candidate.Dispose();throw;}
  finally{CloseHandle(process);}
 }
 static void SendIdle(Candidate candidate){
  var bytes=Encoding.UTF8.GetBytes("{\"op\":\"shutdown\",\"if_idle\":true}\n");uint written;
  if(!WriteFile(candidate.Handle,bytes,(uint)bytes.Length,out written,IntPtr.Zero)||written!=bytes.Length)
   throw new InvalidOperationException("managed_idle_command_write_uncertain");
 }
 static Dictionary<string,object> Execute(string mode,int owner,int child,long ownerTicks,long childTicks,string expectedHash){
  var ownerProcess=Process.GetProcessById(owner);var childProcess=Process.GetProcessById(child);
  if(ownerProcess.StartTime.ToUniversalTime().Ticks!=ownerTicks||childProcess.StartTime.ToUniversalTime().Ticks!=childTicks)
   throw new InvalidOperationException("pid_start_identity_mismatch");
  var writers=Pipes(owner,true);var readers=Pipes(child,false);
  try{
   if(writers.Count!=1||readers.Count<1)throw new InvalidOperationException("managed_stdin_writer_not_unique_"+writers.Count);
   string pipeHash=Hash(owner+":"+ownerTicks+":"+child+":"+childTicks+":"+writers[0].Original);
   if(expectedHash!="-"&&pipeHash!=expectedHash)throw new InvalidOperationException("managed_pipe_identity_changed");
   if(mode=="shutdown-if-idle"){
    if(expectedHash.Length!=64)throw new InvalidOperationException("reviewed_channel_identity_required");
    SendIdle(writers[0]);
   }else if(mode!="probe")throw new InvalidOperationException("unsupported_operation");
   return new Dictionary<string,object>{{"owner_pid",owner},{"bridge_pid",child},{"pipe_sha256",pipeHash},{"matching_channels",1},{"operation",mode}};
  }finally{foreach(var item in writers)item.Dispose();foreach(var item in readers)item.Dispose();}
 }
 public static int Main(string[] args){
  try{
   if(args.Length==1&&args[0]=="selftest"){
    var current=Process.GetCurrentProcess();var before=Pipes(current.Id,true);var beforeHandles=new HashSet<long>();foreach(var candidate in before){beforeHandles.Add(candidate.Original);candidate.Dispose();}
    var start=new ProcessStartInfo("cmd.exe","/d /c set /p line= & exit /b 0"){UseShellExecute=false,CreateNoWindow=true,RedirectStandardInput=true,RedirectStandardOutput=true,RedirectStandardError=true};
    using(var fixture=Process.Start(start)){
     var after=Pipes(current.Id,true);var newPipes=new List<Candidate>();foreach(var candidate in after)if(!beforeHandles.Contains(candidate.Original))newPipes.Add(candidate);
     try{if(newPipes.Count!=1)throw new InvalidOperationException("fixture_writer_not_unique");SendIdle(newPipes[0]);}finally{foreach(var candidate in after)candidate.Dispose();}
     if(!fixture.WaitForExit(5000))throw new InvalidOperationException("fixture_did_not_receive_managed_line");
     Console.WriteLine(new JavaScriptSerializer().Serialize(new{selftest="PASS",channels=1,production_touched=false}));return 0;
    }
   }
   if(args.Length!=6)throw new InvalidOperationException("exact_arguments_required");
   Console.WriteLine(new JavaScriptSerializer().Serialize(Execute(args[0],int.Parse(args[1]),int.Parse(args[2]),long.Parse(args[3]),long.Parse(args[4]),args[5])));return 0;
  }catch(Exception error){Console.Error.WriteLine(error.GetType().Name+":"+error.Message);return 1;}
 }
}
}
