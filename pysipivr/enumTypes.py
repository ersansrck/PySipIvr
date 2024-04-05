from enum import Enum,EnumType
from typing import Callable,Union,Optional,Dict,List
from .libs.codec import decodeiLBC_Ctype,encodeiLBC_Ctype,decodePCMU,decodePCMA,encodePCMA,encodePCMU 

import random




class CallEndState(Enum):
    def __str__(self) -> str:
        return f"{self.value}"
    def __repr__(self) -> str:
        return f"{self.value}"
    def __eq__(self, __value: object) -> bool:
        return self.value==__value.value
    @classmethod
    def get(cls, value): 
        if isinstance(cls,EnumType):
            try: 
                return cls(value)
            except ValueError:
                return None
    SELFCLOSE="KAPAT"
    TARGETCLOSE="KAPATTI"
    BUSYHERE="MEŞGUL"
    NOTFOUND="İNVALIDADDR"
    NOGONE="NOGONE"
    NOTHERE="ULASILAMADI"
    DECLINE="REDDETTİ"
    UNKNOWN="UNKNOWN"
    
    
    
    
    
class CallState(Enum):
    def __str__(self) -> str:
        return f"{self.value}"
    def __repr__(self) -> str:
        return f"{self.value}"
    def __eq__(self, __value: object) -> bool:
        return self.value==__value.value
    @classmethod
    def get(cls, value): 
        if isinstance(cls,EnumType):
            try: 
                return cls(value)
            except ValueError:
                return None
    CREATE="CREATE"
    WAITING="WAITING"
    TRYING="TRYING"
    RINGING="ÇALIYOR"
    START="STARTED"
    CLOSE="CLOSE" 
    FINISH="FINISH"
    
    
    

class AccountRegState(Enum):
    def __str__(self) -> str:
        return f"{self.value}"
    def __repr__(self) -> str:
        return f"{self.value}"
    def __eq__(self, __value: object) -> bool:
        return self.value==__value
    @classmethod
    def get(cls, value): 
        if isinstance(cls,EnumType):
            try: 
                return cls(value)
            except ValueError:
                return None
    CREATE="CREATED"
    WAITING="WAITING"
    AUTHERR="AUTHERR"
    TIMEOUT="TIMEOUT"
    DELETE="DELETED"
    SUCCES="SUCCESS"
    
    
    
    
    
    
    

class MediaTypes(Enum):
    def __str__(self) -> str:
        return f"{self.value}"
    def __repr__(self) -> str:
        return f"{self.value}"
    def __eq__(self, __value: object) -> bool:
        return self.value==__value
    @classmethod
    def get(cls, value): 
        if isinstance(cls,EnumType):
            try: 
                return cls(value)
            except ValueError:
                return None
    AUDIO="audio"
    VIDEO="video"
    DTMF="event"
    
    
    
class MethodNames(Enum):
    def __new__(cls, name:str,iterables:int):
        obj=object.__new__(cls)
        obj._value_=name
        obj.iterid=iterables
        return obj
    def __eq__(self, __value: object) -> bool:
        return self.value==__value
    @classmethod
    def get(cls, value): 
        if isinstance(cls,EnumType):
            try: 
                return cls(value)
            except ValueError:
                return None
    def __str__(self) -> str:
        return f"{self.value}"
    def __repr__(self) -> str:
        return f"{self.value}"
    
    @property
    def getNewId(self):
        self.iterid+=1
        return self.iterid
    def __str__(self) -> str:
        return self._value_
    REGISTER="REGISTER",random.randint(100,5000)
    INVITE="INVITE",random.randint(100,5000)
    UPDATE="UPDATE",random.randint(100,5000)
    ACK="ACK",random.randint(100,5000)
    BYE="BYE",random.randint(100,5000)
    CANCEL="CANCEL",random.randint(100,5000)
    
    
        

    
    
class RESPONSESTATUS(Enum):
    def __new__(cls,value,mean):
        obj=object.__new__(cls)
        obj._value_=value
        obj.mean=mean 
        return obj
    def __eq__(self, __value: object) -> bool:
        return self.value==__value or self==__value 
    
    
    @classmethod
    def get(cls, value): 
        if isinstance(cls,EnumType):
            try: 
                return cls(value)
            except ValueError:
                return None
    RINGING=180,"ÇALIYOR"
    SESSION_RINGING=183,"ÇALIYOR"
    FORWARDEDCALL=181,"ÇAĞRI BAŞKA NUMARAYA YÖNLENDİRLİYOR"
    
    SUCCESS=200,"BAŞLADI"
    DECLINE=603,"MEŞGULE ATTI"
    BUSYHERE=486,"CEVAP VERMEDİ"
    NOTACCAPTABLE=488,"MEDYA BULUNAMADI"
    TIMEOUT=408,"YANIT ALINAMADI" 
    
    
