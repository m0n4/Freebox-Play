# coding: utf-8
import hashlib
import hmac
import json
import sys
import os
import threading
import socket
import time
import requests          # pip install requests
import js2py             # pip install js2py
import magic             # pip install python-magic-bin
from yaml import load    # pip install pyyaml
from yaml import CLoader as Loader
from tkinter import Tk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename
import tkinter.simpledialog
from http.server import HTTPServer, SimpleHTTPRequestHandler

def getChallenge():
    r = s.get(url+'login', headers=headers)
    j = json.loads(r.text)
    parts = j['result']['challenge']
    password_salt = j['result']['password_salt']
    challenge = ''
    for letter in parts:
        challenge += js2py.eval_js(letter)
    return(password_salt, challenge)

def sendPassword(url, password_salt, challenge, password):
    sha1 = hashlib.sha1((password_salt+password).encode('utf-8')).hexdigest()
    if (sys.version_info > (3, 0)):
        sha1 = bytes(sha1, 'utf-8')
        challenge = bytes(challenge, 'utf-8')
    mac = hmac.new(sha1, challenge, hashlib.sha1).hexdigest()
    data = {"password": mac}
    r = s.post(url+'login', data=data, headers=headers)
    return(r.status_code == 200)

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def start_server():
    httpd = HTTPServer(('', int(port)), SimpleHTTPRequestHandler)
    httpd.serve_forever()

def play(url, file):
    filename = os.path.basename(file)
    folder = os.path.dirname(file)    
    os.chdir(folder)
    typeMime = magic.from_file(file, mime=True)
    daemon = threading.Thread(name='daemon_server', target=start_server)
    daemon.setDaemon(True) 
    daemon.start()
    time.sleep(3)
    dest = 'http://{ip}:{port}/{file}'.format(ip=get_ip(), port=port, file=filename)
    data = { 'url': dest, 'type': typeMime }
    r = s.post(url+'player/1/api/v6/control/open', headers=headers, json=data)
    j = json.loads(r.text)
    if j['success'] == False: failed('Une erreur est survenue, essayer de redémarrer le Freebox Player')
    else:
        Tk().withdraw()
        tkinter.messagebox.showinfo(title='Freebox Play', message='Fermez cette fenêtre à la fin de la lecture')

def youtube(url, link):
    data = { "url": link }
    r = s.post('http://mafreebox.freebox.fr/api/v8/player/1/api/v6/control/open', headers=headers, json=data)
    j = json.loads(r.text)
    if j['success'] == False: failed('Une erreur est survenue, essayer de redémarrer le Freebox Player')

def failed(msg):
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Freebox Play', message=msg)
    sys.exit(0)

def config():
    try:
        cfg = load(open("config.txt", "r"), Loader=Loader)
        password = cfg["password"]
        port = cfg["port"]
    except:
        password = 'CHANGE ME'
        port = '9090' 
    if password.encode('utf-8').hex() == '4348414e4745204d45':
        Tk().withdraw()
        password = tkinter.simpledialog.askstring("Password", 'Mot de passe de l\'interface web de la Freebox :')
    return(password, port)

if __name__ == '__main__':
    password, port = config()
    s = requests.session()
    url = 'http://mafreebox.freebox.fr/api/v8/'
    headers = {'X-FBX-FREEBOX0S': '1', 'X-Requested-With': 'XMLHttpRequest'}
    password_salt, challenge = getChallenge()
    success = sendPassword(url, password_salt, challenge, password)
    if success:
        Tk().withdraw()
        MsgBox = tkinter.messagebox.askquestion ('Freebox Play','Lire du contenu local (image, musique, vidéo) ?',icon = 'question')
        if MsgBox == 'yes':
            file = askopenfilename()
            play(url, file) 
        else:
            link = tkinter.simpledialog.askstring("Youtube / Web", 'Lien :'+' '*100)
            youtube(url, link)       
    else:
        failed('Echec, vérifiez le mot de passe')


