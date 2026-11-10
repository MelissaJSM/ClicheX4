"""새 움직임 두 의상의 공통부를 맞춘다. 이전 게임 인체는 덮지 않는다."""
from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from native_pose_pack import SOURCE,SOURCE_SHA
from src.psx_disc import file_hash
MAP={2:[3,5,7,9],3:[15],4:[19,21,23,25],5:[27,29,31]}
# Face and hem landmarks inspected on the newly generated 1x rasters.
LANDMARKS={3:(151,154,168),5:(147,153,166),7:(146,155,168),9:(146,155,168),15:(145,154,167),19:(148,154,167),21:(149,157,170),23:(148,155,168),25:(147,156,169),27:(148,156,169),29:(150,154,167),31:(147,155,168)}
OFFSETS={3:(0,0),5:(0,0),7:(0,1),9:(0,1),15:(0,1),19:(0,0),21:(0,1),23:(0,0),25:(0,1),27:(0,1),29:(4,1),31:(0,0)}
def main():
 assert file_hash(SOURCE)==SOURCE_SHA
 arc=Archive(read_disc(SOURCE,('PL02_U.ARC',))[0]['PL02_U.ARC']);rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in arc.words[:32]],np.int32)
 lut=np.array([0]+[int(((rgb[1:16]-c)**2).sum(1).argmin())+1 for c in rgb[17:32]],np.uint8)
 out=H/'run_registered02';out.mkdir(exist_ok=False)
 for kind in('before','after'):(out/kind).mkdir()
 meta=[];items=[]
 for pg,refs in MAP.items():
  for n in refs:
   source=ROOT/f'work/sprite_style_unification_20261107/shibuki/ultimate_run_detail{pg:02}/native/{n:03}_indices.png';b=np.array(Image.open(source));a=np.array(Image.open(H/'run_after_raw01'/f'{n:03}_indices.png'))
   cx,neck,hip=LANDMARKS[n];dx,dy=OFFSETS[n];a=np.roll(np.roll(a,dx,1),dy,0)
   polygon=[(cx-2,neck),(cx+4,neck),(cx+6,neck+4),(cx+16,neck+5),(cx+18,hip),(cx+9,hip+1),(cx-5,hip+1),(cx-8,neck+6),(cx-8,neck+1)]
   m=Image.new('1',(384,384));ImageDraw.Draw(m).polygon(polygon,fill=1);edit=np.array(m,dtype=bool)
   result=lut[b];result[edit]=a[edit];outside=(result>0)&(b==0);result[outside]=0
   assert np.array_equal(result[~edit],lut[b][~edit])and not np.any((result>0)&(b==0))
   for kind,v,start in(('before',b,16),('after',result,0)):
    Image.fromarray(v).save(out/kind/f'{n:03}_indices.png');arc.rgba(v,start).save(out/kind/f'{n:03}.png')
   yy,xx=np.nonzero(outside);meta.append({'ref':n,'source_before':source.relative_to(ROOT).as_posix(),'source_before_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'editable_polygon':polygon,'landmark_face_x_neck_y_hem_y':[cx,neck,hip],'after_art_integer_translation':[dx,dy],'new_after_costume_pixels':int(np.count_nonzero(a[edit])),'new_before_shared_pixels':int(np.count_nonzero(b[~edit])),'excluded_after_boundary_xy':list(map(list,zip(xx.tolist(),yy.tolist()))),'old_art_pixels_copied':0})
 for n in(11,13,17):
  b=np.array(Image.open(ROOT/f'work/sprite_style_unification_20261107/shibuki/pilot01/native_preview/{n:03}_indices.png'));a=np.array(Image.open(H/f'after_registered02/{n:03}_indices.png'))
  for kind,v,start in(('before',b,16),('after',a,0)):Image.fromarray(v).save(out/kind/f'{n:03}_indices.png');arc.rgba(v,start).save(out/kind/f'{n:03}.png')
  meta.append({'ref':n,'source':'frozen pilot01 / after_registered02','old_art_pixels_copied':0})
 for n in range(3,32,2):items.extend([(f'{n} new jacket',Image.open(out/'before'/f'{n:03}.png')),(f'{n} new swimsuit',Image.open(out/'after'/f'{n:03}.png'))])
 for start in range(0,len(items),8):page(items[start:start+8],arc.composite(0,15)[0],out/f'comparison_{start//8:02}.png',cols=2,scale=4)
 (out/'registration.json').write_text(json.dumps({'source_sha256':SOURCE_SHA,'palette_lut':lut.tolist(),'frames':meta,'runtime_verified':False,'shooting_variants_ready':False},ensure_ascii=False,indent=2)+'\n','utf8')
if __name__=='__main__':main()
