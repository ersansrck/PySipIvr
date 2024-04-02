import uuid,datetime,socket
from typing import Callable,Union,Optional,Dict,List
from .libs.sipauth import DigestAuth

from .enumTypes import AccountRegState



    

class AccountRegConf(DigestAuth): 
    def __init__(self) -> None:
        self.accRegState=AccountRegState.CREATE
        self.accRegTimestamp=None
        self.accRegRetryCount=3
        self.accRegTryCount=self.accRegRetryCount

    @property
    def accIsActive(self):
        return self.accRegState==AccountRegState.SUCCES 
    @property
    def accIsWaiting(self):
        return self.accRegState==AccountRegState.WAITING

    def accStatusTimeout(self,EXPIRESTIME:int): 
        nowtime=datetime.datetime.now().timestamp()
        if nowtime-(self.accRegTimestamp or nowtime)>EXPIRESTIME:
            self.accRegState=AccountRegState.TIMEOUT
            return True
        
    def accStatusSucces(self):
        self.accRegTryCount=self.accRegRetryCount
        self.accRegState=AccountRegState.SUCCES
        self.accRegTimestamp=int(datetime.datetime.now().timestamp())
    def accStatusAuth(self):
        self.accRegTryCount-=1
        self.accRegState=AccountRegState.AUTHERR
        if self.accRegTryCount<1:
            return True
    def accStatusWait(self):
        self.accRegState=AccountRegState.WAITING



    
    
class Account:
    def __init__(self,sipUsername,sipPassword,sipHostname,sipPort=5060,sipDisplayName="") -> None:
        self.accUID=f"{uuid.uuid4()}" 
        
        self.sipUsername=sipUsername
        self.sipPassword=sipPassword
        self.sipHostname=sipHostname
        self.sipPort=sipPort
        self.sipDisplayName=len(sipDisplayName)>0 and f"\"{sipDisplayName}\" " or ""

        self.AccTp:Callable=None
        self.AccRegConf=AccountRegConf()
        

    def getAuth(self,scheme,**kwargs):
        if scheme.strip().lower()=="digest": 
            return self.AccRegConf.build_digest_header(self.sipUsername,self.sipPassword,**kwargs)
    @property
    def sourceIdUri(self):
        return f"{self.sipDisplayName}<{self.sipUserUri}>;"
    @property
    def sipUserUri(self):
        return f"sip:{self.sipUsername}@{self.sipHostname}" 
    def OnRegState(self,msg): 
        print("***OnRegState",msg)
        
        
        
        