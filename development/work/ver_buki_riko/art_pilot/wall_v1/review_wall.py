from pathlib import Path
import sys,json,shutil
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,bank_offsets,decode_stream,composition_frame,compose_indices
D=Path(__file__).parent
old=ROOT/'out/ver_buki_riko/riko_motion_20261024T000131718284Z'
B=ROOT/'out/ver_buki_riko/riko_motion_20261024T012121410066Z'
a=(old/'modified.arc').read_bytes();b=(B/'modified.arc').read_bytes()
entries=psx_arc(a);g=next(e for e in entries if e['type']=='0x2');p=next(e for e in entries if e['type']=='0x3')
assert len(a)==len(b) and [tuple(e[k] for k in ('index','type','offset','size')) for e in psx_arc(a)]==[tuple(e[k] for k in ('index','type','offset','size')) for e in psx_arc(b)]
assert a[:g['offset']]==b[:g['offset']] and a[g['offset']+g['size']:]==b[g['offset']+g['size']:]
ga=a[g['offset']:g['offset']+g['size']];gb=b[g['offset']:g['offset']+g['size']];parts=a[p['offset']:p['offset']+p['size']]
changed=[];composed=0;unknown=[]
for bi in range(len(bank_offsets(ga))):
 for f in graphics_bank(ga,bi)['frames']:
  before=decode_stream(ga,f['offset'],f['limit'],f['tile_count']*128).data;after=decode_stream(gb,f['offset'],f['limit'],f['tile_count']*128).data
  if before!=after:changed.append([bi,f['index']])
  try:
   c=composition_frame(parts,0 if bi==0 else 5,f['index']);pa=compose_indices(before,f['tile_count'],c);pb=compose_indices(after,f['tile_count'],c)
  except ValueError as e:
   assert before==after;unknown.append([bi,f['index'],str(e)]);continue
  composed+=1
  if [bi,f['index']] not in changed:assert pa==pb
assert changed==[[0,n] for n in range(35,44)]
preserved={}
for n in json.loads((old/'manifest.json').read_text('utf8'))['frame_inputs']:
 n=int(n);name=f'{"idle" if n in (0,1,2,146,147,148) else "frame"}_{n:03d}.png'
 assert (old/name).read_bytes()==(B/name).read_bytes();preserved[name]=sha256((B/name).read_bytes())
report={'previous_build':str(old),'new_build':str(B),'decoded_references_checked':444,'composed_references_checked':composed,
 'changed_references':changed,'uninterpreted_unchanged':unknown,'outside_graphics_entry_unchanged':True,'all_palettes_and_parts_unchanged':True,'preserved_pngs':preserved}
(B/'previous_build_comparison.json').write_text(json.dumps(report,indent=2),encoding='utf8')
inv=json.loads((ROOT/'work/ver_buki_riko/animation_inventory/20261023T095844768051Z/inventory.json').read_text('utf8'))
def picture(n,original=False):
 name=f'{"idle" if n in (0,1,2,146,147,148) else "frame"}_{n:03}.png'
 path=ROOT/f'work/ver_buki_riko/animation_inventory/20261023T095844768051Z/bank0_{n:03}.png' if original else B/name
 im=Image.open(path).convert('RGBA');bounds=inv['frames'][f'bank0_{n:03}']['bounds'];canvas=Image.new('RGBA',(96,80));canvas.alpha_composite(im,(48+bounds[0],40+bounds[1]));return canvas
rows=[('Riko wall grab ID13',[35,38,39,40]),('Riko wall kick ID14',[35,36,37,22,23]),('Riko wall slide ID15',[41,42,43]),('Existing design and transitions',[147,22,23,24,46])]
board=Image.new('RGBA',(1440,4*268),(40,43,55,255));draw=ImageDraw.Draw(board)
for row,(label,nums) in enumerate(rows):
 draw.text((6,row*268+4),label,fill='white')
 for col,n in enumerate(nums):
  draw.text((col*288+6,row*268+19),str(n),fill='white');board.alpha_composite(picture(n).resize((288,240),Image.Resampling.NEAREST),(col*288,row*268+28))
board.save(B/'wall_context_sheet.png')
sequences={13:[(35,2),(38,2),(39,2),(40,96)],14:[(35,3),(36,3),(37,3),(22,4),(23,3)],15:[(41,2),(42,2),(43,2)]}
for aid,seq in sequences.items():
 for scale in (1,4):
  images=[];dur=[];ticks=0
  for n,t in seq:
   c=Image.new('RGB',(192*scale,80*scale),(40,43,55));im=picture(n).resize((96*scale,80*scale),Image.Resampling.NEAREST);c.paste(im,(0,0),im);im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT);c.paste(im,(96*scale,0),im);images.append(c)
   start=round(ticks*100/60);ticks+=t;dur.append(max(10,(round(ticks*100/60)-start)*10))
  images[0].save(B/f'wall_{aid}_preview_{scale}x.gif',save_all=True,append_images=images[1:],duration=dur,loop=0,disposal=2)
(B/'preview_metadata.json').write_text(json.dumps({'kind':'Synthetic aligned artwork preview; not game capture','sequences':sequences,'native_tick_duration':'1/60 second assumed for visualization','event_controlled_duration_not_simulated':True},indent=2),encoding='utf8')
shutil.copyfile(D/'art_checks.json',B/'art_checks.json')
print(json.dumps({'changed':changed,'composed':composed,'preserved_pngs':len(preserved)}))
