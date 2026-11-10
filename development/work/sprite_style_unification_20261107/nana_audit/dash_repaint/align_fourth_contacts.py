"""새 포스 구두를 기본 접점에 평행 등록하고 인접 종아리 원화만 정합."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(D),str(D.parent/'native_restore')]
from align_second_feet import transform
sys.path.insert(0,str(D))
from prepare_next_guides import body_path
from preview_restore import Archive,sha,digest,need,write,helper
CONFIG={67:(10,[(-6,19,1,23,3,0),(10,19,15,23,3,0)]),
69:(13,[(3,18,7,23,1,0)]),71:None,75:None,
77:(11,[(0,18,3,22,4,0),(4,18,7,23,6,0)]),
79:(12,[(8,18,12,23,1,0)]),
81:(7,[(-1,19,6,23,2,-1),(23,18,28,23,-1,0)]),
83:(8,[(-10,19,-3,23,2,-1),(5,19,10,23,1,0)]),93:(8,[(1,12,5,18,3,0)]),94:(2,[(18,7,24,12,4,0)])}
def main():
    plan=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/plan['parent_arc']).read_bytes());need(sha(a.data)==plan['parent_arc_sha256'],'Parent');pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],float);out=D/'fourth_contacts_probe_v2';need(not out.exists(),'Fresh output');out.mkdir();rows=[];proof=[]
    for n,config in CONFIG.items():
        folder=D/('fourth_a_registered_v1'if n<77 else'fourth_b_registered_v1'if n<93 else'fourth_c_registered_v1');meta=json.loads((folder/'registration.json').read_text('utf8'));r=next(r for r in meta['frames']if r['ref']==n);source=folder/f'source_{n:03}.png';crop=Image.open(source).convert('RGBA');old=np.array(Image.open(folder/f'fourth_{n:03}.png'));base=np.array(Image.open(body_path(n)))
        if config is None:new,sample,reg=transform(crop,r,old,35,[],pal,n);reg['unchanged_registration']=True
        else:
            start,modules=config;new,sample,reg=transform(crop,r,old,start,modules,pal,n);reg.update(rigid_shoe_modules=modules,upper_y_lt_exact=start)
        Image.fromarray(new).save(out/f'fourth_{n:03}.png');a.rgba(new,16).save(out/f'fourth_{n:03}_rgba.png')
        if sample is not None:Image.fromarray(sample).save(out/f'source_rgba8_{n:03}.png')
        reg.update(ref=n,source_rgba_sha256=digest(source),source_art_sha256=meta['source_art_sha256'],before=sha(old.tobytes()),after=sha(new.tobytes()),floor_y=int(np.nonzero(new)[0].max()-160),flat_fills=0,old_game_pixels_used=0);proof.append(reg);rows.append((f'Fourth dash {n}',[('새 기본',a.rgba(base)),('포스 직접등록',a.rgba(old,16)),('구두 접점 정합 후보',a.rgba(new,16))]))
    for k in range(0,len(rows),2):helper.grid(rows[k:k+2],out/f'comparison_{k//2+1}.png',8)
    write(out/'registration.json',{'source_arc_sha256':sha(a.data),'frames':proof,'native_packed':False,'runtime_verified':False,'scope':'부분파츠 전 새 원화 구두 접점 후보. 가로늘림/단색채움 없이 구두는 강체 이동, 인접 종아리만 같은 원화로 정합.'});print(str(out))
if __name__=='__main__':main()
