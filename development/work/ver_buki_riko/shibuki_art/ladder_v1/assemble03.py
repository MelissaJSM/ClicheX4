import json,sys,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.extract_zero import save_image
from scripts.prepare_shibuki_ladder import mirror_canvas
d=Path(__file__).parent;a=d/'production03';a.mkdir(exist_ok=True);src=d/'production02';art=json.loads((src/'art.json').read_text());inv=json.loads((ROOT/art['source_inventory']).read_text());original=ROOT/Path(art['source_inventory']).parent
def shifted(arr,dx,dy):
 out=np.zeros_like(arr);yy,xx=np.nonzero(arr);assert (yy+dy).min()>=0 and (yy+dy).max()<80 and (xx+dx).min()>=0 and (xx+dx).max()<96;out[yy+dy,xx+dx]=arr[yy,xx];return out
records=[]
for r in art['frames']:
 n=r['frame']
 if n==150:continue
 arr=np.array(Image.open(src/r['image']));dy={146:-5,149:-6,151:-7,153:-6,154:-6,183:-2}.get(n,0);arr=shifted(arr,0,dy);save_image(arr.tobytes(),(96,80),art['palette_words'],a/r['image']);records.append({**r,'registration_shift':[0,dy]})
body=np.array(Image.open(a/'frame_149.png'));arm=np.array(Image.open(d.parent/'standing_buster_v1/production03/registered_arm_085.png'));arm[40:]=0;yy,xx=np.nonzero(arm==4);anchor=np.array([int(xx.min()),float(np.median(yy[xx==xx.min()]))]);registration=[]
mask=Image.new('1',(96,80));ImageDraw.Draw(mask).polygon([(0,34),(39,34),(41,38),(40,42),(0,42)],fill=1);remove=np.array(mask);remove&=body!=7;common=body.copy();common[remove]=0
for n in (150,155):
 orig=np.array(Image.open(original/f'base_{n:03d}.png'));oy,ox=np.nonzero(np.isin(orig,[1,2]));edge=ox<ox.min()+2;bb=inv['base_frames'][n]['bounds'];muzzle=np.array([int(ox.min()+bb[0]+48),float(np.median(oy[edge])+bb[1]+40)]);dx,dy=[round(v) for v in muzzle-anchor];registered=shifted(arm,dx,dy)
 target=common.copy();target[registered!=0]=registered[registered!=0];target[(body!=0)&~remove]=body[(body!=0)&~remove];save_image(target.tobytes(),(96,80),art['palette_words'],a/f'frame_{n:03d}.png');save_image(registered.tobytes(),(96,80),art['palette_words'],a/f'arm_{n:03d}.png');records.append({'frame':n,'image':f'frame_{n:03d}.png','shared_body':149,'original_muzzle_world':(muzzle-[48,40]).tolist(),'arm_shift':[dx,dy]});registration.append(records[-1])
for n,alias,delta in [(144,145,-16),(146,147,-15),(149,148,-15),(151,152,-15)]:
 arr=mirror_canvas(np.array(Image.open(a/f'frame_{n:03d}.png')),delta);save_image(arr.tobytes(),(96,80),art['palette_words'],a/f'frame_{alias:03d}.png')
art['frames']=sorted(records,key=lambda r:r['frame']);(a/'art.json').write_text(json.dumps(art,indent=2));(a/'registration.json').write_text(json.dumps(registration,indent=2))
sheet=Image.new('RGB',(5*288,3*264),'#28394b');dr=ImageDraw.Draw(sheet)
for i,n in enumerate([0]+list(range(143,156))+[183]):
 path=d.parent/'standing_buster_v1/parent_000.png' if n==0 else a/f'frame_{n:03d}.png';im=Image.open(path).convert('RGBA').resize((288,240),Image.Resampling.NEAREST);x=i%5*288;y=i//5*264;sheet.paste(im,(x,y+24),im);dr.text((x+8,y+5),str(n),fill='white')
sheet.save(a/'body_review.png');print(json.dumps(registration))
