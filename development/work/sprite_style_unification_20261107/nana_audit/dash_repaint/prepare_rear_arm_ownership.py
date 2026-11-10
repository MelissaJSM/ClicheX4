"""Source-space rear sleeve masks; do not infer an arm across the hat."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(D),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,need,write,helper
POLYS={93:[(210,215),(225,170),(280,138),(301,96),(315,79),(343,84),(366,106),(352,125),(329,134),(329,180),(300,203),(265,208),(238,224)],94:[(190,216),(217,212),(264,219),(293,229),(343,237),(376,249),(418,252),(439,269),(427,293),(398,303),(358,292),(322,281),(280,266),(236,250),(206,244)]}
def main():
 p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());o=D/'rear_arm_ownership_v1';need(not o.exists(),'Fresh');o.mkdir();rows=[];proof=[];regs=json.loads((D/'fourth_c_registered_v1/registration.json').read_text('utf8'))['frames']
 for n,poly in POLYS.items():
  src=Image.open(D/'fourth_c_registered_v1'/f'source_{n:03}.png').convert('RGBA');r=next(q for q in regs if q['ref']==n);m=Image.new('L',src.size);ImageDraw.Draw(m).polygon(poly,fill=255);m.save(o/f'source_semantic_{n:03}.png');split=r['split'];upper=m.crop((0,0,m.width,split)).resize((r['native_width'],r['height_above']),Image.Resampling.BOX);lower=m.crop((0,split,m.width,m.height)).resize((r['native_width'],r['height_below']),Image.Resampling.BOX);mask=np.zeros((384,384),bool);ox,oy=r['native_position'];ox+=160;oy+=160;mask[oy:oy+r['height_above'],ox:ox+r['native_width']]=np.array(upper)>=100;mask[oy+r['height_above']:oy+r['height_above']+r['height_below'],ox:ox+r['native_width']]=np.array(lower)>=100;idx=np.array(Image.open(D/'fourth_contacts_probe_v2'/f'fourth_{n:03}.png'));mask&=idx>0;Image.fromarray(mask.astype(np.uint8)*255).save(o/f'arm_{n:03}.png');rows.append((str(n),[('포스 전체',a.rgba(idx,16)),('원화 뒤팔만',a.rgba(np.where(mask,idx,0).astype(np.uint8),16))]));proof.append({'ref':n,'source_polygon':poly,'registered_mask_sha256':sha(mask.tobytes()),'pixels':int(mask.sum()),'registration':r})
 helper.grid(rows,o/'comparison.png',9);write(o/'manifest.json',{'frames':proof,'source_arc_sha256':sha(a.data),'not_art_change':True})
if __name__=='__main__':main()
