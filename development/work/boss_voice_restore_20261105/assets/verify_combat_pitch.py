"""Actual JP/US SDK pitch checks and original/restored WAV pairs, no disc writes."""
from pathlib import Path
import hashlib,json,struct,sys,wave
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).parent))
from scripts.discover_inputs import DiscReader
from scripts.inventory_riko_voice import parse_bank
from src.psx_spu_audio import decode_spu
from prepare_native_previews import pitch
OUT=Path(__file__).parent;DEST=OUT/'prepared_combat_v1'
def sha(x):return hashlib.sha256(x).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')
def bank(raw,row):
    he,be=row['header_record'],row['body_record'];h=raw[he['offset']:he['offset']+he['size']];b=raw[be['offset']:be['offset']+be['size']];return h,b,parse_bank(h,b,False)
def tb(q):return q['vab_offset']+32+128*16
def main():
    jp=json.loads((OUT/'jp_inventory.json').read_text('utf8'));us=json.loads((OUT/'ver_buki_riko_inventory.json').read_text('utf8'));exes={r:(OUT.parent/'calls'/n).read_bytes()for r,n in(('jp','SLPS_009.02'),('us','SLUS_005.61'))}
    verification=json.loads((DEST/'ver_buki_riko/verification.json').read_text('utf8'));proposal=json.loads((DEST/'ver_buki_riko/proposal.json').read_text('utf8'));checks=[];pairs=[]
    folder=DEST/'comparison_wavs';folder.mkdir(exist_ok=True)
    with(ROOT/jp['path']).open('rb')as f:
        disc=DiscReader(f,(ROOT/jp['path']).stat().st_size)
        for name,proof in verification.items():
            jr=next(x for x in jp['banks']if x['path']=='/ARC/'+name+';1'and x['bank']['slot']==2);ur=next(x for x in us['banks']if x['path']==jr['path']and x['bank']['slot']==2)
            original=disc.read(jr['record']['lba'],jr['record']['size']);target=(ROOT/proposal['files'][name]['path']).read_bytes();assert sha(target)==proposal['files'][name]['after']
            jh,jb,jq=bank(original,jr);h,b,q=bank(target,ur);tone_checks=[]
            for tone in proof['tones']:
                n=tone['packed_tone'];jt=jh[tb(jq)+n*32:tb(jq)+(n+1)*32];t=h[tb(q)+n*32:tb(q)+(n+1)*32]
                assert jt.hex()==tone['source_jp']and t.hex()==tone['after']
                sourcepitch=pitch(exes['jp'],'jp',jt);newpitch=pitch(exes['us'],'us',t)
                assert sourcepitch==tone['source_pitch']and newpitch==tone['target_pitch_formula']
                expected=bytearray(jt);expected[4]+=tone['center_note_increase'];struct.pack_into('<H',expected,22,tone['target_wave']);assert bytes(expected)==t
                tone_checks.append({'tone':n,'source_pitch':sourcepitch,'target_pitch':newpitch,'actual_rate_ratio':newpitch/sourcepitch,'center_delta':tone['center_note_increase'],
                    'source_other_tone_fields_exact':True,'adsr1':struct.unpack_from('<H',t,16)[0],'adsr2':struct.unpack_from('<H',t,18)[0],'volume':t[2],'pan':t[3]})
            checks.append({'file':name,'source_archive_sha256':sha(original),'target_archive_sha256':sha(target),'tones':tone_checks,'actual_native_pitch_passed':True})
            if name.startswith('ONPARE'):continue
            for change in proof['waves']:
                src,dst=change['source_wave'],change['target_wave'];tn=next(t['packed_tone']for t in proof['tones']if t['source_wave']==src);tc=next(t for t in tone_checks if t['tone']==tn)
                ww=[]
                for region,buf,meta,wi,pvalue in(('jp',jb,jq,src,tc['source_pitch']),('restored',b,q,dst,tc['target_pitch'])):
                    w=meta['waves'][wi-1];raw=buf[w['body_offset']:w['body_offset']+w['bytes']];pcm=np.asarray(decode_spu(raw).pcm,dtype='<i2');path=folder/f'stage{proof["stage"]}_wave{src}_{region}.wav';rate=pvalue*44100/4096
                    with wave.open(str(path),'wb')as audio:audio.setparams((1,2,round(rate),0,'NONE','not compressed'));audio.writeframes(pcm.tobytes())
                    ww.append({'source':region,'sha256':sha(raw),'wav_path':path.relative_to(ROOT).as_posix(),'pitch':pvalue,'sample_rate_exact':rate,'wav_rate':round(rate),'seconds':len(pcm)/rate,'samples':len(pcm)})
                pairs.append({'stage':proof['stage'],'jp_wave':src,'target_wave':dst,'original':ww[0],'restored':ww[1],'reencoded':change.get('reencoded',False),
                     'duration_error_seconds':ww[1]['seconds']-ww[0]['seconds'],'human_listening_completed':False})
    report={'passed':True,'actual_native_tone_checks':sum(len(c['tones'])for c in checks),'checks':checks,'scope':'Actual JP/US note2pitch2 MIPS plus exact source tone ADPCM mapping. No emulator or full key-on path was exercised here.'}
    write(DEST/'native_pitch_verification.json',report);write(DEST/'audition_manifest.json',{'pairs':pairs,'count':len(pairs),'human_listening_completed':False,'pitch_native_verified':True})
    print(json.dumps({'native_tone_cases':report['actual_native_tone_checks'],'audition_pairs':len(pairs),'passed':True}))
if __name__=='__main__':main()
