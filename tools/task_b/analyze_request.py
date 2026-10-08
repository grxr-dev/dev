"""Validate Task B's bounded request trace against actual Flash commits."""
import argparse, hashlib, json, struct
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument("capture",type=Path);p.add_argument("--reference",type=Path)
a=p.parse_args();root=a.capture
trace=[json.loads(x) for x in (root/"request.jsonl").read_text().splitlines()]
flash=[json.loads(x) for x in (root/"flash.jsonl").read_text().splitlines()]
marker=b"CLEAR-RAM-CHECK\0"
def rows(pc):return [e for e in trace if e["pc"]==pc]
def one(pc,pred=lambda e:True):
 r=[e for e in rows(pc) if pred(e)];assert len(r)==1,(hex(pc),len(r));return r[0]
def mem(e,addr,n):
 for m in e["mem"]:
  b=bytes.fromhex(m["hex"]);off=addr-m["addr"]
  if 0<=off and off+n<=len(b):return b[off:off+n]
 raise AssertionError((e["seq"],hex(addr),n))
def word(e,addr):return struct.unpack("<I",mem(e,addr,4))[0]
def system(e):return e["cycle"]//2 if e["cpu"]==9 else e["cycle"]
entry=one(0x202fcc0);assert entry["r"][0]==0
stack=one(0x202fcf8);stackaddr=stack["r"][13];assert mem(stack,stackaddr,16)==marker
loads=rows(0x202fce0);assert [e["r"][4] for e in loads]==list(range(0x20c63b0,0x20c63c0,2))
stores=rows(0x202fd1c);assert bytes(e["r"][0]&255 for e in stores)==marker
call=one(0x202fd34);heap=call["r"][1];assert call["r"][:3]==[0x180,heap,16];assert mem(call,heap,16)==marker
assert [e["r"][3] for e in stores]==list(range(heap,heap+16))
wrapper=one(0x202fa08);api=one(0x200de78)
assert wrapper["r"][:3]==api["r"][:3]==call["r"][:3]
assert wrapper["r"][14]==0x202fd38 and api["r"][14]==0x202fa60
copy=one(0x200e044);buffer=copy["r"][1];assert copy["r"][:3]==[heap,buffer,16]
request=one(0x200e080);shared=request["r"][3]
assert request["r"][1:3]==[7,10]
assert [word(request,shared+i) for i in [12,16,20]]==[buffer,0x180,16]
send=one(0x20091b0,lambda e:e["r"][2]==0x1eb);assert send["r"][1]==0x4000188
receive=one(0x37fe230,lambda e:e["r"][1]==0x1eb);assert receive["r"][7]==0x4100000
callback=one(0x3802d6c,lambda e:e["r"][1]==7);assert callback["r"][:3]==[11,7,1];assert callback["r"][14]==0x37fe280
worker=one(0x3802cf8,lambda e:e["r"][2]==7);assert worker["r"][1]==0x3803a34
adapter=one(0x3803a34);assert word(adapter,adapter["r"][0])==shared
write=one(0x3802f48);assert write["r"][:3]==[0x180,buffer,16];assert mem(write,buffer,16)==marker
header=one(0x3803150,lambda e:e["r"][1]==10);assert header["r"][0]==0x180
serialize=one(0x3803338,lambda e:e["r"][:3]==[buffer,0,16]);assert serialize["r"][3]==0x38032a8;assert mem(serialize,buffer,16)==marker
commits=[e for e in flash if e["offset"]==0x180 and e["new_hex"]=="43"]
assert len(commits)==1;tx=commits[0]["transaction"];commits=[e for e in flash if e["transaction"]==tx]
assert bytes.fromhex("".join(e["new_hex"] for e in commits))==marker
matched=[]
for i,c in enumerate(commits):
 origin=c["byte_origin"];e=one(0x38032b8,lambda e:e["cycle"]==origin["cpu_cycles"] and e["insn"]==origin["instruction"])
 assert e["cpu"]==7 and not e["thumb"] and e["r"][1]==0x40001a2 and e["r"][2]==marker[i]
 assert c["offset"]==0x180+i and origin["pc"]=="0x038032B8"
 assert word(e,e["r"][0]+4)==buffer+i and e["r"][14]==0x3803394
 matched.append(e)
command=one(0x38032b8,lambda e:e["cycle"]==commits[0]["command_origin"]["cpu_cycles"])
assert command["r"][2]==10
chain=[entry,call,wrapper,api,copy,request,send,receive,callback,worker,adapter,write,header,command,serialize,*matched]
assert all(x["seq"]<y["seq"] and system(x)<=system(y) for x,y in zip(chain,chain[1:]))
# Validate the intermediate call boundaries and serialized command/address bytes.
stager=one(0x200e008);assert stager["r"][14]==0x200df1c
submit=one(0x200e88c,lambda e:e["r"][1]==7)
assert submit["r"][14]==0x200e084
fifoapi=one(0x2009124,lambda e:e["r"][1]==7)
assert fifoapi["r"][:3]==[11,7,1] and fifoapi["r"][14]==0x200e93c
queued=one(0x3802d90,lambda e:e["r"][1]==7)
assert queued["r"][:3]==[adapter["r"][0],7,0]
assert worker["r"][14]==0x3802cfc and write["r"][14]==0x3802cfc
assert serialize["r"][14]==0x3802fc8
headercall=one(0x38031e4,lambda e:e["r"][14]==0x3802fb4)
assert headercall["r"][1:4]==[0,4,0x38032a8]
assert mem(headercall,headercall["r"][0],4)==bytes.fromhex("0a000180")
assert word(request,shared+12)==buffer
decoded=one(0x3803a38);assert decoded["r"][2]==shared
assert [word(decoded,shared+i) for i in [12,16,20]]==[buffer,0x180,16]
assert entry["seq"]<stager["seq"]<submit["seq"]<fifoapi["seq"]<send["seq"]<receive["seq"]<queued["seq"]<worker["seq"]
reference_equal=None
if a.reference:
 reference_equal=(a.reference/"flash.jsonl").read_bytes()==(root/"flash.jsonl").read_bytes();assert reference_equal
result={"validated":True,"snapshots":len(trace),"transaction":tx,"sequences":[e["sequence"] for e in commits],"reference_flash_byte_identical":reference_equal,"request_sha256":hashlib.sha256((root/"request.jsonl").read_bytes()).hexdigest(),"stack":hex(stackaddr),"source":hex(heap),"staging_buffer":hex(buffer),"shared_request":hex(shared),"fifo_word":"0x1eb","chain":[{"seq":e["seq"],"cpu":e["cpu"],"pc":hex(e["pc"]),"system_cycle":system(e),"instruction":e["insn"]} for e in chain]}
(root/"request-audit.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({k:v for k,v in result.items() if k!="chain"},indent=2))
