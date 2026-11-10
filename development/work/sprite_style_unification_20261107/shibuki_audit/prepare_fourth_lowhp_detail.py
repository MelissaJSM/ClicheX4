"""포스 저체력 원화에서 칼라/가슴/소매의 실제 픽셀 블록만 복원하는 후보.

현재 공통 머리/손/하체를 보존한다. 전체 미술 통일 완료나 게임 적용본이 아니다.
색을 가까운 위치에서 전파하거나 새 선을 그리지 않는다.
"""
from pathlib import Path
import json,sys,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from native_pose_pack import SOURCE,SOURCE_SHA
from src.psx_disc import file_hash

def shifts(v,dy):
 out=np.zeros_like(v);y,x=np.nonzero(v);out[y+dy,x]=v[y,x];return out

def prepare(arc):
 src=np.array(Image.open(H/'remaining_source_restore01/fourth_action_120_indices.png'))
 yy,xx=np.indices(src.shape)
 # Selected old-source region: actual collar, laced torso, hem and sleeve faces.
 # The illustration's head, hanging hands and different lower-body pose are not used.
 polygon=Image.new('1',(384,384));ImageDraw.Draw(polygon).polygon([(151,154),(163,154),(167,158),(171,165),(169,168),(165,168),(164,166),(151,166),(148,164),(148,158)],fill=1)
 seed=np.array(polygon,dtype=bool)&(src>0)
 data={};records=[]
 for n in range(120,126):
  dy=-((n-120)//2);shifted=shifts(src,dy);region=shifts(seed.astype(np.uint8),dy)>0
  base=arc.layer(n,0)[0];layers={b:arc.layer(n,b)[0].copy()for b in(5,6,7,8)}
  # Existing common face and the raised hand are intentionally outside this clothing repair.
  protected_skin=np.isin(base,[12,13]);protected_head=yy<154+dy
  protected_hair=np.isin(base,[5,8,14])&((xx>=164)|(yy<155+dy))
  region&=~(protected_skin|protected_head|protected_hair)
  region&=yy<169+dy
  owner=np.where((xx<=153)|(xx>=166),7,6)
  # Existing nontransparent clothing ownership wins at original overlaps.
  for b in(8,5,7,6):owner=np.where(arc.layer(n,b)[0]>0,b,owner)
  # No head/leg part recoloring in this upper garment-only experiment.
  region&=~np.isin(owner,[5,8])
  for b in(6,7):
   own=region&(owner==b);layers[b][own]=shifted[own]
  data[n]=layers
  records.append({'ref':n,'source_ref':120,'source_translation':[0,dy],'source_pixels_used':int(region.sum()),'changed_layer_pixels':{str(b):int(np.count_nonzero(layers[b]!=arc.layer(n,b)[0]))for b in layers},'edited_coordinates_world':[[int(x)-160,int(y)-160]for y,x in zip(*np.nonzero(region))],'head_hands_and_lower_pose_preserved':True})
 return data,records

def main():
 assert file_hash(SOURCE)==SOURCE_SHA
 raw=read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC'];arc=Archive(raw)
 d=H/'fourth_lowhp_detail01';d.mkdir(exist_ok=False)
 data,records=prepare(arc);items=[]
 for n,layers in data.items():
  im=arc.composite(n,0)[0]
  for b in(8,5,7,6):im.alpha_composite(arc.rgba(layers[b],16))
  im.save(d/f'{n:03}.png')
  for b,v in layers.items():Image.fromarray(v).save(d/f'{n:03}_layer{b}_indices.png')
  items.extend([(f'{n} current',arc.composite(n,15,arm=1)[0]),(f'{n} source clothing',im)])
 page(items,arc.composite(0,15,arm=1)[0],d/'comparison.png',cols=2,scale=4)
 (d/'manifest.json').write_text(json.dumps({'source_bin_sha256':SOURCE_SHA,'source_arc_sha256':hashlib.sha256(raw).hexdigest(),'scope':'원화 칼라/가슴/소매의 동일 좌표 픽셀 복원 후보. 머리 전체 통일 및 게임 실기 미완료.','records':records,'no_color_propagation':True,'arc_written':False},ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps([{'ref':r['ref'],'pixels':r['changed_layer_pixels']}for r in records]))
if __name__=='__main__':main()
