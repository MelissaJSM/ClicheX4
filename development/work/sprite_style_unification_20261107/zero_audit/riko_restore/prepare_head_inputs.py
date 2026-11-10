"""Semantic rear/idle head cutouts for authored replacement input, no ARC writes."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;OUT=D/'rear_head_inputs';OUT.mkdir(exist_ok=True)
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
arc=(D/'prepared_v1/PL01_U.ARC').read_bytes();assert hashlib.sha256(arc).hexdigest()=='118f04c93c716a36138f903c32d260be2ffa3c6c951cf4993ea93b1f48d249da';pal=struct.unpack_from('<64H',entry(arc,9));rear=np.array(Image.open(ROOT/'work/ver_buki_riko/art_pilot/ladder_v1/rear_head_indexed.png'))
# The top hair ornament, bob silhouette and left hanging lock are head-owned.
# Glove at x20..22/y9..12, collar, shoulder and sleeve below/right are protected.
spans={1:(9,16),2:(7,17),3:(4,18),4:(4,19),5:(3,20),6:(3,20),7:(2,21),8:(2,21),9:(1,20),10:(1,19),11:(1,18),12:(2,18),13:(3,9),14:(3,8)}
rm=np.zeros(rear.shape,bool)
for y,(x0,x1)in spans.items():rm[y,x0:x1]=rear[y,x0:x1]>0
assert np.all(rm[np.isin(rear,[4,8,14])]);rear_only=np.where(rm,rear,0).astype(np.uint8)
front=np.array(Image.open(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'))[:19,12:35];idle=render(arc,0,0,147)[0]
matches=[]
for y in range(110,151):
 for x in range(120,175):
  if np.array_equal(idle[y:y+19,x:x+23][front>0],front[front>0]):matches.append((x-160,y-160))
assert len(matches)==1,matches
source_master={'rear':rear_only,'idle':front};offsets={'rear':(4,8),'idle':(4,4)};records={}
for name,a in source_master.items():
 grid=np.zeros((32,32),np.uint8);x,y=offsets[name];grid[y:y+a.shape[0],x:x+a.shape[1]]=a;p=rgba(grid,pal);p.save(OUT/(name+'_32.png'));p.resize((512,512),Image.Resampling.NEAREST).save(OUT/(name+'_16x.png'));idx=Image.fromarray(grid,'P');rgb=[]
 for word in pal[:16]:rgb.extend([(word&31)*255//31,((word>>5)&31)*255//31,((word>>10)&31)*255//31])
 idx.putpalette(rgb+[0]*(768-len(rgb)));idx.info['transparency']=0;idx.save(OUT/(name+'_indexed.png'));Image.fromarray((grid>0).astype(np.uint8)*255).save(OUT/(name+'_semantic_mask.png'))
 records[name]={'native_size':[32,32],'display_scale':16,'display_size':[512,512],'template_origin_in_grid':[x,y],'original_template_size':list(a.shape[::-1]),'head_bounds':list(p.getbbox()),'old_template_anchor_world':[-11,-24]if name=='rear'else list(matches[0]),'grid_origin_world_for_reference':[-11-x,-24-y]if name=='rear'else[matches[0][0]-x,matches[0][1]-y],'semantic_pixel_count':int((a>0).sum()),'source_ref':'b0_174'if name=='rear'else'b0_147','file':name+'_32.png','enlarged_file':name+'_16x.png','sha256':hashlib.sha256((OUT/(name+'_32.png')).read_bytes()).hexdigest()}
protected=np.where(rm,0,rear).astype(np.uint8);rgba(protected,pal).resize((368,304),Image.Resampling.NEAREST).save(OUT/'protected_hand_shoulder_16x.png')
board=Image.new('RGB',(1024,542),'#65727a');draw=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
for i,name in enumerate(('rear','idle')):
 p=Image.open(OUT/(name+'_16x.png'));board.paste(p,(i*512,30),p);draw.text((i*512+5,5),name+' native32 / x16',font=font,fill='white')
board.save(OUT/'head_comparison.png')
report={'source_arc_sha256':hashlib.sha256(arc).hexdigest(),'source_palette_words':list(pal[:16]),'mask_is_semantic_manual':True,'rear_old_head_spans':{str(k):list(v)for k,v in spans.items()},'rear_old_head_excludes_glove_shoulder_collar':True,'new_alpha_need_not_equal_old':True,'registration_contract':'새 머리 알파는 기존과 같을 필요가 없다. 현재 손/팔/어깨/목 도구는 보호하고, 기존 머리 의미 마스크만 지운 뒤 새 픽셀을 등록한다. 실제 새그림 크기/원점과 28참조의 타일 커버리지를 별도 확인한다. 기존 머리의 저해상도 윤곽을 강제 덮지 않는다.','rear_registration_from_grid':'각 rear_master_references.json의 old_template_origin_world에서 [4,8]을 뺀 곳이 새32grid 원점. 반전참조는 필요 시32grid 전체반전과 anchor변환을 함께 적용.','refs_file':'../rear_master_references.json','heads':records,'game_changed':False,'generated_art':False}
(OUT/'inputs.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(records))
