"""새5머리의 턱 끝을 원타일 끝에 맞추고 원화의 작은 청록 눈 표본을 보존한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';A=D/'ride_head01';O=D/'ride_head_registered_v1';O.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();j=json.loads((A/'inputs.json').read_text('utf8'));arc=(ROOT/j['source_arc']).read_bytes();pal=j['palette_words'];records=[];targets={};masters={}
source=np.array(Image.open(A/'generated.png').convert('RGBA'));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32)
for m in j['masters']:
 n=m['ref'];p=A/'native_fixed'/f'head_{n}_indices32.png';v=np.array(Image.open(p));ops=[]
 if n==66:
  # This is the exact small cyan iris in the generated art, not an invented color.
  cell=source[19*16:20*16,13*16:14*16];nearest=np.argmin(((cell[:,:,:3].astype(np.int32)[:,:,None]-colors[None,None])**2).sum(-1),axis=2)+1
  weight=int(np.where(nearest==15,cell[:,:,3],0).sum());assert 54<=weight/256<=58 and v[19,13]!=15
  ops.append({'operation':'preserve_generated_iris_sample','native_cell':[13,19],'before_index':int(v[19,13]),'after_index':15,'source_cyan_alpha_average':weight/256,'source_pixel_rect':[208,304,224,320]});v[19,13]=15
 z=np.roll(v,1,axis=0);assert not v[-1].any();tile=z[8:24,8:24].copy();outside=z.copy();outside[8:24,8:24]=0;assert not outside.any()and not tile[:,0].any()
 out=O/f'head_{n}_indices16.png';Image.fromarray(tile).save(out);masters[n]=tile
 for ref in m['aliases']:
  x,y,r,b=j['frames'][str(ref)]['world_bounds'];world=np.zeros((384,384),np.uint8);world[y:b,x:r]=tile;targets[ref]=world;Image.fromarray(world).save(O/f'b1_{ref:03}_indices.png')
 records.append({'key':f'head_{n}','source_native_sha256':sha(p),'whole_local_translation':[0,1],'operations':ops,'output_sha256':sha(out),'aliases':m['aliases'],'old_native_height':14,'new_native_height':12,'chin_bottom_old_new':23,'tile_and_world_origin_unchanged':True})
for form,row in [('normal',0),('black',13)]:
 words=struct.unpack_from('<16H',entry(arc,9),row*32);sheet=Image.new('RGB',(1600,670),(28,34,45));dr=ImageDraw.Draw(sheet)
 for i,m in enumerate(j['masters']):
  n=m['ref'];old=render(arc,1,5,n)[0];x,y,r,b=j['frames'][str(n)]['world_bounds']
  for k,v in enumerate([old[y:b,x:r],masters[n]]):
   pic=rgba(v,words).resize((256,256),Image.Resampling.NEAREST);sheet.paste(pic,(i*320+32,k*330+35),pic)
  dr.text((i*320+10,5),f'{n} old above / new below',fill='white')
 sheet.save(O/f'{form}_comparison.png')
reg={'source_arc_sha256':j['source_sha256'],'generated_sha256':sha(A/'generated.png'),'records':records,'new_ref_count':19,'original_master_count':5,'registered_refs':[{'key':f'b1_{n:03}','output_sha256':sha(O/f'b1_{n:03}_indices.png')}for n in targets],'scope':'원래 다섯 머리 각도와19개 위치를 유지한 새 세부 원화.12px높이는 원래14px보다짧아 미술 검토 중이며 턱/조종석 접점만y+1로 정합했다.66눈 한 셀은 실제 원화 청록 표본을 보존했다.','root_review_pending':True,'runtime_verified':False,'user_accepted':False}
(O/'registration.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'refs':len(targets),'records':records}))
