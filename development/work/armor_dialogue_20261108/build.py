"""Guard and build isolated fixed-size dialogue-portrait disc revisions."""
from pathlib import Path
import argparse,sys,json,struct,hashlib,shutil
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc
from scripts.prepare_riko_ui import entry
from src.psx_ui_atlas import write_tile
from src.psx_disc import file_hash,write_archive_copies
from src.psx_sector import validate_checks
from scripts.c01_audio_build import read_disc
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text('utf8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
PARENTS={'ver_buki_riko':'16024438046a8459168a55df93a6eec020d46aa917b192c106774cdda06d4d4f','ver_rin_nana':'52a62c6b00551bd4005eb4febd0f795f9d01652f2345e6df28e98a46f800ffdc'}
BLOCK='3d93ded25a4957f7f5af7ce4b0ed1cc0ae68df70a246b94a8ec1c3146c7a27c0'
NEWBLOCK='3c37d59d7d914ebb25b5b3b7ed5975b47c0856a2a17bd4f9314196371cdd8255'
def verify(mode):
 h=H/mode;a=load(h/'audit.json');v=load(h/'prepared_v2/verification.json');p=a['pointer'];src=ROOT/Path(p['cue']).with_suffix('.bin')
 assert p['sha256']==PARENTS[mode] and file_hash(src)==p['sha256']
 assert load(ROOT/f'projects/{mode}/current_build.json')==p
 proposal={r['file']:(h/'prepared_v2'/r['file']).read_bytes()for r in v['files']};proposal['SLUS_005.61']=(h/'prepared_v2/SLUS_005.61').read_bytes()
 original,records=read_disc(src,list(proposal));checks=[]
 for n,b in original.items():
  new=proposal[n];assert len(new)==len(b)
  if n=='SLUS_005.61':
   start,end=0x22954-0x10000+2048,0x229a0-0x10000+2048
   assert sha(b[start:end])==BLOCK and sha(new[start:end])==NEWBLOCK
   assert b[:start]==new[:start] and b[end:]==new[end:]
   checks.append({'file':n,'allowed_range':[start,end],'unrelated_bytes_exact':True});continue
  record=next(r for r in v['files']if r['file']==n);assert sha(b)==record['before'] and sha(new)==record['after']
  layout=psx_arc(b);assert [(e['type'],e['offset'],e['size'])for e in layout]==[(e['type'],e['offset'],e['size'])for e in psx_arc(new)]
  mask=bytearray(len(b))
  def region(typ,offset,data):
   e=next(e for e in layout if e['type']==hex(typ));assert offset>=0 and offset+len(data)<=e['size'];pos=e['offset']+offset
   for i,x in enumerate(data):mask[pos+i]|=x
  for q in v['graphics']:
   if q['file']!=n:continue
   typ=next(g['type']for g in a['inventory']['graphics']if g['file']==n)
   delta=q['delta_tiles'];scope=bytearray((delta+96)*128)
   for tile in list(range(delta,delta+96))+q['borrowed_border_tiles']:write_tile(scope,tile,bytes([15]*256))
   region(typ,q['new_texture_base'],scope)
   table=entry(b,12)
   for i in range(0,len(table),4):
    if struct.unpack_from('<I',table,i)[0]==q['old_texture_base']:
     assert struct.unpack_from('<I',entry(new,12),i)[0]==q['new_texture_base'];region(12,i,b'\xff'*4)
  for q in a['inventory']['compositions']:
   if q['file']==n:region(10,q['offset'],b'\xff'*q['size'])
  for q in load(h/'border_inventory.json'):
   if q['file']!=n:continue
   before=entry(b,10)[q['offset']:q['offset']+q['size']];after=entry(new,10)[q['offset']:q['offset']+q['size']]
   for i,(x,y)in enumerate(zip(before,after)):
    if x!=y:
     assert {13:12,25:21,27:26}.get(x)==y
     region(10,q['offset']+i,b'\xff')
  diff=np.frombuffer(b,np.uint8)!=np.frombuffer(new,np.uint8)
  assert not np.any(diff & (np.frombuffer(mask,np.uint8)==0)),n
  checks.append({'file':n,'changed_bytes':int(diff.sum()),'unrelated_bytes_exact':True,'layout_preserved':True})
 assert len(proposal)==14
 cpu=load(H/'cpu_verification.json');assert cpu['cases']==96 and cpu['replacement_sha256']==NEWBLOCK
 return src,p,original,proposal,records,checks

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--build',action='store_true');args=ap.parse_args()
 plans={m:verify(m)for m in PARENTS}
 write(H/'static_verification.json',{'passed':True,'modes':{m:q[-1]for m,q in plans.items()}})
 if not args.build:print('Both current-parent proposals verified. No disc writes.');raise SystemExit
 previous=load(ROOT/'work/shibuki_ultimate_swimsuit_20261108/protection_before.json')['files']
 snapshot={n:{'size':(ROOT/n).stat().st_size,'sha256':file_hash(ROOT/n)}for n in previous};write(H/'protection_before.json',{'files':snapshot})
 builds={}
 for mode,(src,p,old,new,records,checks)in plans.items():
  out=ROOT/'out'/mode/'armor_dialogue_20261108_v1';out.mkdir(exist_ok=False);stem='shibuki_riko'if mode=='ver_buki_riko'else'rin_nana';target=out/(stem+'.bin')
  r=write_archive_copies(src,target,[({**records[n],'sha256':sha(old[n])},b)for n,b in new.items()],p['sha256'])
  declared={q['lba']for q in r['changed_sectors']};actual=set();allowed={lba for q in records.values()for lba in range(q['lba'],q['lba']+(q['size']+2047)//2048)}
  with src.open('rb')as f,target.open('rb')as g:
   for lba in range(r['size']//2352):
    a,b=f.read(2352),g.read(2352)
    if a==b:continue
    assert lba in declared and lba in allowed and a[:24]==b[:24];validate_checks(b);actual.add(lba)
   assert not f.read(1) and not g.read(1)
  assert actual==declared and read_disc(target,list(new))[0]==new and file_hash(src)==p['sha256']
  (out/(stem+'.cue')).write_bytes((ROOT/p['cue']).read_bytes());write(out/'sector_changes.json',r)
  manifest={'task':'armor_dialogue_20261108','project':mode,'parent_cue':p['cue'],'parent_sha256':p['sha256'],'modified_bin':{k:v for k,v in r.items()if k!='changed_sectors'},'changed_resources':list(new),'changed_sectors':len(actual),'full_disc_sectors_compared':r['size']//2352,'EDC_ECC_verified':True,'disc_readback_verified':True,'all_unrelated_disc_sectors_identical':True,'arc_lengths_preserved':True,'bounded_portrait_selector_only':True,'static_checks':checks,'runtime_verified':False,'user_accepted':False}
  write(out/'manifest.json',manifest);review=out/'review';review.mkdir()
  shutil.copyfile(H/mode/'native_proposal/review.png',review/'all12.png');shutil.copyfile(H/mode/'current_sheet.png',review/'previous8.png')
  for n in range(12):shutil.copyfile(H/mode/f'native_proposal/{n:02}.png',review/f'{n:02}.png')
  shutil.copyfile(H/mode/'prepared_v2/verification.json',review/'packing_verification.json');shutil.copyfile(H/'cpu_verification.json',review/'cpu_verification.json')
  builds[mode]={'cue':(out/(stem+'.cue')).relative_to(ROOT).as_posix(),'sha256':r['sha256'],'manifest':(out/'manifest.json').relative_to(ROOT).as_posix()};print(json.dumps(builds[mode]),flush=True)
 write(H/'builds.json',builds)
 for n,q in snapshot.items():assert file_hash(ROOT/n)==q['sha256'],n
