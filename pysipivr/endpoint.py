from .packetMng import SIPMesagge
from .TransportConfig import TRANSPORT_UDP, Transport
from .UaClient import Ua
from .account import Account
from .call import Call
from .enumTypes import AccountRegState, CallState,MethodNames,CallEndState
from twisted.internet import reactor,protocol,ssl
from twisted.internet.error import ReactorNotRunning


import logging,time,signal




class LogConfig:
    def __init__(self, log_level=logging.DEBUG):
        self.log_level = log_level
        
        # Logger oluşturma
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.log_level)
        
        # Çıktıya log mesajlarını yazdırmak için bir StreamHandler oluşturma
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(self.log_level)
        
        # Log biçimi belirleme
        formatter = logging.Formatter('[%(asctime)s]:[%(levelname)s]\t-\t[%(message)s]')
        stream_handler.setFormatter(formatter)
        
        # Logger'a stream_handler ekleme
        self.logger.addHandler(stream_handler)
        
    def debug(self, message):
        self.logger.debug(message)
        
    def info(self, message):
        self.logger.info(message)
        
    def warning(self, message):
        self.logger.warning(message)
        
    def error(self, message):
        self.logger.error(message)
        
    def critical(self, message):
        self.logger.critical(message)
        
        
        
        
        
        




        
        
        
        
        
        
