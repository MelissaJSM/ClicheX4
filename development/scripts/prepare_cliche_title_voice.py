"""로컬 TTS 후보를 타이틀 XA의 음성 구간에 맞춘다. 게임 BIN은 쓰지 않는다."""
from pathlib import Path
import sys,json,hashlib,subprocess
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.psx_xa_audio import decode_groups,encode_groups,replace_audio_groups,validate_audio_sector
D=ROOT/'work/ver_buki_riko/title_voice_v1'
RATE=37800;FIRST=117;VOICE_START=6.30
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    raw=(D/'BGM5_U.XA').read_bytes()
    sectors=[raw[i:i+2352] for i in range(0,len(raw),2352)]
    selected=[i for i,s in enumerate(sectors) if s[17]==0 and s[18]&4]
    assert selected==list(range(0,1544,8))
    for i in selected:validate_audio_sector(sectors[i])
    native,history=decode_groups(b''.join(sectors[i][24:2328] for i in selected))
    independent,rate=sf.read(D/'original_title.wav',dtype='int16')
    assert rate==RATE and np.array_equal(native,independent)
    prefix,history=decode_groups(b''.join(sectors[i][24:2328] for i in selected[:FIRST]))
    voice,rate=sf.read(D/'ryan_clean.wav');assert voice.ndim==1 and rate==24000
    voice=resample_poly(voice,63,40)
    # Only remove near-silent ends; preserve the generated pitch and speaking rate.
    energy=np.convolve(voice*voice,np.ones(378)/378,'same')**.5
    active=np.flatnonzero(energy>.0012);lo=max(0,int(active[0])-756);hi=min(len(voice),int(active[-1])+1134)
    voice=voice[lo:hi]
    voice-=voice.mean()
    active_rms=float(np.sqrt(np.mean(voice[abs(voice)>.006]**2)))
    gain=min(.115/active_rms,.65/np.max(abs(voice)))
    voice*=gain
    ramp=min(189,len(voice)//2);voice[:ramp]*=np.linspace(0,1,ramp);voice[-ramp:]*=np.linspace(1,0,ramp)
    target=native.astype(np.float64)/32768
    start=FIRST*2016
    target[start:]=0
    # Fade out only the last 30 ms of the original logo-sound tail before speech.
    tail=int(.03*RATE)
    target[start:start+tail]=native[start:start+tail]/32768*np.linspace(1,0,tail)[:,None]
    voice_at=int(VOICE_START*RATE)
    target[voice_at:voice_at+len(voice)]+=voice[:,None]
    # Restrained stereo reflections; no pitch shifting, chorus, or conversion.
    reflections=[(.061,.11,.07),(.089,.07,.11),(.151,.055,.04),(.213,.035,.05),(.327,.024,.018),(.443,.012,.018)]
    for delay,left,right in reflections:
        at=voice_at+round(delay*RATE)
        target[at:at+len(voice),0]+=voice*left;target[at:at+len(voice),1]+=voice*right
    assert np.max(abs(target))<1
    target_pcm=np.rint(target*32768).astype(np.int16)
    assert np.array_equal(target_pcm[:start],native[:start])
    encoded,final=encode_groups(target_pcm[start:],history)
    decoded,_=decode_groups(encoded,history)
    error=decoded.astype(float)-target_pcm[start:]
    snr=float(10*np.log10(np.sum(target_pcm[start:].astype(float)**2)/np.sum(error**2)))
    assert snr>26,(snr,'poor XA quality')
    patched=list(sectors)
    for n,index in enumerate(selected[FIRST:]):
        patched[index]=replace_audio_groups(sectors[index],encoded[n*2304:(n+1)*2304])
    output=b''.join(patched)
    assert len(output)==len(raw)
    changed=[i for i,(a,b) in enumerate(zip(sectors,patched)) if a!=b]
    assert changed==selected[FIRST:]
    (D/'title_replacement.xa').write_bytes(output)
    sf.write(D/'title_master.wav',target_pcm,RATE,subtype='PCM_16')
    ff=ROOT/'work/tools/voice_env/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
    decoded_path=D/'cliche_title_final.wav'
    subprocess.run([str(ff),'-hide_banner','-loglevel','error','-y','-i',str(D/'title_replacement.xa'),'-map','0:a:0',str(decoded_path)],check=True)
    ffpcm,rate=sf.read(decoded_path,dtype='int16')
    assert rate==RATE and np.array_equal(ffpcm,np.vstack((prefix,decoded)))
    record={'original_raw_sha256':sha(raw),'replacement_raw_sha256':sha(output),
        'source_wav':'ryan_clean.wav','source_wav_sha256':sha((D/'ryan_clean.wav').read_bytes()),
        'selected_voice':'Ryan / Cliché! X four!','sample_rate':RATE,'channels':2,
        'total_pcm_samples':len(native),'duration_seconds':len(native)/RATE,
        'preserved_prefix_sectors':FIRST,'preserved_prefix_seconds':start/RATE,
        'voice_start_seconds':VOICE_START,'generated_trim_samples':[lo,hi],
        'gain':gain,'reflections':reflections,'xa_snr_db':snr,'max_error_lsb':int(np.max(abs(error))),
        'original_decoder_matches_ffmpeg':True,'replacement_decoder_matches_ffmpeg':True,
        'modified_relative_sectors':changed,'nonvoice_channels_and_padding_preserved':True,
        'new_form2_edc_valid':True,'original_form2_edc_absent':True,
        'pitch_shift':False,'time_stretch':False,'human_listening_completed':False,
        'audition_wav':'work/ver_buki_riko/title_voice_v1/cliche_title_final.wav'}
    (D/'preparation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps(record,ensure_ascii=True))
if __name__=='__main__':main()
