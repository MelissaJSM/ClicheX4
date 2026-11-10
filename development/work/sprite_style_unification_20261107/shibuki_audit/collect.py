"""현행 시부키 원본을 읽어 스타일 비교 자료만 만든다. 게임 쓰기 없음."""
from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw
from scripts.export_x_consistency import Archive,page,GROUPS
from scripts.c01_audio_build import read_disc
from src.psx_disc import file_hash
SOURCE=ROOT/'out/ver_buki_riko/sprite_reaudit_20261106_v1/shibuki_riko.bin'
SHA='21bee159a1267d56561d4fa15c99ec652780af782fe08a433859c9eb7676099a'
FORMS=[('base','PL00_U.ARC',0),('fourth','PL00_U.ARC',15),('ultimate_before','PL02_U.ARC',15),('ultimate_after','PL02_U.ARC',0)]
def rel(p):return p.relative_to(ROOT).as_posix()
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 assert file_hash(SOURCE)==SHA
 assets,records=read_disc(SOURCE,('PL00_U.ARC','PL02_U.ARC'));arcs={k:Archive(v)for k,v in assets.items()};sheets=[];exceptions=[];frames=[]
 for form,filename,mask in FORMS:
  folder=H/form;folder.mkdir(parents=True,exist_ok=True);a=arcs[filename];images={}
  for n in range(237):
   try:im,_=a.composite(n,15 if form=='ultimate_after' and 217<=n<=230 else mask)
   except(ValueError,IndexError)as e:exceptions.append({'form':form,'ref':n,'reason':str(e)});continue
   images[n]=im;path=folder/f'{n:03}.png';im.save(path);frames.append({'form':form,'ref':n,'path':rel(path),'rgba_sha256':sha(im.tobytes())})
  for group,refs in GROUPS.items():
   if group=='reserved_or_empty':continue
   for start in range(0,len(refs),24):
    selected=[n for n in refs[start:start+24]if n in images];path=folder/f'{group}_{start//24:02}.png'
    sheets.append({'form':form,'group':group,'refs':selected,**page([(f'{n:03}',images[n])for n in selected],images[0],path)})
  refs=[0,11,33,71,95,100,120,135,143,204,213,217]
  sheet=Image.new('RGB',(320*4,304*3),(26,32,43));d=ImageDraw.Draw(sheet)
  for i,n in enumerate(refs):
   im=images[n].crop((120,122,200,190)).resize((320,272),Image.Resampling.NEAREST);x=i%4*320;y=i//4*304;d.text((x+4,y+5),f'{form} / {n}',fill='white');sheet.paste(im,(x,y+30),im)
  sheet.save(folder/'style_focus.png')
  if form=='ultimate_before':
   # Native-size user example; same crop and scale, no anatomy rescaling.
   panel=Image.new('RGB',(600,410),(26,32,43));dr=ImageDraw.Draw(panel)
   for i,n in enumerate((0,11)):
    im=images[n].crop((135,125,185,188)).resize((300,378),Image.Resampling.NEAREST);panel.paste(im,(i*300,30),im);dr.text((i*300+5,4),f'Ultimate jacket {n:03}',fill='white')
   panel.save(H/'idle_vs_011.png')
 partial=[];a=arcs['PL00_U.ARC']
 for n in (11,33,71,95,120,135,143,204):
  path=H/f'partial_{n:03}.png';partial.append({'ref':n,**page([(f'{n} mask{mask}',a.composite(n,mask)[0])for mask in (0,1,2,4,8,15)],a.composite(0,15)[0],path,cols=3,scale=3)})
 out={'source':rel(SOURCE),'sha256':SHA,'resources':{k:{'sha256':sha(v),'record':records[k]}for k,v in assets.items()},'forms':FORMS,'frames':frames,'sheets':sheets,'partial_sheets':partial,'exceptions':exceptions,'game_written':False}
 (H/'source_manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'main_sheets':len(sheets),'frames':len(frames),'partial_sheets':len(partial)}))
if __name__=='__main__':main()
