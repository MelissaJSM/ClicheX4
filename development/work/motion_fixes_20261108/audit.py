"""Current-build motion audit. Raw origins and native palettes; no per-pose normalization."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,metrics,animation_map
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
from src.psx_disc import file_hash
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
def board(items,path,cols=5):
 result=Image.new('RGB',(cols*300,((len(items)+cols-1)//cols)*320),(31,38,50));d=ImageDraw.Draw(result)
 for i,(label,im)in enumerate(items):
  crop=im.crop((112,120,208,200)).resize((288,240),Image.Resampling.NEAREST);x=i%cols*300;y=i//cols*320;result.paste(crop,(x+6,y+42),crop);d.text((x+8,y+8),label,fill='white');d.line((x+150,y+42,x+150,y+282),fill=(48,58,67))
 result.save(path)
sources={}
for project in('ver_buki_riko','ver_rin_nana'):
 pointer=json.loads((ROOT/'projects'/project/'current_build.json').read_text('utf8'));game=ROOT/Path(pointer['cue']).with_suffix('.bin');assert file_hash(game)==pointer['sha256'];d=W/project;d.mkdir(exist_ok=True)
 assets,records=read_disc(game,['PL00_U.ARC','PL01_U.ARC','PL02_U.ARC','MOJIPAT.ARC','SLUS_005.61']);sources[project]={'pointer':pointer,'records':records,'resources':{n:sha(b)for n,b in assets.items()}}
 for n,b in assets.items():(d/n).write_bytes(b)
 who='nana'if project=='ver_rin_nana'else'shibuki';report={};anims,_=animation_map(assets['SLUS_005.61']);write(d/'x_animations.json',anims)
 for name,arcname,mask in [('base','PL00_U.ARC',0),('fourth','PL00_U.ARC',15),('ultimate_before','PL02_U.ARC',15),('ultimate_after','PL02_U.ARC',0)]:
  a=Archive(assets[arcname]);folder=d/name;folder.mkdir(exist_ok=True);frames={}
  refs=[0,33,35,37,39,41,43,45,47,49,51,53,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85]
  for n in refs:
   im,meta=a.composite(n,mask);im.save(folder/f'{n:03}.png');frames[n]=metrics(im)
  for kind,ns in [('air',[0,33,35,37,39,41,43,45,47,49,53]),('dash',[0,67,69,71,73,75,77,79,81,83]),('shot',[0,68,70,72,74,76,78,80,82,84])]:board([(f'{who} {name} {n}',Image.open(folder/f'{n:03}.png'))for n in ns],d/f'{name}_{kind}.png')
  report[name]=frames
 z=Archive(assets['PL01_U.ARC']);items=[];zs={}
 for n in(147,44,45,46,47,48,49,50,51,52):
  a,m=z.layer(n);z.rgba(a).save(d/f'zero_{n:03}.png');np.save(d/f'zero_{n:03}.npy',a);items.append((f'{project} {n}',z.rgba(a)));zs[n]={'sha256':sha(a.tobytes()),**m}
 board(items,d/'zero_dash.png');write(d/'audit.json',{'x':report,'zero':zs})
 if project=='ver_buki_riko':
  a,_=z.layer(147);items=[]
  for row,label in [(0,'normal'),(13,'current black')]:items.append((label,z.rgba(a,row*16)))
  board(items,d/'riko_palette.png',2);write(d/'riko_palette.json',{'normal_words':list(map(int,z.words[:16])),'black_words':list(map(int,z.words[208:224]))})
write(W/'sources.json',sources)
print(json.dumps({p:{'sha256':q['pointer']['sha256'],'resources':q['resources']}for p,q in sources.items()}))