class RTCPRESPONSESTATUS(Enum):
    def __new__(cls,value,mean):
        obj=object.__new__(cls)
        obj._value_=value
        obj.mean=mean 
        return obj
    def __eq__(self, __value: object) -> bool:
        return self.value==__value
    @classmethod
    def get(cls, value): 
        if isinstance(cls,EnumType):
            try: 
                return cls(value)
            except ValueError:
                return None

    RECEIVERREPORT=201,"Receiver Report"
    SENDERREPORT=200,"Sender Report"
    SOURCEDESCRIPTION=202,"Source Description"
    GOODBYE=203,"Good Bye"
    @classmethod
    def get(cls, value): 
        if isinstance(cls,EnumType):
            try: 
                return cls(value)
            except ValueError:
                return None
            
            
            

        
class PayloadTypes(Enum):

    def __new__(cls,pID:int,mType:Callable,description:str,rate:int,channel:int,samplewidth:int,decodefunc:Callable,encodefunc:Callable,fmtpParams:dict,ptime:int=None): 
        obj = object.__new__(cls)
        obj._value_ = pID
        obj.rate = rate
        obj.mType=mType
        obj.channel = channel
        obj.samplewidth=samplewidth
        obj.description = description
        obj.decode=decodefunc
        obj.encode=encodefunc
        obj.fmtpParams=fmtpParams
        obj.ptime=ptime
        return obj 
    def __eq__(self, __value: object) -> bool:
        return self.value==__value or self==__value
    def __str__(self) -> str:
        if isinstance(self.value, int):
            return self.description
        return str(self.value) 
    @classmethod
    def get(cls, value): 
        if isinstance(cls,EnumType):
            try: 
                return cls(value)
            except ValueError:
                return None
            
    @property
    def isAudio(self):
        return self.mType==MediaTypes.AUDIO.value
    @property
    def isVideo(self):
        return self.mType==MediaTypes.VIDEO.value
    @property
    def isDtmf(self):
        return self.mType==MediaTypes.DTMF.value
    @property
    def PTIMECHUNKS(self): 
        return int(self.rate*self.channel/1000*self.PTIME)
    @property
    def PTIME(self):
        return self.ptime
    
    
    
    @property
    def getChunkTime(self):
        return 1/self.rate*self.channel
    


    @property
    def getPayload(self):
        Par={'payload': self._value_, 'codec': self.description, 'rate': self.rate}
        if self.channel>1:
            Par["encoding"]=self.channel
        return Par
    @property
    def getPayloadFmtp(self):
        if len(self.fmtpParams)>0:
            msg=""
            for val in self.fmtpParams:
                if isinstance(val,str):     msg+=" "+val
                elif isinstance(val,dict):  msg+=" "+(" ".join([f'{key}={value}' for key, value in val.items()]))
            return {'payload': self._value_, 'config': msg.strip()}    
        return None 



    PCMU    =(
        0,#
        MediaTypes.AUDIO,
        "PCMU",#name
        8000,#rate
        1,#channel
        2,#sapmle width
        decodePCMU,#decodefunc(encoded_bytes)>pcm
        encodePCMU,#encodefunc(pcm)>encoded_bytes,
        [],#[{"mode":30}]#format params -> ["0-16",{mode:30}] -> a=fmtp:99 0-16 a=fmtp:99 mode=30
        20
    )


    PCMA    =(
        8,#
        MediaTypes.AUDIO,
        "PCMA",#name
        8000,#rate
        1,#channel
        2,#sapmle width
        decodePCMA,#decodefunc(encoded_bytes)>pcm
        encodePCMA,#encodefunc(pcm)>encoded_bytes,
        [],
        20
    )
    
    #id,name,rate,channel,DECODEFUNC,ENCODEFUNC
    iLBC    =(
        96,#
        MediaTypes.AUDIO,
        "iLBC",
        8000,
        1,
        2,#sapmle width
        decodeiLBC_Ctype,
        encodeiLBC_Ctype,
        [{"mode":30}],
        30
    )
    EVENT   =(
        100,#
        MediaTypes.DTMF,
        "telephone-event",
        8000,
        1,
        2,#sapmle width
        lambda x,*z,**y:x,
        lambda x,*z,**y:x,
        ["0-16"]
    )
    EVENT2   =(
        101,#
        MediaTypes.DTMF,
        "telephone-event",
        16000,
        1,
        2,#sapmle width
        lambda x,*z,**y:x,
        lambda x,*z,**y:x,
        ["0-16"]
    )
    EVENT3   =(
        102,#
        MediaTypes.DTMF,
        "telephone-event",
        48000,
        1,
        2,#sapmle width
        lambda x,*z,**y:x,
        lambda x,*z,**y:x,
        ["0-16"]
    )
