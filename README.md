# pySipIvr
pySipIvr is python VoIP/SIP/RTP library.  Currently, it supports PCMA, PCMU, iLBC and telephone-event.





### Basic Example
This basic code will call the 2 specified addresses simultaneously, communicate through the specified IVR menu, and close them.

```python
from pysipivr import Endpoint,TRANSPORT_UDP,Transport,Account,Call
import os
class EditCall(Call):
    def __init__(self, account: Account, targetUri,IvrOuts=[]) -> None:
        super().__init__(account, targetUri)
        self.IvrOuts=IvrOuts 
    def callHangup(self): 
        new_map={os.path.basename(key):value for key,value in self.CallParam.STREAM.IVRMap.items()}
        new_map["Target"]=self.CallParam.getTargetDisplayName
        self.IvrOuts.append(new_map)

        self.CallParam.STREAM.save(f"{self.CallParam.getTargetDisplayName}.wav")
        
        
    def Dtmf(self,Value): 
        print(f"Receiver dtmf value:{Value}")
    def callStart(self):
        pass

IVRMENU={
    f"../started.wav":{
        "1":{
            f"../menu.wav":{
                "1":False,
                "2":False,
            }
        },
        "2":False
    }
}

targetAddrs=[
    {"target":"sip:+49170xxx1@sip.domain.com","IvrMenu":IVRMENU},
    {"target":"sip:+49170xxx2@sip.domain.com","IvrMenu":IVRMENU}
]

ep=Endpoint() 
ep.MaxCallCount=10
ep.createTransport(Transport(TRANSPORT_UDP,serverPort=5090))

Account1=Account("sipUser","sipPwd","sipHostname",sipDisplayName="+49xxxxx") 
ep.addAccount(Account1) 

IvrOut=[] 
for dictV in targetAddrs:
    call=EditCall(Account1,dictV["target"],IvrOut) 
    call.CallParam.STREAM.setStreamIvr(dictV["IvrMenu"],InputSleep=10)
    ep.addCall(call)
ep.startLib()
#Ctrl+C AND Ctrl+C
print(IvrOut)#>>[{'baslangic.wav': '1', 'menuses.wav': '3', 'Target': '+49170xxx1'}, {'baslangic.wav': '1', 'menuses.wav': '3', 'Target': '+49170xxx2'}]
