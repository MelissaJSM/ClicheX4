"""Restore confirmed eight-boss JP combat lines in fixed-size US sound banks.

Never writes a game disc. Source character audio, existing C06 and SFX remain intact.
"""
from pathlib import Path
import hashlib,itertools,json,math,struct,subprocess,sys,wave
import numpy as np
from scipy.signal import resample_poly
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader,psx_arc
from scripts.inventory_riko_voice import parse_bank
from src.psx_spu_audio import decode_spu,encode_fixed_oneshot,validate_oneshot_template,vag_container
OUT=Path(__file__).parent;DEST=OUT/'prepared_combat_v1'
# source JP wave, destination US wave, packed tone IDs. Same command IDs in both regions.
PLAN={1:[(3,4,[3,4]),(2,5,[1])],2:[(9,8,[18,19]),(6,9,[9,10])],
      3:[(4,4,[5])],5:[(4,4,[6,7])],6:[(9,4,[12,13]),(2,5,[2,3]),(4,6,[4]),(3,7,[14,15])],
      7:[(10,10,[2,3])],8:[(7,8,[9,10])]}
NAMES=[name for s in PLAN for name in(f'ST{s}_1_1.ARC',f'ONPARE{s}.ARC')]
DATA={key:json.loads((OUT/(key+'_inventory.json')).read_text('utf8'))for key in('us','jp','ver_buki_riko','ver_rin_nana')}
def sha(b):return hashlib.sha256(b).hexdigest()
def require(c,msg):
    if not c:raise ValueError(msg)
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')
def load(key):
    inv=DATA[key];p=ROOT/inv['path']
    with p.open('rb')as f:
        hs=hashlib.sha256()
        for chunk in iter(lambda:f.read(8*1024*1024),b''):hs.update(chunk)
        require(hs.hexdigest()==inv['sha256'],'Input disc hash changed');d=DiscReader(f,p.stat().st_size)
        out={}
        for name in NAMES:
            r=next(x for x in inv['banks']if x['path']=='/ARC/'+name+';1'and x['bank']['slot']==2)
            raw=d.read(r['record']['lba'],r['record']['size']);require(sha(raw)==r['archive_sha256'],'ARC hash');out[name]=(raw,r)
        return out
def bank(raw,row):
    he,be=row['header_record'],row['body_record'];h=raw[he['offset']:he['offset']+he['size']];b=raw[be['offset']:be['offset']+be['size']]
    q=parse_bank(h,b,False);require(q['slot']==2,'Not boss bank2');return h,b,q
def tb(q):return q['vab_offset']+32+128*16
def tone(h,q,n):return h[tb(q)+n*32:tb(q)+(n+1)*32]
def sample(b,q,n):
    w=q['waves'][n-1];return b[w['body_offset']:w['body_offset']+w['bytes']]
EXE=(OUT.parent/'calls/SLUS_005.61').read_bytes()
PT=struct.unpack_from('<192H',EXE,0x11c9e8-0x10000+2048)
def get_pitch(t):
    fine=(t[5]*2)>>3;note=t[6]+60-t[4]+fine//16;v=PT[(note%12)*16+fine%16];o=note//12-5
    return v<<o if o>=0 else v>>(-o)
def converted_length(raw,t,delta):
    if delta==0:return len(raw)
    old=get_pitch(t);nt=bytearray(t);nt[4]+=delta;new=get_pitch(nt)
    n=(len(decode_spu(raw).pcm)*new+old-1)//old
    return(math.ceil(n/28)+1)*16
def choose_deltas(jh,jb,jq,budget,rows):
    choices=[]
    for row in rows:
        source,_,tones=row;raw=sample(jb,jq,source);t=tone(jh,jq,tones[0])
        choices.append([(d,converted_length(raw,t,d))for d in range(13)])
    feasible=[]
    for combo in itertools.product(*choices):
        size=sum(c[1]for c in combo)
        if size<=budget:feasible.append((max(c[0]for c in combo),sum(c[0]for c in combo),-size,combo))
    require(bool(feasible),'No permitted <=12-semitone allocation');best=min(feasible)
    return [c[0]for c in best[-1]],{'objective':'Minimize maximum center-note increase; then summed increase; then maximize retained bytes.',
       'budget':budget,'source_bytes':sum(c[0][1]for c in choices),'selected_bytes':-best[2],'center_note_increases':[c[0]for c in best[-1]],'feasible_allocations':len(feasible)}
