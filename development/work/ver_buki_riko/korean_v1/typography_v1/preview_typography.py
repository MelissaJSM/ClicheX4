"""Local font/type treatment comparison; no game resources or originals edited."""
import json
import math
import runpy
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from fontTools.ttLib import TTFont

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static

D=OUT.parent
FONTS=Path('C:/Windows/Fonts')
BG=(14,19,36)
LABEL=ImageFont.truetype(str(FONTS/'malgun.ttf'),16)
SMALL=ImageFont.truetype(str(FONTS/'malgun.ttf'),13)
PROFILES={
 'current_gulim':('gulim.ttc',0,None,'현재 굴림'),
 'dotum':('gulim.ttc',2,None,'돋움'),
 'noto400':('NotoSansKR-VF.ttf',0,400,'Noto Sans KR 400'),
 'noto500':('NotoSansKR-VF.ttf',0,500,'Noto Sans KR 500'),
 'noto600':('NotoSansKR-VF.ttf',0,600,'Noto Sans KR 600'),
 'noto800':('NotoSansKR-VF.ttf',0,800,'Noto Sans KR 800'),
 'hy_gothic':('H2GTRM.TTF',0,None,'HY중고딕'),
 'hy_graphic':('H2GPRM.TTF',0,None,'HY그래픽'),
 'hy_extra':('H2GTRE.TTF',0,None,'HY견고딕'),
 'hy_headline':('H2HDRM.TTF',0,None,'HY헤드라인'),
 'noto_serif':('NotoSerifKR-VF.ttf',0,600,'Noto Serif KR 600'),
}


def font(key,size):
 file,index,weight,_=PROFILES[key]
 f=ImageFont.truetype(str(FONTS/file),size,index=index)
 if weight is not None:f.set_variation_by_axes([weight])
 return f


