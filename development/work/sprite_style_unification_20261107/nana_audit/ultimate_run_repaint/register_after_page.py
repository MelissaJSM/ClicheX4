"""새 의상 donor를 고정96px 셀로 읽는다. 공통 몸체의 의미영역 합성은 별도."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint')]
from preview_restore import Archive,digest,sha,write,need,helper
from register_page import register

def main():
 p=argparse.ArgumentParser();p.add_argument('--page',required=True,choices=list('abcd'));p.add_argument('--version',default='v1');args=p.parse_args();page=args.page
 src=D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC';need(digest(src)=='d1d25c1677f4b108e6cca373ca8cdc7957f1c4e51a4d8480b37a8f06479607d0','Parent');a=Archive(src.read_bytes())
 art=D/f'after_{page}_v1/generated.png';g=json.loads((art.parent/'generation.json').read_text('utf8'));need(digest(art)==g['workspace_sha256'],'Art');im=Image.open(art).convert('RGBA');out=D/f'after_{page}_registered_{args.version}';out.mkdir(exist_ok=False)
 pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32);poses=json.loads((D/f'after_inputs_v1/{page}_poses.json').read_text('utf8'));rows=[];records=[]
 for i,q in enumerate(poses):
  n=q['ref'];box=[round(i%2*im.width/2),round(i//2*im.height/2),round((i%2+1)*im.width/2),round((i//2+1)*im.height/2)];cell=im.crop(box)
  ar=register(cell,(96,96),pal,'area_vote');target=np.zeros((384,384),np.uint8);target[112:208,112:208]=ar;Y,X=np.indices(target.shape);ys,xs=np.nonzero((target==14)&(Y<160+q['eye_world'][1]+5)&(Y>160+q['eye_world'][1]-5));need(len(ys)>0,'Eye');ey=int(ys.min()-160);ex=int(np.median(xs[ys==ys.min()])-160);dx=int(q['eye_world'][0])-ex;dy=int(q['eye_world'][1])-ey;need(abs(dx)<=4 and abs(dy)<=4,'Unexpected drift');target=np.roll(target,(dy,dx),(0,1));need(not target[:80].any()and not target[-80:].any(),'No wrap')
  Image.fromarray(target).save(out/f'after_{n:03}.png');a.rgba(target).save(out/f'after_{n:03}_rgba.png');before=np.array(Image.open(ROOT/q['source']));need(digest(ROOT/q['source'])==q['source_sha256'],'Body');records.append({'ref':n,'cell_crop':box,'native_cell':[96,96],'eye_target':q['eye_world'],'rigid_shift':[dx,dy],'before_path':q['source'],'before_sha256':q['source_sha256'],'native_sha256':sha(target.tobytes()),'components8':int(label(target>0,np.ones((3,3)))[1])});rows.append((f'after run {n}',[('after idle',a.composite(0,0)[0]),('new fixed before',a.rgba(before,16)),('after costume donor only',a.rgba(target))]))
 helper.grid(rows,out/'comparison.png',6);write(out/'registration.json',{'parent_sha256':digest(src),'source_art_sha256':digest(art),'method':'고정96px 셀과 눈 기준 평행이동만. 확대/행워핑 없음. 머리·사지·권총은 후속 의미영역 합성에서 채택된 전폼 새 그림을 보호한다.','frames':records,'native_packed':False,'runtime_verified':False});print(out)
if __name__=='__main__':main()
