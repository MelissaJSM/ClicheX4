"""C-01/C-06: 원본·완성 BIN을 보존하고 같은 길이의 음향 자원 제안을 만든다."""
import json, struct, sys, subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.overhaul_audio_audit import SOURCES,D,digest,sha,entry,bank_commands
from scripts.discover_inputs import DiscReader,psx_arc
from scripts.inventory_riko_voice import parse_bank
from src.psx_spu_audio import decode_spu,encode_fixed_oneshot,validate_oneshot_template,vag_container

PLAYERS=('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC')
STAGES=tuple(f'{p}{n}{s}.ARC' for n in (5,6,7) for p,s in (('ST','_1_1'),('ONPARE','')))
DEST=D/'prepared'
CACHE={}

def load(source,names):
    rel,expected=SOURCES[source];p=ROOT/rel
    if digest(p)!=expected:raise ValueError('Unsupported source SHA256')
    with p.open('rb') as f:
        d=DiscReader(f,p.stat().st_size);info=d.inspect();found={}
        for r in info['files']:
            n=r['name'].split(';')[0]
            if n in names:found[n]=(d.read(r['lba'],r['size']),r)
    if set(found)!=set(names):raise ValueError('Missing requested resources')
    return found

def bank(a,slot):
    es=psx_arc(a)
    for i,e in enumerate(es[:-1]):
        h=entry(a,e);b=entry(a,es[i+1])
        try:q=parse_bank(h,b,False)
        except (ValueError,struct.error,IndexError):continue
        if q['slot']==slot:return i,e,es[i+1],h,b,q
    raise ValueError('Missing bank')

def tone_base(q):return q['vab_offset']+32+128*16
def tone(h,q,n):return h[tone_base(q)+n*32:tone_base(q)+(n+1)*32]
def wave(b,q,n):
    w=q['waves'][n-1];return b[w['body_offset']:w['body_offset']+w['bytes']]

def prepared_wave(jp_raw,length,label):
    key=(sha(jp_raw),length)
    if key in CACHE:return CACHE[key]
    template=bytearray(length);template[17]=4;template[-31]=1;template[-15]=7
    cap=validate_oneshot_template(template)
    source=np.array(decode_spu(jp_raw).pcm,dtype=np.float64)
    # Half the native sampling rate; +12 to the VAB centre note preserves pitch.
    reduced=resample_poly(source,1,2);pcm=np.zeros(cap,dtype=np.int16)
    assert len(reduced)<=cap
    gain=min(1.,32112/max(abs(reduced)));reduced*=gain
    pcm[:len(reduced)]=np.rint(reduced).astype(np.int16);pcm[:28]=0
    raw,proof=encode_fixed_oneshot(pcm,bytes(template));assert proof['snr_db']>18,proof
    assert len(raw)==length and validate_oneshot_template(raw)==cap
    decoded=np.array(decode_spu(raw).pcm,dtype=np.int16)
    preview=DEST/'previews';preview.mkdir(parents=True,exist_ok=True)
    sf.write(preview/f'{label}_{length}.wav',decoded,11025,subtype='PCM_16')
    vag=preview/f'{label}_{length}.vag';vag.write_bytes(vag_container(raw,11025))
    ff=ROOT/'work/tools/voice_env/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
    independent=subprocess.run([str(ff),'-v','error','-i',str(vag),'-f','s16le','pipe:1'],capture_output=True,check=True).stdout
    # ffmpeg decodes the terminating padding block too; playback ends before it.
    independent=np.frombuffer(independent,dtype='<i2')[:len(decoded)]
    delta=independent.astype(np.int32)-decoded.astype(np.int32)
    # FFmpeg's floating predictor and our integer SPU predictor round differently.
    independent_snr=float(10*np.log10(np.sum(decoded.astype(float)**2)/max(1,np.sum(delta.astype(float)**2))))
    assert independent_snr>45 and np.max(abs(delta))<128
    proof.update(source_sha256=sha(jp_raw),encoded_sha256=sha(raw),source_samples=len(source),resampled_samples=len(reduced),playable_samples=cap,sample_rate=11025,resample_peak_gain=gain,independent_ffmpeg_max_error=int(np.max(abs(delta))),independent_ffmpeg_snr_db=independent_snr,source_pitch_preserved=True)
    CACHE[key]=(raw,proof);return raw,proof

def replace(a,e,data):
    assert len(data)==e['size'];a[e['offset']:e['offset']+e['size']]=data

