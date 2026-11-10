"""동결 벽 부모에서 얼티밋 대시 전체 범위와 첫4키를 읽기 수집한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
SRC=N/'ultimate_wall_repaint/packed_wall_candidate_v1/PL02_U.ARC';EXPECTED='e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031';KEYS=(67,71,79,93);ALL=(*range(67,85),93,94);WINDOW=(112,112,208,208)
def merged(a,n,mask):
 z=a.layer(n)[0].copy()
 if mask:
  for pb in(8,5,7,6):
   p=a.layer(n,pb)[0];z[p>0]=p[p>0]
 return z
def main():
 need(digest(SRC)==EXPECTED,'Frozen parent');need(json.loads((SRC.parent/'FROZEN.json').read_text('utf8'))['asset_sha256']==EXPECTED,'Frozen record');a=Archive(SRC.read_bytes());out=D/'inputs_v1';out.mkdir(parents=True,exist_ok=False);recs=[]
 for form,mask in(('before',15),('after',0)):
  rows=[]
  for n in ALL:
   v=merged(a,n,mask);effect=np.where(v>=16,v,0).astype(np.uint8);body=np.where(v<16,v,0).astype(np.uint8);Image.fromarray(body).save(out/f'{form}_{n:03}.png');Image.fromarray(effect).save(out/f'{form}_effect_{n:03}.png');im=a.rgba(body,16 if mask else 0);yy,xx=np.nonzero(body);Y,X=np.indices(body.shape);eye=(body==14)&(Y<165);ey,ex=np.nonzero(eye)
   recs.append({'ref':n,'form':form,'mask':mask,'body_index_sha256':sha(body.tobytes()),'body_rgba_sha256':sha(im.tobytes()),'visible_effect_pixels':int((effect>0).sum()),'effect_sha256':sha(effect.tobytes()),'eye_world':[float(np.median(ex))-160,float(np.median(ey))-160]if len(ex)else None,'bbox_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'tile_count':a.banks[0]['frames'][n]['tile_count'],'stream_offset':a.banks[0]['frames'][n]['offset']})
   if n%2 or n==94:rows.append((f'{form} dash {n}',[('accepted idle',a.composite(0,mask)[0]),('current full',a.composite(n,mask)[0]),('body / effects separate',im),('new air / detail master',a.composite(39,mask)[0])]))
  for i in range(0,len(rows),3):helper.grid(rows[i:i+3],out/f'{form}_review_{i//3+1}.png',5)
  board=Image.new('RGBA',(1536,1536))
  for i,n in enumerate(KEYS):
   im=a.rgba(np.array(Image.open(out/f'{form}_{n:03}.png')),16 if mask else 0);outside=np.array(im)[:,:,3].copy();outside[112:208,112:208]=0;need(not outside.any(),'Input crop');board.alpha_composite(im.crop(WINDOW).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768))
  board.save(out/f'{form}_first4_targets.png')
  master=Image.new('RGBA',(1536,1536))
  for i,n in enumerate((0,39,55,65)):master.alpha_composite(a.composite(n,mask)[0].crop(WINDOW).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768))
  master.save(out/f'{form}_style_master.png')
 playback=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'));anims=[q for q in playback['characters']['nana']['forms']['ultimate_before']['animations']if any(s['frame_ref']in ALL for s in q['steps'])]
 write(out/'manifest.json',{'parent_arc':SRC.relative_to(ROOT).as_posix(),'parent_arc_sha256':EXPECTED,'full_refs':list(ALL),'first_keys':list(KEYS),'input_native_window_world':[-48,-48,48,48],'scale':8,'cell':[768,768],'records':recs,'animations_including_refs':anims,'images':{p.name:digest(p)for p in out.glob('*.png')},'new_art_generated':False,'native_packed':False,'scope':'대시20 입력 수집.93/94는 사격쌍으로 단정하지 않는다. 원래효과는별도보존하고노바머리연결217/218/220은후속감사.'});print(out)
if __name__=='__main__':main()
