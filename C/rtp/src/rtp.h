typedef struct {
   unsigned short version : 2;
   unsigned short padding : 1;
   unsigned short extension : 1;
   unsigned short csrc_count : 4;
   unsigned short marker : 1;
   unsigned short payload_type : 7;
   unsigned short sequence_num : 16;
   unsigned int timestampe : 32;
   unsigned int ssrc : 32;
   unsigned int *csrc;
}RtpHeader;
