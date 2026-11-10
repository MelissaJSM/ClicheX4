"""원작 로고 효과음의 잔향과 새 타이틀 콜을 연결하고 원시 XA 섹터 패치를 준비한다."""
import json,sys,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly,sosfilt,butter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.overhaul_audio_audit import SOURCES,D,digest,sha
from src.psx_xa_audio import decode_groups,encode_groups,replace_audio_groups,validate_audio_sector
RATE=37800;LBA=226570;COUNT=1544;FIRST=108;CUT=6.24;VOICE_AT=6.10
def main():
    out=D/'title/prepared';out.mkdir(exist_ok=False)
    source=ROOT/SOURCES['us'][0];assert digest(source)==SOURCES['us'][1]
    with source.open('rb') as f:f.seek(LBA*2352);raw=f.read(COUNT*2352)
    sectors=[raw[o:o+2352] for o in range(0,len(raw),2352)];selected=list(range(0,COUNT,8))
    for i in selected:validate_audio_sector(sectors[i])
    original,_=decode_groups(b''.join(sectors[i][24:2328] for i in selected))
    prefix,history=decode_groups(b''.join(sectors[i][24:2328] for i in selected[:FIRST]))
    native=original.astype(float)/32768;target=native.copy();cut=round(CUT*RATE);target[cut:]=0
    fade=round(.035*RATE);target[cut-fade:cut]*=np.linspace(1,0,fade)[:,None]
    # Use only pre-speech mechanical logo sound to continue its natural decay.
    tail=native[round(5.25*RATE):cut].copy();tail=sosfilt(butter(2,6500,fs=RATE,output='sos'),tail,axis=0)
    for delay,gain in ((.057,.55),(.103,.38),(.181,.27),(.283,.18),(.431,.12),(.653,.07),(.947,.035)):
        at=round((5.25+delay)*RATE);lo=max(cut,at);hi=min(len(target),at+len(tail))
        if hi>lo:target[lo:hi]+=tail[lo-at:hi-at]*gain
    voice_path=D/'title/aiden_v2.wav';v,sr=sf.read(voice_path);assert v.ndim==1 and sr==24000
    v=resample_poly(v,63,40);energy=np.sqrt(np.convolve(v*v,np.ones(378)/378,mode='same'))
    active=np.flatnonzero(energy>.0015);lo=max(0,int(active[0])-378);hi=min(len(v),int(active[-1])+756);v=v[lo:hi]
    v=sosfilt(butter(2,75,btype='highpass',fs=RATE,output='sos'),v);v-=v.mean()
    gain=min(.19/np.sqrt(np.mean(v[abs(v)>.008]**2)),.66/max(abs(v)));v*=gain
    ramp=189;v[:ramp]*=np.linspace(0,1,ramp);v[-ramp:]*=np.linspace(1,0,ramp)
    at=round(VOICE_AT*RATE);target[at:at+len(v)]+=v[:,None]
    echoes=[(.075,.28,.20),(.128,.20,.25),(.215,.13,.17),(.33,.10,.08),(.49,.06,.07),(.65,.035,.04),(.89,.020,.025)]
    wet=sosfilt(butter(2,5200,fs=RATE,output='sos'),v)
    for delay,l,r in echoes:
        start=at+round(delay*RATE);assert start+len(v)<len(target)
        target[start:start+len(v)]+=wet[:,None]*np.array([l,r])[None,:]
    assert np.max(abs(target))<1,'Clipping in title mix'
    pcm=np.rint(target*32768).astype(np.int16);first=FIRST*2016
    assert np.array_equal(pcm[:first],original[:first])
    encoded,_=encode_groups(pcm[first:],history);decoded,_=decode_groups(encoded,history)
    snr=float(10*np.log10(np.sum(pcm[first:].astype(float)**2)/np.sum((decoded.astype(float)-pcm[first:])**2)))
    assert snr>26
    revised=list(sectors)
    for n,i in enumerate(selected[FIRST:]):revised[i]=replace_audio_groups(sectors[i],encoded[n*2304:(n+1)*2304])
    replacement=b''.join(revised);(out/'title_replacement.xa').write_bytes(replacement)
    sf.write(out/'master.wav',pcm,RATE,subtype='PCM_16');sf.write(out/'preview.wav',np.vstack((prefix,decoded)),RATE,subtype='PCM_16')
    ff=ROOT/'work/tools/voice_env/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
    independent=subprocess.run([str(ff),'-v','error','-i',str(out/'title_replacement.xa'),'-map','0:a:0','-f','s16le','pipe:1'],capture_output=True,check=True).stdout
    assert independent==np.vstack((prefix,decoded)).astype('<i2').tobytes()
    proof=dict(issue='C-07',sample_rate=RATE,voice_source=voice_path.relative_to(ROOT).as_posix(),voice_sha256=digest(voice_path),source_trim=[lo,hi],gain=gain,preserved_prefix_seconds=first/RATE,voice_start_seconds=VOICE_AT,native_voice_removed_from_seconds=CUT,echoes=echoes,peak=float(np.max(abs(target))),xa_snr_db=snr,independent_ffmpeg_decode_exact=True,no_pitch_or_time_stretch=True,runtime_verified=False,human_listening_verified=False,source_sha256=sha(raw),after_sha256=sha(replacement))
    (out/'mix.json').write_text(json.dumps(proof,indent=2),encoding='utf8')
    for project in ('ver_buki_riko','ver_rin_nana'):
        baseline,expected=SOURCES[project];p=ROOT/baseline;assert digest(p)==expected
        with p.open('rb') as f:f.seek(LBA*2352);before=f.read(COUNT*2352)
        dest=out/project;dest.mkdir();records=[]
        for i in range(COUNT):
            old=before[i*2352:(i+1)*2352];new=revised[i]
            if old==new:continue
            assert i in selected[FIRST:]
            validate_audio_sector(old);validate_audio_sector(new,allow_absent_edc=False)
            assert old[:24]==new[:24] and old[2328:2348]==new[2328:2348]
            file=dest/f'{LBA+i}.bin';file.write_bytes(new)
            records.append(dict(lba=LBA+i,before_sha256=sha(old),after_sha256=sha(new),path=file.relative_to(ROOT).as_posix(),size=2352))
        proposal=dict(project=project,issue='C-07',baseline=baseline,baseline_sha256=expected,raw_sectors=records,proof=proof)
        (dest/'raw_sectors.json').write_text(json.dumps(proposal,indent=2),encoding='utf8')
    print(json.dumps({'directory':out.relative_to(ROOT).as_posix(),'changed_sectors':len(selected[FIRST:]),'snr':snr,'peak':proof['peak']}))
if __name__=='__main__':main()
