"""네 가지 사용자 제보 수정분을 최신 두 부모 BIN에 적용한다."""
from pathlib import Path
import sys,json,struct
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path.insert(0,str(ROOT))
from common import sha,write
from scripts.black_variant_palette import ranges
from scripts.prepare_riko_ui import entry
from scripts.c01_audio_build import read_disc
from src.psx_disc import write_archive_copies,file_hash
from src.psx_sector import validate_checks
sources=json.loads((H/'sources.json').read_text('utf8'))
protected=json.loads((ROOT/'work/sprite_style_unification_20261107/protection_before.json').read_text('utf8'))['files']
snapshot={n:{'size':(ROOT/n).stat().st_size,'sha256':file_hash(ROOT/n)} for n in protected}
write(H/'protection_before.json',{'files':snapshot})
br=H/'ver_buki_riko';assets={n:(br/n).read_bytes() for n in ('PL01_U.ARC','MOJIPAT.ARC')};positions=ranges(assets);pal=(br/'riko_inverted_palette.bin').read_bytes()
for n,at in positions.items():
 before=assets[n];after=before[:at]+pal+before[at+32:];assert len(before)==len(after)
 (br/(n.split('_U')[0].split('.')[0]+'_fixed.ARC')).write_bytes(after)
assert entry((br/'PL01_fixed.ARC').read_bytes(),9)[:32]==entry(assets['PL01_U.ARC'],9)[:32]
write(br/'black_palette_patch.json',{'positions':positions,'palette_sha256':sha(pal),'normal_palette_preserved':True,'geometry_preserved':True})
builds={}
for mode,source in sources.items():
 w=H/mode;p=source['pointer'];game=ROOT/Path(p['cue']).with_suffix('.bin');assert file_hash(game)==p['sha256']
 assert json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'))==p
 write(w/'current_build_before.json',p)
 names=['PL00_U.ARC','PL01_U.ARC','PL02_U.ARC']+(['MOJIPAT.ARC'] if mode=='ver_buki_riko' else [])
 changed={n:(w/(n.split('_U')[0].split('.')[0]+'_fixed.ARC')).read_bytes() for n in names};patches=[]
 for n,new in changed.items():
  old=(w/n).read_bytes();assert len(new)==len(old);patches.append(({**source['records'][n],'sha256':sha(old)},new))
 out=ROOT/'out'/mode/'motion_fixes_20261108_v1';assert not out.exists();out.mkdir();stem='shibuki_riko' if mode=='ver_buki_riko' else 'rin_nana';target=out/(stem+'.bin')
 r=write_archive_copies(game,target,patches,p['sha256']);declared={s['lba'] for s in r['changed_sectors']};actual=set()
 with game.open('rb') as old,target.open('rb') as new:
  for lba in range(r['size']//2352):
   a,b=old.read(2352),new.read(2352)
   if a==b:continue
   assert lba in declared and a[:24]==b[:24];validate_checks(b);actual.add(lba)
 assert actual==declared
 check,recs=read_disc(target,[*names,'SLUS_005.61','ST0D_0Z.ARC','ST0E_U0.ARC']);parent,_=read_disc(game,list(check))
 for n,v in check.items():assert v==changed.get(n,parent[n]),n
 assert file_hash(game)==p['sha256']
 (out/(stem+'.cue')).write_bytes((ROOT/p['cue']).read_bytes());write(out/'sector_changes.json',r)
 manifest={'task':'motion_fixes_20261108','project':mode,'parent_cue':p['cue'],'parent_sha256':p['sha256'],'modified_bin':{k:v for k,v in r.items() if k!='changed_sectors'},'changed_resources':{n:{'before':sha(parent[n]),'after':sha(v)} for n,v in changed.items()},'full_disc_sectors_compared':r['size']//2352,'changed_sectors':len(actual),'EDC_ECC_verified':True,'readback_verified':True,'all_other_disc_data_preserved':True,'exe_timing_palette_except_black_riko_preserved':True,'runtime_verified':False,'user_accepted':False}
 write(out/'manifest.json',manifest);builds[mode]={'cue':(out/(stem+'.cue')).relative_to(ROOT).as_posix(),'sha256':r['sha256'],'manifest':(out/'manifest.json').relative_to(ROOT).as_posix()}
 print(mode,builds[mode],flush=True)
write(H/'builds.json',builds)
for n,old in snapshot.items():assert file_hash(ROOT/n)==old['sha256'],n
write(H/'protection_after_build.json',{'unchanged':len(snapshot),'all_equal':True})
