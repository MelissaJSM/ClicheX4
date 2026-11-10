"""원80px셀 축척으로 의상 편집 원화 등록. 새 전폼 몸체는 아직 합성하지 않는다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,sha,digest,write,need,helper
from register_page import register
from prepare_inputs import SRC,EXPECTED
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--page',default='a');parser.add_argument('--version',default='v2');args=parser.parse_args();page=args.page;need(page in'a b c'.split()and args.version.isalnum(),'Page/version');source=D/f'after_{page}_v1/generated.png';g=json.loads((source.parent/'generation.json').read_text('utf8'));need(digest(source)==g['workspace_sha256']and digest(SRC)==EXPECTED,'Input');a=Archive(SRC.read_bytes());out=D/f'after_{page}_registered_{args.version}';out.mkdir(exist_ok=False);im=Image.open(source).convert('RGBA');poses=json.loads((D/f'after_inputs_v1/{page}_poses.json').read_text('utf8'));pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32);rows=[];records=[]
 for i,q in enumerate(poses):
  n=q['ref'];cx=i%2*im.width//2;cy=i//2*im.height//2;box=[cx,cy,cx+im.width//2,cy+im.height//2];cell=im.crop(box);ar=register(cell,(80,80),pal,'area_vote');target=np.zeros((384,384),np.uint8);target[120:200,120:200]=ar;Y,X=np.indices(target.shape);ys,xs=np.nonzero((target==14)&(Y<160+q['eye_world'][1]+4)&(Y>160+q['eye_world'][1]-4));need(len(ys)>0,'Pupil candidate');ey=int(ys.min()-160);ex=int(np.median(xs[ys==ys.min()])-160);dx=int(q['eye_world'][0])-ex;dy=int(q['eye_world'][1])-ey;need(abs(dx)<=4 and abs(dy)<=2,'Local cell shift');target=np.roll(target,(dy,dx),(0,1));need(not target[:80].any()and not target[-80:].any(),'Wrap')
  Image.fromarray(target).save(out/f'after_{n:03}.png');a.rgba(target).save(out/f'after_{n:03}_rgba.png');before=np.array(Image.open(ROOT/q['source']));records.append({'ref':n,'source_crop':box,'native_cell':[80,80],'fixed_origin':[-40,-40],'pupil_before':[ex,ey],'pupil_target':q['eye_world'],'translation':[dx,dy],'indexed_sha256':sha(target.tobytes()),'before_source':q['source'],'before_sha256':q['source_sha256']});rows.append((f'after costume {n}',[('accepted after idle',a.composite(0,0)[0]),('fixed new before',a.rgba(before,16)),('new after donor / not final body',a.rgba(target))]))
 helper.grid(rows,out/'comparison.png',6);write(out/'registration.json',{'source_art_sha256':digest(source),'parent_arc_sha256':EXPECTED,'frames':records,'method':'고정80px입력셀 area-vote. 생성중 발생한 눈 x최대4/y최대2 이동만 평행 정합. 몸체확대/행워핑 없음. 새전폼 머리/손발은 후속 의상 의미영역 합성에서 보호.','native_packed':False,'runtime_verified':False});print(out)
if __name__=='__main__':main()
