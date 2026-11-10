"""Check format acceptance in the system XAudio2 without submitting/playing sound."""
from pathlib import Path
import sys,ctypes,json
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R))
from src.steam_audio import wave_chunks
P=ctypes.c_void_p;U=ctypes.c_uint32;I=ctypes.c_int32
ole=ctypes.OleDLL('ole32');ole.CoInitializeEx(None,0)
engine=P();dll=ctypes.WinDLL('xaudio2_9.dll');dll.XAudio2Create.argtypes=[ctypes.POINTER(P),U,U];dll.XAudio2Create.restype=I
hr=dll.XAudio2Create(ctypes.byref(engine),0,0xffffffff)
if hr<0:raise RuntimeError(hex(hr&0xffffffff))
def method(obj,index,restype,*args):
 vt=ctypes.cast(obj,ctypes.POINTER(ctypes.POINTER(P))).contents
 return ctypes.WINFUNCTYPE(restype,P,*args)(vt[index])
master=P();results=[]
try:
 hr=method(engine,7,I,ctypes.POINTER(P),U,U,U,P,P,U)(engine,ctypes.byref(master),2,48000,0,None,None,6)
 if hr<0:raise RuntimeError('Mastering voice '+hex(hr&0xffffffff))
 for name in ('native','hurt','death'):
  path=(R/'work/steam_port_20261109/original/nativeDX10/X4/sound/se/vo_pl00/wav/VO_PL00_PG00_ID00.xsew') if name=='native' else Path(__file__).parent/(name+'.xsew')
  raw=path.read_bytes();fmt=next(raw[a:a+n] for t,a,n in wave_chunks(raw) if t==b'fmt ')
  data=ctypes.create_string_buffer(fmt);voice=P()
  hr=method(engine,5,I,ctypes.POINTER(P),P,U,ctypes.c_float,P,P,P)(engine,ctypes.byref(voice),data,0,2.0,None,None,None)
  results.append({'effect':name,'CreateSourceVoice_hresult':hr,'source_started':False,'buffer_submitted':False})
  if voice:method(voice,18,None)(voice)
finally:
 if master:method(master,18,None)(master)
 method(engine,2,U)(engine)
 ole.CoUninitialize()
(Path(__file__).parent/'xaudio_format_verification.json').write_text(json.dumps({'passed':all(r['CreateSourceVoice_hresult']==0 for r in results),'checks':results},indent=2)+'\n')
print(results)
