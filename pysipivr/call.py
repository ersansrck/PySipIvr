import uuid,os,time,socket
from twisted.internet import reactor,protocol,ssl

from typing import Callable,Dict,List,Union,Optional

from .TransportConfig import RTCP,RTP
from .packetMng import REPORTER,SIPMesagge,SDP
from .enumTypes import MediaTypes,PayloadTypes,CallState,CallEndState
from .Stream import AUDIOSTREAMER
from .account import Account


 








class CallParam:
    MediaPayloads=[val for val in PayloadTypes._member_map_.values()]
    def __init__(self) -> None: 
        self.callUid=f"{uuid.uuid4()}" 
        self.CallFromTagValue=str(uuid.uuid4())
        self.callSessionId=int.from_bytes(os.urandom(4), 'big')
        self.callSSRC=int.from_bytes(os.urandom(4), 'big')
        self.callCNAME=str(uuid.uuid4())
        
        
        self.CallTargetUri=None
        self.CallTargetContactUri=None
        self.CallRoutes=[]
        
        self.LocalRTCPIp=None
        self.LocalRTCPPort=None
        self.TargetRTCPIp=None
        self.TargetRTCPPort=None
        self.LocalRTPIp=None
        self.LocalRTPPort=None
        self.TargetRTPIp=None
        self.TargetRTPPort=None

        self.CallEndState:CallEndState=None
        self.CallDinamicState:CallState=CallState.CREATE
        
        self.STREAM:AUDIOSTREAMER=AUDIOSTREAMER() 
        self.Reporter:REPORTER=REPORTER(self.callSSRC,self.callCNAME)
        self.CallCodec:dict=self.setCallCodec(self.MediaPayloads)
        
    def setCallSDP(self,SDPOBJ:SDP):
        keyToGet=lambda dics,key1,key2:dics.get(key1) and dics.get(key1).get(key2) or None
        SupportsMedias=list(filter(lambda medvary:medvary["type"]==self.STREAM.MediaType,SDPOBJ.media) )
        TRTPIP,TRTPPORT,TRTCPIP,TRTCPPORT=None,None,None,None
        TRTPIP=keyToGet(SDPOBJ.__dict__,"connection","ip") or TRTPIP 
        for media in SupportsMedias:
            TRTPIP=TRTPIP or keyToGet(media,"connection","ip")  
            TRTPPORT=TRTPPORT or media.get("port")
            if media.get("rtcp"):
                TRTCPIP=TRTCPIP or keyToGet(media,"rtcp","address")
                TRTCPPORT=TRTCPPORT or keyToGet(media,"rtcp","port")
        
            self.CallCodec=self.setCallCodec(filter(lambda x:x,map(lambda tid:PayloadTypes.get(int(tid)),media.get("payloads").split())))
        TRTPPORT=TRTPPORT and int(TRTPPORT) or TRTPPORT
        TRTCPPORT=TRTCPPORT and int(TRTCPPORT) or TRTPPORT and TRTPPORT+1
        TRTCPIP=TRTCPIP or TRTPIP
        self.setTargetAddr(TRTPIP,TRTPPORT,TRTCPIP,TRTCPPORT)  
    def setCallCodec(self,codecs):
        CallCodec={}
        for codec in codecs: 
            if codec.mType.value not in CallCodec.keys():
                CallCodec[codec.mType.value]=[codec]
            else:
                CallCodec[codec.mType.value].append(codec)
        return CallCodec
    def setLocalAddr(self,RTPIP,RTPPORT,RTCPIP=None,RTCPPORT=None):
        self.LocalRTPIp=RTPIP
        self.LocalRTPPort=RTPPORT
        self.LocalRTCPIp=RTCPIP or self.LocalRTPIp
        self.LocalRTCPPort=RTCPPORT or self.LocalRTPPort+1  
    def setTargetAddr(self,RTPIP,RTPPORT,RTCPIP=None,RTCPPORT=None):
        self.TargetRTPIp=RTPIP
        self.TargetRTPPort=RTPPORT
        self.TargetRTCPIp=RTCPIP or RTPIP
        self.TargetRTCPPort=RTCPPORT or RTPPORT+1 



    def setTargetUri(self,TargetContactUri=None,TargetToUri=None): 
        if TargetToUri:
            self.CallTargetUri=TargetToUri
        if TargetContactUri:
            self.CallTargetContactUri=TargetContactUri
    @staticmethod
    def getsiptargetinvalue(value):
        if value:
            return value.split("<",1)[-1].split(">",1)[0]
    @property
    def getTargetPath(self):
        
        return self.getsiptargetinvalue(self.CallTargetContactUri) or self.getsiptargetinvalue(self.CallTargetUri)
    @property
    def getTargetDisplayName(self): 
        return self.getTargetPath.split("sip:",1)[-1].split("@",1)[0].split(":",1)[0]
    
    @property
    def getSSRC(self):
        return {'id':self.callSSRC , 'attribute': 'cname', 'value': self.callCNAME}
    @property
    def TargetRTCPAddr(self):
        return (self.TargetRTCPIp,self.TargetRTCPPort)
    @property
    def TargetRTPAddr(self):
        return (self.TargetRTPIp,self.TargetRTPPort)  
    @property
    def callIsActive(self) -> bool:
        return self.CallDinamicState==CallState.START 
    @property
    def callIsStarted(self):
        return self.callIsActive or self.CallDinamicState in [CallState.TRYING,CallState.RINGING,CallState.WAITING]
        
    @property
    def getMediaSDPS(self) -> list:
        kwargst_to_dict=lambda **x:x
        IpVersion=lambda Ip:4 if len(Ip.split("."))==4 else 6

        mediaList=[
            kwargst_to_dict(
                type=self.STREAM.MediaType.value,
                port=self.LocalRTPPort,
                protocol=self.STREAM.MediaProtocol,
                direction=self.STREAM.MediaTranportType,
                
                rtp=[val.getPayload for val in  self.getSetedUseMediaCodec],
                fmtp=[val.getPayloadFmtp for val in  self.getSetedUseMediaCodec if val.getPayloadFmtp],
                payloads=" ".join([str(val.value) for val in self.getSetedUseMediaCodec]),
                connection=kwargst_to_dict(
                    ip=self.LocalRTPIp,
                    version=IpVersion(self.LocalRTPIp)), 
                rtcp=kwargst_to_dict(
                    port=int(self.LocalRTCPPort),
                    netType="IN",
                    ipVer=IpVersion(self.LocalRTCPIp),
                    address=self.LocalRTCPIp),
                ssrcs=[self.getSSRC]
            )
        ]  
        return mediaList
    @property
    def isSetMediaCodec(self):
        return sum(map(len,self.CallCodec.values()))!=len(self.CallCodec.keys())
    @property
    def getSetedUseMediaCodec(self):
        if sum(map(len,self.CallCodec.values()))!=len(self.MediaPayloads): 
            return [codecs[0] for codecs in self.CallCodec.values()] 
        return self.MediaPayloads 
    @property
    def getAudioPayload(self):
        if self.CallCodec.get(MediaTypes.AUDIO.value):
            return self.CallCodec.get(MediaTypes.AUDIO.value)[0]












