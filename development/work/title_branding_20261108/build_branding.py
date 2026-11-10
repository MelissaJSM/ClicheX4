"""Validate title-only native resource changes, then build separate disc copies."""
from pathlib import Path
import hashlib,json,shutil,struct,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import psx_arc,DiscReader
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static
from src.psx_disc import write_archive_copies,file_hash
from src.psx_sector import validate_checks
sha=lambda b:hashlib.sha256(b).hexdigest()
expected={'ver_buki_riko':'677cb525c64e4684ff1daf22d7d52905c9e9f1a0967e015363e038ecc9f60e6d','ver_rin_nana':'3c05824c27f9d78822aa88d3c1c231768a986ab631d6c1e4ed7c3b725bd2f3c1'}
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
old_protected=json.loads((ROOT/'work/sprite_style_unification_20261107/protection_before.json').read_text('utf8'))['files'];protection={n:{'size':(ROOT/n).stat().st_size,'sha256':file_hash(ROOT/n)}for n in old_protected}
if (W/'protection_before.json').exists():assert json.loads((W/'protection_before.json').read_text('utf8'))['files']==protection
else:write(W/'protection_before.json',{'files':protection})
outputs={}
for project in expected:
 d=W/project;c=d/'candidate03';recipe=json.loads((c/'proposal.json').read_text('utf8'));source=json.loads((d/'source.json').read_text('utf8'));parent=ROOT/recipe['parent']['cue'];game=parent.with_suffix('.bin');assert file_hash(game)==expected[project]==recipe['parent']['sha256']
 before=(d/'before_ST0E_U0.ARC').read_bytes();after=(c/'ST0E_U0.ARC').read_bytes();assert sha(before)==recipe['before_sha256']and sha(after)==recipe['after_sha256']and len(before)==len(after)
 assert [(q['type'],q['offset'],q['size'])for q in psx_arc(before)]==[(q['type'],q['offset'],q['size'])for q in psx_arc(after)]
 for e in psx_arc(before):
  k=int(e['type'],16)
  if k not in(0x10002,0x12):assert entry(before,k)==entry(after,k)
 og=entry(before,0x10002);ng=entry(after,0x10002);op=struct.pack('<I',4)+entry(before,0x12);np_=struct.pack('<I',4)+entry(after,0x12);checks=[];pixels=np.load(c/'expected_title_indices.npy')
 def decode(g,p,n):
  co=aliased_composition(p,0,n);px,sz,bb,_=compose_static(g,local_composition(co));return co,np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]),bb
 for n in range(35):
  oldco,oa,ob=decode(og,op,n);co,a,b=decode(ng,np_,n)
  for part in co['parts']:
   assert part['page']*256+part['tile']<len(ng)//128 and not part['unknown_flags']
   if n in(0,17,*range(10,17)):assert part['clut']==0
  if n in(0,17):
   canvas=np.zeros((112,240),np.uint8);dx,dy=b[0]+104,b[1]+64;assert min(dx,dy)>=0;canvas[dy:dy+a.shape[0],dx:dx+a.shape[1]]=a;assert np.array_equal(canvas,pixels);assert np.array_equal(canvas[24:88],oa[24:88])
  elif n in range(10,17):assert np.array_equal(a,oa)and b==(ob[0],ob[1]-8,ob[2],ob[3]-8)
  else:
   assert np.array_equal(a,oa)and b==ob
   assert [op[p['record_offset']:p['record_offset']+4]for p in oldco['parts']]==[np_[p['record_offset']:p['record_offset']+4]for p in co['parts']]
  checks.append({'frame':n,'part_count':len(co['parts']),'composition_bounds':list(b),'scope':'title_layout'if n in(0,17,*range(10,17))else'unchanged'})
 # Menu ink remains clear of the new subtitle, with all three native anchors.
 for n,y in((2,128),(29,144),(30,160)):
  _,a,b=decode(ng,np_,n);ys,xs=np.nonzero(a);assert y+b[1]+int(ys.min())>=122
 record=source['records']['ST0E_U0.ARC'];current,_=read_disc(game,['ST0E_U0.ARC']);assert current['ST0E_U0.ARC']==before
 out=ROOT/'out'/project/'title_branding_20261108_v1';assert not out.exists();out.mkdir();stem=parent.stem;target=out/(stem+'.bin');result=write_archive_copies(game,target,[({**record,'sha256':sha(before)},after)],expected[project]);declared={s['lba']for s in result['changed_sectors']};actual=set()
 with game.open('rb')as a,target.open('rb')as b:
  for lba in range(result['size']//2352):
   old,new=a.read(2352),b.read(2352)
   if old==new:continue
   assert lba in declared and record['lba']<=lba<record['lba']+(record['size']+2047)//2048 and old[:24]==new[:24]
   off=(lba-record['lba'])*2048;chunk=after[off:off+2048];assert new[24:24+len(chunk)]==chunk and new[24+len(chunk):2072]==old[24+len(chunk):2072];validate_checks(new);actual.add(lba)
 assert actual==declared
 got,_=read_disc(target,['ST0E_U0.ARC','COL0E_U0.ARC','SLUS_005.61']);assert got['ST0E_U0.ARC']==after
 for n in('COL0E_U0.ARC','SLUS_005.61'):assert got[n]==(d/('before_'+n)).read_bytes()
 assert file_hash(game)==expected[project]
 (out/(stem+'.cue')).write_bytes(parent.read_bytes())
 for n,data in got.items():(out/n).write_bytes(data)
 shutil.copyfile(c/'proposal.json',out/'proposal.json');write(out/'sector_changes.json',result)
 report={'project':project,'task':'title_fan_notice_and_mode_subtitle','parent_cue':parent.relative_to(ROOT).as_posix(),'parent_sha256':expected[project],'modified_bin':{k:v for k,v in result.items()if k!='changed_sectors'},'changed_resources':['ST0E_U0.ARC'],'changed_entries':[65538,18],'changed_sectors':len(actual),'full_disc_sectors_compared':result['size']//2352,'EDC_ECC_verified':True,'readback_verified':True,'all_other_disc_data_preserved':True,'logo_pixels_preserved':True,'logo_shift_y':-8,'menu_pixels_and_coords_preserved':True,'exe_palette_audio_sprites_unchanged':True,'runtime_verified':False,'user_accepted':False,'composition_checks':checks,'proposal_sha256':file_hash(c/'proposal.json')}
 write(out/'manifest.json',report);outputs[project]={'cue':(out/(stem+'.cue')).relative_to(ROOT).as_posix(),'sha256':result['sha256'],'manifest':(out/'manifest.json').relative_to(ROOT).as_posix()};print(json.dumps({'project':project,'sha256':result['sha256'],'changed_sectors':len(actual)}))
write(W/'builds.json',outputs)
