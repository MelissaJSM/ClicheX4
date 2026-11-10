"""새 포스 공중 원화를 기본 눈/발 높이 및 고정 게임 팔레트에 등록."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint'),str(D.parent/'wall_repaint')]
from preview_restore import Archive,sha,digest,need,write,helper
from register_page import register
from register_fourth_wall import eye,crops
from register_air_page import crop_count
from review_all_bodies import source as body_source
PAGES={'a':('fourth_air_a_v1',[33,35,37,39],'2c623d64879b49554b5ef781c16c7221a9b4d3ae1511018b7fe7493dfb943c9a'),
       'b':('fourth_air_b_v1',[41,43,45,47],'b6b2a211154ad9721a6bcb625f5952e27733010cf7065063c363adcd89ee6c8f'),
       'c':('fourth_air_c_v1',[49,51,53],'e20b788d837ea24d28e0a3419013770c1f316be4a41e663e225f10deab025d2b'),
       'joint':('fourth_joint_edits_v1',[37,47,51],'cae077e4c068c07348b27f6dfcc06b4ab0e6284463e8a55b5583438eabbada20'),
       'knee51':('fourth51_knee_v1',[51],'0deac6695d2133a7071ad9ca080c166fea60fac329227b07764ff498880b05e3')}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--page',choices=PAGES,default='a');ap.add_argument('--out');args=ap.parse_args()
    folder,refs,expected=PAGES[args.page];p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());need(sha(a.data)==p['parent_arc_sha256'],'Parent')
    art=D/folder/'generated.png';need(digest(art)==expected,'Art source');out=D/(args.out or f'fourth_{args.page}_registered_v1');need(not out.exists(),'Fresh output');out.mkdir();im=Image.open(art).convert('RGBA')
    pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32);rows=[];records=[]
    for n,(crop,box) in zip(refs, [crop_count(im,i,len(refs))for i in range(len(refs))]):
        crop.save(out/f'source_{n:03}.png');base=np.array(Image.open(body_source(n)/f'base_{n:03}.png'));sx,sy=eye(crop);q=next(q for q in p['frames']if q['ref']==n);ex,ey=[int(np.floor(v))for v in q['eye']]
        mask=np.array(crop)[:,:,3]>=128;Y,X=np.indices(mask.shape);ys,_=np.nonzero(mask&(X>=sx-40)&(X<sx+45));crown=float(ys.min());scale=10/(sy-crown+1);width=round(crop.width*scale);split=round(sy+1);top=ey-round(split*scale)+1;hu=ey-top+1;bottom=int(np.where(base>0)[0].max()-160)+1;hl=bottom-ey-1
        upper=register(crop.crop((0,0,crop.width,split)),(width,hu),pal,'area_vote');lower=register(crop.crop((0,split,crop.width,crop.height)),(width,hl),pal,'area_vote');native=np.concatenate((upper,lower));ec=round((sx+.5)*width/crop.width-.5);native[:hu][native[:hu]==14]=12;native[hu-1,ec]=14;ox=ex-ec
        target=np.zeros((384,384),np.uint8);target[160+top:160+top+len(native),160+ox:160+ox+width]=native;Image.fromarray(target).save(out/f'fourth_{n:03}.png');a.rgba(target,16).save(out/f'fourth_{n:03}_rgba.png')
        records.append({'ref':n,'source':art.relative_to(ROOT).as_posix(),'source_sha256':expected,'source_crop':box,'source_eye':[sx,sy],'source_crown':crown,'native_position':[ox,top],'native_width':width,'source_scale_x':scale,'split':split,'height_above':hu,'height_below':hl,'eye':[ex,ey],'foot_y':bottom-1,'alpha_components_8':label(target>0,np.ones((3,3)))[1],'old_art_pixels_used':0,'indexed_sha256':sha(target.tobytes())})
        rows.append((f'fourth air{n}',[('포스 대기',a.composite(0,15)[0]),('현재 포스',a.composite(n,15)[0]),('새 기본 몸체',a.rgba(base)),('새 포스 직접등록',a.rgba(target,16))]))
    for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',8)
    write(out/'registration.json',{'source_arc_sha256':sha(a.data),'frames':records,'scope':'새 포스 원화 직접 인덱스 등록. 공통 머리/발 접점과 부분파츠 검증 전 후보. 옛 몸체나 단색 덮기 없음.','native_packed':False,'runtime_verified':False});print(json.dumps(records))
if __name__=='__main__':main()
