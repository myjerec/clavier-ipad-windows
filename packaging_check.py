"""Packaged executable smoke test. Never injects any real keyboard event."""
def run(app,report):
    import http.client
    import tempfile
    import json
    import ssl
    import threading
    from pathlib import Path
    checks=[]
    try:
        window=app.tk.Tk()
        window.withdraw()
        window.update_idletasks()
        window.destroy()
        checks.append('real-tcl-tk-window-initialization')
        with tempfile.TemporaryDirectory() as temp:
            private=Path(temp)
            cert,key,_=app.certificate('127.0.0.1',private)
            checks.append('certificate-generation')
            state=app.State(sink=lambda events:None,pairing_path=private/'pairing.json')
            server=app.ThreadingHTTPServer(('127.0.0.1',0),app.handler(state,'unused'))
            host=f'127.0.0.1:{server.server_port}'
            server.RequestHandlerClass=app.handler(state,host)
            context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.load_cert_chain(cert,key)
            server.socket=context.wrap_socket(server.socket,server_side=True)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            trust=ssl.create_default_context(cafile=str(cert))
            def request(path,data=None,cookie=None):
                client=http.client.HTTPSConnection('127.0.0.1',server.server_port,context=trust,timeout=5)
                headers={'Origin':'https://'+host,'X-Keyboard':'1','Content-Type':'application/json'}
                if cookie:headers['Cookie']=cookie
                client.request('POST' if data is not None else 'GET',path,json.dumps(data) if data is not None else None,headers)
                response=client.getresponse();result=(response.status,dict(response.getheaders()),response.read());client.close();return result
            try:
                for name in ['/', '/app.js','/style.css','/native-draft.js','/extras.js','/app-icon.png','/app-icon.ico']:
                    status,_,body=request(name)
                    assert status==200 and len(body)>10,name
                checks.append('all-embedded-assets-over-verified-https')
                assert request('/command',{'type':'status'})[0]==401
                status,headers,_=request('/pair',{'code':state.code});assert status==200
                cookie=headers['Set-Cookie'].split(';')[0]
                assert request('/command',{'type':'text','text':'Bonjour été'},cookie)[0]==200
                token=cookie.split('=',1)[1]
                restored=app.State(sink=lambda events:None,pairing_path=private/'pairing.json')
                restored.command(token,{'type':'status'})
                restored.rotate()
                checks.extend(['auth-and-simulated-input','persistent-pairing'])
            finally:server.shutdown();server.server_close();thread.join()
        report.write_text(json.dumps({'ok':True,'frozen':getattr(app.sys,'frozen',False),'checks':checks},indent=2),encoding='utf-8')
    except Exception as exc:
        report.write_text(json.dumps({'ok':False,'checks':checks,'error':repr(exc)}),encoding='utf-8')
        raise
