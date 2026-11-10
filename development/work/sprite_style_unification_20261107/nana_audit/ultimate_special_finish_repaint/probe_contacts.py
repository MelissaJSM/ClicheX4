"""새 원화의 손/원권총 접점을 강체 조각으로 등록하는 진단."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,write,helper,sha
Y,X=np.indices((384,384));Y-=160;X-=160
def move_piece(z,mask,dx,dy):
 src=z.copy();piece=np.where(mask,src,0);z[mask]=0;dest=np.roll(np.roll(piece,dy,0),dx,1);occupied=dest>0;overlap=occupied&(z>0);z[occupied]=dest[occupied]
 return {'translation':[dx,dy],'source_cells':[[int(x-160),int(y-160),int(src[y,x])]for y,x in np.argwhere(mask&(src>0))],'destination_overlap_existing':int(overlap.sum())}
def main():
 m=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/m['parent_arc']).read_bytes());out=D/'contacts_probe_v1';out.mkdir(exist_ok=False);rows=[];records=[];canon=a.layer(85)[0];gm=(X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(canon,range(1,10));gun=np.where(gm,canon,0);assert np.count_nonzero(gun)==20;case=np.roll(np.roll(gun,-3,1),1,0)
 for n in(95,98):
  for form,start,am in(('before',16,15),('after',0,0)):
   p=D/(f'head_body95_probe_v1/{form}_095_indices.png'if n==95 else f'torso98_registered_v1/{form}_098_indices.png');z=np.array(Image.open(p));old=z.copy();pieces=[];wp={}
   if n==95:
    mask=(X<=-11)&(Y>=-10)&(Y<=4);pieces.append(move_piece(z,mask,2,-3));mask=(X>=12)&(Y>=-2)&(Y<=4);pieces.append(move_piece(z,mask,-3,-3))
   else:
    mask=(X<=-14)&(Y>=-8)&(Y<=4);pieces.append(move_piece(z,mask,0,-2));mask=(X>=17)&(Y>=-7)&(Y<=3);pieces.append(move_piece(z,mask,-1,-2))
    source=z.copy();skin=(X>=-24)&(X<=-17)&(Y>=-8)&(Y<=0)&np.isin(z,(10,11,12,13));rm=(X>=-29)&(X<=-18)&(Y>=-10)&(Y<=0)&np.isin(z,range(1,10));z[rm]=0;vis=(case>0)&~skin;z[vis]=case[vis];z[skin]=source[skin];wp={'canonical_ref':85,'translation':[-3,1],'canonical_texels':20,'gun_removed':[[int(x-160),int(y-160),int(source[y,x])]for y,x in np.argwhere(rm)],'skin':[[int(x-160),int(y-160),int(source[y,x])]for y,x in np.argwhere(skin)],'gun_skin_contact8':int(((case>0)&binary_dilation(skin,np.ones((3,3)))).sum())}
   Image.fromarray(z).save(out/f'{form}_{n:03}_indices.png');lab,c=label(z>0,np.ones((3,3)));sizes=np.bincount(lab.flat)[1:];records.append({'ref':n,'form':form,'source':p.relative_to(ROOT).as_posix(),'pieces':pieces,'weapon':wp,'components8':int(c),'component_sizes':sizes.tolist(),'target_sha256':sha(z.tobytes()),'candidate_only':True});rows.append((f'{form}{n}',[('idle',a.composite(0,am)[0]),('old pose',a.composite(n,am)[0]),('new registered',a.rgba(old,start)),('contact probe',a.rgba(z,start))]))
 for i in range(0,4,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',7)
 write(out/'manifest.json',{'scope':'새원화 강체조각과98정본85모듈 위치만 등록한 미채택 진단. 옛몸복사·새도트임의채움 없음.','records':records,'native_packed':False,'runtime_verified':False});print(json.dumps([{'ref':q['ref'],'form':q['form'],'components':q['component_sizes'],'contact':q['weapon'].get('gun_skin_contact8')}for q in records]))
if __name__=='__main__':main()
