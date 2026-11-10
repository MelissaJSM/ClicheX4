"""다리별 같은 행의 새 원화 명암을 공통 외곽에 등록하는 제한 후보."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
LIMITS={100:(3,10),101:(4,5),102:(6,14),103:(6,13),104:(5,11),231:(7,17)}
def spans(mask):
 xs=np.flatnonzero(mask);return []if not len(xs)else np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)
def register_module(z,box,target_height):
 x0,y0,x1,y1=box;patch=z[y0+160:y1+160,x0+160:x1+160].copy();rows=np.rint(np.linspace(0,len(patch)-1,target_height)).astype(int);out=z.copy();out[y0+160:y1+160,x0+160:x1+160]=0;out[y0+160:y0+160+target_height,x0+160:x1+160]=patch[rows]
 links=[]
 for y,x in np.argwhere(patch[rows]>0):links.append({'world':[int(x+x0),int(y+y0)],'source_world':[int(x+x0),int(rows[y]+y0)],'index':int(patch[rows[y],x])})
 return out,links
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--v2',action='store_true');args=ap.parse_args()
 a=Archive((N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC').read_bytes());out=D/('common_legs_probe_v2'if args.v2 else'common_legs_probe_v1');out.mkdir(exist_ok=False);source=D/'body_contacts_probe_v1';rows=[];records=[]
 for n,(start,xmax)in LIMITS.items():
  authored_b=np.array(Image.open(source/f'base_{n:03}_indices.png'));authored_f=np.array(Image.open(source/f'fourth_{n:03}_indices.png'));b=authored_b.copy();f=authored_f.copy();modules=[]
  if args.v2:
   if n==100:
    f,ls=register_module(f,(4,6,11,10),5);modules.append({'form':'fourth','region':'folded ankle/shoe','source_box':[4,6,11,10],'target_height':5,'links':ls})
   if n in(101,102,104):
    box={101:(-11,9,-6,13),102:(8,18,15,22),104:(-9,3,-2,7)}[n];b,ls=register_module(b,box,3);modules.append({'form':'base','region':'terminal shoe module','source_box':list(box),'target_height':3,'links':ls})
  new=b.copy();links=[];rejected=[];region=(Y>=start)&(X<=xmax)
  for y in range(160+start,190):
   bs=spans((b[y]>0)&region[y]);fs=spans((f[y]>0)&region[y])
   if not bs:continue
   if args.v2 and n==102 and y==172 and len(bs)==1 and len(fs)==2:
    bs=[bs[0][bs[0]<162],bs[0][bs[0]>=162]]
   if args.v2 and n==231 and y in(167,168) and len(bs)==2 and len(fs)==1:
    left=bs[0];new[y,left]=0;new[y,left+1]=b[y,left];links.extend({'world':[int(x-159),y-160],'source_world':[int(x-160),y-160],'index':int(b[y,x])}for x in left);continue
   if len(bs)!=len(fs):
    # Extra Fourth shoe coverage does not require changing an already covered
    # base branch. It is explicitly retained, not nearest-neighbour filled.
    if args.v2 and all(np.all(f[y,s]>0)for s in bs):continue
    rejected.append({'world_y':y-160,'reason':'different branch count','base':[[(int(x)-160)for x in s]for s in bs],'fourth':[[(int(x)-160)for x in s]for s in fs]});continue
   for src,dst in zip(bs,fs):
    if np.array_equal(src,dst):continue
    minratio=1/3 if args.v2 and n==101 and y==180 else .5
    if abs(float(src.mean()-dst.mean()))>2 or min(len(src),len(dst))/max(len(src),len(dst))<minratio:
     rejected.append({'world_y':y-160,'reason':'large local shift or width ratio','base':[(int(x)-160)for x in src],'fourth':[(int(x)-160)for x in dst]});continue
    samples=np.rint(np.linspace(0,len(src)-1,len(dst))).astype(int);new[y,src]=0;new[y,dst]=b[y,src[samples]]
    links.extend({'world':[int(x-160),y-160],'source_world':[int(sx-160),y-160],'index':int(b[y,sx])}for x,sx in zip(dst,src[samples]))
  need(np.array_equal(new[~region],b[~region]),'Upper body exact');full=np.where(f,f,new).astype(np.uint8);res=(new>0)&(f==0)&region;Image.fromarray(new).save(out/f'base_{n:03}_indices.png');Image.fromarray(full).save(out/f'fourth_{n:03}_indices.png')
  Image.fromarray(f).save(out/f'fourth_authored_contacts_{n:03}_indices.png')
  rows.append((f'common leg {n}',[('authored base',a.rgba(authored_b)),('local row registration',a.rgba(new)),('authored Fourth',a.rgba(authored_f,16)),('actual full / residuals kept',a.rgba(full,16))]));records.append({'ref':n,'source_base_sha256':sha(authored_b.tobytes()),'source_fourth_sha256':sha(authored_f.tobytes()),'base_after_sha256':sha(new.tobytes()),'source_links':links,'localized_foot_modules':modules,'rejected_rows_preserved':rejected,'remaining_lower_base_pixels':int(res.sum()),'base_components_8':int(label(new>0,np.ones((3,3)))[1]),'upper_body_and_gun_exact':True})
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',7)
 write(out/'manifest.json',{'frames':records,'scope':'동일 행/동일 다리 순서에서 새 원화 색인만 국소 재등록한 비교 후보. 두다리 가지 수가 다르거나2px 초과 이동/폭2배 이상은 거부하고 원안을 보존하며 잔류를 공개한다. 완성 후보가 아니다.','native_packed':False,'runtime_verified':False,'art_accepted':False});print(json.dumps({q['ref']:{'rejected':len(q['rejected_rows_preserved']),'remaining':q['remaining_lower_base_pixels'],'components':q['base_components_8']}for q in records}))
if __name__=='__main__':main()
