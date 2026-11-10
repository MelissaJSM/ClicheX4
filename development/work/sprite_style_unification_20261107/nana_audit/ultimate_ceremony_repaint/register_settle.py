"""138 두 의상을 정확한1536x1024 전체 셀비로 등록한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(D)]
from preview_restore import Archive,digest,sha,write,need,helper
from register_page import register
from register_first import bbox,full
from register_second import optional_eye
def main():
    cli=argparse.ArgumentParser();cli.add_argument('--source',choices=['settle_v1','raised138_v1'],default='settle_v1');cli.add_argument('--out',default='settle_registered_v1');args=cli.parse_args()
    meta=json.loads((D/'settle_inputs_v1/manifest.json').read_text('utf8'));src=ROOT/meta['source_arc'];need(digest(src)==meta['source_arc_sha256'],'부모');a=Archive(src.read_bytes())
    gen=json.loads((D/args.source/'generation.json').read_text('utf8'));art=ROOT/gen['workspace_path'];need(digest(art)==gen['workspace_sha256'],'원화');im=Image.open(art).convert('RGBA');need(im.size==(1536,1024),'전체 셀비')
    out=D/args.out;need(out.resolve().is_relative_to(D.resolve()),'작업폴더');out.mkdir(exist_ok=False);records=[];rows=[]
    for q in meta['frames']:
        i,mask=q['cell'],q['mask'];form=q['form'];start=16 if mask else 0;crop=(i*768,0,(i+1)*768,1024);cell=im.crop(crop);ar=np.array(cell);labs,k=label(ar[:,:,3]>=128,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;need(sum(sizes>1000)==1,'하나의 몸체')
        pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32);fixed=np.zeros((384,384),np.uint8);fixed[96:224,112:208]=register(cell,(96,128),pal,'area_vote');old=full(a,138,mask)
        Image.fromarray(fixed).save(out/f'{form}_138_indices.png');a.rgba(fixed,start).save(out/f'{form}_138_rgba.png');oldbb=bbox(old);newbb=bbox(fixed)
        records.append({'ref':138,'form':form,'mask':mask,'cell':i,'source_crop':list(crop),'old_bbox_world':oldbb,'fixed_bbox_world':newbb,'old_eye_world':optional_eye(old),'fixed_eye_world':optional_eye(fixed),'translation':[0,0],'floor_delta':newbb[3]-oldbb[3],'native_components8':int(label(fixed>0,np.ones((3,3)))[1]),'native_sha256':sha(fixed.tobytes()),'old_pixels_copied':0})
        rows.append((f'{form} 138',[('idle',a.composite(0,mask)[0]),('previous 138',a.composite(138,mask)[0]),('new fixed',a.rgba(fixed,start))]))
    helper.grid(rows,out/'comparison.png',7);write(out/'registration.json',{'source_art_path':art.relative_to(ROOT).as_posix(),'source_art_sha256':digest(art),'source_size':list(im.size),'parent_arc_sha256':digest(src),'method':'전체768x1024셀→96x128 면적투표. bbox재축척/원점이동/옛머리덮기 없음. 실제알파로만배경분리.','frames':records,'native_packed':False,'runtime_verified':False});print(json.dumps(records))
if __name__=='__main__':main()
