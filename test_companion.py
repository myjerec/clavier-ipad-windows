import ctypes
import http.client
import json
import ssl
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from pathlib import Path
import companion as c

class ProtocolTests(unittest.TestCase):
    def test_pairing_survives_restart_and_revokes_on_disk(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'pairing.json'
            original=c.State(lambda e:None,pairing_path=path)
            token=original.pair(original.code)
            self.assertNotIn(token,path.read_text())
            restarted=c.State(lambda e:None,pairing_path=path)
            restarted.command(token,{'type':'status'})
            with self.assertRaises(PermissionError):restarted.command('wrong',{'type':'status'})
            restarted.rotate()
            with self.assertRaises(PermissionError):c.State(lambda e:None,pairing_path=path).command(token,{'type':'status'})
            path.write_text('broken')
            self.assertIsNone(c.State(lambda e:None,pairing_path=path).token)

    def test_media_and_apps_require_auth_and_known_actions(self):
        events=[];launched=[]
        state=c.State(events.append,launcher=launched.append)
        with self.assertRaises(PermissionError):state.command('',{'type':'app','app':'notepad'})
        token=state.pair(state.code)
        state.command(token,{'type':'app','app':'notepad'})
        self.assertEqual(launched,['notepad'])
        for action,vk in c.MEDIA.items():
            state.command(token,{'type':'media','action':action})
            self.assertEqual([e.data.ki.wVk for e in events[-1]],[vk,vk])
            self.assertEqual([e.data.ki.dwFlags for e in events[-1]],[1,3])
        for data in [{'type':'app','app':'powershell'},{'type':'app','app':'calc.exe & evil'},{'type':'media','action':'shutdown'}]:
            with self.assertRaises(ValueError):state.command(token,data)
        state.enabled=False
        with self.assertRaises(ValueError):state.command(token,{'type':'media','action':'volume_up'})

    def test_launcher_fixed_arguments_no_shell(self):
        with patch.object(c.Path,'is_file',return_value=True),patch.object(c.subprocess,'Popen') as launch:
            c.launch_application('discord')
            self.assertEqual(launch.call_args.args[0][-2:],['--processStart','Discord.exe'])
            self.assertFalse(launch.call_args.kwargs['shell'])
        with self.assertRaises(ValueError):c.launch_application('cmd.exe')
        with patch.object(c.Path,'is_file',return_value=False):
            with self.assertRaises(ValueError):c.launch_application('discord')

    def test_direct_letters_corrections_and_guards(self):
        captured=[];context=[(10,20,30)]
        state=c.State(captured.append,lambda:context[0]);token=state.pair(state.code)
        def direct(base,text,draft='test'):
            state.command(token,{'type':'direct','draft':draft,'base':base,'text':text})
        direct('','B');self.assertEqual(len(captured),1)
        direct('B','Bonjor');direct('Bonjor','Bonjour')
        self.assertEqual(sum(e.data.ki.wVk==8 and e.data.ki.dwFlags==0 for e in captured[-1]),1)
        direct('Bonjour','Bonjou')
        with self.assertRaises(ValueError):direct('Bonjour','Bonjour!')
        context[0]=(10,20,31)
        with self.assertRaises(ValueError):direct('Bonjou','Bonjour')
        direct('','Nouvelle','new')
        state.command(token,{'type':'key','key':'Left'})
        with self.assertRaises(ValueError):direct('Nouvelle','Nouvelle suite','new')

    def test_direct_ambiguous_deletions_fail_closed(self):
        for old,new in [('😀',''),('e\u0301','e'),('ligne\n','ligne')]:
            with self.assertRaises(ValueError):c.direct_events(old,new)
        self.assertEqual(len(c.direct_events('été','ét')),2)

    def test_unicode_and_balanced_shortcuts(self):
        events=c.prepare({'type':'text','text':'é😀\n'})
        self.assertEqual(len(events),8)
        self.assertEqual(events[0].data.ki.wScan,233)
        events=c.prepare({'type':'key','key':'C','mods':['Ctrl','Shift']})
        self.assertEqual([e.data.ki.wVk for e in events],[17,16,67,67,16,17])
        self.assertEqual([e.data.ki.dwFlags for e in events],[0,0,0,2,2,2])
        self.assertEqual(ctypes.sizeof(c.INPUT),40 if ctypes.sizeof(ctypes.c_void_p)==8 else 28)

    def test_invalid_commands(self):
        for data in [{'type':'key','key':'Delete','mods':['Ctrl','Alt']}, {'type':'key','key':'Shell'}, {'type':'text','text':'x'*2001}, {'type':'key','key':'A','mods':['Ctrl','Ctrl']}]:
            with self.assertRaises(ValueError): c.prepare(data)

    def test_auth_expiry_pause_revoke(self):
        captured=[]; state=c.State(captured.append)
        with self.assertRaises(PermissionError):state.command('',{'type':'text','text':'a'})
        token=state.pair(state.code)
        with self.assertRaises(ValueError):state.pair(state.code)
        state.command(token,{'type':'text','text':'a'})
        self.assertEqual(len(captured),1)
        state.enabled=False
        with self.assertRaises(ValueError):state.command(token,{'type':'text','text':'a'})
        state.enabled=True;state.expiry=time.monotonic()-1
        with self.assertRaises(PermissionError):state.command(token,{'type':'text','text':'a'})
        state.rotate()
        with self.assertRaises(PermissionError):state.command(token,{'type':'text','text':'a'})

    def test_pair_lock_and_local_scope(self):
        state=c.State(lambda x:None)
        for _ in range(10):
            with self.assertRaises(ValueError):state.pair('incorrect')
        with self.assertRaises(ValueError):state.pair(state.code)
        self.assertTrue(c.local('192.168.1.12'));self.assertFalse(c.local('8.8.8.8'))
        state.rotate();state.deadline=time.monotonic()-1
        with self.assertRaises(ValueError):state.pair(state.code)

    def test_https_end_to_end(self):
        captured=[];state=c.State(captured.append)
        with tempfile.TemporaryDirectory() as temp:
            cert,key,fp=c.certificate('127.0.0.1',Path(temp))
            server=c.ThreadingHTTPServer(('127.0.0.1',0),c.handler(state,'placeholder'))
            port=server.server_address[1];host=f'127.0.0.1:{port}'
            server.RequestHandlerClass=c.handler(state,host)
            context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.load_cert_chain(cert,key)
            server.socket=context.wrap_socket(server.socket,server_side=True)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            clientcontext=ssl.create_default_context(cafile=str(cert))
            def request(path,data=None,extra=None):
                conn=http.client.HTTPSConnection('127.0.0.1',port,context=clientcontext,timeout=5)
                headers={'Origin':'https://'+host,'X-Keyboard':'1','Content-Type':'application/json'}
                headers.update(extra or {})
                conn.request('POST' if data is not None else 'GET',path,json.dumps(data) if data is not None else None,headers)
                response=conn.getresponse();body=response.read();result=(response.status,dict(response.getheaders()),body);conn.close();return result
            try:
                self.assertEqual(request('/')[0],200)
                self.assertEqual(request('/private/server-key.pem')[0],404)
                self.assertEqual(request('/command',{'type':'text','text':'a'})[0],401)
                self.assertEqual(request('/pair',{'code':state.code},{'Origin':'https://evil.example'})[0],403)
                self.assertEqual(request('/pair',{'code':state.code},{'Host':'evil.example'})[0],403)
                status,headers,_=request('/pair',{'code':state.code});self.assertEqual(status,200)
                cookie=headers['Set-Cookie'].split(';')[0]
                self.assertEqual(request('/command',{'type':'text','text':'Bonjour é😀'},{'Cookie':cookie})[0],200)
                self.assertEqual(len(captured),1)
                self.assertEqual(request('/command',{'type':'key','key':'Delete','mods':['Ctrl','Alt']},{'Cookie':cookie})[0],400)
                state.rotate()
                self.assertEqual(request('/command',{'type':'text','text':'a'},{'Cookie':cookie})[0],401)
            finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main()
