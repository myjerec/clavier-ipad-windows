"""Clavier iPad V1 — HTTPS local, pairing and bounded Windows SendInput."""
import ctypes as C
from ctypes import wintypes as W
import datetime as dt
import ipaddress
import json
from pathlib import Path
import secrets
import socket
import ssl
import threading
import time
import unicodedata
import os
import subprocess
import hashlib
import sys
from windows_clipboard import clipboard
import tkinter as tk
from tkinter import ttk, messagebox
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

ASSET_ROOT = Path(__file__).resolve().parent
ROOT = Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else ASSET_ROOT
PORT = 18443
MODS = {'Ctrl': 0x11, 'Alt': 0x12, 'Shift': 0x10, 'Win': 0x5B, 'AltGr': 0xA5}
KEYS = {'Tab':9,'Esc':27,'Enter':13,'Backspace':8,'Delete':46,'Space':32,
        'Left':37,'Up':38,'Right':39,'Down':40,'Home':36,'End':35,
        'PageUp':33,'PageDown':34,'Insert':45,'CapsLock':20,'PrintScreen':44}
KEYS.update({f'F{i}':111+i for i in range(1,13)})
KEYS.update({c:ord(c) for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'})
MEDIA={'volume_up':0xAF,'volume_down':0xAE,'mute':0xAD,'play_pause':0xB3,'next':0xB0,'previous':0xB1,'stop':0xB2}

def launch_application(name):
    windows=Path(os.environ.get('WINDIR',r'C:\Windows'))
    localapp=Path(os.environ.get('LOCALAPPDATA',''))
    catalog={
        'notepad':[str(windows/'System32'/'notepad.exe')],
        'calculator':[str(windows/'System32'/'calc.exe')],
        'explorer':[str(windows/'explorer.exe')],
        'paint':[str(windows/'System32'/'mspaint.exe')],
        'discord':[str(localapp/'Discord'/'Update.exe'),'--processStart','Discord.exe'],
    }
    if name=='browser':
        os.startfile('https://www.google.com')
        return
    if not isinstance(name,str) or name not in catalog: raise ValueError('Application non autorisée')
    command=catalog[name]
    if not Path(command[0]).is_file(): raise ValueError('Cette application n’est pas installée à son emplacement habituel sur le PC.')
    subprocess.Popen(command,shell=False)
NETWORKS = [ipaddress.ip_network(s) for s in ('10.0.0.0/8','172.16.0.0/12','192.168.0.0/16','127.0.0.0/8')]

def local(ip):
    try:
        return any(ipaddress.ip_address(ip) in n for n in NETWORKS)
    except ValueError:
        return False

class KEYBDINPUT(C.Structure):
    _fields_ = [('wVk',W.WORD),('wScan',W.WORD),('dwFlags',W.DWORD),('time',W.DWORD),('dwExtraInfo',C.c_size_t)]
class MOUSEINPUT(C.Structure):
    _fields_ = [('dx',W.LONG),('dy',W.LONG),('mouseData',W.DWORD),('dwFlags',W.DWORD),('time',W.DWORD),('dwExtraInfo',C.c_size_t)]
class UNION(C.Union):
    _fields_ = [('ki',KEYBDINPUT),('mi',MOUSEINPUT)]
class INPUT(C.Structure):
    _fields_ = [('type',W.DWORD),('data',UNION)]

def event(vk=0, scan=0, flags=0):
    return INPUT(1, UNION(ki=KEYBDINPUT(vk,scan,flags,0,0)))

def prepare(data):
    if not isinstance(data,dict):
        raise ValueError('Commande invalide')
    kind = data.get('type')
    if kind == 'text':
        value = data.get('text')
        if not isinstance(value,str) or not 1 <= len(value) <= 2000:
            raise ValueError('Texte requis : 1 à 2000 caractères')
        events = []
        for char in value.replace('\r\n','\n').replace('\r','\n'):
            if char in '\n\t':
                vk = 13 if char == '\n' else 9
                events.extend([event(vk),event(vk,flags=2)])
            else:
                raw = char.encode('utf-16-le')
                for i in range(0,len(raw),2):
                    unit = int.from_bytes(raw[i:i+2],'little')
                    events.extend([event(scan=unit,flags=4),event(scan=unit,flags=6)])
        return events
    if kind != 'key' or data.get('key') not in KEYS:
        raise ValueError('Touche inconnue')
    mods = data.get('mods',[])
    if not isinstance(mods,list) or len(mods)>5 or any(not isinstance(m,str) or m not in MODS for m in mods) or len(set(mods))!=len(mods):
        raise ValueError('Modificateurs invalides')
    if data['key']=='Delete' and 'Ctrl' in mods and 'Alt' in mods:
        raise ValueError('Ctrl+Alt+Suppr est réservé par Windows. Utilise le clavier du PC.')
    extended = data['key'] in {'Delete','Insert','Home','End','PageUp','PageDown','Left','Right','Up','Down','PrintScreen'}
    result = [event(MODS[m],flags=1 if m in ('Win','AltGr') else 0) for m in mods]
    vk=KEYS[data['key']]
    result += [event(vk,flags=int(extended)),event(vk,flags=2|int(extended))]
    result += [event(MODS[m],flags=2|(1 if m in ('Win','AltGr') else 0)) for m in reversed(mods)]
    return result

def inject(events):
    api=C.WinDLL('user32',use_last_error=True)
    clock=C.WinDLL('kernel32');clock.GetTickCount.restype=W.DWORD
    stamp=clock.GetTickCount()
    for item in events: item.data.ki.time=stamp
    api.SendInput.argtypes=[W.UINT,C.POINTER(INPUT),C.c_int]
    api.SendInput.restype=W.UINT
    batch=(INPUT*len(events))(*events)
    if api.SendInput(len(batch),batch,C.sizeof(INPUT)) != len(batch):
        release=(INPUT*len(MODS))(*(event(v,flags=2|(1 if k in ('Win','AltGr') else 0)) for k,v in MODS.items()))
        api.SendInput(len(release),release,C.sizeof(INPUT))
        raise RuntimeError('Windows a refusé la saisie. Vérifie la fenêtre active et ses droits.')
    return stamp

_activity_revision=0
_activity_ready=threading.Event()
_activity_started=False
_activity_ok=False
_activity_lock=threading.Lock()

def physical_activity():
    """Count physical clicks/keys only; never retain their contents."""
    global _activity_started
    def monitor():
        global _activity_revision,_activity_ok
        user=C.WinDLL('user32',use_last_error=True)
        kernel=C.WinDLL('kernel32',use_last_error=True)
        callback_type=C.WINFUNCTYPE(C.c_ssize_t,C.c_int,W.WPARAM,W.LPARAM)
        user.SetWindowsHookExW.argtypes=[C.c_int,callback_type,W.HINSTANCE,W.DWORD]
        user.SetWindowsHookExW.restype=W.HANDLE
        user.CallNextHookEx.argtypes=[W.HANDLE,C.c_int,W.WPARAM,W.LPARAM]
        user.CallNextHookEx.restype=C.c_ssize_t
        kernel.GetModuleHandleW.argtypes=[W.LPCWSTR];kernel.GetModuleHandleW.restype=W.HMODULE
        class KEYHOOK(C.Structure):
            _fields_=[('vk',W.DWORD),('scan',W.DWORD),('flags',W.DWORD),('time',W.DWORD),('extra',C.c_size_t)]
        class MOUSEHOOK(C.Structure):
            _fields_=[('point',W.POINT),('data',W.DWORD),('flags',W.DWORD),('time',W.DWORD),('extra',C.c_size_t)]
        @callback_type
        def keyboard(code,kind,pointer):
            global _activity_revision
            if code>=0 and kind in (0x100,0x104) and not C.cast(pointer,C.POINTER(KEYHOOK)).contents.flags&0x10:
                _activity_revision+=1
            return user.CallNextHookEx(None,code,kind,pointer)
        @callback_type
        def mouse(code,kind,pointer):
            global _activity_revision
            if code>=0 and kind in (0x201,0x204,0x207,0x20B) and not C.cast(pointer,C.POINTER(MOUSEHOOK)).contents.flags&1:
                _activity_revision+=1
            return user.CallNextHookEx(None,code,kind,pointer)
        module=kernel.GetModuleHandleW(None)
        kh=user.SetWindowsHookExW(13,keyboard,module,0)
        mh=user.SetWindowsHookExW(14,mouse,module,0)
        _activity_ok=bool(kh and mh);_activity_ready.set()
        if _activity_ok:
            msg=W.MSG()
            while user.GetMessageW(C.byref(msg),None,0,0)>0:
                user.TranslateMessage(C.byref(msg));user.DispatchMessageW(C.byref(msg))
        user.UnhookWindowsHookEx.argtypes=[W.HANDLE]
        if kh:user.UnhookWindowsHookEx(kh)
        if mh:user.UnhookWindowsHookEx(mh)
    with _activity_lock:
        if not _activity_started:
            _activity_started=True
            threading.Thread(target=monitor,daemon=True).start()
    if not _activity_ready.wait(2) or not _activity_ok:
        raise ValueError('Le contrôle de saisie Windows est indisponible')
    return _activity_revision

def input_context():
    """Track target plus intervening physical keyboard/mouse input."""
    class LASTINPUTINFO(C.Structure):
        _fields_=[('cbSize',W.UINT),('dwTime',W.DWORD)]
    class GUITHREADINFO(C.Structure):
        _fields_=[('cbSize',W.DWORD),('flags',W.DWORD),('hwndActive',W.HWND),('hwndFocus',W.HWND),('hwndCapture',W.HWND),('hwndMenuOwner',W.HWND),('hwndMoveSize',W.HWND),('hwndCaret',W.HWND),('rcCaret',W.RECT)]
    api=C.WinDLL('user32',use_last_error=True)
    api.GetForegroundWindow.restype=W.HWND
    last=LASTINPUTINFO(C.sizeof(LASTINPUTINFO),0)
    gui=GUITHREADINFO();gui.cbSize=C.sizeof(gui)
    if not api.GetLastInputInfo(C.byref(last)) or not api.GetGUIThreadInfo(0,C.byref(gui)):
        raise ValueError('Impossible de vérifier la fenêtre active du PC')
    foreground=api.GetForegroundWindow()
    if not foreground: raise ValueError('Clique dans une zone de texte du PC')
    return (foreground,gui.hwndFocus,physical_activity())

def direct_events(previous, text):
    common=0
    while common<min(len(previous),len(text)) and previous[common]==text[common]: common+=1
    removed=previous[common:]
    # Editors disagree on how many backspaces erase an emoji/combining sequence.
    # Refuse ambiguous deletion rather than risk removing surrounding PC text.
    if any(ord(char)>0xFFFF or unicodedata.combining(char) or char in '\u200d\ufe0f\n\r\t' for char in removed):
        raise ValueError('Cette correction est ambiguë : vérifie le texte sur le PC. La prochaine saisie repartira automatiquement.')
    events=[]
    for _ in removed: events.extend([event(8),event(8,flags=2)])
    if text[common:]: events.extend(prepare({'type':'text','text':text[common:]}))
    return events

class State:
    def __init__(self, sink=inject, context=input_context, launcher=launch_application, pairing_path=None, clipboard_io=clipboard):
        self.lock=threading.RLock()
        self.sink=sink
        self.context=context
        self.launcher=launcher
        self.clipboard_io=clipboard_io
        self.enabled=True
        self.pairing_path=Path(pairing_path) if pairing_path else None
        self.token=None
        self.expiry=float('inf')
        self.draft=None
        self.new_code()
        if self.pairing_path and self.pairing_path.exists():
            try:
                saved=json.loads(self.pairing_path.read_text(encoding='utf-8'))
                digest=saved.get('token_hash')
                if isinstance(digest,str) and len(digest)==64 and all(char in '0123456789abcdef' for char in digest):self.token=digest
            except (ValueError,OSError,AttributeError):pass
    def new_code(self):
        self.code=f'{secrets.randbelow(100000000):08d}'
        self.deadline=time.monotonic()+300
        self.attempts=0
    def rotate(self):
        with self.lock:
            # Revoke on disk first; an I/O failure must not claim success.
            if self.pairing_path:self.pairing_path.unlink(missing_ok=True)
            self.new_code()
            self.token=None
            self.expiry=float('inf')
            self.draft=None
    def pair(self, code):
        with self.lock:
            if self.attempts>=10 or time.monotonic()>self.deadline or self.token:
                raise ValueError('Code expiré ou bloqué : renouvelle-le sur le PC.')
            self.attempts+=1
            if not isinstance(code,str) or not secrets.compare_digest(code,self.code):
                raise ValueError('Code incorrect')
            token=secrets.token_urlsafe(32)
            digest=hashlib.sha256(token.encode()).hexdigest()
            if self.pairing_path:
                self.pairing_path.parent.mkdir(exist_ok=True)
                temporary=self.pairing_path.with_suffix('.tmp')
                temporary.write_text(json.dumps({'version':1,'token_hash':digest}),encoding='utf-8')
                temporary.replace(self.pairing_path)
            self.token=digest
            self.expiry=float('inf')
            return token
    def command(self, token, data):
        with self.lock:
            if not isinstance(token,str) or not self.token or not secrets.compare_digest(hashlib.sha256(token.encode()).hexdigest(),self.token) or time.monotonic()>self.expiry:
                raise PermissionError('Appairage requis')
            if isinstance(data,dict) and data.get('type')=='status':
                return
            if not self.enabled:
                raise ValueError('Clavier en pause sur le PC')
            if isinstance(data,dict) and data.get('type')=='clipboard':
                action=data.get('action')
                if action not in ('read','write'): raise ValueError('Action presse-papiers inconnue')
                value=data.get('text')
                if action=='write' and (not isinstance(value,str) or len(value)>2000 or '\0' in value):
                    raise ValueError('Texte de 2 000 caractères maximum requis')
                result=self.clipboard_io(action,value)
                return {'text':result} if action=='read' else {'copied':True}
            if isinstance(data,dict) and data.get('type')=='media':
                action=data.get('action')
                if not isinstance(action,str) or action not in MEDIA: raise ValueError('Commande multimédia inconnue')
                vk=MEDIA[action]
                self.sink([event(vk,flags=1),event(vk,flags=3)])
                return
            if isinstance(data,dict) and data.get('type')=='app':
                name=data.get('app')
                if name not in ('browser','notepad','calculator','explorer','paint','discord'):
                    raise ValueError('Application non autorisée')
                if self.draft:self.draft['blocked']=True
                try:self.launcher(name)
                except OSError as exc:raise ValueError('Windows n’a pas pu ouvrir cette application.') from exc
                return
            if isinstance(data,dict) and data.get('type')=='direct':
                draft_id,base,value=data.get('draft'),data.get('base'),data.get('text')
                if not all(isinstance(x,str) for x in (draft_id,base,value)) or not 1<=len(draft_id)<=80 or max(len(base),len(value))>2000:
                    raise ValueError('Saisie directe invalide')
                current=self.context()
                # Opt-in for the automatic client; old native clients keep their strict protocol.
                if data.get('auto') is True and (self.draft is None and base or self.draft is not None and
                        (self.draft['id']!=draft_id or self.draft['blocked'] or base!=self.draft['text'] or current!=self.draft['context'])):
                    # Only a known appended suffix is safe at a new cursor. Never replay the old draft.
                    suffix=value[len(base):] if value.startswith(base) else ''
                    self.draft=None
                    if suffix:self.sink(prepare({'type':'text','text':suffix}))
                    return {'reset':True,'discardedCorrection':not value.startswith(base)}
                if self.draft is None or self.draft['id']!=draft_id:
                    if base: raise ValueError('Ouvre une nouvelle zone de saisie')
                    self.draft={'id':draft_id,'text':'','context':current,'blocked':False}
                draft=self.draft
                if draft['blocked'] or base!=draft['text']:
                    raise ValueError('Saisie désynchronisée : ouvre une nouvelle zone')
                if current!=draft['context']:
                    draft['blocked']=True
                    raise ValueError('Le curseur ou le clavier du PC a changé : ouvre une nouvelle zone sur l’iPad.')
                try:
                    events=direct_events(base,value)
                    stamp=None
                    if events:
                        stamp=self.sink(events)
                        if self.sink is inject: time.sleep(.025)
                    draft['text']=value
                    after=self.context()
                    if after!=current: raise ValueError('La fenêtre ou le clavier du PC a changé pendant la saisie')
                    draft['context']=after
                except Exception:
                    draft['blocked']=True
                    raise
                return
            if self.draft: self.draft['blocked']=True
            self.sink(prepare(data))

def handler(state, host):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def setup(self):
            super().setup()
            self.connection.settimeout(5)
        def reply(self,status,body,ctype='application/json; charset=utf-8',cookie=None):
            raw=body if isinstance(body,bytes) else json.dumps(body,ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type',ctype)
            self.send_header('Content-Length',str(len(raw)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; connect-src 'self'")
            if cookie: self.send_header('Set-Cookie',cookie)
            self.end_headers()
            self.wfile.write(raw)
        def allowed(self):
            return local(self.client_address[0]) and self.headers.get('Host')==host
        def do_GET(self):
            if not self.allowed(): return self.reply(403,{'error':'Accès local uniquement'})
            files={'/':('index.html','text/html; charset=utf-8'),'/extras.js':('extras.js','text/javascript; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/native-draft.js':('native-draft.js','text/javascript; charset=utf-8'),'/style.css':('style.css','text/css; charset=utf-8')}
            if self.path not in files: return self.reply(404,{'error':'Introuvable'})
            filename,ctype=files[self.path]
            self.reply(200,(ASSET_ROOT/filename).read_bytes(),ctype)
        def do_POST(self):
            if not self.allowed() or self.headers.get('Origin')!='https://'+host or self.headers.get('X-Keyboard')!='1':
                return self.reply(403,{'error':'Origine refusée'})
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=20000: raise ValueError('Commande trop longue')
                data=json.loads(self.rfile.read(size))
                if not isinstance(data,dict): raise ValueError('Commande invalide')
                if self.path=='/pair':
                    token=state.pair(data.get('code'))
                    return self.reply(200,{'ok':True},cookie=f'keyboard={token}; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=31536000')
                if self.path!='/command': return self.reply(404,{'error':'Introuvable'})
                from http.cookies import SimpleCookie
                cookies=SimpleCookie(self.headers.get('Cookie',''))
                token=cookies['keyboard'].value if 'keyboard' in cookies else ''
                result=state.command(token,data)
                self.reply(200,{'ok':True,**(result or {})},cookie=f'keyboard={token}; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=31536000')
            except PermissionError as exc: self.reply(401,{'error':str(exc)})
            except (ValueError,TypeError,KeyError) as exc: self.reply(400,{'error':str(exc)})
            except Exception: self.reply(500,{'error':'Échec de saisie Windows ou connexion interrompue'})
    return Handler

def certificate(ip, directory):
    directory.mkdir(exist_ok=True)
    keypath=directory/'server-key.pem'
    certpath=directory/'server.pem'
    # Keep the same identity for this address between launches.
    if certpath.exists() and keypath.exists():
        cert=x509.load_pem_x509_certificate(certpath.read_bytes())
        if ipaddress.ip_address(ip) in cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(x509.IPAddress) and cert.not_valid_after_utc>dt.datetime.now(dt.timezone.utc)+dt.timedelta(days=1):
            return certpath,keypath,cert.fingerprint(hashes.SHA256()).hex()
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Clavier iPad local')])
    now=dt.datetime.now(dt.timezone.utc)
    cert=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-dt.timedelta(minutes=5)).not_valid_after(now+dt.timedelta(days=365)).add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address(ip))]),False).add_extension(x509.BasicConstraints(ca=True,path_length=0),True).sign(key,hashes.SHA256()))
    keypath.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    certpath.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    (directory/'Clavier-iPad.cer').write_bytes(cert.public_bytes(serialization.Encoding.DER))
    return certpath,keypath,cert.fingerprint(hashes.SHA256()).hex()

def main():
    import companion_ui
    companion_ui.run(sys.modules[__name__])

if __name__=='__main__':
    if '--self-test' in sys.argv:
        import packaging_check
        packaging_check.run(sys.modules[__name__],Path(sys.argv[sys.argv.index('--self-test')+1]))
    else:main()
