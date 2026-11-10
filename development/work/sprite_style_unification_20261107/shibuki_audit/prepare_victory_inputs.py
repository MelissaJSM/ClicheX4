"""승리 네 자세와 선택18의 실제 대응을 읽기 전용으로 고정한다."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static
from src.psx_disc import file_hash

def main():
 parent=H/'prepared_ladder_wall_front02';data=(parent/'PL00_U.ARC').read_bytes();ui=(parent/'ST0E_U1.ARC').read_bytes()
 need(sha(data)=='76f19a188ad58dd447eec058b669f8d62a4b8c00f957de3b229aeaa67f37495b','Parent changed')
 need(sha(ui)=='80da6cbfa706a3fce1f79133390ed12b719940046e7670eebda81977d1e2325b','Selection changed')
 need(file_hash(SOURCE)==SOURCE_SHA,'Baseline changed');assets,_=read_disc(SOURCE,('PL00_U.ARC','COL0E_U1.ARC','SLUS_005.61'))
 a=Archive(data);baseline=Archive(assets['PL00_U.ARC']);out=H/'victory_inputs01';need(not out.exists(),'Output exists');out.mkdir()
 refs=list(range(204,208));rows=[]
 for n in refs:
  f=a.banks[0]['frames'][n];v=a.layer(n)[0];y,x=np.nonzero(v)
  need(np.array_equal(v,baseline.layer(n)[0]),'Victory parent changed unexpectedly')
  rows.append(dict(ref=n,bbox=[int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)],native_sha256=sha(v.tobytes()),shared=[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']]))
  for label,mask in [('base',0),('fourth',15)]:a.composite(n,mask)[0].save(out/f'{label}_{n:03}.png')
 for label,mask in [('base',0),('fourth',15)]:
  page([(f'{n} current',a.composite(n,mask)[0])for n in refs],a.composite(0,mask)[0],out/f'{label}_current.png',cols=2,scale=5)
 for number,ns in enumerate((refs[:2],refs[2:]),1):
  board=Image.new('RGBA',(1024,1024))
  for row,mask in enumerate((0,15)):
   for col,n in enumerate(ns):
    im=a.composite(n,mask)[0];bb=im.getbbox();need(bb[0]>=128 and bb[1]>=128 and bb[2]<=192 and bb[3]<=192,'Crop clips pose')
    board.alpha_composite(im.crop((128,128,192,192)).resize((512,512),Image.Resampling.NEAREST),(col*512,row*512))
  board.save(out/f'page{number:02}_poses.png')
 style=Image.new('RGBA',(1536,1024))
 for row,mask in enumerate((0,15)):
  for col,n in enumerate((0,156,55)):
   style.alpha_composite(a.composite(n,mask)[0].crop((128,128,192,192)).resize((512,512),Image.Resampling.NEAREST),(col*512,row*512))
 style.save(out/'accepted_style.png')
 # Decode the fixed selection object into the same world coordinate canvas.
 comp=aliased_composition(entry(ui,10),2,18);texture=entry(ui,0x10102)[90112:]
 px,size,bb,_=compose_static(texture,local_composition(comp));small=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);selection=np.zeros((384,384),np.uint8)
 yy,xx=np.nonzero(small);selection[yy+bb[1]+160,xx+bb[0]+160]=small[yy,xx]
 game=a.layer(207)[0];matches=[]
 for flip in (False,True):
  yy,xx=np.nonzero(game);wx=-(xx-160)-1 if flip else xx-160;wy=yy-160
  for dy in range(-3,4):
   for dx in range(-3,4):
    v=np.zeros_like(game);v[wy+160+dy,wx+160+dx]=game[yy,xx]
    if np.array_equal(v,selection):matches.append(dict(flip=flip,dx=dx,dy=dy))
 need(len(matches)==1,'Selection18 correspondence not unique')
 palette=entry(assets['COL0E_U1.ARC'],5);need(palette[512:544]==a.p[:32],'Selection/game palette differs')
 inventory=json.loads((ROOT/'work/sprite_consistency_20261105/coverage/ver_buki_riko/x_animations.json').read_text('utf8'))
 animation=next(x for x in inventory['animations']if x['id']==39)
 write(out/'manifest.json',dict(parent_arc=str((parent/'PL00_U.ARC').relative_to(ROOT)),parent_arc_sha256=sha(data),selection_sha256=sha(ui),refs=rows,page01=refs[:2],page02=refs[2:],native_crop=[128,128,192,192],scale=8,forms=['base','fourth'],style_reference_refs=[0,156,55],selection18_game207=matches[0],selection_native_bounds=bb,selection_palette_same=True,selection_others_not_written=True,animation=animation,source_bin_sha256=SOURCE_SHA,not_runtime=True))
 page([('actual selection18',a.rgba(selection)),('game207',a.composite(207,0)[0])],a.composite(0,0)[0],out/'selection18_binding.png',cols=2,scale=5)
 print(json.dumps(dict(refs=rows,selection18_game207=matches)))
if __name__=='__main__':main()
