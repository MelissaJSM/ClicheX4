"""Read-only style comparison against current idle; no game/art edits."""
from pathlib import Path
import hashlib,json,sys
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
OUT=Path(__file__).parent
SOURCES={
 'riko':('ver_buki_riko','shibuki_riko','21bee159a1267d56561d4fa15c99ec652780af782fe08a433859c9eb7676099a'),
 'rin':('ver_rin_nana','rin_nana','f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720')}
GROUPS={
 'locomotion':['b0_008','b0_014','b0_021','b0_027','b0_035','b0_039','b0_044','b0_049','b0_135'],
 'saber_special':['b0_067','b0_095','b0_131','b0_164','b0_213','b0_229','b1_054','b1_086','b1_103'],
 'rare_rear':['b0_149','b0_174','b0_196','b0_249','b1_001','b1_005','b1_020','b1_132','b1_148','b1_163','b1_183','b1_066']}
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def main():
 report={}
 font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',14)
 for char,(mode,stem,expected)in SOURCES.items():
  source=ROOT/f'out/{mode}/sprite_reaudit_20261106_v1/{stem}.bin';assert sha(source)==expected
  old=ROOT/f'out/{mode}/hurt_capsule_fix_20261106_v1/{stem}.bin'
  a,_=read_disc(source,('PL01_U.ARC',));b,_=read_disc(old,('PL01_U.ARC',));assert a==b
  baseline=ROOT/'out/sprite_consistency_20261105'/char
  revpath=ROOT/'out/sprite_consistency_20261105/revised'/char/'mapping.json'
  rev=json.loads(revpath.read_text('utf8'))['frames']if revpath.exists()else{}
  paths={};sheets=[]
  for variant in ('normal','black'):
   for group,refs in GROUPS.items():
    rows=[]
    for start in range(0,len(refs),3):rows.append(['b0_147']+refs[start:start+3])
    images={}
    for ref in {v for row in rows for v in row}:
     p=ROOT/rev[f'{variant}:{ref}']if f'{variant}:{ref}'in rev else baseline/variant/'native'/(ref+'.png')
     images[ref]=Image.open(p).convert('RGBA');paths[f'{variant}:{ref}']=str(p.relative_to(ROOT))
    boxes=[im.getbbox()for im in images.values()if im.getbbox()]
    box=(min(132,min(v[0]for v in boxes))-3,min(120,min(v[1]for v in boxes))-3,max(190,max(v[2]for v in boxes))+3,max(187,max(v[3]for v in boxes))+3)
    scale=5;w=(box[2]-box[0])*scale;h=(box[3]-box[1])*scale;cw,ch=w+8,h+28
    board=Image.new('RGB',(cw*4,ch*len(rows)), '#68747c');draw=ImageDraw.Draw(board)
    for y,row in enumerate(rows):
     for x,ref in enumerate(row):
      px,py=x*cw,y*ch;draw.text((px+3,py+3),f'{char} {variant} {ref}',font=font,fill='white')
      im=images[ref].crop(box).resize((w,h),Image.Resampling.NEAREST);board.paste(im,(px,py+28),im)
    path=OUT/f'{char}_{variant}_{group}.png';board.save(path)
    sheets.append({'path':str(path.relative_to(ROOT)),'refs':refs,'idle':'b0_147','variant':variant,'world_box':[v-160 for v in box],'scale':scale,'viewed':False})
  report[char]={'source':str(source.relative_to(ROOT)),'sha256':expected,'PL01_sha256':hashlib.sha256(a['PL01_U.ARC']).hexdigest(),'PL01_exact_previous_reaudit':True,'native_paths':paths,'detail_sheets':sheets}
 dump(OUT/'sources.json',report)
 print(json.dumps({'sources_verified':2,'detail_sheets':12}))
if __name__=='__main__':main()
