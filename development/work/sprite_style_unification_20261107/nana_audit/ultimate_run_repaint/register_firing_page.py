"""새 사격 원화를 입력96px셀의 고정 축척으로 등록한다. 최종 몸체 아님."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,digest,sha,write,need,helper
from register_page import register
SRC=N/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC'
EXPECTED='d1d25c1677f4b108e6cca373ca8cdc7957f1c4e51a4d8480b37a8f06479607d0'
def pupil(v):
 Y,X=np.indices(v.shape);ys,xs=np.nonzero((v==14)&(Y<180));need(len(ys)>0,'Eye');ey=int(ys.min());ex=int(np.median(xs[ys==ey]));return ex,ey
def main():
 p=argparse.ArgumentParser();p.add_argument('--page',choices=list('abcd'),required=True);p.add_argument('--form',choices=['before','after'],default='before');p.add_argument('--version',default='v1');args=p.parse_args();page=args.page;form=args.form
 art=D/f'firing_{page}_{form}_{args.version}/generated.png';gen=json.loads((art.parent/'generation.json').read_text('utf8'));need(digest(art)==gen['workspace_sha256']and digest(SRC)==EXPECTED,'Input');a=Archive(SRC.read_bytes());out=D/f'firing_{page}_{form}_registered_{args.version}';out.mkdir(exist_ok=False);off=16 if form=='before'else 0;pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[off:off+16]],np.float32);im=Image.open(art).convert('RGBA');rows=[];recs=[]
 inputs=json.loads((D/'firing_inputs_v1/manifest.json').read_text('utf8'));refs=inputs['pages'][page]
 for i,n in enumerate(refs):
  q=next(x for x in inputs['frames']if x['ref']==n)['sources'][form];bp=ROOT/q['body_path'];need(digest(bp)==q['body_sha256'],'Body provenance');body=np.array(Image.open(bp));ex,ey=pupil(body);cx=i%2*im.width//2;cy=i//2*im.height//2;box=(cx,cy,cx+im.width//2,cy+im.height//2);ar=register(im.crop(box),(96,96),pal,'area_vote');v=np.zeros((384,384),np.uint8);v[112:208,112:208]=ar
  Y,X=np.indices(v.shape);gy,gx=np.nonzero((v==14)&(abs(Y-ey)<=4)&(abs(X-ex)<=6));need(len(gy)>0,'Local eye');sy=int(gy.min());sx=int(np.median(gx[gy==sy]));dx,dy=ex-sx,ey-sy;need(abs(dx)<=5 and abs(dy)<=4,'Source scale/position drift');v=np.roll(v,(dy,dx),(0,1));need(not v[:80].any()and not v[-80:].any(),'Wrap')
  Image.fromarray(v).save(out/f'{form}_{n:03}.png');a.rgba(v,off).save(out/f'{form}_{n:03}_rgba.png');recs.append({'ref':n,'source_crop':box,'native_fixed_cell':[96,96],'translation':[dx,dy],'eye_world':[ex-160,ey-160],'source_eye_world':[sx-160,sy-160],'body_path':bp.relative_to(ROOT).as_posix(),'body_sha256':digest(bp),'index_sha256':sha(v.tobytes()),'whole_source_for_review_only':True});rows.append((f'run firing {n}',[('fixed new body',a.rgba(body,off)),('original shot',a.composite(n,15 if off else 0)[0]),('new arm source / fixed scale',a.rgba(v,off))]))
 for i in(0,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
 write(out/'registration.json',{'source_art_sha256':digest(art),'parent_arc_sha256':EXPECTED,'frames':recs,'method':'96px 고정 입력셀을 area-vote로 양자화하고 눈 위치만 평행 정합. 전신 원화는 팔 출처 비교용이며 최종 몸체 대체 아님.','native_packed':False,'runtime_verified':False});print(out)
if __name__=='__main__':main()
