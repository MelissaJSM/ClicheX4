"""Exact Rin native input sheet for the next art pilot, without changing assets."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;OUT=D/'rin_art_inputs';OUT.mkdir(exist_ok=True)
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
source=json.loads((D/'sources.json').read_text('utf8'))['rin'];arc=read_disc(ROOT/source['source'],('PL01_U.ARC',))[0]['PL01_U.ARC'];assert hashlib.sha256(arc).hexdigest()==source['PL01_sha256'];pal=struct.unpack_from('<64H',entry(arc,9))
refs=[(0,147,'idle standard'),(0,8,'run A'),(0,14,'run B'),(0,49,'dash'),(0,95,'ground slash'),(1,183,'crouch special'),(0,229,'air slash')];pics={};arrays={}
for b,n,label in refs:
 key=f'b{b}_{n:03d}';a=render(arc,b,0 if b==0 else 5,n)[0];arrays[key]=a;pics[key]=rgba(a,pal)
boxes=[p.getbbox()for p in pics.values()];lo=np.min(np.array(boxes)[:,:2],axis=0)-5;hi=np.max(np.array(boxes)[:,2:],axis=0)+5;crop=[int(np.floor(v/8)*8)for v in lo]+[int(np.ceil(v/8)*8)for v in hi];scale=6;cw=(crop[2]-crop[0])*scale;ch=(crop[3]-crop[1])*scale;header=30
records=[]
for key,p in pics.items():
 p.save(OUT/(key+'.png'));q=Image.fromarray(arrays[key],'P');colors=[]
 for v in pal[:16]:colors.extend([(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31])
 q.putpalette(colors+[0]*(768-len(colors)));q.info['transparency']=0;q.save(OUT/(key+'_indexed.png'))
for name,selection in [('rin_inputs',refs[:6]),('rin_air_extra',[refs[0],refs[-1]])]:
 rows=(len(selection)+1)//2;board=Image.new('RGBA',(cw*2,(ch+header)*rows));draw=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
 for i,(b,n,label)in enumerate(selection):
  key=f'b{b}_{n:03d}';x,y=i%2*cw,i//2*(ch+header);p=pics[key];board.alpha_composite(p.crop(crop).resize((cw,ch),Image.Resampling.NEAREST),(x,y+header));draw.text((x+5,y+5),key+' '+label,font=font,fill='white');records.append({'key':key,'bank':b,'parts_bank':0 if b==0 else 5,'ref':n,'label':label,'sheet':name+'.png','file':str((OUT/(key+'.png')).relative_to(ROOT)),'sha256':hashlib.sha256((OUT/(key+'.png')).read_bytes()).hexdigest(),'indexed_file':str((OUT/(key+'_indexed.png')).relative_to(ROOT)),'native_canvas':[384,384],'native_origin':[160,160],'native_alpha_bbox':list(p.getbbox()),'pixelcrop':crop,'scale':scale,'cell':[i%2,i//2],'cell_pixel_origin':[x,y],'world_origin_on_sheet':[x+(160-crop[0])*scale,y+header+(160-crop[1])*scale]})
 board.save(OUT/(name+'_transparent.png'));bg=Image.new('RGBA',board.size,'#65727a');bg.alpha_composite(board);bg.convert('RGB').save(OUT/(name+'.png'))
report={'source_bin':source['source'],'source_bin_sha256':source['sha256'],'source_arc_sha256':source['PL01_sha256'],'source_assets_are_authored_replacement_sprites':True,'purpose':'대기147의 머릿결·눈/턱/목·선택적 윤곽·의상 명암 밀도로 전신 동작의 단순화된 부분을 재작화하는 입력. 같은 캐릭터 체형과 각 동작의 관절·무기·발 기준점을 유지한다.','main_layout':[2,3],'extra_layout':[2,1],'cell_size':[cw,ch+header],'sprite_cell_size':[cw,ch],'label_height':header,'pixelcrop':crop,'worldcrop':[crop[0]-160,crop[1]-160,crop[2]-160,crop[3]-160],'scale':scale,'resampling':'nearest','full_native_pose_unclipped':True,'palette_words':list(pal[:16]),'refs':records,'game_changed':False,'generated_art':False}
(OUT/'inputs.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'main_size':[cw*2,(ch+header)*3],'extra_size':[cw*2,ch+header],'crop':crop,'refs':len(refs)}))
