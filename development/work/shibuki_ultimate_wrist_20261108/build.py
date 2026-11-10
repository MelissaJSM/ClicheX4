from pathlib import Path
import sys,json,shutil
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'work/motion_fixes_20261108')]
from common import write,sha
from src.psx_disc import file_hash,write_archive_copies
from src.psx_sector import validate_checks
from scripts.c01_audio_build import read_disc
source=json.loads((H/'source.json').read_text('utf8'));p=source['pointer'];game=ROOT/Path(p['cue']).with_suffix('.bin');assert file_hash(game)==p['sha256']
current=json.loads((ROOT/'projects/ver_buki_riko/current_build.json').read_text('utf8'))
assert current['sha256']=='40630dbd3415245765e4bf39882f17a609bbe8bc9c94b518b35e38d976b65f80'
protected=json.loads((ROOT/'work/motion_fixes_20261108/protection_before.json').read_text('utf8'))['files'];snapshot={n:{'size':(ROOT/n).stat().st_size,'sha256':file_hash(ROOT/n)} for n in protected};write(H/'protection_before.json',{'files':snapshot})
before=(H/'PL02_U.ARC').read_bytes();after=(H/'PL02_fixed.ARC').read_bytes();assert len(before)==len(after)
out=ROOT/'out/ver_buki_riko/ultimate_wrist_20261108_v3';assert not out.exists();out.mkdir();target=out/'shibuki_riko.bin';record=source['records']['PL02_U.ARC']
r=write_archive_copies(game,target,[({**record,'sha256':sha(before)},after)],p['sha256']);declared={q['lba'] for q in r['changed_sectors']};actual=set()
with game.open('rb') as old,target.open('rb') as new:
 for lba in range(r['size']//2352):
  a,b=old.read(2352),new.read(2352)
  if a==b:continue
  assert lba in declared and record['lba']<=lba<record['lba']+(record['size']+2047)//2048 and a[:24]==b[:24];validate_checks(b);actual.add(lba)
assert actual==declared
check,_=read_disc(target,['PL00_U.ARC','PL01_U.ARC','PL02_U.ARC','MOJIPAT.ARC','SLUS_005.61']);old,_=read_disc(game,list(check))
assert check['PL02_U.ARC']==after
for n in check:
 if n!='PL02_U.ARC':assert check[n]==old[n]
(out/'shibuki_riko.cue').write_bytes((ROOT/p['cue']).read_bytes());write(out/'sector_changes.json',r)
manifest={'task':'shibuki_ultimate_wrist','project':'ver_buki_riko','parent_cue':p['cue'],'parent_sha256':p['sha256'],'modified_bin':{k:v for k,v in r.items() if k!='changed_sectors'},'changed_resource':'PL02_U.ARC','resource_sha256':sha(after),'changed_sectors':len(actual),'full_disc_sectors_compared':r['size']//2352,'EDC_ECC_verified':True,'readback_verified':True,'all_other_disc_data_preserved':True,'runtime_verified':False,'user_accepted':False}
write(out/'manifest.json',manifest);write(H/'build.json',{'cue':(out/'shibuki_riko.cue').relative_to(ROOT).as_posix(),'sha256':r['sha256'],'manifest':(out/'manifest.json').relative_to(ROOT).as_posix()})
review=out/'review';review.mkdir()
for name in ['before.png','after.png','before.gif','after.gif','registration.json']:shutil.copyfile(H/'candidate'/name,review/name)
shutil.copyfile(H/'validation.json',review/'validation.json')
for n,rec in snapshot.items():assert file_hash(ROOT/n)==rec['sha256']
print(json.dumps({'cue':str(out/'shibuki_riko.cue'),'sha256':r['sha256'],'sectors':len(actual)}))
