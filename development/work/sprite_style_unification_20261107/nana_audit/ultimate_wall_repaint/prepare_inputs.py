"""나나 얼티밋 벽6몸체의 원점 고정 입력/대기 및 새 공중 스타일 기준을 준비한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3];N=D.parent
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
SOURCE=N/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC';EXPECTED='122c92c29fd0599772e18ac5ed3f918c8f0d40703fe08c396e4ccbdbb92f2c18'
WINDOW=(120,120,200,200);KEYS=(55,57,59,61,63,65)
def indices(a,n,mask):
 v=a.layer(n,0)[0].copy()
 if mask:
  for pb in(8,5,7,6):
   p=a.layer(n,pb)[0];v[p>0]=p[p>0]
 return v
def main():
 need(digest(SOURCE)==EXPECTED,'Cumulative parent');a=Archive(SOURCE.read_bytes());out=D/'inputs_v1';out.mkdir(parents=True,exist_ok=False);records=[]
 for mask,form in[(15,'before'),(0,'after')]:
  rows=[]
  for n in KEYS:
   im=a.composite(n,mask)[0];ar=indices(a,n,mask);Image.fromarray(ar).save(out/f'{form}_{n:03}.png');Y,X=np.indices(ar.shape);eye=(ar==14)&(Y<165);gy,gx=np.nonzero(eye);yy,xx=np.nonzero(ar)
   records.append({'ref':n,'form':form,'mask':mask,'indexed_sha256':sha(ar.tobytes()),'rgba_sha256':sha(im.tobytes()),'eye_world':[float(np.median(gx))-160,float(np.median(gy))-160]if len(gx)else None,'bbox_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'tile_count':a.banks[0]['frames'][n]['tile_count'],'paired_firing_ref':n+1})
   rows.append((f'{form} wall {n}/{n+1}',[('accepted idle',a.composite(0,mask)[0]),('old wall pose',im),('old firing',a.composite(n+1,mask)[0]),('new air style',a.composite(33,mask)[0])]))
  for page,keys in [('a',KEYS[:3]),('b',KEYS[3:])]:
   board=Image.new('RGBA',(1280,1280));meta=[]
   for i,n in enumerate((*keys,0)):
    im=a.composite(n,mask)[0];pic=im.crop(WINDOW).resize((640,640),Image.Resampling.NEAREST);board.alpha_composite(pic,(i%2*640,i//2*640));meta.append({'cell':i,'ref':n,'role':'target'if i<3 else'accepted_idle_style_reference','origin_in_cell':[320,320],'scale':8})
   board.save(out/f'{form}_{page}_pose_targets.png');write(out/f'{form}_{page}_cells.json',meta)
  for k in range(2):helper.grid(rows[k*3:k*3+3],out/f'{form}_current_{k+1}.png',5)
 master=Image.new('RGBA',(1280,1280));masters=[]
 for i,(n,mask)in enumerate([(0,15),(33,15),(53,15),(0,0)]):
  pic=a.composite(n,mask)[0].crop(WINDOW).resize((640,640),Image.Resampling.NEAREST);master.alpha_composite(pic,(i%2*640,i//2*640));masters.append({'cell':i,'ref':n,'mask':mask,'role':'accepted_idle'if n==0 else'new_air_style_reviewed_by_root'})
 master.save(out/'style_master.png')
 write(out/'manifest.json',{'parent_arc':SOURCE.relative_to(ROOT).as_posix(),'parent_arc_sha256':EXPECTED,'keys':list(KEYS),'future_firing_refs':[n+1 for n in KEYS],'native_window_world':[-40,-40,40,40],'cell':[640,640],'scale':8,'originals_readonly':True,'new_art_generated':False,'records':records,'style_master_cells':masters,'images':{p.name:digest(p)for p in out.glob('*.png')},'scope':'벽 비사격6몸체 입력 준비. 새 원화·등록·패킹·실기 미수행. 공중22 후보와 분리.'})
 print(str(out))
if __name__=='__main__':main()
