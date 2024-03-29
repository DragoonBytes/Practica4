import requests
import urllib
import webbrowser
from socket import AF_INET, socket, SOCK_STREAM
import json
import helper

app_key = '0d5chasx4cc0mwx'
app_secret = 'el8k82hfxqc0x4d'
server_addr = "localhost"
server_port = 8090
redirect_uri = "http://" + server_addr + ":" + str(server_port)

class Dropbox:
    _access_token = ""
    _path = "/"
    _files = []
    _root = None
    _msg_listbox = None

    def __init__(self, root):
        self._root = root


    def local_server(self):
        # 8090. portuan entzuten dagoen zerbitzaria sortu
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind((server_addr, server_port))
        server_socket.listen(1)
        print("\tLocal server listening on port " + str(server_port))

        # nabitzailetik 302 eskaera jaso
        client_connection, client_address = server_socket.accept()
        eskaera = client_connection.recv(1024)
        print("\tRequest from the browser received at local server:")
        print (eskaera)

        # eskaeran "auth_code"-a bilatu
        lehenengo_lerroa = eskaera.decode('UTF8').split('\n')[0]
        aux_auth_code = lehenengo_lerroa.split(' ')[1]
        auth_code = aux_auth_code[7:].split('&')[0]


        # erabiltzaileari erantzun bat bueltatu
        http_response = "HTTP/1.1 200 OK\r\n\r\n" \
                        "<html>" \
                        "<head><title>Proba</title></head>" \
                        "<body>The authentication flow has completed. Close this window.</body>" \
                        "</html>"
        client_connection.sendall(http_response.encode(encoding="utf-8"))
        client_connection.close()
        server_socket.close()

        return auth_code


    def do_oauth(self):
        uri = 'https://www.dropbox.com/oauth2/authorize'
        params = {'response_type': 'code',
                  'client_id': app_key,
                  'redirect_uri': redirect_uri}
        params_encoded = urllib.parse.urlencode(params)

        #MANDAR AL NAVEGADOR LOS PARAMETROS PARA QUE LO ABRA UNA PESTAÑA
        webbrowser.open(uri + '?' + params_encoded)

        auth_code = self.local_server()
        print('auth_code -->: ' + auth_code)

        # Codigo de autorizacion para acceder al token
        uri = 'https://api.dropboxapi.com/oauth2/token'
        cabecera = {'Content-Type': 'application/x-www-form-urlencoded'}

        datos = {'code': auth_code,
                 'client_id': app_key,
                 'client_secret': app_secret,
                 'redirect_uri': redirect_uri,
                 'grant_type': 'authorization_code'}

        respuesta = requests.post(uri, headers=cabecera, data=datos, allow_redirects=False)


        status = respuesta.status_code
        print('Status: ' + str(status))

        #OBTENER LA PAGINA --> PASARLA A JSON --> EXTRAER ACCESS TOKEN
        content = respuesta.text
        content_json = json.loads(content)
        access_token = content_json['access_token']
        print('access_token --> ' + access_token)

        self._access_token = access_token
        self._root.destroy()

    def list_folder(self, msg_listbox):
        print("/list_folder")
        uri = 'https://api.dropboxapi.com/2/files/list_folder'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-list_folder

        if self._path == '/':
            path = ''
        else:
            path = self._path

        data = {'path': path}
        data_encoded = json.dumps(data)
        cabecera = {'Host': 'api.dropboxapi.com',
                    'Authorization': 'Bearer ' + self._access_token,
                    'Content-Type': 'application/json'}

        respuesta = requests.post(uri, headers=cabecera, data=data_encoded, allow_redirects=False)
        print('Status: ' + str(respuesta.status_code))

        print('Content: \n' + str(respuesta.text))
        contenido_json = json.loads(respuesta.text)

        self._files = helper.update_listbox2(msg_listbox, self._path, contenido_json)

    def transfer_file(self, file_path, file_data):
        print("/upload" + file_path)
        uri = 'https://content.dropboxapi.com/2/files/upload'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-upload
        dropbox_conf = {'path': file_path,
                        'mode': 'add',
                        'autorename': True,
                        'mute': False}

        dropbox_conf_json = json.dumps(dropbox_conf)

        cabecera = {'Host': 'content.dropboxapi.com',
                    'Authorization': 'Bearer ' + self._access_token,
                    'Content-Type': 'application/octet-stream',
                    'Dropbox-API-Arg': dropbox_conf_json}

        respuesta = requests.post(uri, headers=cabecera, data=file_data, allow_redirects=False)
        print("\n ++++++ respuesta +++++")
        print(str(respuesta.status_code) + " " + respuesta.reason)

    def delete_file(self, file_path):
        print("/delete_file" + file_path)
        uri = 'https://api.dropboxapi.com/2/files/delete_v2'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-delete

        cabecera = {'Host': 'api.dropboxapi.com',
                    'Authorization': 'Bearer ' + self._access_token,
                    'Content-Type': 'application/json'}

        print(file_path)
        data = {'path': file_path}
        data_encoded = json.dumps(data)

        respuesta = requests.post(uri, headers=cabecera, data=data_encoded, allow_redirects=False)
        print("\n ++++++ respuesta +++++")
        print(str(respuesta.status_code) + " " + respuesta.reason)

    def create_folder(self, path):
        print("/create_folder" + path)
        uri = 'https://api.dropboxapi.com/2/files/delete_v2'
       # https://www.dropbox.com/developers/documentation/http/documentation#files-create_folder

        cabecera = {'Host': 'api.dropboxapi.com',
                    'Authorization': 'Bearer ' + self._access_token,
                    'Content-Type': 'application/json'}

        data = {'autorename': False,
                'path': path}
        data_encoded = json.dumps(data)

        respuesta = requests.put(uri, headers=cabecera, data=data_encoded, allow_redirects=False)
        print("\n ++++++ respuesta +++++")
        print(str(respuesta.status_code) + " " + respuesta.reason)

        Dropbox.transfer_file(self, path+"/kk.txt", '')
        Dropbox.delete_file(self, path + "/kk.txt")