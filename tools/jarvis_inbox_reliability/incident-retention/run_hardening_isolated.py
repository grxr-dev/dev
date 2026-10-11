"""Run existing full hardening suite with isolated ephemeral listener/native fixture."""
import pathlib,socket,sys
p=pathlib.Path(__file__).resolve().parents[4]/'bridge/inbox-v1/tests/test_hardening.py';sys.path.insert(0,str(p.parent))
with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
s=p.read_text();a,b=s.split('class HandlerTests',1);b=b.replace('18741',str(port));needle="        exe=host/'jarvis_inbox_host.exe'"
b=b.replace(needle,"        hp=host/'jarvis_inbox_host.py';hp.write_text(hp.read_text().replace('18741','"+str(port)+"'))\n        cp=host/'config.json';cp.write_text(cp.read_text().replace('18741','"+str(port)+"'))\n"+needle)
s=(a+'class HandlerTests'+b).replace('cls.tmp=tempfile.TemporaryDirectory();','cls.tmp=tempfile.TemporaryDirectory(ignore_cleanup_errors=True);')
globals()['__file__']=str(p);exec(compile(s,str(p),'exec'),globals())
