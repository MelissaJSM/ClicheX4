"""Exact native Riko rear-pose references; no authored or gameplay changes."""
from pathlib import Path
import sys,hashlib,json,struct
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;OUT=D/'rear_art_inputs';OUT.mkdir(exist_ok=True)
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba

def sha(b):return hashlib.sha256(b).hexdigest()
arc=(D/'baseline_PL01_U.ARC').read_bytes();assert sha(arc)=='949f1066ed1471f8ad64a275f82020ab9109dd525a1d172628c0b7a3cd8e6178'
approved=(D/'prepared_v1/PL01_U.ARC').read_bytes();assert sha(approved)=='118f04c93c716a36138f903c32d260be2ffa3c6c951cf4993ea93b1f48d249da'
refs=[(0,147,'idle standard'),(0,174,'ladder A'),(0,178,'ladder B'),(0,160,'ground dash slash A'),(0,168,'ground dash slash B'),(1,148,'rising flame rear')]
pal=struct.unpack_from('<64H',entry(arc,9));template=np.array(Image.open(ROOT/'work/ver_buki_riko/art_pilot/ladder_v1/rear_head_indexed.png'));tm=np.isin(template,[4,8,14]);pics={};arrays={};records=[]
for b,n,label in refs:
 a=render(arc,b,0 if b==0 else 5,n)[0];check=render(approved,b,0 if b==0 else 5,n)[0];assert np.array_equal(a,check);key=f'b{b}_{n:03d}';arrays[key]=a;pics[key]=rgba(a,pal)
boxes=[p.getbbox()for p in pics.values()];lo=np.min(np.array(boxes)[:,:2],axis=0)-5;hi=np.max(np.array(boxes)[:,2:],axis=0)+5
crop=[int(np.floor(v/8)*8)for v in lo]+[int(np.ceil(v/8)*8)for v in hi];scale=6;cw=(crop[2]-crop[0])*scale;ch=(crop[3]-crop[1])*scale;header=30
board=Image.new('RGBA',(cw*2,(ch+header)*3),(0,0,0,0));draw=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
for i,(b,n,label)in enumerate(refs):
 key=f'b{b}_{n:03d}';a=arrays[key];p=pics[key];p.save(OUT/(key+'.png'));idx=Image.fromarray(a,'P');rgb=[]
 for v in pal[:16]:rgb.extend([(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31])
 idx.putpalette(rgb+[0]*(768-len(rgb)));idx.info['transparency']=0;idx.save(OUT/(key+'_indexed.png'))
 x,y=i%2*cw,i//2*(ch+header);q=p.crop(crop).resize((cw,ch),Image.Resampling.NEAREST);board.alpha_composite(q,(x,y+header));draw.text((x+5,y+5),key+' '+label,font=font,fill='white')
 head=None
 if n!=147:
  matches=[]
  for wy in range(-55,1):
   for wx in range(-42,31):
    patch=a[160+wy:160+wy+19,160+wx:160+wx+23];equal=int((patch[tm]==template[tm]).sum());matches.append((equal,wx,wy))
  equal,wx,wy=max(matches);head={'old_template_origin_world':[wx,wy],'old_template_size':[23,19],'green_sample_exact':equal,'green_sample_total':int(tm.sum()),'warning':'기존 템플릿 사각형에는 어깨/손이 들어 있다. 재작화 등록 때 머리 의미 마스크로 분리하고 손/어깨를 보호해야 한다.'}
 records.append({'key':key,'bank':b,'parts_bank':0 if b==0 else 5,'ref':n,'label':label,'file':str((OUT/(key+'.png')).relative_to(ROOT)),'sha256':sha((OUT/(key+'.png')).read_bytes()),'indexed_file':str((OUT/(key+'_indexed.png')).relative_to(ROOT)),'native_canvas':[384,384],'native_origin':[160,160],'native_alpha_bbox':list(p.getbbox()),'pixelcrop':crop,'scale':scale,'resampling':'nearest','cell':[i%2,i//2],'cell_pixel_origin':[x,y],'sprite_area_origin':[x,y+header],'world_origin_on_sheet':[x+(160-crop[0])*scale,y+header+(160-crop[1])*scale],'head_binding_hint':head})
board.save(OUT/'rear_inputs_transparent.png');neutral=Image.new('RGBA',board.size,'#65727a');neutral.alpha_composite(board);neutral.convert('RGB').save(OUT/'rear_inputs.png')
report={'source_bin':'out/ver_buki_riko/sprite_reaudit_20261106_v1/shibuki_riko.bin','source_bin_sha256':'21bee159a1267d56561d4fa15c99ec652780af782fe08a433859c9eb7676099a','source_arc_sha256':sha(arc),'accepted_3rd_saber_arc_sha256':sha(approved),'all_references_equal_accepted_3rd_saber_arc':True,'source_assets_are_authored_replacement_sprites':True,'purpose':'대기147의 머릿결/색 분할/선택적 윤곽 수준을 목표 후면 자세에 반영하는 재작화 입력. 현재 팔·손·몸통·발·기준점은 보호. 새 얼굴을 정면으로 복제하지 않는다.','sheet':'rear_inputs.png','transparent_sheet':'rear_inputs_transparent.png','layout':[2,3],'cell_size':[cw,ch+header],'sprite_cell_size':[cw,ch],'label_height':header,'pixelcrop':crop,'worldcrop':[crop[0]-160,crop[1]-160,crop[2]-160,crop[3]-160],'scale':scale,'full_native_pose_unclipped':True,'palette_words':list(pal[:16]),'refs':records,'game_changed':False,'generated_art':False}
(OUT/'inputs.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sheet_size':list(board.size),'crop':crop,'refs':[r['key']for r in records],'head_hints':[r['head_binding_hint']for r in records]},ensure_ascii=False))
