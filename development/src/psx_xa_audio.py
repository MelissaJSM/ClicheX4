"""제한된 37,800 Hz / 4-bit stereo XA 음원 교체. 섹터 배치는 호출자가 보존한다.

CD-XA sound-group 명세를 구현한다. SPU의 다섯 번째 예측 필터는 사용하지 않는다.
독립 FFmpeg 디코더와 실제 원본으로 검증한다. 원본/다른 채널은 쓰지 않는다.
"""
import struct
import numpy as np
from numba import njit
from src.psx_sector import edc

SAMPLES_PER_SECTOR = 2016
COEFFICIENTS = np.array(((0,0),(60,0),(115,-52),(98,-55)),dtype=np.int64)

def validate_audio_sector(raw, *, file_number=1, channel=0, allow_absent_edc=True):
    if len(raw)!=2352 or raw[:12]!=b'\0'+b'\xff'*10+b'\0' or raw[15]!=2:
        raise ValueError('Expected raw Mode2 sector')
    if raw[16:20]!=raw[20:24] or raw[16]!=file_number or raw[17]!=channel:
        raise ValueError('XA channel/subheader mismatch')
    if raw[18]&0x7e != 0x64 or raw[19]!=1:
        raise ValueError('Expected realtime Form2 stereo 37800 Hz 4-bit XA')
    checksum=struct.unpack_from('<I',raw,2348)[0]
    if checksum!=edc(raw[16:2348]) and not (allow_absent_edc and checksum==0):
        raise ValueError('XA Form2 EDC mismatch')
    validate_groups(raw[24:2328])

def validate_groups(data):
    if not data or len(data)%128:
        raise ValueError('Incomplete XA sound group')
    for off in range(0,len(data),128):
        g=data[off:off+128]
        if g[:4]!=g[4:8] or g[8:12]!=g[12:16]:
            raise ValueError('XA duplicate group parameters differ')
        if any(p>>4>3 or p&15>12 for p in g[4:12]):
            raise ValueError('Unsupported XA predictor/shift')

@njit(cache=True)
def _decode(data,history):
    groups=len(data)//128
    pcm=np.zeros((groups*112,2),dtype=np.int16)
    hist=history.copy()
    for group in range(groups):
        base=group*128
        for block in range(4):
            for ch in range(2):
                param=int(data[base+4+block*2+ch]);shift=12-(param&15)
                a,b=COEFFICIENTS[param>>4]
                old,older=hist[ch]
                for j in range(28):
                    nibble=(int(data[base+16+block+j*4])>>(ch*4))&15
                    signed=nibble if nibble<8 else nibble-16
                    value=(signed<<shift)+((old*a+older*b+32)>>6)
                    value=min(32767,max(-32768,value))
                    pcm[group*112+block*28+j,ch]=value
                    older=old;old=value
                hist[ch,0]=old;hist[ch,1]=older
    return pcm,hist

def decode_groups(data,history=None):
    validate_groups(data)
    hist=np.zeros((2,2),dtype=np.int64) if history is None else np.asarray(history,dtype=np.int64)
    if hist.shape!=(2,2):raise ValueError('Invalid stereo predictor history')
    return _decode(np.frombuffer(data,dtype=np.uint8),hist)

@njit(cache=True)
def _encode(pcm,history):
    groups=len(pcm)//112
    data=np.zeros(groups*128,dtype=np.uint8);hist=history.copy()
    for group in range(groups):
        base=group*128
        for block in range(4):
            for ch in range(2):
                offset=group*112+block*28
                best_error=1e30;best_param=0
                best_nibbles=np.zeros(28,dtype=np.uint8)
                best_old=0;best_older=0
                for filt in range(4):
                    a,b=COEFFICIENTS[filt]
                    for shift in range(13):
                        step=1<<(12-shift);old,older=hist[ch]
                        error=0.0;packed=np.zeros(28,dtype=np.uint8)
                        for j in range(28):
                            predicted=(old*a+older*b+32)>>6
                            nibble=int(np.rint((int(pcm[offset+j,ch])-predicted)/step))
                            nibble=min(7,max(-8,nibble))
                            value=min(32767,max(-32768,predicted+nibble*step))
                            delta=float(int(pcm[offset+j,ch])-value);error+=delta*delta
                            packed[j]=nibble&15;older=old;old=value
                        if error<best_error:
                            best_error=error;best_param=filt*16+shift
                            best_nibbles=packed.copy();best_old=old;best_older=older
                data[base+4+block*2+ch]=best_param
                for j in range(28):data[base+16+block+j*4]|=int(best_nibbles[j])<<(ch*4)
                hist[ch,0]=best_old;hist[ch,1]=best_older
        data[base:base+4]=data[base+4:base+8]
        data[base+12:base+16]=data[base+8:base+12]
    return data,hist

def encode_groups(pcm,history=None):
    pcm=np.asarray(pcm)
    if pcm.ndim!=2 or pcm.shape[1]!=2 or len(pcm)==0 or len(pcm)%112:
        raise ValueError('PCM must be complete stereo XA sound groups')
    if not np.isfinite(pcm).all() or np.min(pcm)<-32768 or np.max(pcm)>32767:
        raise ValueError('PCM outside signed 16-bit range')
    hist=np.zeros((2,2),dtype=np.int64) if history is None else np.asarray(history,dtype=np.int64)
    if hist.shape!=(2,2):raise ValueError('Invalid stereo predictor history')
    data,final=_encode(np.rint(pcm).astype(np.int16),hist)
    result=data.tobytes();validate_groups(result)
    return result,final

def replace_audio_groups(raw,groups, *, file_number=1, channel=0):
    validate_audio_sector(raw,file_number=file_number,channel=channel)
    if len(groups)!=2304:raise ValueError('XA sector sound-group length changed')
    validate_groups(groups)
    result=bytearray(raw);result[24:2328]=groups
    result[2348:]=struct.pack('<I',edc(result[16:2348]))
    validate_audio_sector(result,file_number=file_number,channel=channel,allow_absent_edc=False)
    return bytes(result)
