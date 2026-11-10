"""Inspect capsule silhouette agreement against the current accepted body assets."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
from scipy.ndimage import binary_fill_holes,binary_dilation
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from src.psx_disc import file_hash
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 ptr=json.loads((ROOT/'projects/ver_buki_riko/current_build.json').read_text('utf8'))
 source=(ROOT/ptr['cue']).with_suffix('.bin');assert file_hash(source)==ptr['sha256']
 old=D/'before';old.mkdir(exist_ok=False)
 data,records=read_disc(source,['PL00_U.ARC','PL02_U.ARC','SLUS_005.61'])
 for n,b in data.items():(old/n).write_bytes(b)
 save(old/'current_build.json',ptr);(old/'project.json').write_bytes((ROOT/'projects/ver_buki_riko/project.json').read_bytes())
 paths=json.loads((ROOT/'work/hq_armor_20261109/fix_v3/protection_before.json').read_text('utf8'))['files']
 save(D/'protection_before.json',{'files':{n:{'size':(ROOT/n).stat().st_size,'sha256':file_hash(ROOT/n)}for n in paths}})
 rows=[];board=Image.new('RGB',(4*300,2*330),(29,39,52));dr=ImageDraw.Draw(board)
 for row,name in enumerate(['PL00_U.ARC','PL02_U.ARC']):
  arc=Archive(data[name]);ultimate=row==1
  for col,gb in enumerate(range(10,14)):
   mask=0 if ultimate else 1<<col;body=arc.composite(0,mask)[0];alpha=np.array(body)[:,:,3]>0;filled=binary_fill_holes(alpha)
   outline=arc.layer(9 if ultimate else 0,gb+8,gb)[0]>0;expected=binary_dilation(filled)&~filled
   q={'file':name,'bank':gb,'body_mask':mask,'body_pixels':int(alpha.sum()),'expected_outline_pixels':int(expected.sum()),'old_outline_pixels':int(outline.sum()),'outline_mismatched_pixels':int((outline^expected).sum())}
   if ultimate:q['filled_body_mismatched_pixels']=int(((arc.layer(5,gb+8,gb)[0]>0)^filled).sum())
   rows.append(q);im=np.array(body);im[outline]=[255,255,255,255];im[expected&~outline]=[0,220,240,255]
   picture=Image.fromarray(im).crop((122,121,198,193)).resize((288,273),Image.Resampling.NEAREST)
   board.paste(picture,(col*300,row*330+40),picture);dr.text((col*300+4,row*330+4),f'{name} bank{gb}\nwhite=old / cyan=current contour',fill='white')
 board.save(D/'before_comparison.png')
 save(D/'audit.json',{'source':ptr,'records':records,'archive_sha256':{n:sha(b)for n,b in data.items()},'cases':rows,'actual_gameplay':False})
 print(json.dumps(rows))
if __name__=='__main__':main()
