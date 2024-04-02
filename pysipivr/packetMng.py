from .enumTypes import PayloadTypes,RESPONSESTATUS,RTCPRESPONSESTATUS,MediaTypes
from .libs.headerSdp import HEADER,SDP

import uuid,datetime,struct






class SIPMesagge:
    REQUESTS=1
    RESPONSE=0 
    endRowText="--end-msg--"
    def __init__(self,version="SIP/2.0",BodyType="application/sdp") -> None:
        self.version=version
        self._status_code=None
        
        self.Msg=None
        self.MsgType=None
        self.MsgName=None
        self.MsgPath=None
        
        self.Header=None
        self.Body=None
        self.BodyType=BodyType
        self.BODYPRIMARYVALUES={
            "branch":f"z9hG4bKPj{uuid.uuid4()}", 
            "tag":f"{uuid.uuid4()}",
            "Call-ID":f"{uuid.uuid4()}",
        }
    def delNamesTags(self,*tagnames):
        for tagname in tagnames:
            self.Header.delTags(*self.Header.getTagUid(tagname).keys()) 
    @classmethod
    def createRESPONSE(cls,statuscode,msg,body=None,bodytype=None):
        self=cls()
        self._status_code=statuscode
        self.Msg=msg
        self.Header=HEADER()
        self.MsgType=self.RESPONSE
        self.Body=body
        self.BodyType=bodytype
        return self
    @classmethod
    def createREQUEST(cls,method,path):
        cls=cls()
        cls.MsgName=method
        cls.MsgType=cls.REQUESTS 
        cls.Header=HEADER()
        cls.MsgPath=path 
        return cls

    @classmethod
    def createParseMsg(cls,stringVector):
        
        cls=cls()
        MsgFirstLine,Msg=stringVector.replace("\r\n","\n").split("\n",1) 
        One,Two,Three=MsgFirstLine.split(" ",2)
        if Two.isnumeric() and len(Two)==3:
            cls.MsgType=cls.RESPONSE
            cls.version=One
            cls._status_code=Two
            cls.Msg=Three
        else:
            cls.MsgType=cls.REQUESTS
            cls.MsgName=One
            cls.MsgPath=Two
            cls.version=Three
        
        PartSplit=Msg.strip().split("\n\n")
        
        if len(PartSplit)==1:
            Header,Body=PartSplit[0],""
        else:
            Header,Body=PartSplit[:2] 
        
        cls.Header=HEADER.getParse(Header)
        
        if len(Body)>0:
            cls.BodyType=cls.Header.getFirstTag("Content-Type").getValue
            if cls.BodyType=="application/sdp":
                cls.Body=SDP.parse(Body) 
        return cls
    @property
    def toString(self):
        if self.MsgType==self.REQUESTS:
            mline=f"{self.MsgName} {self.MsgPath} {self.version}\r\n"
        else:
            mline=f"{self.version} {self.status_code} {self.Msg}\r\n"
            
        body=""
        if self.Body:  
            if self.BodyType=="application/sdp":
                body=SDP.write(self.Body.__dict__)+"\r\n\r\n"
                self.Header.delTags(*self.Header.getTagUid("Content-Type").keys())
                if len(body)>0: 
                    self.Header.addTag("Content-Type",self.BodyType)
                
        
        self.Header.delTags(*self.Header.getTagUid("Content-Length").keys())
        self.Header.addTag("Content-Length",f"{len(body)}")
        
        header=[]
        for tagUid,TagOb in self.Header.TAGCONTENTS.items(): 
            Tagname=TagOb.RESPONSENAME
            if self.MsgType==self.REQUESTS:
                Tagname=TagOb.REQUESTNAME
            header.append(f"{Tagname}: {TagOb.getValue}")
        header="\r\n".join(header)+"\r\n\r\n" 
        

                
        MsgText=f"{mline}{header}{body}{self.endRowText}"
        return MsgText

    @property
    def status_code(self):
        return int(self._status_code)
    @property
    def getCallId(self):
        callID=self.Header.getFirstTag("Call-ID")
        return callID and callID.getValue 
    @property
    def BodyInToNewBranch(self):
        vals=f"z9hG4bKPj{uuid.uuid4()}"
        self.BODYPRIMARYVALUES["branch"]=vals
        return self.BodyInToBranch
    @property
    def BodyInToBranch(self):
        return self.BODYPRIMARYVALUES["branch"]
    @property
    def BodyInToTag(self):
        return self.BODYPRIMARYVALUES["tag"]
    
    
    
    
    
    



