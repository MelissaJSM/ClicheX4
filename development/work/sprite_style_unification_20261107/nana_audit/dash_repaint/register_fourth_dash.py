"""새 포스 대시 원화를 고정 CLUT/눈/발 높이에 직접 등록한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent; ROOT=D.parents[3]
sys.path[:0]=[str(D),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,digest,need,write,helper
from refine_second_inputs import one,crop_count
from register_last_keys import horizontal_crop
sys.path.insert(0,str(D))
from prepare_next_guides import body_path
PAGES={'a':('fourth_a_v1',(67,69,71,75),'987fb9f508ae95af7f5aa446482c8b6472723e5fb592fa1a588701d95251a1c8'),
       'b':('fourth_b_v1',(77,79,81,83),'9993e77a07688e918e4ffdf8eff74291f7f52cabcf874d6d93d0a39fbf5f43ac'),
       'c':('fourth_c_v1',(93,94),'d096addf6d8b76e2b8d70c04427ad4ded072c329262da5921cfcedf32ab45602')}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--page',choices=PAGES,default='a');args=ap.parse_args()
    folder,refs,expected=PAGES[args.page];plan=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/plan['parent_arc']).read_bytes());need(sha(a.data)==plan['parent_arc_sha256'],'Parent')
    source=D/folder/'generated.png';need(digest(source)==expected,'Source');im=Image.open(source).convert('RGBA');out=D/f'fourth_{args.page}_registered_v1';need(not out.exists(),'Fresh output');out.mkdir()
    pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32);rows=[];proof=[]
    for k,n in enumerate(refs):
        crop,box=horizontal_crop(im,k) if len(refs)==2 else crop_count(im,k,len(refs));crop.save(out/f'source_{n:03}.png');q=next(q for q in plan['frames']if q['ref']==n);native,r=one(crop,q,pal);base=np.array(Image.open(body_path(n)));yy,xx=np.nonzero(native)
        need(yy.max()==np.nonzero(base)[0].max(),'Base foot height');Image.fromarray(native).save(out/f'fourth_{n:03}.png');a.rgba(native,16).save(out/f'fourth_{n:03}_rgba.png')
        r.update(ref=n,source_crop=box,source_art_sha256=expected,indexed_sha256=sha(native.tobytes()),components_8=int(label(native>0,np.ones((3,3)))[1]),native_bbox=[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],old_game_pixels_used=0)
        proof.append(r);rows.append((f'Fourth dash {n}',[('대기',a.composite(0,15)[0]),('기존',a.composite(n,15)[0]),('새 기본',a.rgba(base)),('새 포스 직접 등록',a.rgba(native,16))]))
    for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',8)
    write(out/'registration.json',{'source_arc_sha256':sha(a.data),'source_art_sha256':expected,'frames':proof,'native_packed':False,'runtime_verified':False,'scope':'새 원화 직접 등록 후보. 부분파츠/공통 접점 검증 전. 옛 몸체 덮기 없음.'});print(json.dumps(proof))
if __name__=='__main__':main()
