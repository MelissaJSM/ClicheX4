"""포스 저체력 새 원화의 파츠/불투명 경계와 원래 호흡 공유를 조사한다."""
from pathlib import Path
import json,sys,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from native_pose_pack import SOURCE,SOURCE_SHA
from src.psx_disc import file_hash

def main():
 assert file_hash(SOURCE)==SOURCE_SHA
 arc=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC'])
 d=H/'fourth_lowhp_feasibility01';d.mkdir(exist_ok=True)
 new=np.array(Image.open(H/'remaining_source_restore01/fourth_action_120_indices.png'))
 base=arc.layer(120)[0];old=np.array(arc.composite(120,15)[0]);pic=arc.rgba(new,16)
 missing=(base>0)&(new==0);y,x=np.nonzero(missing)
 marked=np.array(pic);marked[missing]=(255,0,0,255)
 union=arc.composite(120,0)[0];union.alpha_composite(pic)
 items=[('current full120',arc.composite(120,15)[0]),('new whole source',pic),('base outside source RED',Image.fromarray(marked)),('source over base (candidate)',union)]
 for b in(0,5,6,7,8):items.append((f'current120 layer{b}',arc.rgba(arc.layer(120,b)[0],32 if b==7 else 16 if b else 0)))
 page(items,arc.composite(0,15)[0],d/'overlap_and_layers.png',cols=3,scale=5)
 rows=[]
 for n in range(120,126):
  rec={'ref':n,'graphics_offset':arc.banks[0]['frames'][n]['offset'],'layers':{}}
  for b in(0,5,6,7,8):
   a,m=arc.layer(n,b);best=None
   for dy in range(-3,4):
    for dx in range(-2,3):
     s=np.roll(np.roll(arc.layer(120,b)[0],dx,axis=1),dy,axis=0);count=int(np.count_nonzero(a!=s));key=(count,abs(dx)+abs(dy),dx,dy)
     if best is None or key<best:best=key
   rec['layers'][str(b)]={'opaque':int((a>0).sum()),'relative_to120':{'different_pixels':best[0],'dx':best[2],'dy':best[3]},'parts':m['parts']}
  rows.append(rec)
 report={'source_sha256':SOURCE_SHA,'new_source_palette':16,'uncovered_base_pixels':[{'x':int(xx)-160,'y':int(yy)-160,'palette_index':int(base[yy,xx])}for yy,xx in zip(y,x)],'uncovered_count':int(missing.sum()),'native_pose_rows':rows,'palette0_16_differences':[{'index':i,'base':int(arc.words[i]),'fourth':int(arc.words[i+16])}for i in range(16)if arc.words[i]!=arc.words[i+16]],'arc_written':False,'not_final_art':True}
 (d/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'uncovered':report['uncovered_base_pixels'],'shifts':[{k:v for k,v in r.items()if k!='layers'}|{'layers':{k:v['relative_to120']for k,v in r['layers'].items()}}for r in rows]}))
if __name__=='__main__':main()
