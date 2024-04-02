
from typing import Dict,List
from .packetMng import SIPMesagge,SDP 
from .account import Account
from .call import Call
from .enumTypes import MethodNames





class SipConfig:
    def __init__(self) -> None:
        self.EXPIRESTIME=300
        self.USERAGENT="Python VoIP"
        self.SERVERNAME="Python VoIP CLI" 
        self.SESSIONEXPIRESTIME=1800
        self.MAXFORWARDS=70
        self.ALLOWED="PRACK, INVITE, ACK, BYE, CANCEL, UPDATE, SUBSCRIBE, NOTIFY, REFER, MESSAGE, OPTIONS"
        self.SUPPORTED="100rel, timer" 
    def decorator_with_args(mainfunc): 
        return lambda *args, **kwargs:lambda func:lambda self, *func_args, **func_kwargs:mainfunc(self, func, func_args, func_kwargs, *args, **kwargs)
    @decorator_with_args
    def loadSipSettings(self,func,funcargs=(),funckwargs={},new_branch=False,nextSeq=False):   
        Msg:SIPMesagge=func(self,*funcargs,**funckwargs)
        if isinstance(Msg,SIPMesagge): 
            Msg.delNamesTags("Max-Forwards","Allow","User-Agent","Expires","Server","Supported","Session-Expires")
            Msg.Header.addTag("Max-Forwards",f"{self.MAXFORWARDS}") 
            Msg.Header.addTag("Expires", f"{self.EXPIRESTIME}")  
            Msg.Header.addTag("Session-Expires", f"{self.SESSIONEXPIRESTIME}")   
            Msg.Header.addTag("User-Agent", f"{self.USERAGENT}") 
            Msg.Header.addTag("Server", f"{self.SERVERNAME}") 
            Msg.Header.addTag("Allow", f"{self.ALLOWED}")  
            Msg.Header.addTag("Supported", f"{self.SUPPORTED}") 
            if MethodNames(Msg.MsgName)==MethodNames.REGISTER:
                Msg.delNamesTags("Supported","Session-Expires")
                if not Msg.Header.getFirstTag("Contact"):
                    Msg.Header.getFirstTag("Expires").getValue=f"{0}"
                    
            elif MethodNames(Msg.MsgName) in [MethodNames.ACK,MethodNames.BYE]:
                Msg.delNamesTags("Expires","Supported","Session-Expires","Allow")
            elif MethodNames(Msg.MsgName)==MethodNames.INVITE:
                Msg.delNamesTags("Expires")
            if MethodNames(Msg.MsgName)==MethodNames.UPDATE:
                Msg.delNamesTags("Expires")
                
            if new_branch or funckwargs.get("new_branch"):
                Msg.Header.replaceKwargsValue("Via","branch",Msg.BodyInToNewBranch) 
            if nextSeq:
                newCSeqvalue=f"{MethodNames(Msg.MsgName).getNewId} {Msg.MsgName}"
                Msg.delNamesTags("CSeq")
                Msg.Header.addTag("CSeq", newCSeqvalue)
        return Msg 
    
    @loadSipSettings(nextSeq=True)
    def createREGISTER(self,Acc: Account,accDelete=False) -> SIPMesagge:  
        target=f"sip:{Acc.sipHostname}"
        Msg:SIPMesagge=SIPMesagge.createREQUEST(MethodNames.REGISTER,target)
        Msg.Header.addTag("Via",f"{Msg.version}/{Acc.AccTp.getVia};rport={Acc.AccTp.ServerPort};branch={Msg.BodyInToNewBranch}")
        Msg.Header.addTag("From",f"{Acc.sourceIdUri}tag={Msg.BodyInToTag}")
        Msg.Header.addTag("To",f"{Acc.sipDisplayName}<sip:{Acc.sipUsername}@{Acc.sipHostname}>") 
        Msg.Header.addTag("Call-ID", Acc.accUID)
        if not accDelete:
            Msg.Header.addTag("Contact", f"{Acc.sipDisplayName}<sip:{Acc.sipUsername}@{Acc.AccTp.getContact};ob>") 
        return Msg
    
    @loadSipSettings()
    def createACK(self,response:SIPMesagge,TargetUri:str,new_branch=False): 
        CSeqId,ResMetNames=response.Header.getFirstTag("CSeq").getValue.split()
        ackMag=SIPMesagge.createREQUEST(MethodNames.ACK,TargetUri)
        NotTags=set(["Contact","Proxy-Authorization","Content-Type","Authorization","Supported","CSeq","Route","Max-Forwards"])
        for TAGv in response.Header.TAGCONTENTS.values():
            if len(set(TAGv.tagNames) & NotTags)==0:
                ackMag.Header.addTag(TAGv.REQUESTNAME,TAGv.getValue)  
        ackMag.Header.addTag("CSeq",f"{CSeqId} {ackMag.MsgName}")
        return ackMag
    
    @loadSipSettings(new_branch=True)
    def createAUTH(self,Account,request,response):
        request.Header.delTags(*request.Header.getTagUid("Authenticate").keys()) 
        AuthTag=response.Header.getFirstTag("Authenticate")
        AuthString=Account.getAuth(scheme=AuthTag.getMainValue,method=request.MsgName,urione=request.MsgPath,**AuthTag.getKwargsDict)
        request.Header.addTag(AuthTag.REQUESTNAME,AuthString)  
        return request
    


    @loadSipSettings(nextSeq=True)
    def createINVITE(self,call:Call): 
        Msg:SIPMesagge=SIPMesagge.createREQUEST(MethodNames.INVITE,call.CallParam.getTargetPath)
        Msg.Header.addTag("Via",f"{Msg.version}/{call.Account.AccTp.getVia};rport;branch={Msg.BodyInToNewBranch}") 
        Msg.Header.addTag("From",f"{call.Account.sourceIdUri}tag={call.CallParam.CallFromTagValue}")
        Msg.Header.addTag("Contact", f"{call.Account.sipDisplayName}<sip:{call.Account.sipUsername}@{call.Account.AccTp.getContact};ob>") 
        Msg.Header.addTag("Call-ID", call.CallParam.callUid)
        Msg.Header.addTag("To",f"{call.CallParam.CallTargetUri}")   
        Msg.Body=SDP.createSDP(
            username=call.Account.sipUsername,
            rtpIp=call.CallParam.LocalRTPIp, 
            sessionId=call.CallParam.callSessionId,
            sessionVersion=call.CallParam.callSessionId,
            mediaList=call.CallParam.getMediaSDPS
        ) 
        return Msg


    @loadSipSettings(new_branch=True,nextSeq=True)
    def createUPDATE(self,call:Call): 
        Msg:SIPMesagge=SIPMesagge.createREQUEST(MethodNames.UPDATE,call.CallParam.getTargetPath)
        Msg.Header.addTag("Via",f"{Msg.version}/{call.Account.AccTp.getVia};rport;branch={Msg.BodyInToNewBranch}") 
        Msg.Header.addTag("From",f"{call.Account.sourceIdUri}tag={call.CallParam.CallFromTagValue}")
        Msg.Header.addTag("Contact", f"{call.Account.sipDisplayName}<sip:{call.Account.sipUsername}@{call.Account.AccTp.getContact};ob>") 
        Msg.Header.addTag("Call-ID", call.CallParam.callUid)
        Msg.Header.addTag("To",f"{call.CallParam.CallTargetUri}") 
        for route in call.CallParam.CallRoutes:
            Msg.Header.addTag("Route",route)
        Msg.Body=SDP.createSDP(
            username=call.Account.sipUsername,
            rtpIp=call.CallParam.LocalRTPIp, 
            sessionId=call.CallParam.callSessionId,
            sessionVersion=call.CallParam.callSessionId,
            mediaList=call.CallParam.getMediaSDPS
        ) 
        return Msg



    @loadSipSettings(nextSeq=True)
    def createBYE(self,call: Call):
        Msg=SIPMesagge.createREQUEST(MethodNames.BYE,call.CallParam.getTargetPath) 
        Msg.Header.addTag("Via",f"{Msg.version}/{call.Account.AccTp.getVia};rport;branch={Msg.BodyInToNewBranch}") 
        Msg.Header.addTag("From",f"{call.Account.sourceIdUri}tag={call.CallParam.CallFromTagValue}") 
        Msg.Header.addTag("Call-ID", call.CallParam.callUid)
        Msg.Header.addTag("To",f"{call.CallParam.CallTargetUri}") 
        return Msg
    
    
    
    
    @loadSipSettings()
    def createCANCEL(self,call: Call,requests:SIPMesagge):
        CSeqId,ResMetNames=requests.Header.getFirstTag("CSeq").getValue.split()
        Msg=SIPMesagge.createREQUEST(MethodNames.CANCEL,call.CallParam.getTargetPath) 
        NotTags=set(["Contact","Proxy-Authorization","Content-Type","Authorization","Supported","CSeq","Route","Max-Forwards"])
        for TAGv in requests.Header.TAGCONTENTS.values():
            if len(set(TAGv.tagNames) & NotTags)==0:
                Msg.Header.addTag(TAGv.REQUESTNAME,TAGv.getValue)  
        Msg.Header.addTag("CSeq",f"{CSeqId} {Msg.MsgName}")
        return Msg
    
    
    def convertRESPONSE(self,response : SIPMesagge,statusCode:int,Message: str):
        Msg:SIPMesagge=SIPMesagge.createRESPONSE(statusCode,Message)
        NotTags=set(["User-Agent","User-agent","Allow","Contact","Proxy-Authorization","Server","Content-Type","Expires","Authorization"])
        for TAGv in response.Header.TAGCONTENTS.values():
            if len(set(TAGv.tagNames) & NotTags)==0:
                Msg.Header.addTag(TAGv.REQUESTNAME,TAGv.getValue)  
        return Msg
    
    
    
    
    
    