def prepare_player(a,jp6):
    original=a;result=bytearray(a);_,he,be,h,b,q=bank(a,3);_,_,_,native,_,nq=bank(a,0)
    assert (q['program_count'],q['command_count'])==(1,13)
    assert all(not any(decode_spu(wave(b,q,n)).pcm) for n in range(1,q['wave_count']+1))
    h=bytearray(h);b=bytearray(b);changes=[]
    for target,source in ((0,6),(1,6),(12,0)):
        off=8+target*4;old=bytes(h[off:off+4]);c=native[8+source*4:12+source*4]
        assert c==bytes.fromhex('80006003' if source==6 else '80000006')
        new=c[:3]+bytes([(c[3]&0xe0)|(old[3]&31)])
        h[off:off+4]=new;changes.append(dict(issue='C-01',command=target,before=old.hex(),after=new.hex(),native_bank=0,native_command=source,spu_channel=new[3]&31))
    # Last muted death sample is unused after command 12 was redirected above.
    death=q['waves'][-1];last=death['wave_id'];assert death['bytes'] in (14448,15744)
    for c in bank_commands(bytes(h),bytes(b))['commands']:
        if c['bank']==3:assert all(t['wave_id']!=last for t in c['tones'])
    _,_,_,jh,jb,jq=bank(jp6,2)
    sizes=(6720,death['bytes']-6720);encoded=[];proofs=[]
    for num,jwave,tn in ((0,5,5),(1,8,10)):
        raw,proof=prepared_wave(wave(jb,jq,jwave),sizes[num],f'peacock_{jwave}')
        encoded.append(raw);proofs.append(proof)
        t=bytearray(tone(jh,jq,tn));t[3]=64;t[4]+=12;struct.pack_into('<H',t,22,last+num)
        off=tone_base(q)+(14+num)*32;h[off:off+32]=t
    # X has an unused tone 13 inside the expanded 16-record program: keep it silent.
    if q['tone_count']==13:
        off=tone_base(q)+13*32;h[off:off+32]=tone(h,q,0)
    struct.pack_into('<HH',h,q['vab_offset']+20,16,last+1)
    h[q['vab_offset']+32]=16
    size_table=tone_base(q)+16*32
    struct.pack_into('<HH',h,size_table+last*2,sizes[0]//8,sizes[1]//8)
    b[death['body_offset']:death['body_offset']+death['bytes']]=b''.join(encoded)
    after=parse_bank(bytes(h),bytes(b),False);assert after['body_bytes']==q['body_bytes'] and after['wave_count']==last+1
    assert after['waves'][:-2]==q['waves'][:-1]
    for c in bank_commands(bytes(h),bytes(b))['commands']:
        if c['bank']==3:
            assert all(t['tone']<14 and not any(decode_spu(wave(b,after,t['wave_id'])).pcm) for t in c['tones'])
        else:assert c['id'] in (0,1,10,12)
    assert h[8+2*4:8+10*4]==bank(original,3)[3][8+2*4:8+10*4]
    assert h[8+10*4:8+12*4]==bank(original,3)[3][8+10*4:8+12*4]
    assert len(h)==he['size'] and len(b)==be['size']
    replace(result,he,h);replace(result,be,b)
    changes.append(dict(issue='C-06',kind='unused_muted_death_storage_for_boss_only',wave_ids=[last,last+1],tones=[14,15],original_bytes=death['bytes'],new_bytes=sizes,proofs=proofs,all_player_voice_commands_still_mute=True,all_player_sfx_commands_preserved=True,program_tones=16,total_spu_bytes_unchanged=True))
    return bytes(result),changes,[he['offset'],he['size'],be['offset'],be['size']]

def prepare_stage(a,jp,stage):
    result=bytearray(a);_,he,be,h,b,q=bank(a,2);_,_,_,jh,jb,jq=bank(jp,2);h=bytearray(h);b=bytearray(b);changes=[]
    if stage==5:
        old=tone(h,q,9);new=tone(jh,jq,9);assert old[2]==0 and new[2]==110
        assert old[:2]+old[3:]==new[:2]+new[3:] and wave(b,q,6)==wave(jb,jq,6)
        h[tone_base(q)+9*32+2]=110
        changes.append(dict(issue='C-06',kind='restore_jp_tone_volume',tone=9,wave=6,before=0,after=110,waveform_unchanged=True))
    elif stage==6:
        for command,toneid,expected in ((196,14,'82805030'),(199,15,'8280a030')):
            off=8+command*4;old=bytes(h[off:off+4]);assert old.hex()==expected
            selected=bank_commands(bytes(h),bytes(b))['commands'][command]
            assert all(t['volume']==0 for t in selected['tones'])
            new=bytes([0x83,old[1]&0x80,toneid<<4,old[3]&31]);h[off:off+4]=new
            changes.append(dict(issue='C-06',kind='boss_only_cross_bank_command',command=command,before=old.hex(),after=new.hex(),target_bank=3,target_tone=toneid,spu_channel=new[3],mono_center=True))
        assert bytes(b)==bank(a,2)[4]
    elif stage==7:
        for n in range(q['program_count']*16):
            assert struct.unpack_from('<H',tone(h,q,n),22)[0]!=9,'Replacement wave is referenced'
        slot=q['waves'][8];raw,proof=prepared_wave(wave(jb,jq,8),slot['bytes'],'owl_8')
        b[slot['body_offset']:slot['body_offset']+slot['bytes']]=raw
        for n in (13,14):
            assert tone(h,q,n)[2]==0
            t=bytearray(tone(jh,jq,n));assert t[2]==110;t[4]+=12;struct.pack_into('<H',t,22,9)
            off=tone_base(q)+n*32;h[off:off+32]=t
        changes.append(dict(issue='C-06',kind='unused_wave_restore',wave=9,tones=[13,14],proof=proof,stereo_pan_preserved=True))
    else:raise ValueError('Unsupported boss')
    assert len(h)==he['size'] and len(b)==be['size'];parse_bank(bytes(h),bytes(b),False)
    replace(result,he,h);replace(result,be,b)
    return bytes(result),changes,[he['offset'],he['size'],be['offset'],be['size']]

def main():
    DEST.mkdir(parents=True,exist_ok=True)
    jp=load('jp',STAGES);native=load('us',STAGES)
    audit=json.loads((D/'audit.json').read_text(encoding='utf8'))
    # No other archive key-on command can accidentally reach the new boss tones.
    for r in audit['arc_banks']['us']:
        if r['bank']['slot']!=3:
            assert not any((int(c['hex'][:2],16)&0xc0)==0x80 and c['bank']==3 for c in r['bank']['commands'])
    reports=[]
    for project in ('ver_buki_riko','ver_rin_nana'):
        sources=load(project,PLAYERS+STAGES);out=DEST/project;out.mkdir(exist_ok=True);files={};checks=[]
        for name,(before,record) in sources.items():
            if name in PLAYERS:
                fn=lambda a:prepare_player(a,jp['ST6_1_1.ARC'][0])
            else:
                assert before==native[name][0]
                stage=int(name[2] if name.startswith('ST') else name[6]);fn=lambda a:prepare_stage(a,jp[name][0],stage)
            after,edits,bounds=fn(before);assert fn(before)[0]==after and len(after)==len(before)
            changed=[i for i,(x,y) in enumerate(zip(before,after)) if x!=y]
            h,hs,b,bs=bounds;assert all(h<=i<h+hs or b<=i<b+bs for i in changed)
            assert [(e['type'],e['offset'],e['size']) for e in psx_arc(before)]==[(e['type'],e['offset'],e['size']) for e in psx_arc(after)]
            file=out/name;file.write_bytes(after)
            files[name]=dict(before=sha(before),after=sha(after),size=len(after),path=file.relative_to(ROOT).as_posix(),record=record)
            checks.append(dict(file=name,changed_bytes=len(changed),changed_offsets=changed,edits=edits,only_sound_entries_changed=True,arc_layout_unchanged=True,repeat_exact=True))
        proposal=dict(project=project,issues=['C-01','C-06'],baseline=SOURCES[project][0],baseline_sha256=SOURCES[project][1],files=files,validation='validation.json',runtime_verified=False,human_listening_verified=False)
        (out/'proposal.json').write_text(json.dumps(proposal,indent=2),encoding='utf8')
        (out/'validation.json').write_text(json.dumps(checks,indent=2),encoding='utf8');reports.append(dict(project=project,files=len(files),changed_bytes=sum(c['changed_bytes'] for c in checks)))
    (DEST/'summary.json').write_text(json.dumps(reports,indent=2),encoding='utf8');print(json.dumps(reports))
if __name__=='__main__':main()
