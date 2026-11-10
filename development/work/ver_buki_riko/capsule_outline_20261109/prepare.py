"""Register the post-grant contour on the current swimsuit edge, retaining all other effect frames."""
import sys,json,struct,hashlib
from pathlib import Path
import numpy as np
from scipy.ndimage import binary_fill_holes,binary_erosion
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_shibuki_capsule_nova import raster,packed_bank
from scripts.export_x_consistency import Archive
from src.psx_player import bank_offsets,graphics_bank,decode_stream,composition_frame
from scripts.discover_inputs import psx_arc
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 old=(D/'before/PL02_U.ARC').read_bytes();g,c=entry(old,2),entry(old,3);ng,nc=g,c
 body=binary_fill_holes(raster(g,c,0,0,0)>0);edge=body&~binary_erosion(body)
 assert edge.any() and np.all(~edge|body)
 output=D/'prepared';output.mkdir(exist_ok=True);proofs=[];all_images={};changed=[]
 for gb in range(10,14):
  images=[raster(g,c,gb,gb+8,n)for n in range(12)]
  for n,color in [(9,3),(10,1)]:
   v=np.zeros((160,160),np.uint8);v[edge]=color;images[n]=v
  ng,nc,proof=packed_bank(ng,nc,gb,gb+8,images);proofs.append(proof);all_images[gb]=images
  print('packed',gb,proof['graphics_slack'],flush=True)
 for before,after,allowed in [(g,ng,range(10,14)),(c,nc,range(18,22))]:
  bounds=bank_offsets(before,allow_aliases=True);assert bounds==bank_offsets(after,allow_aliases=True)
  for bank,start in enumerate(bounds):
   end=min((v for v in bounds if v>start),default=len(before))
   if bank not in allowed:assert before[start:end]==after[start:end],bank
  assert len(before)==len(after)
 for gb in range(10,14):
  for n in range(12):
   original=raster(g,c,gb,gb+8,n);actual=raster(ng,nc,gb,gb+8,n);assert np.array_equal(actual,all_images[gb][n])
   if not np.array_equal(original,actual):changed.append([gb,n])
   if n not in (9,10):assert np.array_equal(original,actual)
   else:assert np.array_equal(actual>0,edge)
 assert changed==[[gb,n]for gb in range(10,14)for n in (9,10)]
 new=replace_entry(replace_entry(old,2,ng),3,nc);assert len(new)==len(old)
 for e in psx_arc(old):
  kind=int(e['type'],16)
  if kind not in [2,3]:assert entry(old,kind)==entry(new,kind)
 (output/'PL02_U.ARC').write_bytes(new)
 arc=Archive(old);current=arc.composite(0,0)[0].crop((80,80,240,240));pal=np.array([(0,0,0,0),(255,255,255,255),(100,220,255,255),(150,175,255,255)]+[(255,110,90,255)]*12,np.uint8)
 font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
 board=Image.new('RGB',(900,340),'#1c293a');dr=ImageDraw.Draw(board)
 for i,(label,img)in enumerate([('현재 수영복 대기',current),('수정 전 · 바깥쪽 흰 선',Image.alpha_composite(current,Image.fromarray(pal[raster(g,c,10,18,10)]))),('수정 후 · 몸 가장자리 흰 선',Image.alpha_composite(current,Image.fromarray(pal[all_images[10][10]])))]):
  small=img.crop((44,44,116,116)).resize((288,288),Image.Resampling.NEAREST);board.paste(small,(i*300,40),small);dr.text((i*300+4,5),label,font=font,fill='white')
 board.save(output/'comparison.png')
 report={'task':'shibuki_capsule_outline_20261109','input_sha256':sha(old),'output_sha256':sha(new),'changed_visual_frames':changed,
  'outline_policy':'inner one-pixel boundary of filled current acquired swimsuit idle silhouette',
  'body_opaque_pixels':int(body.sum()),'edge_pixels':int(edge.sum()),'banks':proofs,
  'only_capsule_graphics10_13_and_composition18_21_changed':True,'other40_capsule_frames_pixel_identical':True,
  'gameplay_banks_palettes_animations_other_entries_byte_identical':True,'native_timing_and_ownership_unchanged':True,
  'diagnosis':'Current post-grant outer contour already matched the current swimsuit; no old X silhouette or GPU mismatch reproduced. This revision draws the flashing contour on the actual body edge instead of outside it.',
  'actual_gameplay_verified':False,'user_accepted':False}
 (output/'recipe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print('Prepared',sha(new),flush=True)
if __name__=='__main__':main()