ENCODED={}
def encode(raw,t,delta,label):
    key=sha(raw),t.hex(),delta
    if key in ENCODED:return ENCODED[key]
    original=np.asarray(decode_spu(raw).pcm,dtype=np.float64);p=get_pitch(t);nt=bytearray(t);nt[4]+=delta;npitch=get_pitch(nt);rate=npitch*44100/4096
    proof={'source_raw_sha256':sha(raw),'source_bytes':len(raw),'source_native_pitch':p,'target_pitch_formula':npitch,
       'source_rate':p*44100/4096,'target_rate':rate,'center_note_increase':delta,'source_samples':len(original),'source_duration_seconds':len(original)/(p*44100/4096)}
    if delta==0:
        result=raw;proof.update(reencoded=False,original_adpcm_exact=True,decoded_samples=len(original),duration_error_seconds=0.)
    else:
        common=math.gcd(p,npitch);up,down=npitch//common,p//common
        converted=resample_poly(original,up,down);peak=max(1,float(np.max(abs(converted))))
        length=converted_length(raw,t,delta);template=bytearray(length);template[17]=4;template[-31]=1;template[-15]=7
        capacity=validate_oneshot_template(template)
        for headroom_attempt in range(7):
            gain=min(1.,32700*(.95**headroom_attempt)/peak)
            pcm=np.zeros(capacity,dtype=np.int16);pcm[:len(converted)]=np.rint(converted*gain).astype(np.int16);pcm[:28]=0
            result,quality=encode_fixed_oneshot(pcm,bytes(template));restored=np.asarray(decode_spu(result).pcm,dtype=np.float64)
            if np.max(abs(restored))<32760:break
        else:raise ValueError('ADPCM reconstructed clipping persists')
        require(quality['snr_db']>17,'Low ADPCM quantizer SNR')
        back=resample_poly(restored,down,up);n=min(len(original),len(back));err=original[:n]-back[:n];den=float(np.sum(err*err));sig=float(np.sum(original[:n]**2))
        corr=float(np.corrcoef(original[:n],back[:n])[0,1]);end=len(restored)/rate
        proof.update(reencoded=True,original_adpcm_exact=False,resample_ratio=[up,down],gain=gain,decoded_samples=len(restored),converted_samples=len(converted),
           encoded_quality=quality,comparison_to_source_snr_db=10*math.log10(sig/max(1,den)),comparison_to_source_correlation=corr,
           target_duration_seconds=end,duration_error_seconds=end-proof['source_duration_seconds'],
           reserved_first_28_samples_zeroed=True,quality_metrics_are_not_listening=True,headroom_attempt=headroom_attempt,reconstructed_clipping=False)
        require(abs(proof['duration_error_seconds'])<.004,'Excess duration error')
    directory=DEST/'previews';directory.mkdir(parents=True,exist_ok=True)
    rawpath=directory/(label+'.spu');rawpath.write_bytes(result)
    pcm=np.asarray(decode_spu(result).pcm,dtype='<i2');wavpath=directory/(label+'.wav')
    with wave.open(str(wavpath),'wb')as w:w.setparams((1,2,round(rate),0,'NONE','not compressed'));w.writeframes(pcm.tobytes())
    proof.update(result_raw_sha256=sha(result),result_bytes=len(result),raw_path=rawpath.relative_to(ROOT).as_posix(),wav_path=wavpath.relative_to(ROOT).as_posix(),human_listening_completed=False)
    if delta:
        vag=directory/(label+'.vag');vag.write_bytes(vag_container(result,round(rate)))
        ff=ROOT/'work/tools/voice_env/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
        ffraw=subprocess.run([str(ff),'-v','error','-i',str(vag),'-f','s16le','pipe:1'],check=True,capture_output=True).stdout
        ffpcm=np.frombuffer(ffraw,dtype='<i2')[:len(pcm)].astype(np.int32);diff=ffpcm-pcm.astype(np.int32)
        proof['independent_ffmpeg_max_error']=int(max(abs(diff)));proof['independent_ffmpeg_snr_db']=10*math.log10(float(np.sum(pcm.astype(float)**2))/max(1,float(np.sum(diff.astype(float)**2))))
        require(proof['independent_ffmpeg_snr_db']>45 and proof['independent_ffmpeg_max_error']<128,'Independent ADPCM decode mismatch '+label+' '+str((proof['independent_ffmpeg_snr_db'],proof['independent_ffmpeg_max_error'])))
    ENCODED[key]=result,proof;return result,proof
