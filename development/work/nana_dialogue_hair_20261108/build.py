"""Validate and build the current Nana dialogue seam correction."""
from pathlib import Path
import json,sys,hashlib,struct,shutil
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import psx_arc
from src.psx_ui_atlas import write_tile,aliased_composition
from src.psx_static_effect import compose_static
from src.psx_disc import file_hash,write_archive_copies
from src.psx_sector import validate_checks
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text('utf8'))
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
prepared=H/'packed_rn_v3';v=load(prepared/'verification.json');p=v['pointer'];src=ROOT/Path(p['cue']).with_suffix('.bin')
assert p['sha256']=='01447e9a037074e58e9cdbb1c4f7f5f3367337753a864b606ca7d0fcd9b8600e'
assert file_hash(src)==p['sha256'] and load(ROOT/'projects/ver_rin_nana/current_build.json')==p
original,records=read_disc(src,[r['file']for r in v['files']]);replacement={n:(prepared/n).read_bytes()for n in original}
inv=load(ROOT/'work/armor_dialogue_20261108/ver_rin_nana/audit.json')['inventory'];checks=[]
for n,b in original.items():
 new=replacement[n];record=next(r for r in v['files']if r['file']==n)
 assert sha(b)==record['before'] and sha(new)==record['after'] and len(b)==len(new)
 layout=psx_arc(b);assert [(e['type'],e['size'],e['offset'])for e in layout]==[(e['type'],e['size'],e['offset'])for e in psx_arc(new)]
 mask=bytearray(len(b))
 def allow(typ,offset,data):
  e=next(e for e in layout if e['type']==hex(typ));assert 0<=offset and offset+len(data)<=e['size']
  for i,x in enumerate(data):mask[e['offset']+offset+i]|=x
 for q in v['graphics']:
  if q['file']==n:
   tiles=list(range(q['delta'],q['delta']+96))+q['border_free']+[q['npc_base']+t for t in q['npc_borrowed']]
   scope=bytearray(q['texture_bytes'])
   for t in tiles:write_tile(scope,t,bytes([15]*256))
   allow(q['type'],q['start'],scope)
  for c in q['npc_compositions']:
   if c['file']==n:
    for offset in c['redirect_offsets']:allow(10,offset,b'\xff')
 for q in inv['compositions']:
  if q['file']==n:allow(10,q['offset'],b'\xff'*q['size'])
 diff=np.frombuffer(b,np.uint8)!=np.frombuffer(new,np.uint8)
 assert not np.any(diff&(np.frombuffer(mask,np.uint8)==0)),n
 checks.append({'file':n,'changed_bytes':int(diff.sum()),'layout_preserved':True,'all_bytes_outside_certified_regions_exact':True})
 # Every NPC/background bank apart from the X bank is rendered unchanged.
 for q in v['graphics']:
  if q['file']!='ST00_00.ARC' or n!='ST00_00.ARC':continue
  oldparts,newparts=entry(b,10),entry(new,10)
  oldg=entry(b,q['type'])[q['start']:];newg=entry(new,q['type'])[q['start']:]
  for bank in [9,10]:
   for frame in range(aliased_composition(oldparts,bank,0)['bank_frame_count']):
    assert compose_static(oldg,aliased_composition(oldparts,bank,frame))[:3]==compose_static(newg,aliased_composition(newparts,bank,frame))[:3]
snapshot={n:{'size':(ROOT/n).stat().st_size,'sha256':file_hash(ROOT/n)}for n in load(ROOT/'work/armor_dialogue_20261108/protection_before.json')['files']}
write(H/'protection_before.json',{'files':snapshot})
out=ROOT/'out/ver_rin_nana/armor_dialogue_20261108_v2';out.mkdir(exist_ok=False);target=out/'rin_nana.bin'
r=write_archive_copies(src,target,[({**records[n],'sha256':sha(original[n])},b)for n,b in replacement.items()],p['sha256'])
declared={q['lba']for q in r['changed_sectors']};actual=set();allowed={l for q in records.values()for l in range(q['lba'],q['lba']+(q['size']+2047)//2048)}
with src.open('rb')as f,target.open('rb')as g:
 for lba in range(r['size']//2352):
  old,new=f.read(2352),g.read(2352)
  if old!=new:
   assert lba in allowed and lba in declared and old[:24]==new[:24];validate_checks(new);actual.add(lba)
assert actual==declared and read_disc(target,list(replacement))[0]==replacement and file_hash(src)==p['sha256']
(out/'rin_nana.cue').write_bytes((ROOT/p['cue']).read_bytes());write(out/'sector_changes.json',r)
manifest={'project':'ver_rin_nana','task':'armor_dialogue_seams_20261108','parent_cue':p['cue'],'parent_sha256':p['sha256'],'modified_bin':{k:v for k,v in r.items()if k!='changed_sectors'},'changed_resources':list(replacement),'changed_sectors':len(actual),'full_disc_sectors_compared':r['size']//2352,'EDC_ECC_verified':True,'readback_verified':True,'all_other_disc_sectors_exact':True,'exe_and_palettes_unchanged':True,'static_checks':checks,'portrait_scene_runtime_verified':False,'user_accepted':False}
write(out/'manifest.json',manifest);write(H/'build.json',{'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),'sha256':r['sha256'],'manifest':(out/'manifest.json').relative_to(ROOT).as_posix()})
for n,q in snapshot.items():assert file_hash(ROOT/n)==q['sha256'],n
print(json.dumps({'cue':str(out/'rin_nana.cue'),'sha256':r['sha256'],'changed_sectors':len(actual)}))
