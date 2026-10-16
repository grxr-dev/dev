"""Isolated listener for exactly next/ack. Never attached to the relay listener."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from inbox_wire import encoded,unique_json,MAX_HTTP_BYTES
from inbox_queue import Conflict
from inbox_recovery import RecoveryAdmin
from inbox_supersession import SupersessionAdmin

def read_body(handler):
    headers=handler.headers
    lengths=headers.get_all('Content-Length',[])
    if headers.get('Transfer-Encoding') or len(lengths)!=1 or not lengths[0].isascii() or not lengths[0].isdecimal():raise ValueError('invalid framing')
    n=int(lengths[0])
    if not 0<n<=MAX_HTTP_BYTES:raise ValueError('body too large or empty')
    if headers.get_content_type()!='application/json' or headers.get('Content-Encoding','identity')!='identity':raise ValueError('expected uncompressed JSON')
    raw=handler.rfile.read(n)
    if len(raw)!=n:raise ValueError('incomplete body')
    return unique_json(raw.decode('utf-8'))

class LocalHandler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup();self.connection.settimeout(10)
    def log_message(self,*args):pass
    def respond(self,status,body):
        data=b'' if status==204 else encoded(body)
        self.send_response(status);self.send_header('Content-Length',str(len(data)))
        self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store')
        self.send_header('Connection','close');self.end_headers();self.wfile.write(data)
    def guarded(self):
        return (self.client_address[0]=='127.0.0.1' and self.headers.get_all('X-Jarvis-Local',[])==['1'] and
                self.headers.get_all('Host',[])==[f'127.0.0.1:{self.server.server_port}'] and
                self.headers.get('Origin') is None and self.headers.get('Referer') is None)
    def do_GET(self):
        if not self.guarded():return self.respond(403,{'ok':False,'error':'local_transport_only'})
        if self.path=='/local/inbox/admin/supersede-watchdog':
            if not self.server.recovery.authorized(self.headers):return self.respond(403,{'ok':False,'error':'local_admin_required'})
            return self.respond(200,self.server.supersession.status())
        if self.path=='/local/inbox/admin/recovery-once':
            if not self.server.recovery.authorized(self.headers):return self.respond(403,{'ok':False,'error':'local_admin_required'})
            return self.respond(200,self.server.recovery.status())
        if self.path!='/local/inbox/next':return self.respond(404,{'ok':False,'error':'not_found'})
        try:self.respond(*self.server.inbox.local_next())
        except (OSError,ValueError):self.respond(503,{'ok':False,'error':'inbox_unavailable'})
    def do_POST(self):
        if not self.guarded():return self.respond(403,{'ok':False,'error':'local_transport_only'})
        if self.path=='/local/inbox/admin/supersede-watchdog':
            if not self.server.recovery.authorized(self.headers):return self.respond(403,{'ok':False,'error':'local_admin_required'})
            try:return self.respond(200,self.server.supersession.cancel(read_body(self)))
            except Conflict as e:return self.respond(409,{'ok':False,'error':str(e)})
            except (ValueError,UnicodeError,TypeError,RecursionError):return self.respond(400,{'ok':False,'error':'invalid_supersession_request'})
            except OSError:return self.respond(503,{'ok':False,'error':'supersession_persistence_failed'})
        if self.path=='/local/inbox/admin/recovery-once':
            if not self.server.recovery.authorized(self.headers):return self.respond(403,{'ok':False,'error':'local_admin_required'})
            try:return self.respond(200,self.server.recovery.recover(read_body(self)))
            except Conflict as e:return self.respond(409,{'ok':False,'error':str(e)})
            except (ValueError,UnicodeError,TypeError,RecursionError):return self.respond(400,{'ok':False,'error':'invalid_recovery_request'})
            except OSError:return self.respond(503,{'ok':False,'error':'recovery_persistence_failed'})
        if self.path!='/local/inbox/ack':return self.respond(404,{'ok':False,'error':'not_found'})
        try:self.respond(*self.server.inbox.local_ack(read_body(self)))
        except (ValueError,UnicodeError,RecursionError):self.respond(400,{'ok':False,'error':'malformed_request'})
        except OSError:self.respond(503,{'ok':False,'error':'inbox_unavailable'})
class LocalInboxServer(ThreadingHTTPServer):
    daemon_threads=True
    allow_reuse_address=False
    def __init__(self,port,inbox):
        self.inbox=inbox;self.recovery=RecoveryAdmin(inbox.queue);self.supersession=SupersessionAdmin(inbox.queue);super().__init__(('127.0.0.1',port),LocalHandler)
