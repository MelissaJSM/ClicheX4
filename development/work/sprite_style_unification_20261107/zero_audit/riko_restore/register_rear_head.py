"""Register the newly authored rear head and prepare 28 native targets."""
from pathlib import Path
import sys,hashlib,json,struct
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;H=D/'rear_head_inputs';OUT=D/'rear_registered_v1';OUT.mkdir(exist_ok=True)
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
from src.psx_player import graphics_bank,composition_frame,decode_stream
from src.psx_frame_edit import frame_coverage
def sha(b):return hashlib.sha256(b).hexdigest()
arc=(D/'prepared_v1/PL01_U.ARC').read_bytes();assert sha(arc)=='118f04c93c716a36138f903c32d260be2ffa3c6c951cf4993ea93b1f48d249da';pal=struct.unpack_from('<64H',entry(arc,9));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[:16]],np.float32)
source=H/'generated.png';im=Image.open(source).convert('RGBA');a=np.array(im);opaque=a[:,:,3]>=192;ix=np.zeros(a.shape[:2],np.uint8);rgb=a[opaque,:3].astype(np.float32);ix[opaque]=1+np.argmin(((rgb[:,None,:]-colors[None,1:,:])**2).sum(2),1)
votes=np.stack([np.array(Image.fromarray(((ix==i)&opaque).astype(np.float32),'F').resize((32,32),Image.Resampling.BOX))for i in range(1,16)]);coverage=np.array(Image.fromarray(opaque.astype(np.float32),'F').resize((32,32),Image.Resampling.BOX));head=(votes.argmax(0)+1).astype(np.uint8);head[coverage<.5]=0
out=Image.fromarray(head,'P');out.putpalette(colors.astype(np.uint8).ravel().tolist()+[0]*720);out.info['transparency']=0;out.save(OUT/'head_registered.png');rgba(head,pal).resize((512,512),Image.Resampling.NEAREST).save(OUT/'head_registered_16x.png')
meta=json.loads((H/'inputs.json').read_text('utf8'));old=np.array(Image.open(ROOT/'work/ver_buki_riko/art_pilot/ladder_v1/rear_head_indexed.png'));mask=np.zeros_like(old,bool)
for y,(x0,x1)in meta['rear_old_head_spans'].items():mask[int(y),x0:x1]=old[int(y),x0:x1]>0
bindings=json.loads((D/'rear_master_references.json').read_text('utf8'))['frames'];targets={};proof=[];g,c=entry(arc,2),entry(arc,3)
for r in bindings:
 b,n,pb=r['bank'],r['ref'],r['parts_bank'];world=render(arc,b,pb,n)[0];x,y=r['old_template_origin_world'];mirror=r['view']=='rear_mirrored';local=np.fliplr(mask)if mirror else mask;newhead=np.fliplr(head)if mirror else head;ox=x-(5 if mirror else 4);oy=y-8;owned=np.zeros_like(world,bool);owned[160+y:160+y+19,160+x:160+x+23]=local;protected=(world>0)&~owned;new=np.zeros_like(world);new[160+oy:160+oy+32,160+ox:160+ox+32]=newhead;visible=(new>0)&~protected;target=world.copy();target[owned]=0;target[visible]=new[visible];assert np.array_equal(world[protected],target[protected]);targets[r['id']]=target
 f=graphics_bank(g,b)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;cov,size,bb=frame_coverage(raw,f['tile_count'],composition_frame(c,pb,n));cover=np.zeros_like(world,bool);cover[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.array([bool(v)for v in cov]).reshape(size[1],size[0]);missing=visible&~cover
 proof.append({**r,'new_grid_origin_world':[ox,oy],'changed_pixels':int(np.count_nonzero(world!=target)),'new_visible_pixels':int(visible.sum()),'new_head_occluded_by_existing_body':int(((new>0)&protected).sum()),'new_alpha_pixels':int(((world==0)&(target>0)).sum()),'removed_alpha_pixels':int(((world>0)&(target==0)).sum()),'outside_current_parts':[[int(xx-160),int(yy-160)]for yy,xx in np.argwhere(missing)],'protected_body_exact':True})
np.savez_compressed(OUT/'targets.npz',**targets)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15);normal=pal;black=list(pal);black[:16]=struct.unpack_from('<16H',entry(arc,9),13*32);crop=(112,104,208,200);scale=4;cw=384;ch=408
for start in range(0,len(bindings),7):
 selection=bindings[start:start+7];board=Image.new('RGB',(cw*4,ch*(len(selection)+1)),'#65727a');dr=ImageDraw.Draw(board)
 for row,r in enumerate([{'id':'idle147','bank':0,'ref':147,'parts_bank':0}]+selection):
  before=render(arc,r['bank'],r['parts_bank'],r['ref'])[0];after=targets.get(r['id'],before)
  for col,(v,p,label)in enumerate(((before,normal,'normal before'),(after,normal,'normal new'),(before,black,'black before'),(after,black,'black new'))):
   pic=rgba(v,p).crop(crop).resize((cw,ch-24),Image.Resampling.NEAREST);board.paste(pic,(col*cw,row*ch+24),pic);dr.text((col*cw+4,row*ch+3),r['id']+' '+label,font=font,fill='white')
 board.save(OUT/f'comparison_{start//7:02}.png')
report={'source_image':str(source.relative_to(ROOT)),'source_sha256':sha(source.read_bytes()),'actual_source_size':list(im.size),'native_size':[32,32],'normalization':'원본 전체 정사각형 유지. alpha>=192의 원팔레트 최근접 색을32×32 셀별 면적 투표. alpha coverage>=0.5. 임의 윤곽 덮기 없음.','indexed_head_sha256':sha((OUT/'head_registered.png').read_bytes()),'targets_sha256':sha((OUT/'targets.npz').read_bytes()),'head_bbox':list(rgba(head,pal).getbbox()),'head_pixels':int((head>0).sum()),'palette_words':list(pal[:16]),'source_arc_sha256':sha(arc),'frames':proof,'all_targets_fit_current_parts':all(not r['outside_current_parts']for r in proof),'native_packing_done':False,'runtime_verified':False}
(OUT/'registration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'source_size':list(im.size),'head_bbox':report['head_bbox'],'head_pixels':report['head_pixels'],'frames':len(proof),'outside':{r['id']:r['outside_current_parts']for r in proof if r['outside_current_parts']}}))