def rgb_indices(pixels,size,palette=None):
 a=np.frombuffer(pixels,np.uint8).reshape(size[1],size[0]);out=np.zeros((*a.shape,4),np.uint8)
 if palette is None:
  out[:,:,:3]=(a*17)[:,:,None]
 else:
  table=np.array([[(v>>s&31)*255//31 for s in (0,5,10)] for v in palette],np.uint8)
  out[:,:,:3]=table[a]
 out[:,:,3]=np.where(a,255,0)
 return Image.fromarray(out)


def native_frames():
 frames=[];metadata=[]
 raw=(D/'ui_inventory/ST0E_U0.ARC').read_bytes()
 pal=entry((D/'ui_inventory/COL0E_U0.ARC').read_bytes(),5)
 p=struct.pack('<I',4)+entry(raw,0x12);g=entry(raw,0x10002)
 for n,caption in ((2,'타이틀 GAME START'),(29,'타이틀 CONTINUE'),(30,'타이틀 OPTION')):
  pixels,size,bounds,_=compose_static(g,local_composition(aliased_composition(p,0,n)))
  frames.append((caption,rgb_indices(pixels,size,struct.unpack_from('<16H',pal,6*32))))
  metadata.append({'role':caption,'archive':'ST0E_U0.ARC','frame':n,'size':size,'bounds':bounds,'indices':sorted(set(pixels))})
 load=(D/'inventory/LOAD_U.ARC').read_bytes();p=(D/'inventory/MOJIPAT.ARC').read_bytes()
 for bank,kind,n,caption in ((0,0x10001,0,'일반 메뉴 CONTINUE'),(0,0x10001,8,'일반 메뉴 LOAD DATA'),(0,0x10001,41,'일반 메뉴 MISSION COMPLETED'),(2,0x10008,4,'로딩 Now Loading...'),(2,0x10008,8,'스테이지 SKY LAGOON'),(2,0x10008,0,'원작 READY')):
  pixels,size,bounds,_=compose_static(entry(load,kind),local_composition(aliased_composition(p,bank,n)))
  frames.append((caption,rgb_indices(pixels,size)))
  metadata.append({'role':caption,'archive':'LOAD_U.ARC / MOJIPAT.ARC','bank':bank,'frame':n,'size':size,'bounds':bounds,'indices':sorted(set(pixels))})
 boss=(D/'boss_intro_inventory/STD_1_1U.ARC').read_bytes();start=struct.unpack('<2I',entry(boss,12))[1]
 pixels,size,bounds,_=compose_static(entry(boss,0x10102)[start:],local_composition(aliased_composition(entry(boss,10),1,0)))
 frames.append(('보스 소개 원작 설명',rgb_indices(pixels,size)))
 metadata.append({'role':'boss_description','archive':'STD_1_1U.ARC','bank':1,'size':size,'indices':sorted(set(pixels))})
 return frames,metadata


def dialogue(key):
 f=font(key,12);im=Image.new('RGBA',(240,54));d=ImageDraw.Draw(im)
 lines=['유즈하 리코','5567지점에 이레귤러가','출현했다! 지금 출동한다.']
 for row,line in enumerate(lines):
  for col,ch in enumerate(line):
   if ch==' ':continue
   tile=Image.new('1',(12,12));b=f.getbbox(ch);ImageDraw.Draw(tile).text((0,-b[1]),ch,font=f,fill=1)
   ink=Image.new('RGBA',tile.size,(247,250,255));ink.putalpha(tile.convert('L'))
   im.alpha_composite(ink,(col*12,row*18+2))
 return im


def raster(text,key,size,shear=0,shade=False,shadow=False,boss=False):
 f=font(key,size);b=f.getbbox(text)
 mask=Image.new('L',(b[2]-b[0],b[3]-b[1]));ImageDraw.Draw(mask).text((-b[0],-b[1]),text,font=f,fill=255)
 mask=mask.crop(mask.getbbox());w,h=mask.size
 if shear:
  skew=Image.new('L',(w+math.ceil(shear*(h-1)),h))
  for y in range(h):skew.paste(mask.crop((0,y,w,y+1)),(round((h-1-y)*shear),y))
  mask=skew
 # Actual-size alpha coverage quantized onto native-style discrete shades;
 # row-wise skew never resamples pixels. This is a preview, not CLUT insertion.
 aa=np.asarray(mask)
 if shade:
  levels=np.array([0,3,4,6,8,10,12,15],np.uint8)
  index=levels[np.minimum(7,(aa.astype('uint16')*7+127)//255)]
  mask=Image.fromarray((index*17).astype('uint8'))
 else:mask=mask.point(lambda v:255 if v>=128 else 0)
 w,h=mask.size;out=Image.new('RGBA',(w+4,h+4))
 if boss:
  solid=mask.point(lambda v:255 if v>=80 else 0)
  outline=solid.filter(ImageFilter.MaxFilter(3))
  dark=Image.new('RGBA',(w,h),(28,29,36));dark.putalpha(outline);out.alpha_composite(dark,(3,3))
  edge=Image.new('RGBA',(w,h),(230,236,255));edge.putalpha(outline);out.alpha_composite(edge,(1,1))
  cutout=Image.new('RGBA',(w,h),(3,5,9));cutout.putalpha(solid);out.alpha_composite(cutout,(1,1))
 else:
  if shadow:
   dark=Image.new('RGBA',(w,h),(34,39,57));dark.putalpha(mask.point(lambda v:255 if v else 0));out.alpha_composite(dark,(2,2))
  bright=Image.new('RGBA',(w,h),(248,250,255));bright.putalpha(mask);out.alpha_composite(bright,(1,1))
 return out


def main():
 chars=set()
 for r in json.loads((D/'dialogue_full_v5/proposal.json').read_text('utf-8'))['dialogue'].values():chars.update(r['glyphs'])
 data=runpy.run_path(str(D/'menu_ko.py'))
 chars.update(c for text in data['TEXT'].values() for c in text if '\uac00'<=c<='\ud7a3')
 chars.update('게임시작이어하기설정캐릭터선택불러오는중프로스트월러스')
 metadata={}
 for key,(file,index,weight,label) in PROFILES.items():
  tt=TTFont(FONTS/file,fontNumber=index,lazy=True);cmap=tt.getBestCmap();tt.close()
  f=font(key,12);oversized=[]
  for ch in sorted(chars):
   b=f.getbbox(ch)
   if b[2]>12 or b[3]-b[1]>12 or b[0]<0:oversized.append({'char':ch,'bbox':b})
  metadata[key]={'file':file,'face_index':index,'weight':weight,'family':f.getname(),
                 'required_hangul_count':len(chars),'missing':''.join(c for c in sorted(chars) if ord(c) not in cmap),
                 'bbox_outside_12px':oversized,'label':label}
 (OUT/'fonts.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
 native,source=native_frames()
 (OUT/'native_sources.json').write_text(json.dumps(source,ensure_ascii=False,indent=2),encoding='utf-8')
 board=Image.new('RGB',(1300,1230),BG);dr=ImageDraw.Draw(board)
 dr.text((20,14),'기준: 한글화 전 수용본의 실제 UI 자산 / 원본 크기 + 최근접 확대',font=LABEL,fill='white')
 for i,(label,im) in enumerate(native):
  y=55+i*110;dr.text((20,y),label,font=LABEL,fill=(177,201,234));board.paste(im,(300,y),im)
  large=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST)
  if im.height<=32:board.paste(large,(300,y+32),large)
 board.save(OUT/'native_reference.png')
 keys=['current_gulim','dotum','noto400','noto500','noto600','hy_gothic','hy_graphic','hy_extra','hy_headline','noto_serif']
 board=Image.new('RGB',(1340,1250),BG);dr=ImageDraw.Draw(board)
 dr.text((20,12),'12×12 대사 비트맵 비교 / 1배와 2배 / 실기 캡처 아님',font=LABEL,fill='white')
 for i,key in enumerate(keys):
  y=48+i*118;im=dialogue(key);dr.text((20,y),PROFILES[key][3],font=LABEL,fill=(177,201,234))
  dr.text((20,y+25),f"누락 {len(metadata[key]['missing'])} / 칸 초과 {len(metadata[key]['bbox_outside_12px'])}",font=SMALL,fill=(170,177,193))
  board.paste(im,(240,y),im)
  # 2x comparison preserves the three-line sample within each row.
  large=im.resize((480,108),Image.Resampling.NEAREST);board.paste(large,(520,y),large)
 board.save(OUT/'dialogue_candidates.png')
 role_rows=[
 ('타이틀 메뉴 / 게임 시작',('current_gulim',12,0,False,False,False),('hy_extra',12,.20,True,True,False),('noto800',12,.20,True,True,False),'게임 시작'),
 ('보통 메뉴 / 불러오기',('current_gulim',12,0,False,False,False),('noto600',12,.10,True,True,False),('hy_gothic',12,.10,True,True,False),'불러오기'),
 ('로딩 / 불러오는 중...',('current_gulim',12,0,False,False,False),('hy_graphic',12,.25,True,True,False),('hy_extra',12,.25,True,True,False),'불러오는 중...'),
 ('큰 제목 / 캐릭터 선택',('current_gulim',22,0,False,False,False),('hy_headline',22,.17,True,True,False),('noto800',22,.17,True,True,False),'캐릭터 선택'),
 ('보스 설명 / 비밀 병기를 지킨다',('current_gulim',16,0,False,False,False),('hy_extra',16,.20,True,True,False),('noto800',16,.20,True,True,False),'비밀 병기를 지킨다'),
 ('보스 대형 이름 / 프로스트',('noto800',52,0,False,False,True),('hy_headline',52,0,False,False,True),('hy_extra',52,0,False,False,True),'프로스트'),
 ]
 board=Image.new('RGB',(1640,1240),BG);dr=ImageDraw.Draw(board)
 dr.text((20,14),'용도별 처리 비교 / 좌: 단일 서체 방식 참고, 중·우: 후보 / 게임 미적용',font=LABEL,fill='white')
 report=[]
 for row,(label,*rest) in enumerate(role_rows):
  choices=rest[:3];text=rest[3];y=55+row*190;dr.text((20,y),label,font=LABEL,fill=(177,201,234))
  for col,choice in enumerate(choices):
   key,size,shear,shade,shadow,boss=choice;im=raster(text,key,size,shear,shade,shadow,boss)
   x=20+col*535;dr.text((x,y+28),f'{PROFILES[key][3]} / {size}px / 경사 {shear}',font=SMALL,fill=(200,207,218))
   board.paste(im,(x,y+55),im)
   scale=3 if im.height<22 and im.width<170 else 2 if im.width<250 and im.height<50 else 1
   large=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST);board.paste(large,(x,y+90),large)
   report.append({'role':label,'candidate':col,'font':key,'font_size':size,'shear':shear,'shades':shade,'shadow':shadow,'preview_size':im.size})
 board.save(OUT/'role_candidates.png')
 (OUT/'profiles.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'output':str(OUT),'profiles':len(metadata),'required_characters':len(chars),'missing':{k:v['missing'] for k,v in metadata.items()},'sheets':3},ensure_ascii=False))


if __name__=='__main__':main()