class SOURCE:
    def __init__(self,Identifier) -> None:
        self.secondPart=1/8000
        
        self.Identifier=Identifier
        self.FractionLost=0
        self.CumulativePacket=0
        self.HighestSeqNumberReceived=0
        self.Jitter=0
        self.LastSRTimeStamp=0
        self.DelaySinceLastSRTimteStamp=0 
        
        
        self.SENDPAKETCOUNT=0
        self.SENDOCTETCOUNT=0
        self.RTPTIME=0  
        self.STARTSEQID=None
        self.STARTRTPTIME=None
        self.RECVRTPTIMES=[]
        self.SENDEDRTPTIMES=[]
        
            
        self.CSRCS=[]

        
    def setJitter(self,recvtime,sendtime,secondPart): 
        getjitter=lambda nwj,oldj=0:oldj + (abs(nwj) - oldj)/16
        
        
        if len(self.RECVRTPTIMES)==2:
            rrfark=self.RECVRTPTIMES[1]-self.SENDEDRTPTIMES[1]*secondPart
            ssfark=self.RECVRTPTIMES[0]-self.SENDEDRTPTIMES[0]*secondPart
            self.Jitter=getjitter(rrfark-ssfark,self.Jitter*secondPart)/secondPart
        
            self.RECVRTPTIMES=[]
            self.SENDEDRTPTIMES=[]
        else:
            self.RECVRTPTIMES.append(recvtime)
            self.SENDEDRTPTIMES.append(sendtime) 
    
    
    def setDelat(self,timsestamp):
        if self.LastSRTimeStamp==0:
            self.DelaySinceLastSRTimteStamp=0
        else:
            self.DelaySinceLastSRTimteStamp=timsestamp-self.LastSRTimeStamp
    @staticmethod
    def getNTPtimestamp(msw, lsw): 
        return ((msw & 0xFFFF) << 16) | ((lsw >> 16) & 0xFFFF)
    
    @property
    def getNTPtime(self):
        dt = datetime.datetime.now(datetime.timezone.utc)#datetime(2024, 3, 20, 17, 45, 7, tzinfo=timezone.utc)
        unix_timestamp = int(dt.timestamp())
        msw = unix_timestamp + 2208988800
        lsw = (dt.microsecond * (2**32 // 10**6)) 
        return (msw, lsw)
    
    def parse(self,sourceData):
        (self.Identifier,
        self.FractionLost,
        self.CumulativePacket,
        self.HighestSeqNumberReceived,
        self.Jitter,
        self.LastSRTimeStamp,
        self.DelaySinceLastSRTimteStamp)=struct.unpack_from('!LB3sLLLL', sourceData) 
        
        self.CumulativePacket=int.from_bytes(self.CumulativePacket, byteorder='big')
        #self.Jitter=int(self.Jitter*self.secondPart)
    @property
    def getCumulativePacket(self):
        val=int.to_bytes(int(self.CumulativePacket),byteorder="big")
        return (0).to_bytes(3-len(val), byteorder='big')+val
        
        
    @property
    def getpacket(self):  
        args=(
            self.Identifier,
            self.FractionLost,
            self.getCumulativePacket,
            self.HighestSeqNumberReceived,
            int(self.Jitter),#int(self.Jitter/self.secondPart),
            self.LastSRTimeStamp,
            self.DelaySinceLastSRTimteStamp
        )  
        return struct.pack("!LB3sLLLL",*args)
    
    
    
class CHUNK:
    def __init__(self,Identifier,cname,toolname="deneme") -> None:
        self.Identifier=Identifier
        self.cname={}
        self.tool={}

        if cname:
            self.cname={1:cname.encode()}
        if toolname:
            self.tool={5:toolname.encode()}
        self.extravals=[] 
        
        
    @property
    def getpacket(self):
        data=struct.pack("!L",int(self.Identifier))
        
        for key,value in self.cname.items():
            data+=struct.pack(f"!BB{len(value)}s",key,len(value),value)  
        for key,value in self.tool.items():
            data+=struct.pack(f"!BB{len(value)}s",key,len(value),value)  
        
        for dtyp,dtval in self.extravals: 
            data+=struct.pack(f"!BB{len(dtval)}s",dtyp,len(dtval),dtyp)  
        data+=struct.pack(f"!BB",0,0) 
        return data
        
        
    def parse(self,chunkdata): 
        self.Identifier,=struct.unpack_from('!L', chunkdata,0)    
        chunkdata=chunkdata[4:] 
        while len(chunkdata)>2: 
            valtype,=struct.unpack_from('!B', chunkdata,0)
            if valtype==0:chunkdata=chunkdata[1:];break  #END 
            vallenght,=struct.unpack_from('!B', chunkdata,1)
            value,=struct.unpack_from(f'!{vallenght}s', chunkdata,2)
            if valtype==1:
                self.cname[1]=value
            elif valtype==5:
                self.tool[5]=value
            else:
                self.extravals.append([valtype,value])
            chunkdata=chunkdata[vallenght+2:]  
        


class REPORTER:
    def __init__(self,SelfSSRC=None,SelfCname=None) -> None:
        
        self.SelfSource=SOURCE(SelfSSRC)
        self.SelfChunks=CHUNK(SelfSSRC,SelfCname,None)

        self.TargetSource=SOURCE(0) 
        self.TargetChunk=CHUNK(0,"",None)
        
    def setTargetSSRC(self,TargetSSRC,TargetCname=None): 
        self.TargetSource=SOURCE(TargetSSRC) 
        self.TargetChunk=CHUNK(TargetSSRC,TargetCname,None)
        
        

    @staticmethod
    def parseHeaderRTCP(packet):
        first_byte, packet_type, length = struct.unpack('!BBH', packet)
        version=(first_byte >>6) & 0x03
        padding = (first_byte >> 5) & 0x01
        unkks_count = first_byte & 0x1F
        real_length = (length + 1) * 4  
        return version,padding,unkks_count,length,real_length,packet_type
    def getHeaderRTCP(self,version,padding,ptype=0,count=1,lenght=7):
        first_byte = (version << 6) | (padding << 5) | count 
        return struct.pack('!BBH', first_byte,ptype,lenght)  
    def parseRTCP(self,rtcppacket): 
        while len(rtcppacket)>0:
            version,padding,unkks_count,length,real_length,packet_type=self.parseHeaderRTCP(rtcppacket[:4])
            paket=rtcppacket[:real_length]
            rtcppacket=rtcppacket[real_length:]
            
            if RTCPRESPONSESTATUS.get(packet_type)==RTCPRESPONSESTATUS.SENDERREPORT:
                self.TargetSSRC,MWTIME,LWTIME,*_=struct.unpack_from("!LLLLLL",paket,4)
                self.TargetSource.LastSRTimeStamp=self.TargetSource.getNTPtimestamp(MWTIME,LWTIME)
            elif RTCPRESPONSESTATUS.get(packet_type)==RTCPRESPONSESTATUS.RECEIVERREPORT: 
                self.TargetSSRC=struct.pack("!L",paket[4:])
                self.TargetSource.parse(paket[8:]) 
            elif RTCPRESPONSESTATUS.get(packet_type)==RTCPRESPONSESTATUS.SOURCEDESCRIPTION:
                self.TargetChunk.parse(paket[4:])
            elif RTCPRESPONSESTATUS.get(packet_type)==RTCPRESPONSESTATUS.GOODBYE:
                pass


    def getRTP(self,  marker:bool=False, PayloadType:PayloadTypes=None,pcmBytes: bytes=b""):
        version=2
        padding=0
        extension=0 
        payload=PayloadType.encode(pcmBytes,mspart=PayloadType.PTIME)
        
        self.SelfSource.RTPTIME=self.SelfSource.RTPTIME + PayloadType.PTIMECHUNKS
        SEQID,TIMESTAMP=self.SelfSource.SENDPAKETCOUNT,self.SelfSource.RTPTIME
        self.SelfSource.SENDPAKETCOUNT+=1
        self.SelfSource.SENDOCTETCOUNT+=len(payload)
        
        
        first_byte = (version << 6) | (padding << 5) | (extension << 4) | len(self.SelfSource.CSRCS)
        second_byte = (marker << 7) | PayloadType.value
        header = bytearray([first_byte, second_byte]) + SEQID.to_bytes(2, byteorder='big') + \
                TIMESTAMP.to_bytes(4, byteorder='big') + self.SelfSource.Identifier.to_bytes(4, byteorder='big')
                
        for csrc in self.SelfSource.CSRCS:
            header += csrc.to_bytes(4, byteorder='big')
        
        packet = header + payload
        return bytes(packet)
    def parseRTP(self,packet):   
        sourceS=self.TargetSource
        
        VerPadExCC=format(packet[0:1][0], '08b')
        MarkPayType=format(packet[1:2][0], '08b')
        
        version = int(VerPadExCC[0:2], 2)
        padding = bool(int(VerPadExCC[2], 2))
        extension = bool(int(VerPadExCC[3], 2)) 
        CC=int(VerPadExCC[4:], 2)
    
        marker = bool(int(MarkPayType[0], 2))
        PayloadTypeId = int(MarkPayType[1:], 2)
        
        sequenceID = int.from_bytes(packet[2:4], 'big')
        timestamp = int.from_bytes(packet[4:8], 'big')
        recvtime=datetime.datetime.now().timestamp()
        pyTYPE=PayloadTypes.get(PayloadTypeId)
        
        SSRC = int.from_bytes(packet[8:12], 'big')
        
        i = 12
        CSRC = []
        for x in range(CC):
            CSRC.append(packet[i : i + 4])
            i += 4 
            
            
        sourceS.SENDPAKETCOUNT+=1
        sourceS.SENDOCTETCOUNT+=len(packet[i:])
        sourceS.HighestSeqNumberReceived=sequenceID
        if isinstance(sourceS.STARTSEQID,type(None)): 
            sourceS.STARTSEQID=sequenceID 
        if isinstance(sourceS.STARTRTPTIME,type(None)): 
            sourceS.STARTRTPTIME=timestamp 
        sourceS.CumulativePacket=abs(sequenceID-sourceS.STARTSEQID-sourceS.SENDPAKETCOUNT)
        if sourceS.Identifier!=SSRC:
            self.setTargetSSRC(SSRC)
        

        
        if pyTYPE:
            sourceS.setJitter(recvtime,timestamp,pyTYPE.getChunkTime)
            pyMedType=MediaTypes(pyTYPE.mType)
            if not marker:
                if pyMedType==MediaTypes.AUDIO: 
                    return pyMedType,pyTYPE.decode(packet[i:],mspart=pyTYPE.PTIME)
            else:
                if pyMedType==MediaTypes.DTMF: 
                    return pyMedType,pyTYPE.decode(packet[i]) 
 

    
    
    @property
    def getSourceDescription(self): 
        chunks=self.SelfChunks.getpacket 
        real_lenght= 4 + len(chunks)
        header=self.getHeaderRTCP(version=2,padding=0,count=1,ptype=RTCPRESPONSESTATUS.SOURCEDESCRIPTION.value,lenght=int(real_lenght/4)-1)
        return header+chunks
    @property
    def getGoodBye(self): 
        srcdata=struct.pack("!L",int(self.SelfSource.Identifier))
        real_lenght= 4 + len(srcdata)
        header=self.getHeaderRTCP(version=2,padding=0,count=1,ptype=RTCPRESPONSESTATUS.GOODBYE.value,lenght=int(real_lenght/4)-1)
        return self.SendReceiverReport+header+srcdata
    @property
    def SendReceiverReport(self):
        MWTIME,LWTIME=self.TargetSource.getNTPtime
        NTPTimestamp=self.TargetSource.getNTPtimestamp(MWTIME,LWTIME)
        self.TargetSource.setDelat(NTPTimestamp)

        sources=self.TargetSource.getpacket
        srcdata=struct.pack("!L",int(self.SelfSource.Identifier))
        real_lenght= 4 + len(sources) + len(srcdata)
        header=self.getHeaderRTCP(version=2,padding=0,count=1,ptype=RTCPRESPONSESTATUS.RECEIVERREPORT.value,lenght=int(real_lenght/4)-1)  
        data=header+srcdata+sources+self.getSourceDescription 
        return data
    @property
    def SendSenderReport(self):
        MWTIME,LWTIME=self.SelfSource.getNTPtime
        NTPTimestamp=self.SelfSource.getNTPtimestamp(MWTIME,LWTIME)
        self.TargetSource.setDelat(NTPTimestamp) 
        sources=self.TargetSource.getpacket  
        srcdata=struct.pack("!LLLLLL",int(self.SelfSource.Identifier),MWTIME,LWTIME,self.SelfSource.RTPTIME,self.SelfSource.SENDPAKETCOUNT,self.SelfSource.SENDOCTETCOUNT)  
        real_lenght= 4 + len(sources) + len(srcdata) 
        header=self.getHeaderRTCP(version=2,padding=0,count=1,ptype=RTCPRESPONSESTATUS.SENDERREPORT.value,lenght=int(real_lenght/4)-1)    

        
        self.SelfSource.LastSRTimeStamp=NTPTimestamp 
        return  header+srcdata+sources+self.getSourceDescription 