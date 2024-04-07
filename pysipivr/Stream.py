import io,wave
from .enumTypes import MediaTypes,PayloadTypes

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample


class STREAM:
    def __init__(self,chanell=1,rate=8000,width=2) -> None:
        self.chanell=chanell
        self.rate=rate
        self.width=width
        self.ioBytes=io.BytesIO() 
        self.WriteWave=self.createWAVE()  
    @classmethod
    def FileToStream(cls,filepath,new_rate,new_channel,new_samplewidth):
        sr, data = wavfile.read(filepath,"rb") 
        num_samples = round(len(data) * float(new_rate) / sr)
        data_resampled = resample(data, num_samples).astype(np.int16).tobytes()
        cls=cls(new_channel,new_rate,new_samplewidth)
        cls.write(data_resampled) 
        return cls
    
    def ReadWave(self):
        self.ioBytes.seek(0)  
        wf=wave.open(self.ioBytes, 'rb') 
        return wf
    def createWAVE(self): 
        self.ioBytes.seek(0, io.SEEK_END)
        wav_dosyasi=wave.open(self.ioBytes, 'wb')
        wav_dosyasi.setnchannels(self.chanell)
        wav_dosyasi.setsampwidth(self.width)
        wav_dosyasi.setframerate(self.rate) 
        return wav_dosyasi
    def write(self,data):
        self.WriteWave.writeframes(data)  
        
    def read(self,endChunk,startChunk=0):
        wf=self.ReadWave()
        if startChunk!=0:
            wf.readframes(startChunk)
        data=wf.readframes(endChunk)
        wf.close()
        return data
    
    
    def __del__(self): 
        if self.WriteWave:
            self.WriteWave.close()
        if not self.ioBytes.closed:
            self.ioBytes.close()
            
            
            
            
class SPEAKER(STREAM):
    def __init__(self, chanell=1, rate=8000, width=2) -> None:
        super().__init__(chanell, rate, width) 
        self._minMuteEg=None
        
        self.procLastSeconds=2
        self._lastTenSpeakCheck=[]
        

    
    def write(self, data): 
        self.WriteWave.writeframes(data) 
        self._addlastEg(data)
        print(self.speakCheck,"  ",end="\r") 
        
    def getEgValue(self,data):  
        return round(np.sqrt(np.mean(np.abs(np.frombuffer(data,dtype=np.int16)**2) )  ),1)
        
    def _addlastEg(self,data): 
        self._lastTenSpeakCheck.append(self.getEgValue(data)<=self.minMuteEg)
        self._lastTenSpeakCheck=self._lastTenSpeakCheck[-60:]#[-60:]
        
    @property
    def speakCheck(self): 
        if not self.minMuteEg or isinstance(self.minMuteEg,bool):
            check=True
        else:
            check=len(self._lastTenSpeakCheck)*0.8>sum(self._lastTenSpeakCheck)
        return check
    @property
    def totalSeconds(self):
        return round(self.WriteWave.getnframes()/self.WriteWave.getframerate(),1)
    @property
    def minMuteEg(self): 
        if self.totalSeconds<1:
            return True
        endchunk=int(self.WriteWave.getframerate()*self.procLastSeconds)
        startsChunk=self.WriteWave.getnframes()-endchunk
        startsChunk=startsChunk>0 and startsChunk or 0 
        
        np_data=np.frombuffer(self.read(endchunk,startsChunk),dtype=np.int16)
        self._minMuteEg=round(np.mean([self.getEgValue(np_data[i:i+178]) for i in range(0,len(np_data),178)]),1)
        return self._minMuteEg





