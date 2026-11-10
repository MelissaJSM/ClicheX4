"""새 재킷/수영복 그림끼리만 공통부를 맞춘다. 과거 스프라이트는 사용 안 함."""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from scripts.prepare_rin_run import quantize
from native_pose_pack import SOURCE,SOURCE_SHA
from src.psx_disc import file_hash
PILOT=ROOT/'work/sprite_style_unification_20261107/shibuki/pilot01'
POLYGONS={
 11:[[(147,155),(154,155),(155,158),(162,159),(164,166),(159,167),(157,169),(151,169),(145,167),(145,160),(147,160)]],
 13:[[(147,155),(154,155),(155,158),(161,159),(164,165),(158,168),(147,169),(145,165),(144,158)]],
 17:[[(149,157),(155,157),(157,160),(164,162),(166,168),(160,170),(152,168),(147,166),(146,160)]],
 33:[[(146,157),(158,157),(160,159),(166,159),(168,167),(160,170),(147,169),(143,166),(143,160)]],
 71:[[(145,170),(153,169),(154,168),(173,168),(174,173),(161,176),(155,178),(145,178)],[(134,171),(142,171),(146,174),(144,178),(139,180),(134,178)]]}
def main():
 assert file_hash(SOURCE)==SOURCE_SHA
 arc=Archive(read_disc(SOURCE,('PL02_U.ARC',))[0]['PL02_U.ARC'])
 rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in arc.words[:32]],np.int32)
 mapping=np.array([0]+[int(((rgb[1:16]-c)**2).sum(1).argmin())+1 for c in rgb[17:32]],np.uint8)
 sheet=Image.open(PILOT/'generated_after.png').convert('RGBA');info=json.loads((PILOT/'inputs.json').read_text())
 out=H/'after_registered02';out.mkdir(exist_ok=False);report=[];items=[]
 for t in info['targets']:
  n=t['ref']
  if n not in POLYGONS:continue
  x,y=t['cell'];raw=np.zeros((384,384),np.uint8);raw[128:192,128:192]=quantize(sheet.crop((512*x,512*y,512*x+512,512*y+512)),rgb[1:16],.125)
  before=np.array(Image.open(PILOT/'native_preview'/f'{n:03}_indices.png'))
  mi=Image.new('1',(384,384));d=ImageDraw.Draw(mi)
  for points in POLYGONS[n]:d.polygon(points,fill=1)
  edit=np.array(mi,dtype=bool);v=mapping[before]
  v[edit]=raw[edit]
  conflict=(v>0)&(before==0)
  # Only the newly generated costume boundary is clipped to its paired coat.
  # Common head/hand/leg pixels are taken from the new pilot, never old art.
  v[conflict]=0
  assert not np.any((v>0)&(before==0))
  assert np.array_equal(v[~edit],mapping[before][~edit])
  Image.fromarray(v).save(out/f'{n:03}_indices.png');arc.rgba(v).save(out/f'{n:03}.png')
  Image.fromarray(np.where(edit,255,0).astype(np.uint8)).save(out/f'{n:03}_editable.png')
  items.extend([(f'{n} BEFORE new',arc.rgba(before,16)),(f'{n} AFTER aligned',arc.rgba(v))])
  yy,xx=np.nonzero(conflict)
  report.append({'ref':n,'scale':.125,'origin':[160,160],'editable_polygons':POLYGONS[n],
    'new_after_costume_pixels':int(np.count_nonzero(edit&(raw>0))),
    'new_before_common_pixels':int(np.count_nonzero((~edit)&(before>0))),
    'after_edge_outside_coat_removed_xy':list(map(list,zip(xx.tolist(),yy.tolist()))),
    'old_art_overwrite':False,'common_alpha_and_shape_exact':True,'alpha_after_subset_before':True})
 page(items,arc.composite(0,0)[0],out/'comparison.png',cols=2,scale=4)
 (out/'registration.json').write_text(json.dumps({'source_bin_sha256':SOURCE_SHA,'source_art_sha256':hashlib.sha256((PILOT/'generated_after.png').read_bytes()).hexdigest(),'palette_mapping_before_to_after':mapping.tolist(),'palette_changed':False,'common_palette_approximate_indices':[1,4,11],'frames':report,'excluded_001':'현재 수용 시작 자세 유지 권고. 새 after의 pose/위치가 before와 다름.'},ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps(report))
if __name__=='__main__':main()