class Endpoint:
                    
    def __init__(self) -> None: 
        self.StartedLib=False
        self.destroyedLib=False
        self.handlePerTime=100
        self.MaxCallCount=5
        
        self.libUa:Ua=Ua()
        self.LogConfig:LogConfig=LogConfig()
        self.Transport:Transport=None
        
        
        
    def sleep(self):
        time.sleep(self.handlePerTime/1000)
        
        
    def createTransport(self,Transport:Transport):
        Transport.setReceiver(self.response)
        Transport.connect()
        self.Transport=Transport 
        self.LogConfig.debug(f"{self.Transport.ServerIp}:{self.Transport.ServerPort} bağlantı noktası {self.Transport.TpType} oluşturuldu")


    def response(self,data,*addr):   
        print(data.decode())
        response=SIPMesagge.createParseMsg(data.decode("ascii"))
        ViaTag=response.Header.getFirstTag("Via")
        branchVal=ViaTag and ViaTag.getKwargsDict["branch"]
        CseqTag=response.Header.getFirstTag("CSeq") 
        callIdTag=response.Header.getFirstTag("Call-ID")
        callId=callIdTag and callIdTag.getValue
        Account=self.libUa.getValidAccount(callId)
        Call=self.libUa.getCall(callId)
        Requests=branchVal and self.libUa.SendMsgs.get(branchVal)
        
        if not (ViaTag and CseqTag and callIdTag and branchVal and callId and Account): 
            return  
        
        
        CseqId,MsgName=CseqTag.getValue.split()
        if not MethodNames.get(MsgName):
            self.libUa.requestMsgResp(response,405,"Method Not Allowed") 
        
        elif response.MsgType==response.RESPONSE:
            if response.status_code==401:#auth reister
                self.libUa.responseAUTH(Account,Requests,response)
            elif response.status_code==407:#auth INVITE
                self.libUa.responseAUTHINVITE(Call,Requests,response)
            elif response.status_code==100:
                Call.CallParam.CallDinamicState=CallState.TRYING 
            elif response.status_code==110:
                Call.CallParam.CallDinamicState=CallState.TRYING 
            elif response.status_code in [180,183]:
                Call.CallParam.CallDinamicState=CallState.RINGING 
                if response.status_code==183:
                    self.libUa.updateSetCallSipConfig(Call,response)
            elif response.status_code in [181,182]:
                self.libUa.requestCANCEL(Call,Requests) 
                Call.CallParam.CallEndState=CallEndState.SELFCLOSE
                Call.endCall()
            elif response.status_code==200:#succes
                if MethodNames.get(MsgName)==MethodNames.REGISTER:
                    Account.AccRegConf.accStatusSucces()
                    self.libUa.responseREGISTRATION(Account,Requests,response)
                elif MethodNames.get(MsgName)==MethodNames.INVITE:
                    self.libUa.responseOKINVITE(Call,Requests,response)   
                    
                    
            elif response.status_code in [408,486,603]:
                self.libUa.responseACK(Call,response) 
                if response.status_code==603:
                    Call.CallParam.CallEndState=CallEndState.DECLINE   
                elif response.status_code==486:
                    Call.CallParam.CallEndState=CallEndState.BUSYHERE  
                else:
                    Call.CallParam.CallEndState=CallEndState.NOTHERE   
                Call.endCall()
                    
                    
            elif str(response.status_code)[0] in ["3","4","5","6"]:
                if Call or Account:
                    AckPath=Call.CallParam.getTargetPath or Account.sipUserUri
                    self.libUa.responseACK(response,AckPath) 
                    if Call and Call.CallParam.callIsStarted:
                        self.libUa.requestBYENEW(Call,Requests)
                        Call.CallParam.CallEndState=CallEndState.UNKNOWN   
                        Call.endCall() 
                
        elif response.MsgType==response.REQUESTS:
            if MethodNames.get(MsgName)==MethodNames.BYE:
                self.libUa.requestMsgResp(response,200,"Ok")
                Call.CallParam.CallEndState=CallEndState.TARGETCLOSE  
                Call.endCall()
                
                
                
                
    
    def requests(self,Msg:SIPMesagge):  
        acc:Account=self.libUa.getValidAccount(Msg.getCallId) 
        if acc:
            if not self.StartedLib:
                reactor.callLater(0.1, lambda :self.requests(Msg)) 
            else:  
                TargetIP=self.Transport.domainToIp(acc.sipHostname)
                TargetPort=acc.sipPort 
                self.Transport.sender(Msg.toString.encode(),TargetIP,TargetPort)  
                if Msg.REQUESTS==Msg.MsgType and MethodNames(Msg.MsgName)!=MethodNames.ACK and MethodNames(Msg.MsgName)!=MethodNames.CANCEL\
                and MethodNames(Msg.MsgName)!=MethodNames.BYE:
                    self.libUa.SendMsgs[Msg.BodyInToBranch]=Msg  
                print(Msg.toString)





    def startLib(self):  
        self.LogConfig.info("Lib Starting")
        signal.signal(signal.SIGINT, lambda sig, frame: reactor.callInThread(self.__del__) ) 
        self.StartedLib=True  
        reactor.callInThread(self.libHandles)
        reactor.run() 
        

    def addAccount(self,account: Account):
        self.LogConfig.debug(f"kullanıcı ekleniyor..")
        account.AccTp=self.Transport
        self.libUa.Accounts[account.accUID]=account
    
    def addCall(self,call: Call):
        self.LogConfig.debug(f"Çağrı oluşturuluyor") 
        self.libUa.Calls[call.CallParam.callUid]=call
    




    def libHandles(self):
        self.LogConfig.info("Lib Started")
        self.LogConfig.debug(f"{self.Transport.ServerIp}:{self.Transport.ServerPort} {self.Transport.TpType} dinleniyor")
        
        while self.StartedLib:  
            self.sleep()   
            ######################################################################################################################################
            for accUid,acc in list(self.libUa.Accounts.items()): 
                if acc.AccRegConf.accRegState==AccountRegState.CREATE  or acc.AccRegConf.accStatusTimeout(self.libUa.SipConfig.EXPIRESTIME): 
                    self.LogConfig.debug(f"Kullanıcı Kayıt Ediliyor")
                    acc.AccRegConf.accStatusWait() 
                    self.requests(self.libUa.SipConfig.createREGISTER(acc))  
            ######################################################################################################################################
            while len(self.libUa.WaitingSendMsgs)>0:
                Msg=self.libUa.WaitingSendMsgs[0]
                self.libUa.WaitingSendMsgs.remove(Msg)
                self.requests(Msg) 
            ######################################################################################################################################
            for callUid,call in list(self.libUa.Calls.items()):  
                if call.CallParam.CallDinamicState==CallState.CREATE:
                    if call.Account.AccRegConf.accIsActive and self.MaxCallCount>self.libUa.ActiveCallCount:
                        call.CallParam.CallDinamicState=CallState.WAITING 
                        self.requests(self.libUa.SipConfig.createINVITE(call))
                elif call.CallParam.CallDinamicState==CallState.CLOSE and call.CallParam.CallEndState==CallEndState.SELFCLOSE: 
                    self.requests(self.libUa.SipConfig.createBYE(call)) 
                    call.endCall() 
                    
                if not call.ConnectState:
                    self.libUa.CallDestroy(call)
            ######################################################################################################################################  
                    
                    
    def __del__(self):
        if not self.StartedLib:
            return 
        elif not self.destroyedLib:
            self.destroyedLib=True
            self.LogConfig.debug(f"Aktif Çağrılar Sonlandırılıyor")
            for callUid,call in list(self.libUa.Calls.items()):
                #call cancell
                if call.CallParam.callIsStarted:
                    Msg=self.libUa.getLastMsg(callUid,MethodNames.INVITE)
                    if Msg and call.CallParam.CallDinamicState in [CallState.TRYING,CallState.RINGING]: 
                        self.requests(self.libUa.SipConfig.createCANCEL(call,Msg) ) 
                        call.CallParam.CallEndState=CallEndState.SELFCLOSE
                        call.endCall()  
                    elif call.CallParam.CallDinamicState==CallState.START:
                        self.requests(self.libUa.SipConfig.createBYE(call)) 
                        call.endCall()  
                    time.sleep(0.5)
            ##################################################
            self.LogConfig.debug(f"Aktif kullanıcılar siliniyor")
            for accUid,acc in list(self.libUa.Accounts.items()): 
                if acc.AccRegConf.accIsActive: 
                    self.LogConfig.debug(f"Kullanıcı siliniyor") 
                    self.requests(self.libUa.SipConfig.createREGISTER(acc,accDelete=True))  
                    time.sleep(0.5)
            time.sleep(1)
            ##################################################
            self.LogConfig.debug(f"{self.Transport.ServerIp}:{self.Transport.ServerPort} {self.Transport.TpType} Kapatılıyor")
            self.Transport.close()
            self.LogConfig.debug(f"tüm veriler temizlendi..")
            if reactor.running:
                self.StartedLib=False
                reactor.stop()  
            self.LogConfig.debug(f"Çıkmak için Ctrl+C")
    
    



