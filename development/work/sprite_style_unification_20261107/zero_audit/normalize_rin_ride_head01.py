"""다섯 탑승 머리 원화를 고정1/16로 등록하고 단일타일 경계를 검사한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize,connected_groups
from scripts.overhaul_sprites_audit import rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension/ride_head01';O=D/'native_fixed';O.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();j=json.loads((D/'inputs.json').read_text('utf8'));arc=(ROOT/j['source_arc']).read_bytes();assert hashlib.sha256(arc).hexdigest()==j['source_sha256'];pal=j['palette_words'];black=struct.unpack_from('<16H',entry(arc,9),13*32)
src=D/'generated.png';assert sha(src)=='2283d7060f40e64730007807c86a166c0e40e5e072d6269ecffbf4945c2890b2';im=Image.open(src).convert('RGBA');assert im.size==(1024,1536)
colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32)
full=quantize(im,colors,1/16);assert full.shape==(96,64)and not full[64:96,32:64].any()
records=[]
for m in j['masters']:
 n=m['ref'];cx,cy=m['cell'];v=full[cy*32:(cy+1)*32,cx*32:(cx+1)*32];old=np.array(Image.open(D/f'head_{n}_native.png'))
 tile=v[8:24,8:24].copy();outside=v.copy();outside[8:24,8:24]=0
 Image.fromarray(v).save(O/f'head_{n}_indices32.png');Image.fromarray(tile).save(O/f'head_{n}_indices16.png')
 yy,xx=np.nonzero(v)
 records.append({'ref':n,'actual_bbox':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],'outside_tile_pixels':int(np.count_nonzero(outside)),'gpu_firstcolumn_pixels':int(np.count_nonzero(tile[:,0])),'components':[len(g)for g in connected_groups(tile>0)],'path':str((O/f'head_{n}_indices16.png').relative_to(ROOT)),'sha256':sha(O/f'head_{n}_indices16.png')})
for form,words in [('normal',pal),('black',black)]:
 sheet=Image.new('RGB',(5*320,680),(28,34,45));dr=ImageDraw.Draw(sheet)
 for i,m in enumerate(j['masters']):
  n=m['ref'];before=Image.open(D/f'head_{n}_native.png').convert('RGBA');v=full[m['cell'][1]*32:(m['cell'][1]+1)*32,m['cell'][0]*32:(m['cell'][0]+1)*32]
  # Before is original normal source; black is independently indexed from frame metadata.
  if form=='black':
   oldrgba=np.array(before);table=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]+[0 if k==0 else 255]for k,w in enumerate(pal)],np.uint8)
   ind=np.zeros((32,32),np.uint8)
   for k in range(1,16):ind[np.all(oldrgba==table[k],axis=2)]=k
   before=rgba(ind,words)
  for row,pic in enumerate((before,rgba(v,words))):
   view=pic.resize((320,320),Image.Resampling.NEAREST);sheet.paste(view,(i*320,row*340+20),view)
  dr.text((i*320+4,2),f'{n} old / new below',fill='white')
 sheet.save(O/f'{form}_comparison.png')
r={'source_sha256':sha(src),'source_size':list(im.size),'fixed_scale':1/16,'alpha_threshold_mean':128,'old_art_override':False,'old_tile_boundary_crop_applied':False,'records':records,'all_within_tile':all(x['outside_tile_pixels']==0 and x['gpu_firstcolumn_pixels']==0 for x in records),'scope':'고정 전체격자 등록만 수행했다. 밖으로 넘는 새 픽셀은 조용히 자르지 않고 별도 검사 실패로 기록한다.'}
(O/'registration.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
(D/'generation.json').write_text(json.dumps({'generated_sha256':sha(src),'prompt_sha256':sha(D/'prompt.txt'),'tool':'builtin imagegen','default_saved_path':'<LOCAL_PATH>','references':[{'path':str((D/n).relative_to(ROOT)),'sha256':sha(D/n)}for n in ['input.png','idle_head_style0.png','idle_full_style0.png']]},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(r))
