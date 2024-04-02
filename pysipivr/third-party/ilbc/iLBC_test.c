
   /******************************************************************

       iLBC Speech Coder ANSI-C Source Code

       iLBC_test.c

       Copyright (C) The Internet Society (2004).
       All Rights Reserved.

   ******************************************************************/

   #include <math.h>
   #include <stdlib.h>
   #include <stdio.h>
   #include <string.h>
   #include "iLBC_define.h"
   #include "iLBC_encode.h"
   #include "iLBC_decode.h"

   /* Runtime statistics */
   #include <time.h>

   #define ILBCNOOFWORDS_MAX   (NO_OF_BYTES_30MS/2)




    short encodeiLBC_Ctype(   /* (o) Number of bytes encoded */ 
        short *normal_data,                /* (i) The signal block to encode*/
        short *encoded_data,            /* (o) The encoded bytes */
        short mspart                    /* 30 ms ,20ms*/
    ){ 
        iLBC_Enc_Inst_t iLBCenc_inst;
        initEncode(&iLBCenc_inst, mspart);  
        float block[BLOCKL_MAX];
 

        for (int k=0; k<iLBCenc_inst.blockl; k++)
            block[k] = (float)normal_data[k];
        iLBC_encode((unsigned char *)encoded_data, block, &iLBCenc_inst);
        return (iLBCenc_inst.no_of_bytes);
    }

   

 



    short decodeiLBC_Ctype(       /* (o) Number of decoded samples */ 
        short *decoded_data,        /* (o) Decoded signal block*/
        short *encoded_data,        /* (i) Encoded bytes */
        short bad_packet,                   /* (i) 0=PL, 1=Normal */
        short enhancer,                      /* use enhancer*/
        short mspart                        /* 30 ms ,20ms*/
    ){ 
        int k;
        iLBC_Dec_Inst_t iLBCdec_inst;
        initDecode(&iLBCdec_inst, mspart, enhancer); // 30ms mod
        float decblock[BLOCKL_MAX], dtmp;  

        iLBC_decode(decblock, (unsigned char *)encoded_data,&iLBCdec_inst, bad_packet);

        for (k=0; k<iLBCdec_inst.blockl; k++){
            dtmp=decblock[k];

            if (dtmp<MIN_SAMPLE)
                dtmp=MIN_SAMPLE;
            else if (dtmp>MAX_SAMPLE)
                dtmp=MAX_SAMPLE;
            decoded_data[k] = (short) dtmp;
        } 

        return (iLBCdec_inst.blockl);
    } 
    


int main() { 
 
    
    FILE* encodedFile;
    encodedFile = fopen("/home/ersan/Downloads/testfile.ilbc", "rb");

    if (!encodedFile) {
        printf("Encoded file açılamadı.\n");
        return 1;
    }  
    short encodedData[ILBCNOOFWORDS_MAX];

    fread(encodedData, sizeof(short), ILBCNOOFWORDS_MAX, encodedFile);
    fclose(encodedFile);
    printf("\n"); 
    for (int i = 0; i < 25; i++) {
        printf("%d ", encodedData[i]);
    }
    printf("\n"); 
   
    short decodedData[BLOCKL_MAX];

 
    int decodedLength = decodeiLBC_Ctype(decodedData, encodedData, 1,0,30);
    for (int i = 0; i < decodedLength; i++) {
        printf("%d ", decodedData[i]);
    }

    printf("\n"); 
    short encodedData2[ILBCNOOFWORDS_MAX];
    int encodelenght=encodeiLBC_Ctype(decodedData,encodedData2,30);

    for (int i = 0; i < 25; i++) {
        printf("%d ", encodedData2[i]);
    }


    return 0;
}
