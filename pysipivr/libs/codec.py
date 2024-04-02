
import os
from ctypes import *
import struct,numpy as np,audioop





 
ILBCNOOFWORDS_MAX=25#encode frame
BLOCKL_MAX=240#frame

 
ilbc_lib = CDLL(os.path.join(os.path.dirname(os.path.dirname(__file__)),"third-party/ilbc/iLBC_test.so"))



decodeiLBC_CtypeCon=ilbc_lib.decodeiLBC_Ctype
decodeiLBC_CtypeCon.argtypes=(POINTER(c_short), POINTER(c_short),c_short,c_short,c_short,)
decodeiLBC_CtypeCon.restype = c_short
def decodeiLBC_Ctype(ilbcbytes,enhancer=0,bad_packet=1,mspart=30):  
    ilbcpcmarray=np.frombuffer(ilbcbytes,dtype=np.int16)
    ilbcpcmarray=(c_short * len(ilbcpcmarray))(*ilbcpcmarray)
    decode_data = (c_short * BLOCKL_MAX)(0,)   
    result=decodeiLBC_CtypeCon(decode_data,ilbcpcmarray,bad_packet,enhancer,mspart) 
    return np.frombuffer(decode_data,dtype=np.int16).tobytes()


 

encodeiLBC_CtypeCon=ilbc_lib.encodeiLBC_Ctype
encodeiLBC_CtypeCon.argtypes=(POINTER(c_short), POINTER(c_short),c_short)
encodeiLBC_CtypeCon.restype = c_short
def encodeiLBC_Ctype(pcmarray,mspart=30): 
    pcmarray=np.frombuffer(pcmarray,dtype=np.int16)
    pcmarray=(c_short * len(pcmarray))(*pcmarray)
    encoded_data = (c_short * ILBCNOOFWORDS_MAX)(0,)   
    lenght=encodeiLBC_CtypeCon(pcmarray, encoded_data, mspart)
    return np.frombuffer(encoded_data,dtype=np.int16).tobytes()





def encodePCMU(packet,*args,**kwargs) -> bytes:   
    return audioop.lin2ulaw(packet, 2)

def decodePCMU(packet,*args,**kwargs) -> None:
    return audioop.ulaw2lin(packet, 2) 


def decodePCMA(packet,*args,**kwargs) -> bytes:
    data = audioop.alaw2lin(packet, 2)
    #data = audioop.bias(data, 1, 128)
    return data


def encodePCMA(packet,*args,**kwargs) -> bytes: 
    #packet = audioop.bias(packet, 1, -128)
    packet = audioop.lin2alaw(packet, 2)
    return packet
    
    
__all__=[
    "decodeiLBC_Ctype",
    "encodeiLBC_Ctype"
]



