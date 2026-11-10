"""명암복원→142→183 순차 통합 ARC를 담당 구현과 별개로 읽어 검사한다."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts import restore_shibuki_special_detail as r
from src.psx_player import indexed_atlas,composition_frame,bank_offsets,graphics_bank

D=ROOT/'work/sprite_consistency_20261105/x/shibuki_ladder_fix'
q=json.loads((D/'combined_v1/proposal.json').read_text('utf8'));f=q['files']['PL00_U.ARC']
baseline=(ROOT/'work/sprite_consistency_20261105/x/shibuki/PL00_U.ARC').read_bytes()
tone=(r.D/'prepared_v1/PL00_U.ARC').read_bytes();new=(ROOT/f['path']).read_bytes()
assert r.sha(baseline)==f['before']==r.BASE and r.sha(new)==f['after']
assert r.sha(tone)=='f1c3ae2c4f11fec6275abd4e33205abf0ca350f37febcd53a35d6e4136e7c118'
g,c,p=(r.unique_entry(tone,t) for t in(2,3,9));ng,nc,npal=(r.unique_entry(new,t)for t in(2,3,9))
assert r.entry_replace(r.entry_replace(new,2,g),3,c)==tone and p==npal
assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True) and bank_offsets(c)==bank_offsets(nc)
rawchecks=0
for bank in range(len(bank_offsets(g,allow_aliases=True))):
 for oldf in graphics_bank(g,bank,allow_bank_aliases=True)['frames']:
  n=oldf['index'];old,of=r.native_raw(g,bank,n);actual,af=r.native_raw(ng,bank,n)
  if bank==0 and n==142:
   goal,gf=r.native_raw(g,0,0);assert actual==goal and af['tile_count']==gf['tile_count']
  elif bank==0 and n==183:
   assert af['tile_count']==of['tile_count']<=32
   aa=np.frombuffer(indexed_atlas(old,of['tile_count'])[0],np.uint8).reshape(-1,256)
   bb=np.frombuffer(indexed_atlas(actual,af['tile_count'])[0],np.uint8).reshape(-1,256)
   for cb in(0,5):
    for part in composition_frame(c,cb,n)['parts']:
     y,x=part['tile']//16*16,part['tile']%16*16;assert np.array_equal(aa[y:y+16,x:x+16],bb[y:y+16,x:x+16])
  else:assert old==actual and of['tile_count']==af['tile_count']
  rawchecks+=1
def records(comp):return [{k:v for k,v in pp.items()if k not in('index','record_offset')}for pp in comp['parts']]
for cb,off in enumerate(bank_offsets(c)):
 count=struct.unpack_from('<I',c,off)[0]>>16
 for n in range(count):
  a=composition_frame(c,cb,0 if cb in r.PARTS and n==142 else n)
  b=composition_frame(nc,cb,n)
  if n==183 and cb in(6,7,8):continue
  assert records(a)==records(b)

# Independently recover the approved garment mask from the fixed master.
reg=json.loads((D/'registration.json').read_text('utf8'))
master=ROOT/reg['master'];assert r.file_sha(master)==reg['master_sha256']
raw,f183=r.native_raw(g,0,183);base=r.layer(raw,f183['tile_count'],c,0,183)
art=np.array(Image.open(master));yy,xx=np.indices(base.shape)
hair=np.isin(base,[5,8,14]);pad=np.pad(hair,1)
dilate=hair|pad[:-2,1:-1]|pad[2:,1:-1]|pad[1:-1,:-2]|pad[1:-1,2:]
hair|=dilate&np.isin(base,[2,15]);skin=np.isin(base,[12,13]);head=(yy<84)&(xx>=70)&(xx<=91)
garment=(base>0)&~hair&~skin&~head
assert int(garment.sum())==reg['garment_pixels']
coords=np.argwhere((art>0)&~np.isin(art,[4,5,6,9]));mapped=np.zeros_like(base)
for y,x in np.argwhere(garment):
 distances=(coords[:,0]-y)**2*2+(coords[:,1]-x)**2;sy,sx=coords[np.argmin(distances)];mapped[y,x]=art[sy,sx]
legs=garment&(yy>=98);arms=garment&~legs&((xx<76)|(xx>88));body=garment&~legs&~arms
targets={cb:np.where(mask,mapped,0)for cb,mask in((6,body),(7,arms),(8,legs))}
for cb in targets:
 saved=np.load(D/f'layer{cb}.npy');assert np.array_equal(targets[cb],saved[80:240,80:240])
layerchecks=0
for n in range(237):
 if n in r.X_PLACEHOLDERS:continue
 old,of=r.native_raw(g,0,n);actual,af=r.native_raw(ng,0,n)
 for cb in r.PARTS:
  if n==142:
   z,zf=r.native_raw(g,0,0);goal=r.layer(z,zf['tile_count'],c,cb,0)
  elif n==183 and cb in targets:goal=targets[cb]
  else:goal=r.layer(old,of['tile_count'],c,cb,n)
  assert np.array_equal(r.layer(actual,af['tile_count'],nc,cb,n),goal)
  layerchecks+=1
pal=struct.unpack_from('<64H',p);maskchecks=0
for n in(142,183):
 old,of=r.native_raw(g,0,0 if n==142 else n);actual,af=r.native_raw(ng,0,n)
 goal={cb:r.layer(old,of['tile_count'],c,cb,0 if n==142 else n)for cb in r.PARTS}
 if n==183:goal.update(targets)
 observed={cb:r.layer(actual,af['tile_count'],nc,cb,n)for cb in r.PARTS}
 for arm in(1,2):
  for mask in range(16):
   assert np.array_equal(r.composite(goal,pal,mask,arm),r.composite(observed,pal,mask,arm));maskchecks+=1
newraw,nf=r.native_raw(ng,0,183);atlas=np.frombuffer(indexed_atlas(newraw,nf['tile_count'])[0],np.uint8).reshape(-1,256)
gpuchecks=[]
for cb in(6,7,8):
 for part in composition_frame(nc,cb,183)['parts']:
  t=part['tile'];tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
  assert t%16!=0 or not np.any(tile[:,0]);assert not part['flip_y']or t//16%16!=0 or not np.any(tile[0])
  gpuchecks.append({'bank':cb,'tile':t,'flip_y':part['flip_y']})
report={'passed':True,'resource_sha256':r.sha(new),'all_raw_checks':rawchecks,'all_main_layers':layerchecks,'mask142_and183_checks':maskchecks,
 'six_recovered_frames_byte_exact':True,'all_other_layers_exact':True,'ref142_equals_idle0_all_layers':True,
 'ref183_master_hash':reg['master_sha256'],'ref183_garment_pixels':int(garment.sum()),'ref183_base_head_hands_hair_exact':True,
 'new183_gpu_boundary_parts':gpuchecks,'palette_audio_other_entries_exact':True,'game_runtime_verified':False}
r.write(Path(__file__).with_name('shibuki_combined_independent.json'),report)
print(json.dumps({'passed':True,'raw':rawchecks,'layers':layerchecks,'mask':maskchecks}))
