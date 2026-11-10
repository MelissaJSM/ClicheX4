"""Use only true body-edge pixels shared by every valid equipment state for each granted part."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
from scipy.ndimage import binary_erosion,binary_fill_holes
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_shibuki_capsule_nova import raster,packed_bank
from scripts.export_x_consistency import Archive
from src.psx_player import bank_offsets
from scripts.discover_inputs import psx_arc
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 old=(D/'before/PL00_U.ARC').read_bytes();g,c=entry(old,2),entry(old,3);ng,nc=g,c;proofs=[];targets={};changed=[]
 arc=Archive(old);cases=[]
 for gb in range(10,14):
  images=[raster(g,c,gb,gb+8,n)for n in range(11)];bit=1<<(gb-10)
  silhouettes={mask:(np.array(arc.composite(0,mask)[0])[:,:,3]>0)[80:240,80:240]for mask in range(16)if mask&bit}
  # A capsule bank cannot see the previously equipped mask. Never draw a
  # conflicting silhouette: retain only actual edge pixels shared by all eight
  # possible resulting outfits. The existing acquired-part scan remains exact.
  inner=np.logical_and.reduce([a&~binary_erosion(binary_fill_holes(a))for a in silhouettes.values()])
  second=np.logical_and.reduce([a&binary_erosion(binary_fill_holes(a))&~binary_erosion(binary_fill_holes(a),iterations=2)for a in silhouettes.values()])
  first=np.zeros((160,160),np.uint8);first[inner]=3
  next_=np.zeros_like(first);next_[second]=3;next_[inner]=1
  images[0]=first;images[1]=next_;targets[gb]=images
  for owned in range(16):
   if not owned&bit:continue
   a=np.array(arc.composite(0,owned)[0])[:,:,3]>0;a=a[80:240,80:240]
   assert not np.any((inner|second)&~a),(gb,owned,'edge outside equipped body')
   filled=binary_fill_holes(silhouettes[owned]);assert not np.any(inner&~(filled&~binary_erosion(filled)))
   cases.append({'bank':gb,'equipped_mask':owned,'all_flash_pixels_on_equipped_body':True,'white_pixels_on_actual_body_boundary':True,'white_pixels':int(inner.sum())})
  ng,nc,p=packed_bank(ng,nc,gb,gb+8,images);proofs.append(p);print('Force packed',gb,p['graphics_slack'],flush=True)
 for before,after,allowed in [(g,ng,range(10,14)),(c,nc,range(18,22))]:
  offsets=bank_offsets(before,allow_aliases=True);assert offsets==bank_offsets(after,allow_aliases=True)
  for bank,start in enumerate(offsets):
   end=min((v for v in offsets if v>start),default=len(before))
   if bank not in allowed:assert before[start:end]==after[start:end]
  assert len(before)==len(after)
 for gb in range(10,14):
  for n in range(11):
   actual=raster(ng,nc,gb,gb+8,n);assert np.array_equal(actual,targets[gb][n])
   if not np.array_equal(actual,raster(g,c,gb,gb+8,n)):changed.append([gb,n])
 assert changed==[[gb,n]for gb in range(10,14)for n in [0,1]]
 new=replace_entry(replace_entry(old,2,ng),3,nc)
 for e in psx_arc(old):
  k=int(e['type'],16)
  if k not in [2,3]:assert entry(old,k)==entry(new,k)
 output=D/'prepared';(output/'PL00_U.ARC').write_bytes(new)
 report={'input_sha256':sha(old),'output_sha256':sha(new),'changed_visual_frames':changed,'banks':proofs,
         'policy':'Final flash uses only true body-edge pixels shared by all eight possible resulting outfits per granted part. Existing 36 part scan/spark/blank refs unchanged. Regions whose outline depends on other parts are omitted, not drawn at a wrong position.',
         'compatible_equipment_combinations':cases,'only_capsule_banks_changed':True,'palettes_gameplay_animations_unchanged':True,
         'actual_gameplay_verified':False,'user_accepted':False}
 (output/'force_recipe.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
 pal=np.array([(0,0,0,0),(255,255,255,255),(100,220,255,255),(150,175,255,255)]+[(255,110,90,255)]*12,np.uint8)
 board=Image.new('RGB',(1200,620),'#1c293a');draw=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
 for col,gb in enumerate(range(10,14)):
  body=arc.composite(0,15)[0].crop((80,80,240,240))
  for row,(label,a)in enumerate([('수정 전 · 다른 파츠 무시',raster(g,c,gb,gb+8,1)),('수정 후 · 실제 외곽 공통선',targets[gb][1])]):
   im=Image.alpha_composite(body,Image.fromarray(pal[a])).crop((44,44,116,116)).resize((276,276),Image.Resampling.NEAREST)
   board.paste(im,(col*300,row*310+30),im);draw.text((col*300+4,row*310+3),['머리','몸','팔','다리'][col]+' · '+label,font=font,fill='white')
 board.save(output/'force_comparison.png');print('Force prepared',sha(new),flush=True)
if __name__=='__main__':main()
