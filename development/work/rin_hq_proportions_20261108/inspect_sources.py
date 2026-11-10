from pathlib import Path
import json,sys,struct,hashlib
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_ui_atlas import aliased_composition
from src.psx_ui_render import render_static_rgba
pointer=json.loads((ROOT/'projects/ver_rin_nana/current_build.json').read_text('utf8'))
game=ROOT/Path(pointer['cue']).with_suffix('.bin')
assert hashlib.sha256(game.read_bytes()).hexdigest()==pointer['sha256']
for name,file in [('reference',ROOT/'character/ver_rin_nana/rin(zero).webp'),('old_generated',ROOT/'work/ver_rin_nana/illustrations/hunter_v1/generated.png')]:
 im=Image.open(file).convert('RGBA');im.thumbnail((1000,1000));im.save(W/(name+'.png'))
report={}
for key,path in [('current',game),('original',ROOT/'MegaMan X4.bin')]:
 raw,records=read_disc(path,['ST0D_0Z.ARC','COL0D_0Z.ARC']);d=W/key;d.mkdir(exist_ok=True)
 for n,data in raw.items():(d/n).write_bytes(data)
 p=entry(raw['ST0D_0Z.ARC'],10);g=entry(raw['ST0D_0Z.ARC'],0x10102)[63488:81920]
 col=entry(raw['COL0D_0Z.ARC'],5);pals={i:struct.unpack_from('<16H',col,(35+i)*32)for i in range(min(8,len(col)//32-35))}
 sheet=Image.new('RGB',(7*180,2*300),(32,40,52));draw=ImageDraw.Draw(sheet);bounds=[]
 for n in range(14):
  c=aliased_composition(p,2,n);im,bb=render_static_rgba(g,c,pals);im.save(d/f'frame_{n:02d}.png')
  canvas=Image.new('RGBA',(256,144));canvas.paste(im,(bb[0]+128,bb[1]+64));canvas.save(d/f'world_{n:02d}.png')
  pic=im.crop(im.getbbox());pic=pic.resize((pic.width*2,pic.height*2),Image.Resampling.NEAREST);x=n%7*180;y=n//7*300;sheet.paste(pic,(x+(180-pic.width)//2,y+38),pic);draw.text((x+8,y+8),f'{key} {n}',fill='white')
  bounds.append({'frame':n,'bounds':bb,'ink_bounds':im.getbbox(),'parts':len(c['parts']),'cluts':sorted(set(q['clut']for q in c['parts']))})
 sheet.save(d/'sheet.png');report[key]={'path':str(path),'records':records,'frames':bounds}
(W/'source.json').write_text(json.dumps({'parent':pointer,'resources':report},indent=2,ensure_ascii=False)+'\n','utf8')
print(json.dumps({k:v['frames']for k,v in report.items()}))
