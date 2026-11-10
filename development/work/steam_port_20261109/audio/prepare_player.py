from pathlib import Path
import sys,struct,json,hashlib,subprocess,math,wave
import numpy as np
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R))
from scripts.c01_audio_build import read_disc,get_bank
from src.psx_spu_audio import decode_spu
from src.steam_audio import wave_info,wave_chunks,encode_native_mono
W=R/'work/steam_port_20261109';D=W/'audio';O=W/'original'
FF=R/'work/tools/voice_env/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
def sha(b):return hashlib.sha256(b).hexdigest()
assets=[]
for mode in ['ver_rin_nana','ver_buki_riko']:
 p=json.loads((R/'projects'/mode/'current_build.json').read_text('utf8'));path=(R/p['cue']).with_suffix('.bin')
 with path.open('rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest()==p['sha256']
 a,_=read_disc(path,['PL00_U.ARC','PL01_U.ARC','PL02_U.ARC']);assets.append(a)
for name in assets[0]:
 assert get_bank(assets[0][name],3)[:2]==get_bank(assets[1][name],3)[:2]
 h,b,q,*_=get_bank(assets[0][name],3)
 assert h[8:16]==bytes.fromhex('8300001483000014') and h[56:60]==bytes.fromhex('83001014')
 tone=q['vab_offset']+32+128*16
 assert h[tone+2]==104 and h[tone+32+2]==100
 waves=[]
 for wid in (1,2):
  t=q['waves'][wid-1];raw=b[t['body_offset']:t['body_offset']+t['bytes']];waves.append(raw)
 if name=='PL00_U.ARC': chosen=waves
 else:assert waves==chosen
assert sha(chosen[0])=='3849f73da2ec664732118255463da30fcd8438fc29ef37db4b0b18c1b8c51029'
assert sha(chosen[1])=='bca9ec5b6b47b1247ec483f6b95cb8de3d94c58e03132255c63df5f434e4cfbc'
report=[]
for label,raw,pitch in [('hurt',chosen[0],1024),('death',chosen[1],1290)]:
 pcm=np.array(decode_spu(raw).pcm,dtype='<i2')
 # Exact native pitch ratio: interpolate the decoded sample at 48 kHz.
 rate=44100*pitch/4096; count=round(len(pcm)*48000/rate)
 scaled=np.interp(np.arange(count)*rate/48000,np.arange(len(pcm)),pcm.astype(float))
 # Keep one common peak headroom. Hurt retains the accepted +5.02 dB increase
 # relative to a 0.40-peak baseline. This is an initial Steam mix, not PS1 SPU emulation.
 peak=.40*10**(5.02/20) if label=='hurt' else .65
 scaled*=peak*32767/max(abs(scaled));scaled=np.rint(scaled).astype('<i2')
 master=D/(label+'_master.wav')
 with wave.open(str(master),'wb') as f:f.setparams((1,2,48000,len(scaled),'NONE',''));f.writeframes(scaled.tobytes())
 template=(O/'nativeDX10/X4/sound/se/vo_pl00/wav/VO_PL00_PG00_ID00.xsew').read_bytes()
 result=encode_native_mono(scaled,template);info=wave_info(result)
 out=D/(label+'.xsew');out.write_bytes(result)
 decoded=subprocess.run([str(FF),'-v','error','-i',str(out),'-f','s16le','pipe:1'],capture_output=True,check=True).stdout
 decoded=np.frombuffer(decoded,dtype='<i2');assert len(decoded)>=len(scaled)
 delta=decoded[:len(scaled)].astype(float)-scaled
 snr=10*math.log10(np.sum(scaled.astype(float)**2)/max(1,np.sum(delta*delta)))
 assert snr>20 and max(abs(decoded.astype(int)))<32767,(label,snr)
 report.append({'effect':label,'source_adpcm_sha256':sha(raw),'pitch':pitch,'native_sample_rate':rate,'duration':len(pcm)/rate,'output':out.relative_to(R).as_posix(),'sha256':sha(result),'encoded_duration':info['frames']/info['rate'],'snr_db':snr,'peak':int(max(abs(decoded.astype(int)))),'actual_listening_verified':False})
(D/'player_sources.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