def patch(raw,row,jp,jrow,stage):
    original=raw;h,b,q=bank(raw,row);jh,jb,jq=bank(jp,jrow);require(q['program_count']==jq['program_count'],'Program layout')
    oldh=h;oldb=b;h=bytearray(h);waves=[sample(b,q,i+1)for i in range(q['wave_count'])];plan=PLAN[stage]
    replace_rows=[x for x in plan if sample(jb,jq,x[0])!=waves[x[1]-1]]
    budget=sum(len(waves[x[1]-1])for x in replace_rows);deltas,allocation=choose_deltas(jh,jb,jq,budget,replace_rows)if replace_rows else([],{'budget':0,'reconnect_only':True})
    dm={r[1]:d for r,d in zip(replace_rows,deltas)};changed_tones=[];waveproof=[]
    for source,target,tones in plan:
        delta=dm.get(target,0);jraw=sample(jb,jq,source)
        for n in tones:
            t=bytearray(tone(jh,jq,n));require(struct.unpack_from('<H',t,22)[0]==source,'JP source tone mismatch');t[4]+=delta;struct.pack_into('<H',t,22,target)
            h[tb(q)+n*32:tb(q)+(n+1)*32]=t
            changed_tones.append({'packed_tone':n,'before':tone(oldh,q,n).hex(),'source_jp':tone(jh,jq,n).hex(),'after':t.hex(),
              'source_wave':source,'target_wave':target,'center_note_increase':delta,'source_pitch':get_pitch(tone(jh,jq,n)),'target_pitch_formula':get_pitch(t),
              'native_rate_ratio':get_pitch(t)/get_pitch(tone(jh,jq,n))})
        if target in dm:
            encoded,proof=encode(jraw,tone(jh,jq,tones[0]),delta,f'stage{stage}_jpwave{source}_delta{delta}')
            waves[target-1]=encoded;waveproof.append({'source_wave':source,'target_wave':target,**proof})
        else:waveproof.append({'source_wave':source,'target_wave':target,'reconnected_existing_raw':True,'source_raw_sha256':sha(jraw),'result_raw_sha256':sha(waves[target-1]),'original_adpcm_exact':True,'reencoded':False})
    if replace_rows:
        leftover=len(b)-sum(map(len,waves));require(leftover>=0 and leftover%16==0,'Body budget')
        last=replace_rows[-1][1]-1;waves[last]+=bytes(leftover)
        allocation['nonplayed_zero_padding_bytes']=leftover;allocation['padding_wave']=last+1
    newbody=b''.join(waves);require(len(newbody)==len(b),'SPU size changed')
    sizebase=tb(q)+q['program_count']*16*32
    for i,w in enumerate(waves):struct.pack_into('<H',h,sizebase+(i+1)*2,len(w)//8)
    newq=parse_bank(bytes(h),newbody,False)
    require((newq['program_count'],newq['wave_count'],newq['body_bytes'])==(q['program_count'],q['wave_count'],q['body_bytes']),'Bank structure changed')
    targettones={n for _,_,ids in plan for n in ids};targetwaves={target for _,target,_ in replace_rows}
    for n in range(q['program_count']*16):
        if n not in targettones:require(tone(oldh,q,n)==tone(h,q,n),'Non-target tone changed')
    for i in range(1,q['wave_count']+1):
        if i not in targetwaves:require(sample(oldb,q,i)==sample(newbody,newq,i),'Existing SFX/C06 sample changed')
    for n in range(q['program_count']*16):
        t=tone(oldh,q,n);wi=struct.unpack_from('<H',t,22)[0]
        if n not in targettones and wi in targetwaves:require(t[2]==0,'Audible non-target tone shares replaced wave')
    require(h[:q['vab_offset']]==oldh[:q['vab_offset']],'Sound command changed')
    require(h[q['vab_offset']:tb(q)]==oldh[q['vab_offset']:tb(q)],'VAB program/master fields changed')
    if stage==5:require(tone(h,q,9)==tone(oldh,q,9)and sample(newbody,newq,6)==sample(oldb,q,6),'C06 Stingray altered')
    if stage==6:
        require(h[8+196*4:12+196*4]==oldh[8+196*4:12+196*4]and h[8+199*4:12+199*4]==oldh[8+199*4:12+199*4],'C06 Peacock commands altered')
    if stage==7:require(all(tone(h,q,n)==tone(oldh,q,n)for n in(13,14))and sample(newbody,newq,9)==sample(oldb,q,9),'C06 Owl altered')
    result=bytearray(raw)
    for e,data in((row['header_record'],h),(row['body_record'],newbody)):result[e['offset']:e['offset']+e['size']]=data
    layout=lambda a:[{k:v for k,v in e.items()if k!='sha256'}for e in psx_arc(a)]
    require(len(result)==len(raw)and layout(result)==layout(raw),'ARC structure changed')
    allowed=set(range(row['header_record']['offset'],row['header_record']['offset']+row['header_record']['size']))|set(range(row['body_record']['offset'],row['body_record']['offset']+row['body_record']['size']))
    diff=[i for i,(a,b)in enumerate(zip(raw,result))if a!=b];require(all(i in allowed for i in diff),'Unrelated ARC bytes')
    return bytes(result),{'stage':stage,'allocation':allocation,'tones':changed_tones,'waves':waveproof,'changed_bytes':len(diff),
       'header_entry':row['header_record'],'body_entry':row['body_record'],'non_target_tones_exact':True,'non_target_waves_exact':True,
       'commands_exact':True,'master_program_exact':True,'same_spu_body_bytes':len(newbody),'same_arc_layout':True,'existing_C06_preserved':True}
def main():
    DEST.mkdir(exist_ok=True);jp=load('jp');allreports={}
    for mode in('ver_buki_riko','ver_rin_nana'):
        source=load(mode);folder=DEST/mode;folder.mkdir(exist_ok=True);files={};reports={}
        for name,(raw,row)in source.items():
            stage=int(name[2]if name.startswith('ST')else name[6]);jr,jrow=jp[name]
            after,report=patch(raw,row,jr,jrow,stage);require(patch(raw,row,jr,jrow,stage)[0]==after,'Reproduction mismatch')
            path=folder/name;path.write_bytes(after);files[name]={'path':path.relative_to(ROOT).as_posix(),'before':sha(raw),'after':sha(after),'size':len(after),'record':row['record'],
                'allowed_entries':[row['header_record'],row['body_record']]};reports[name]=report
        proposal={'project':mode,'baseline':DATA[mode]['path'],'baseline_sha256':DATA[mode]['sha256'],'files':files,
            'scope':'Twelve additional JP combat samples at21 tones; C06, player audio, commonSFX and English later-boss speech preserved.',
            'runtime_verified':False,'human_listening_verified':False,'native_pitch_independent_verification_pending':True}
        write(folder/'proposal.json',proposal);write(folder/'verification.json',reports);allreports[mode]=reports
    require(all((DEST/'ver_buki_riko'/n).read_bytes()==(DEST/'ver_rin_nana'/n).read_bytes()for n in NAMES),'Mode boss resources differ')
    write(DEST/'summary.json',{'projects':list(allreports),'same_resources_both_modes':True,'files_per_mode':len(NAMES),'unique_source_samples':12,'target_tones_per_boss_bank':21,'static_passed':True})
    print(json.dumps({'prepared':True,'files_per_mode':len(NAMES),'same_resources_both_modes':True,'native_pitch_verification_pending':True}),flush=True)
if __name__=='__main__':main()
