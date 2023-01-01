import socketio

class MyCustomNamespace(socketio.ClientNamespace):
    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    def on_connected(self, data):
        self.emit('update', data)

    # def emitt(self,data):
    #     self.emit('updateutterance',data)

    # def disconnecttt(self):
    #     self.disconnect()




class SocketToba:
    def __init__(self,phonenumber):
        self.host='http://localhost:8080'
        self.namespaceupdate=['/api/v1']
        self.sio=socketio.Client(logger=True)
        self.updatequery='%s?phone=%s' % (self.host,phonenumber)
        self.sclient=MyCustomNamespace('/api/v1')


    def connect(self):
        self.sio.connect(self.updatequery,namespaces=self.namespaceupdate)

    def register(self):
        self.sio.register_namespace(self.sclient)

    def disconnectt(self):
        self.sclient.disconnect()

    def updateutterances(self,id):
        self.sclient.emit('updateutterance',{'id':id})


# app=SocketToba(37498000662)
# app.connect()
# app.register()
# app.disconnectt()
    



