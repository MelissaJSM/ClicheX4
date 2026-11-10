"""효과 타일을 보존한32타일 몸체 패킹 가능성만 시험한다. ARC 출력 없음."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,sha,digest,write,need
from pack_cycle import raw
from scripts.prepare_shibuki_ultimate_production import pack_shared
from src.psx_player import indexed_atlas

def tile_copy(old_raw,count,tiles):
    arr=np.frombuffer(indexed_atlas(old_raw,count)[0],np.uint8).reshape(-1,256)
    dst=np.zeros((32,256),np.uint8)
    for t in tiles:dst[t//16*16:t//16*16+16,t%16*16:t%16*16+16]=arr[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
    return bytes((dst[:,::2]|(dst[:,1::2]<<4)).ravel())

def main():
    p=N/'rising_repaint/packed_base_candidate_v1/PL00_U.ARC';a=Archive(p.read_bytes())
    r=ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_hurt_relations01/report.json';m=json.loads(r.read_text('utf8'))
    need(m['source_sha256']==sha(a.data),'효과 감사 부모 불일치')
    out=[]
    for n,effect_refs in((106,(107,108)),(110,(111,)),(233,()),(234,())):
        keep=set()
        for q in m['body_plus_effect_relations']:
            if q['ref']in effect_refs:
                for ls in q['layers'].values():keep.update(ls['effect_tiles'])
        cnt=a.banks[0]['frames'][n]['tile_count'];seed=tile_copy(raw(a,0,n),cnt,keep)
        ims=[np.array(Image.open(D/'joint_layers_probe_v1'/f'layer{pb}_{n:03}.png'))[80:240,80:240]for pb in(0,5,6,7,8)]
        try:
            nr,parts=pack_shared(seed,32,ims,set(range(32))-{0,16}-keep,[16]*5)
            aa=np.frombuffer(indexed_atlas(seed,32)[0],np.uint8).reshape(32,256);bb=np.frombuffer(indexed_atlas(nr,32)[0],np.uint8).reshape(32,256)
            for t in keep:need(np.array_equal(aa[t//16*16:t//16*16+16,t%16*16:t%16*16+16],bb[t//16*16:t//16*16+16,t%16*16:t%16*16+16]),'효과 타일 변경')
            out.append({'ref':n,'passed':True,'protected_effect_tiles':sorted(keep),'parts':[len(x)for x in parts],'raw_sha256':sha(nr)})
        except ValueError as e:out.append({'ref':n,'passed':False,'protected_effect_tiles':sorted(keep),'error':str(e)})
    write(D/'body_capacity_v1.json',{'scope':'새4몸체의 고정32타일/효과보호 패킹 가능성 시험만. ARC 미출력.','frames':out,'arc_written':False,'runtime_verified':False})
    print(json.dumps(out))
if __name__=='__main__':main()
