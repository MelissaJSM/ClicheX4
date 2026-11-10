"""Mapped JP samples that still exist elsewhere in the US bank, plus native rate."""
from pathlib import Path
import hashlib,json,struct,sys,wave
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).parent))
from scripts.discover_inputs import DiscReader
from src.psx_spu_audio import decode_spu
from prepare_native_previews import pitch
OUT=Path(__file__).parent
def main():
    inv=json.loads((OUT/'jp_inventory.json').read_text('utf8'));exe=(OUT.parent/'calls/SLPS_009.02').read_bytes();rows=[];folder=OUT/'extra_native_previews';folder.mkdir(exist_ok=True)
    with(ROOT/inv['path']).open('rb')as f:
        d=DiscReader(f,(ROOT/inv['path']).stat().st_size)
        for stage,wi in((3,4),(5,4),(7,10),(8,1)):
            a=next(x for x in inv['banks']if x['path']==f'/ARC/ST{stage}_1_1.ARC;1'and x['bank']['slot']==2);b=a['bank'];w=b['waves'][wi-1];r=a['record'];arc=d.read(r['lba'],r['size']);off=a['body_record']['offset']+w['body_offset'];raw=arc[off:off+w['bytes']];assert hashlib.sha256(raw).hexdigest()==w['sha256']
            stem=f'jp_ST{stage}_wave{wi}_{w["sha256"][:10]}';(folder/(stem+'.spu')).write_bytes(raw);pcm=np.asarray(decode_spu(raw).pcm,dtype='<i2');variants={}
            for t in b['tones']:
                if not(t['active']and t['wave_id']==wi):continue
                p=pitch(exe,'jp',bytes.fromhex(t['record_hex']));variant=variants.setdefault(p,{'pitch':p,'sample_rate_exact':p*44100/4096,'wav_rate':round(p*44100/4096),'tones':[]})
                variant['tones'].append(t)
            for p,v in variants.items():
                path=folder/(stem+f'_pitch{p:04x}.wav')
                with wave.open(str(path),'wb')as target:target.setparams((1,2,v['wav_rate'],0,'NONE','not compressed'));target.writeframes(pcm.tobytes())
                v['wav_path']=path.relative_to(ROOT).as_posix();v['seconds']=len(pcm)/v['sample_rate_exact']
            rows.append({'source':'jp','sha256':w['sha256'],'bytes':len(raw),'raw_path':(folder/(stem+'.spu')).relative_to(ROOT).as_posix(),'occurrences':[{'path':a['path'],'wave_id':wi}],
                'native_variants':list(variants.values()),'native_pitch_verified':True,'human_listening_completed':False})
    (OUT/'extra_native_manifest.json').write_text(json.dumps({'rows':rows,'count':len(rows),'reason':'JP wave exists in US, but a changed native-used tone points elsewhere. No speech classification inferred.'},ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'extra_native_rows':len(rows)}))
if __name__=='__main__':main()
