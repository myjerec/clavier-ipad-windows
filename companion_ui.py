"""Native, dependency-free Windows companion dashboard."""
import json
import socket
import ssl
import sys
import threading
import time
import tkinter as tk
import qrcode
import queue
import pystray
from PIL import Image, ImageDraw
from tkinter import ttk, messagebox


def run(app):
    bg, panel, border = '#10151e', '#1b2432', '#344258'
    white, muted, lime = '#f3f6fc', '#afbdd0', '#c5ed82'
    root = tk.Tk()
    root.title('Clavier iPad · Compagnon Windows')
    root.geometry('800x760')
    root.minsize(760, 740)
    root.configure(bg=bg)
    root.option_add('*Font', '{Segoe UI} 11')
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('TCombobox', padding=8, fieldbackground=panel, background=border,
                    foreground=white, arrowcolor=white)
    style.map('TCombobox', fieldbackground=[('readonly', panel)],
              foreground=[('readonly', white)])
    state = app.State(pairing_path=app.ROOT/'private'/'pairing.json')
    server = None
    fingerprint = ''
    ips = sorted({r[4][0] for r in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
                  if app.local(r[4][0]) and not r[4][0].startswith('127.')}) or ['127.0.0.1']
    address = tk.StringVar(value=ips[0])
    config = app.ROOT/'private'/'connection.json'
    try:
        remembered = json.loads(config.read_text(encoding='utf-8')).get('ip')
        if remembered in ips:
            address.set(remembered)
    except (OSError, ValueError, AttributeError):
        pass

    def label(parent, text='', size=11, color=white, bold=False, **kw):
        return tk.Label(parent, text=text, bg=parent.cget('bg'), fg=color,
                        font=('Segoe UI', size, 'bold' if bold else 'normal'), anchor='w', **kw)

    def button(parent, text, command, primary=False):
        return tk.Button(parent, text=text, command=command, bg=lime if primary else border,
                         fg=bg if primary else white, activebackground='#d8f5ac' if primary else '#465976',
                         activeforeground=bg if primary else white, disabledforeground=muted,
                         relief='flat', bd=0, padx=18, pady=12, cursor='hand2',
                         highlightthickness=2, highlightbackground=parent.cget('bg'),
                         highlightcolor=lime, font=('Segoe UI', 11, 'bold'))

    outer = tk.Frame(root, bg=bg, padx=28, pady=22)
    outer.pack(fill='both', expand=True)
    header = tk.Frame(outer, bg=bg)
    header.pack(fill='x')
    tray_events = queue.SimpleQueue()
    tray_ready = threading.Event()
    hidden_dialogs = []

    def restore_window():
        root.deiconify()
        root.lift()
        root.focus_force()
        for dialog in hidden_dialogs:
            if dialog.winfo_exists():
                dialog.deiconify()
        hidden_dialogs.clear()

    def hide_window():
        if not tray_ready.is_set() or not tray.visible:
            messagebox.showinfo('Icône indisponible',
                                'L’icône près de l’horloge n’est pas encore disponible. Réessaie dans un instant.', parent=root)
            return
        for child in root.winfo_children():
            if isinstance(child, tk.Toplevel) and child.state() != 'withdrawn':
                hidden_dialogs.append(child)
                child.withdraw()
        root.withdraw()

    button(header, 'Masquer près de l’horloge', hide_window).pack(side='right', anchor='n')
    label(header, 'CLAVIER iPAD', 10, lime, True).pack(anchor='w')
    label(header, 'Ton clavier, sans fil.', 27, bold=True).pack(anchor='w', pady=(4, 0))
    label(header, 'Le compagnon de ton iPad sur Windows.', color=muted).pack(anchor='w', pady=(3, 18))
    banner = tk.Frame(outer, bg=panel, padx=16, pady=12)
    banner.pack(fill='x', pady=(0, 16))
    badge = label(banner, '●  Prêt à démarrer', 12, lime, True)
    badge.pack(side='left')
    label(banner, 'HTTPS · Réseau local', 10, muted).pack(side='right')

    def card(title):
        frame = tk.Frame(outer, bg=panel, padx=20, pady=16,
                         highlightthickness=1, highlightbackground=border)
        frame.pack(fill='x', pady=(0, 14))
        label(frame, title, 10, muted, True).pack(anchor='w')
        return frame

    connection = card('01   CONNEXION')
    label(connection, 'Ouvre cette adresse dans Safari sur l’iPad.', color=muted).pack(anchor='w', pady=(8, 10))
    row = tk.Frame(connection, bg=panel)
    row.pack(fill='x')
    link = tk.StringVar(value='Connexion arrêtée')
    entry = tk.Entry(row, textvariable=link, state='readonly', readonlybackground=panel,
                     fg=white, relief='flat', bd=0, font=('Segoe UI', 18, 'bold'))
    entry.pack(side='left', fill='x', expand=True, padx=(0, 12), ipady=10)

    def copy_address():
        if server:
            root.clipboard_clear()
            root.clipboard_append(link.get())
            copy_btn.configure(text='Copié !')
            root.after(1800, lambda: copy_btn.configure(text='Copier'))

    copy_btn = button(row, 'Copier', copy_address)
    copy_btn.pack(side='right')

    def show_qr():
        if not server:
            return
        dialog = tk.Toplevel(root)
        dialog.title('Scanner avec ton iPad')
        dialog.configure(bg=bg, padx=28, pady=24)
        dialog.transient(root)
        dialog.resizable(False, False)
        label(dialog, 'Scanne et ouvre le clavier.', 21, bold=True).pack(anchor='w')
        label(dialog, 'Ouvre Appareil photo sur ton iPad, puis vise ce QR code.',
              color=muted).pack(anchor='w', pady=(8, 20))
        qr = qrcode.QRCode(border=4, error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(link.get())
        qr.make(fit=True)
        matrix = qr.get_matrix()
        bitmap = tk.PhotoImage(width=len(matrix), height=len(matrix))
        bitmap.put(' '.join('{'+' '.join('#000000' if cell else '#ffffff' for cell in row)+'}'
                            for row in matrix))
        rendered = bitmap.zoom(max(6, 300//len(matrix)))
        picture = tk.Label(dialog, image=rendered, bg='white', bd=0)
        picture.image = rendered
        picture.pack(pady=(0, 16))
        label(dialog, link.get(), 14, lime, True).pack(anchor='center')
        label(dialog, 'Même Wi-Fi que le PC · saisis ensuite le code d’appairage.\n'
              'Le QR code ouvre l’adresse ; il ne remplace pas l’appairage\n'
              'ni la configuration du certificat HTTPS.', color=muted,
              justify='center').pack(pady=(12, 16))
        button(dialog, 'Fermer', dialog.destroy).pack(anchor='e')

    qr_btn = button(connection, 'Connecter mon iPad avec un QR code', show_qr, True)
    qr_btn.pack(fill='x', pady=(12, 0))
    pairing = card('02   APPAIRAGE')
    code_label = label(pairing, 'En attente', 28, lime, True)
    code_label.pack(anchor='w', pady=(6, 0))
    hint = label(pairing, 'Démarre la connexion pour afficher ton code.', color=muted)
    hint.pack(anchor='w', pady=(4, 0))
    actions = tk.Frame(outer, bg=bg)
    actions.pack(fill='x', pady=(2, 10))
    actions.columnconfigure((0, 1), weight=1)

    def update():
        running = server is not None
        badge.configure(text='●  En pause · frappes bloquées' if running and not state.enabled else
                        '●  Prêt à recevoir les frappes' if running else '●  Connexion arrêtée',
                        fg='#ffd28a' if running and not state.enabled else lime if running else muted)
        main_btn.configure(text=('Mettre en pause' if state.enabled else 'Reprendre la saisie')
                           if running else 'Démarrer la connexion')
        copy_btn.configure(state='normal' if running else 'disabled')
        qr_btn.configure(state='normal' if running else 'disabled')
        reset_btn.configure(state='normal' if running else 'disabled')
        if running and state.token:
            code_label.configure(text='iPad mémorisé', fg=lime)
            hint.configure(text='L’appairage est conservé pour les prochaines connexions.')
        elif running:
            left = max(0, int(state.deadline-time.monotonic()))
            raw = str(state.code)
            code_label.configure(text=f'{raw[:4]}  {raw[4:]}' if left else 'Code expiré', fg=lime if left else '#ffd28a')
            hint.configure(text=f'Saisis ce code sur l’iPad · valable {left//60}:{left%60:02d}.' if left else
                           'Clique sur « Nouvel appairage » pour obtenir un code.')

    def start():
        nonlocal server, fingerprint
        candidate = None
        try:
            ip = address.get()
            cert, key, fingerprint = app.certificate(ip, app.ROOT/'private')
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.load_cert_chain(cert, key)
            candidate = app.ThreadingHTTPServer((ip, app.PORT), app.handler(state, f'{ip}:{app.PORT}'))
            candidate.socket = context.wrap_socket(candidate.socket, server_side=True)
            threading.Thread(target=candidate.serve_forever, daemon=True).start()
            server = candidate
            try:
                config.write_text(json.dumps({'ip': ip}), encoding='utf-8')
            except OSError:
                pass
            link.set(f'https://{ip}:{app.PORT}')
        except Exception as exc:
            if candidate:
                candidate.server_close()
            messagebox.showerror('Connexion impossible', str(exc), parent=root)
        update()

    def toggle():
        if server is None:
            start()
        else:
            with state.lock:
                state.enabled = not state.enabled
            update()

    def reset_pairing():
        if state.token and not messagebox.askyesno('Nouvel appairage',
                'L’iPad mémorisé sera déconnecté. Tu devras saisir le nouveau code pour le reconnecter.', parent=root):
            return
        try:
            state.rotate()
            update()
        except OSError as exc:
            messagebox.showerror('Appairage impossible', str(exc), parent=root)

    main_btn = button(actions, 'Démarrer la connexion', toggle, True)
    main_btn.grid(row=0, column=0, sticky='ew', padx=(0, 6))
    reset_btn = button(actions, 'Nouvel appairage', reset_pairing)
    reset_btn.grid(row=0, column=1, sticky='ew', padx=(6, 0))

    def settings():
        dialog = tk.Toplevel(root)
        dialog.title('Réseau et connexion')
        dialog.configure(bg=bg, padx=24, pady=24)
        dialog.transient(root)
        dialog.resizable(False, False)
        label(dialog, 'Réseau et connexion', 20, bold=True).pack(anchor='w')
        label(dialog, 'Adresse Wi-Fi / Ethernet de ce PC', color=muted).pack(anchor='w', pady=(20, 8))
        selected_address = tk.StringVar(value=address.get())
        ttk.Combobox(dialog, textvariable=selected_address, values=ips, width=38,
                     state='readonly').pack(fill='x')
        label(dialog, 'Choisis le réseau partagé avec ton iPad.\nAppliquer redémarre la connexion locale.',
              color=muted, justify='left').pack(anchor='w', pady=12)
        label(dialog, 'Empreinte SHA-256 du certificat', 10, muted).pack(anchor='w', pady=(10, 6))
        label(dialog, fingerprint or 'Disponible après le démarrage.', 10,
              wraplength=440, justify='left').pack(anchor='w')
        def apply_network():
            nonlocal server
            address.set(selected_address.get())
            if server:
                server.shutdown()
                server.server_close()
                server = None
            dialog.destroy()
            start()
        button(dialog, 'Appliquer', apply_network, True).pack(anchor='e', pady=(20, 0))

    footer = tk.Frame(outer, bg=bg)
    footer.pack(fill='x', side='bottom')
    button(footer, 'Réseau et détails', settings).pack(side='right')
    label(footer, 'Les frappes vont dans la fenêtre active du PC.\nMême masqué, le compagnon reste connecté.',
          10, muted, justify='left').pack(side='left')

    def refresh():
        update()
        root.after(1000, refresh)

    if ('--start' in sys.argv or getattr(sys, 'frozen', False)) and '--no-start' not in sys.argv:
        if '--start' in sys.argv:
            index = sys.argv.index('--start')
            if index+1 < len(sys.argv) and sys.argv[index+1] in ips:
                address.set(sys.argv[index+1])
        root.after(200, start)
    icon_image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon_image)
    draw.rounded_rectangle((3, 10, 61, 54), radius=9, fill=bg, outline=lime, width=3)
    for y in (20, 30):
        for x in (12, 23, 34, 45):
            draw.rounded_rectangle((x, y, x+6, y+5), radius=1, fill=lime)
    draw.rounded_rectangle((17, 41, 47, 45), radius=2, fill=lime)
    tray = pystray.Icon('Clavier-iPad', icon_image, 'Clavier iPad · Compagnon Windows',
                        pystray.Menu(
                            pystray.MenuItem('Afficher le compagnon', lambda: tray_events.put('show'), default=True),
                            pystray.MenuItem('Masquer le compagnon', lambda: tray_events.put('hide')),
                            pystray.Menu.SEPARATOR,
                            pystray.MenuItem('Quitter et couper la connexion', lambda: tray_events.put('quit'))))

    def tray_setup(icon):
        icon.visible = True
        tray_ready.set()

    def poll_tray():
        while not tray_events.empty():
            event = tray_events.get()
            if event == 'quit':
                root.destroy()
                return
            if event == 'show':
                restore_window()
            elif event == 'hide':
                hide_window()
        # If Explorer loses the tray icon, never leave an inaccessible window.
        if root.state() == 'withdrawn' and not tray.visible:
            restore_window()
        root.after(100, poll_tray)

    tray.run_detached(setup=tray_setup)
    refresh()
    poll_tray()
    try:
        root.mainloop()
    finally:
        tray.stop()
    if server:
        server.shutdown()
        server.server_close()
