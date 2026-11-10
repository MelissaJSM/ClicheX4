"""사다리 원화의 임시 무손실 타일 용량만 검사한다. ARC를 쓰지 않는다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import crop,lossless_pack,write
from src.psx_player import indexed_atlas

def mirror(v,delta):
    out=np.zeros_like(v);yy,xx=np.nonzero(v);dest=320+delta-xx
    if np.any((dest<0)|(dest>=384)):raise ValueError('Mirrored source clipped')
    out[yy,dest]=v[yy,xx]
    return out

def main():
    source=H/'ladder_parts_probe03';rows=[]
    for refs,key,delta in [([143],143,None),([144,145],144,-1),([146,147],146,0),([151,152],151,0),([153],153,None),([154],154,None),([183],183,None)]:
        images=[];keys=[]
        for n in refs:
            for b in(0,5,6,7,8):
                v=np.array(Image.open(source/f'{key:03}_bank{b}_indices.png'))
                if n!=key:v=mirror(v,delta)
                if v.any():images.append(crop(v));keys.append((n,b))
        try:
            raw,parts,method=lossless_pack(images)
            atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256)
            for target,rr in zip(images,parts):
                restored=np.zeros_like(target)
                for tile,x,y,flags in rr:
                    tex=atlas[(tile//16)*16:(tile//16+1)*16,(tile%16)*16:(tile%16+1)*16]
                    if flags&64:tex=tex[:,::-1]
                    if flags&128:tex=tex[::-1]
                    if not(0<=x<=144 and 0<=y<=144):raise ValueError('Part outside native staging')
                    dest=restored[y:y+16,x:x+16];dest[tex>0]=tex[tex>0]
                if not np.array_equal(target,restored):raise ValueError('Actual tile reconstruction mismatch')
            row={'refs':refs,'passed':not bool(atlas[:,0].any()),'method':method,'tiles':len({t for rr in parts for t,x,y,f in rr}),'max_parts':max(map(len,parts)),'all_target_texels_retained':True,'gpu_first_column_transparent':not bool(atlas[:,0].any()),'parts':{f'{n}:{b}':len(rr)for(n,b),rr in zip(keys,parts)}}
        except ValueError as exc:row={'refs':refs,'passed':False,'reason':str(exc),'art_not_simplified':True}
        rows.append(row)
    write(H/'ladder_parts_probe03/capacity.json',{'rows':rows,'all_passed':all(r['passed']for r in rows),'excluded_pending_shooting_group':[148,149,150,155],'not_arc_packed':True,'reconstruction_and_composition_capacity_still_pending':True})
    print(json.dumps(rows))

if __name__=='__main__':main()
