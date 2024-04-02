from twisted.internet import reactor,protocol,ssl
import dns.resolver,socket
from typing import Callable
 
TRANSPORT_UDP="UDP"
TRANSPORT_TCP="TCP"


class UDP(protocol.DatagramProtocol):
    def datagramReceived(self,*args,**kwargs):
        pass
    def sender(self,data,addr):
        self.transport.write(data,addr)
    def closeConnect(self):
        if self.transport:
            self.transport.stopListening()
class TCP(protocol.Protocol):
    def dataReceived(self,*args,**kwargs):
        pass
    def sender(self,data,*args,**kwargs):
        self.transport.write(data)
    def closeConnect(self):
        if self.transport:
            self.transport.stopListening()

class RTCP(protocol.DatagramProtocol):
    def __init__(self,param:Callable) -> None:
        reactor.listenUDP(param.LocalRTCPPort,self) 
    def startProtocol(self):
        print(self)
    def datagramReceived(self,*args,**kwargs):
        pass
    def sender(self,data,addr):
        self.transport.write(data,addr)
    def closeConnect(self):
        if self.transport:
            self.transport.stopListening()
        
class RTP(protocol.DatagramProtocol):
    def __init__(self,param:Callable) -> None: 
        reactor.listenUDP(param.LocalRTPPort,self) 
    def startProtocol(self):
        print(self)
    def datagramReceived(self,*args,**kwargs):
        pass
    def sender(self,data,addr):
        self.transport.write(data,addr)
    def closeConnect(self):
        if self.transport:
            self.transport.stopListening()



class Transport(UDP,TCP):
    def __init__(self,TpType,serverIp=None,serverPort=None) -> None:
        super().__init__()
        self.TpType=TpType
        self.ServerIp=serverIp or self.get_local_ip
        self.ServerPort=serverPort or self.randomPort
        self.protocol=None 
    def setReceiver(self,recvFunc):
        if self.TpType==TRANSPORT_UDP:
            self.datagramReceived=recvFunc
        elif self.TpType==TRANSPORT_TCP:
            self.dataReceived=recvFunc
    def sender(self,data,*addr):
        if self.TpType==TRANSPORT_TCP:
            self.transport.write(data)
        elif self.TpType==TRANSPORT_UDP:
            self.transport.write(data,addr)
    def connect(self):
        if self.TpType==TRANSPORT_UDP:
            reactor.listenUDP(self.ServerPort,self) 
        elif self.TpType==TRANSPORT_TCP:
            reactor.listenTCP(self.ServerPort,self)

    def close(self):
        self.transport.stopListening() 

    @property
    def getVia(self):
        return f"{self.TpType} {self.getContact}"
    @property
    def getContact(self):
        return f"{self.ServerIp}:{self.ServerPort}"
    
    @staticmethod
    def domainToIp(domain):
        try:return list(dns.resolver.resolve(domain, 'A'))[0].address
        except Exception as e: return  
    @property
    def randomPort(self): 
        sock = socket.socket()
        sock.bind(('', 0))
        return sock.getsockname()[1]
    @property
    def get_local_ip(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Bu adres üzerinde herhangi bir gerçek bağlantı kurulmaz
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]