class Ua:
    def __init__(self) -> None:
        self.SipConfig=SipConfig()
        self.Calls:Dict[str,Call]={} 
        self.Accounts:Dict[str,Account]={}
        self.SendMsgs:Dict[str,SIPMesagge]={}
        self.WaitingSendMsgs:List[SIPMesagge]=[]#:Dict[int,SIPMesagge]={}

    def responseAUTH(self,account: Account,request:SIPMesagge,response:SIPMesagge): 
        if not account.AccRegConf.accStatusAuth(): 
            account.OnRegState(response.Msg)
            authMSG=self.SipConfig.createAUTH(account,request,response)
            self.WaitingSendMsgs.append(authMSG)
        else:
            account.OnRegState(response.Msg)
    def responseAUTHINVITE(self,call: Call,requests:SIPMesagge,response:SIPMesagge):
        self.WaitingSendMsgs.extend([
            self.SipConfig.createACK(response,call.CallParam.getTargetPath),
            self.SipConfig.createAUTH(call.Account,requests,response)
        ]) 
        
        
    
        

    def responseREGISTRATION(self,account: Account,request:SIPMesagge,response:SIPMesagge): 
        account.OnRegState(response.Msg) 
        Msg=self.SipConfig.createACK(response,account.sipUserUri)
        self.WaitingSendMsgs.append(Msg) 

    


        

    
    def responseOKINVITE(self,call: Call,requests: SIPMesagge,response: SIPMesagge):
        self.updateSetCallSipConfig(call,response)
        call.CallParam.setCallSDP(response.Body)
        call.makeCall()  
        self.WaitingSendMsgs.append(
            self.SipConfig.createACK(response,call.CallParam.getTargetPath,new_branch=True))  
        
        if call.CallParam.isSetMediaCodec:  
            self.WaitingSendMsgs.append(self.SipConfig.createUPDATE(call))
            
            
            
            

        
        
    def responseACK(self,response:Call,TargetPath:SIPMesagge):
        self.WaitingSendMsgs.append(
            self.SipConfig.createACK(response,TargetPath),
        )
    def requestBYENEW(self,call,request):
        self.WaitingSendMsgs.append(
            self.SipConfig.createCANCEL(call,request) 
        )
    def requestCANCEL(self,call,request):
        self.WaitingSendMsgs.append(
            self.SipConfig.createCANCEL(call,request) 
        )
        
    def requestMsgResp(self,response: SIPMesagge,statusCode,Msg):
        self.WaitingSendMsgs.append(
            self.SipConfig.convertRESPONSE(response,statusCode,Msg)
        )
        
    def updateSetCallSipConfig(self,call,response):
        CallTargetUriTag=response.Header.getFirstTag("To")
        if CallTargetUriTag:
            call.CallParam.CallTargetUri=CallTargetUriTag.getValue
        CallTargetContactUriTag=response.Header.getFirstTag("Contact")
        if CallTargetContactUriTag:
            call.CallParam.CallTargetContactUri=CallTargetContactUriTag.getValue 
            
            
    
    def getAcount(self,AccUid):
        if AccUid:
            return self.Accounts.get(AccUid)
    def getCall(self,CallUid):
        if CallUid:
            return self.Calls.get(CallUid)
    def getValidAccount(self,Uid):
        return self.getAcount(Uid) or self.getCall(Uid) and self.getCall(Uid).Account


    def CallDestroy(self,call):
        pass
    def getLastMsg(self,CallUid,searchMethod):
        Msgs={}
        for branch,sendMsg in list(self.SendMsgs.items()):
            CallIDTag=sendMsg.Header.getFirstTag("Call-ID")
            CseqTag=sendMsg.Header.getFirstTag("CSeq")
            if CallIDTag and CallIDTag.getValue==CallUid and CseqTag:
                CSeq,Methods=sendMsg.Header.getFirstTag("CSeq").getValue.split()
                if searchMethod==Methods and CSeq.isnumeric():
                    Msgs[int(CSeq)]=sendMsg
        return Msgs[max(Msgs.keys())]
    
    
    @property
    def ActiveCallCount(self):
        callList=list(self.Calls.values())         
        activeCalls=list(filter(lambda call:call.CallParam.callIsStarted,callList))
        return len(activeCalls)