class Call:
    def __init__(self,account:Account,targetUri) -> None:  
        self.ConnectState=True
        self.Account=account
        self.CallParam=CallParam()
        self.CallParam.setTargetUri(TargetToUri=targetUri)
        self.CallParam.setLocalAddr(RTPIP=self.Account.AccTp.ServerIp,RTPPORT=self.Account.AccTp.randomPort) 
        self.RTP=RTP(self.CallParam)
        self.RTCP=RTCP(self.CallParam)
        self.RTP.datagramReceived=self.MediaReceiver 
        self.RTCP.datagramReceived=self.ReportReceiver 

    def makeCall(self):
        if not self.CallParam.callIsActive:   
            self.CallParam.CallDinamicState=CallState.START
            self.RTCP.sender(self.CallParam.Reporter.SendReceiverReport,self.CallParam.TargetRTCPAddr) 
            self.RTCP.sender(self.CallParam.Reporter.SendReceiverReport,self.CallParam.TargetRTCPAddr) 
            reactor.callInThread(self.MediaSender) 
            reactor.callInThread(self.ReportSender) 
            self.callStart()
            
            
    def endCall(self):
        if self.ConnectState:
            self.ConnectState=False
            if set(self.CallParam.TargetRTCPAddr)!={None}:
                self.RTCP.sender(self.CallParam.Reporter.getGoodBye,self.CallParam.TargetRTCPAddr)
                self.RTCP.sender(self.CallParam.Reporter.getGoodBye,self.CallParam.TargetRTCPAddr) 
                self.callHangup()
            self.RTCP.closeConnect()
            self.RTP.closeConnect()
            self.CallParam.CallDinamicState=CallState.FINISH
        

    def MediaReceiver(self,data,addr):
        if self.CallParam.callIsActive:#callstat 
            pars=self.CallParam.Reporter.parseRTP(data)
            if not pars:
                return
            PyTypeMedType,Data=pars
            if PyTypeMedType==self.CallParam.STREAM.MediaType:
                self.CallParam.STREAM.write(Data)
            elif PyTypeMedType==MediaTypes.DTMF:  
                if self.CallParam.STREAM.isWithIvr:
                    self.CallParam.STREAM.setDTMFIVRStream(str(Data))
                else:
                    self.Dtmf(str(Data))
    
    def MediaSender(self):
        PayloadObj=self.CallParam.getAudioPayload 
        if not PayloadObj:
            self.CallParam.CallEndState=CallEndState.SELFCLOSE
            self.CallParam.CallDinamicState=CallState.CLOSE 
            return
        self.CallParam.STREAM.loadStream(chanell=PayloadObj.channel,rate=PayloadObj.rate,width=PayloadObj.samplewidth)
        while self.CallParam.callIsActive: 
            pcmarray=self.CallParam.STREAM.read(PayloadObj.PTIMECHUNKS)
            if not pcmarray:
                self.CallParam.CallEndState=CallEndState.SELFCLOSE 
                self.CallParam.CallDinamicState=CallState.CLOSE 
                break
            packet=self.CallParam.Reporter.getRTP(False,PayloadObj,pcmarray)
            self.RTP.sender(packet,self.CallParam.TargetRTPAddr)
            time.sleep(PayloadObj.PTIME/1000)  
        
    def ReportSender(self):
        while self.CallParam.callIsActive: 
            self.RTCP.sender(self.CallParam.Reporter.SendSenderReport,self.CallParam.TargetRTCPAddr)
            time.sleep(3) 
    def ReportReceiver(self,data,addr):
        self.CallParam.Reporter.parseRTCP(data) 


    def callStart(self):
        """
        """
    def callHangup(self):
        """
        """  
    def Dtmf(self,Value): 
        """
        
        """