class AUDIOSTREAMER:
    MediaType=MediaTypes.AUDIO
    MediaProtocol="RTP/AVP"
    MediaTranportType="sendrecv"
    ENDSTREAM="ENDSTREAM"
    def __init__(self) -> None:
        self.IVRMap=None
        self.IVRMenu=None
        self.IVRLastplayFile=None 
        self.InputSleep=None 
        
        self.StreamPlayed=None
        self.StreamOutData=None
        self.StreamInData=None
    @property
    def createPlayedStream(self):
        return STREAM.FileToStream(
            self.IVRLastplayFile,
            new_rate=self.StreamInData.WriteWave.getframerate(),
            new_channel=self.StreamInData.WriteWave.getnchannels(),
            new_samplewidth=self.StreamInData.WriteWave.getsampwidth(),
        )

    @property
    def isWithIvr(self):
        return isinstance(self.IVRMap,dict)
    def setStreamMc(self):
        #self.StreamPlayed
        pass
    def setStreamIvr(self,IVRMenu,InputSleep=5):
        self.IVRMap={}
        self.IVRMenu=IVRMenu
        self.InputSleep=InputSleep
        
    def loadStream(self,chanell=1,rate=8000,width=2):
        self.StreamOutData=STREAM(chanell=chanell,rate=rate,width=width)
        self.StreamInData=STREAM(chanell=chanell,rate=rate,width=width)
        self.setDTMFIVRStream()
    def setDTMFIVRStream(self,IvrKey=None):  
        if self.isWithIvr: 
            if not IvrKey:
                self.IVRLastplayFile=list(self.IVRMenu.keys())[0]
                self.IVRMenu=self.IVRMenu[self.IVRLastplayFile]
                self.StreamPlayed=self.createPlayedStream
            elif isinstance(self.IVRMenu.get(IvrKey),dict):
                self.IVRMenu=self.IVRMenu.get(IvrKey)
                self.IVRMap[self.IVRLastplayFile]=IvrKey
                self.IVRLastplayFile=list(self.IVRMenu.keys())[0]
                self.IVRMenu=self.IVRMenu[self.IVRLastplayFile] 
                self.StreamPlayed=self.createPlayedStream
            elif not self.IVRMenu.get(IvrKey):
                if IvrKey in self.IVRMenu.keys():
                    self.StreamPlayed=self.ENDSTREAM
                else:
                    self.StreamPlayed=None
                self.IVRMap[self.IVRLastplayFile]=IvrKey 
        else:
            return IvrKey
        
    def read(self,chunk):
        if self.StreamPlayed==self.ENDSTREAM:
            return
        pcmarray=bytes() 
        pcmarraynull=bytes()
        if self.StreamPlayed:
            pcmarray=self.StreamPlayed.ReadWave.readframes(chunk) 
        pcmarraynull=bytes([0x00] * (chunk-len(pcmarray)))
        if not self.StreamPlayed:
            self.InputSleep-=1/self.StreamOutData.WriteWave.getframerate()*len(pcmarraynull) 
        if self.InputSleep>0:
            self.StreamOutData.write(pcmarray+pcmarraynull)
            return pcmarray+pcmarraynull
    def write(self,data):
        self.StreamInData.write(data) 


    def save(self,savefile,onlyIn=False):  
        Input=self.StreamInData.readWAVE() 
        if not onlyIn:
            Output=self.StreamOutData.readWAVE()
            sound1=np.frombuffer(Output.readframes(Output.getnframes()), dtype=np.int16)
            sound2=np.frombuffer(Input.readframes(Input.getnframes()), dtype=np.int16)
            max_len = max(len(sound1), len(sound2))
            sound1 = np.pad(sound1, (0, max_len - len(sound1)), 'constant', constant_values=(0))
            sound2 = np.pad(sound2, (0, max_len - len(sound2)), 'constant', constant_values=(0))
            mixed_sound = sound1 + sound2
            mixed_sound = np.int16(mixed_sound / 2)
        else: 
            mixed_sound=np.frombuffer(Input.readframes(Input.getnframes()), dtype=np.int16)
        wavfile.write(savefile, 8000, mixed_sound)
        
        
