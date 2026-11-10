"""현 동결 나나 피격/저체력의 고유 몸체와 파생효과를 읽기 조사한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
N=Path(__file__).resolve().parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
REFS=list(range(106,115))+list(range(120,126))+list(range(233,237))

def main():
    p=N/'rising_repaint/packed_base_candidate_v1/PL00_U.ARC';need(digest(p)=='3bd156730cb932f2a97b43acc85f0d2209537c76cbab6d298c973438bc251b42','동결 부모')
    a=Archive(p.read_bytes());out=N/'hurt_repaint/scope_v1';out.mkdir(parents=True,exist_ok=False);records=[];images={};rows=[]
    for n in REFS:
        z=a.layer(n)[0];body=z>0;yy,xx=np.nonzero(body);bbox=[int(xx.min())-160,int(yy.min())-160,int(xx.max())-159,int(yy.max())-159]if len(xx)else None
        for pb in(0,5,6,7,8):Image.fromarray(a.layer(n,pb)[0]).save(out/f'{n:03}_bank{pb}.png')
        indices={}
        for mask in(0,15):
            im=a.composite(n,mask)[0];im.save(out/f'{n:03}_mask{mask}.png');indices[str(mask)]=sha(im.tobytes());images[n,mask]=im
        records.append({'ref':n,'bbox_world':bbox,'base_opaque':int(body.sum()),'base_indices_sha256':sha(z.tobytes()),'base_colors':{str(k):int(v)for k,v in zip(*np.unique(z[body],return_counts=True))},'composite_RGBA_sha256':indices,'layers':{str(pb):sha(a.layer(n,pb)[0].tobytes())for pb in(0,5,6,7,8)}})
        rows.append((f'ref {n}',[('base idle',a.composite(0,0)[0]),('current base',images[n,0]),('Fourth idle',a.composite(0,15)[0]),('current Fourth',images[n,15])]))
    for i in range(0,len(rows),4):helper.grid(rows[i:i+4],out/f'comparison_{i//4+1}.png',6)
    relations=[]
    for n in REFS:
        for m in REFS:
            if m<=n:continue
            if all(records[REFS.index(n)]['layers'][str(pb)]==records[REFS.index(m)]['layers'][str(pb)]for pb in(0,5,6,7,8)):relations.append({'source':n,'target':m,'all5_layers_exact':True})
    write(out/'manifest.json',{'source_arc':p.relative_to(ROOT).as_posix(),'source_arc_sha256':digest(p),'refs':records,'exact_relations':relations,'scope':'새 도안 전 현재 몸체/깜박임/부수효과 관계 조사. 같은 색 해시만으로 게임 역할이나 고유동작을 단정하지 않는다.','new_art_generated':False,'runtime_verified':False})
    print(json.dumps({'relations':relations,'frames':[{k:q[k]for k in('ref','base_opaque','bbox_world','base_colors')}for q in records]}))
if __name__=='__main__':main()
