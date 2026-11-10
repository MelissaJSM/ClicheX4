"""새 피격4의 전후 의상을 실제 Ultimate bank0/5 구조로 분리한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,need,write,helper
PBS=(0,5,6,7,8)
def composite(a,ls,mask=0,arm=2):
    im=a.rgba(ls[0])
    for bit,pb in((8,8),(1,5),(4,7),(2,6)):
        if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
    return im
def main():
    src=D/'costume_pair_probe_v4';out=D/'body_layers_probe_v1';out.mkdir(exist_ok=False)
    p=N/'rising_repaint/packed_ultimate_candidate_v1/PL02_U.ARC';a=Archive(p.read_bytes());rows=[];rec=[]
    for n in(106,110,233,234):
        b=np.array(Image.open(src/f'before_{n:03}.png'));v=np.array(Image.open(src/f'after_{n:03}.png'))
        need(not np.any((v>0)&(b==0)),'後폼 밖 불투명오버레이 삭제불가')
        over=np.where((b!=v)|(b==15),b,0).astype(np.uint8);ls={0:v,5:over,6:np.zeros_like(v),7:np.zeros_like(v),8:np.zeros_like(v)}
        need(composite(a,ls,15).tobytes()==a.rgba(b,16).tobytes(),'전폼 native합성')
        for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
        rec.append({'ref':n,'before':sha(b.tobytes()),'after':sha(v.tobytes()),'layer_hashes':{str(pb):sha(z.tobytes())for pb,z in ls.items()},'before_exact':True})
        rows.append((f'Ultimate hurt {n}',[('before idle',a.composite(0,15)[0]),('new before',composite(a,ls,15)),('after idle',a.composite(0)[0]),('new after',composite(a,ls))]))
    for i in range(0,4,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',7)
    write(out/'manifest.json',{'parent_sha256':digest(p),'source_manifest':src.relative_to(ROOT).as_posix()+'/manifest.json','source_manifest_sha256':digest(src/'manifest.json'),'frames':rec,'scope':'4몸체의새20층. Ultimate 실제전폼mask15/후폼mask0,부분마스크는후속검사. 파생효과/ARC패킹 전.','runtime_verified':False})
if __name__=='__main__':main()
