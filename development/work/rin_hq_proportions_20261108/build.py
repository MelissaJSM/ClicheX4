from pathlib import Path
import hashlib,json,sys,argparse
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import psx_arc
from src.psx_disc import write_archive_copies,file_hash
from src.psx_sector import validate_checks
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
ap=argparse.ArgumentParser();ap.add_argument('--candidate',default='candidate01');ap.add_argument('--revision',default='v1');args=ap.parse_args();candidate=W/args.candidate
source=json.loads((W/'source.json').read_text('utf8'));p=source['parent'];game=ROOT/Path(p['cue']).with_suffix('.bin');assert file_hash(game)==p['sha256']=='60f1a19803917c3f84796245ad7f0214e9ac8f1e332b582f0dbed4a2106ce01d'
assert json.loads((ROOT/'projects/ver_rin_nana/current_build.json').read_text('utf8'))==p
protected=json.loads((ROOT/'work/sprite_style_unification_20261107/protection_before.json').read_text('utf8'))['files']
snapshot={n:{'size':(ROOT/n).stat().st_size,'sha256':file_hash(ROOT/n)}for n in protected}
if (W/'protection_before.json').exists():assert json.loads((W/'protection_before.json').read_text('utf8'))['files']==snapshot
else:write(W/'protection_before.json',{'files':snapshot})
name='ST0D_0Z.ARC';record=source['resources']['current']['records'][name];before=(W/'current'/name).read_bytes();after=(candidate/name).read_bytes()
assert len(before)==len(after)
assert [(q['type'],q['offset'],q['size'])for q in psx_arc(before)]==[(q['type'],q['offset'],q['size'])for q in psx_arc(after)]
for e in psx_arc(before):
 k=int(e['type'],16)
 if k not in(0x10102,10):assert entry(before,k)==entry(after,k)
assert entry(before,0x10102)[:63488]==entry(after,0x10102)[:63488]and entry(before,0x10102)[81920:]==entry(after,0x10102)[81920:]
assert (W/'current/COL0D_0Z.ARC').read_bytes()==(candidate/'COL0D_0Z.ARC').read_bytes()
out=ROOT/'out/ver_rin_nana'/('rin_hunter_proportions_20261108_'+args.revision);assert not out.exists();out.mkdir();target=out/'rin_nana.bin'
result=write_archive_copies(game,target,[({**record,'sha256':sha(before)},after)],p['sha256']);declared={s['lba']for s in result['changed_sectors']};actual=set()
with game.open('rb')as a,target.open('rb')as b:
 for lba in range(result['size']//2352):
  old,new=a.read(2352),b.read(2352)
  if old==new:continue
  assert lba in declared and record['lba']<=lba<record['lba']+(record['size']+2047)//2048 and old[:24]==new[:24]
  off=(lba-record['lba'])*2048;chunk=after[off:off+2048];assert new[24:24+len(chunk)]==chunk and new[24+len(chunk):2072]==old[24+len(chunk):2072];validate_checks(new);actual.add(lba)
assert declared==actual
check,records=read_disc(target,[name,'COL0D_0Z.ARC','SLUS_005.61','ST0E_U0.ARC']);parent,_=read_disc(game,list(check));assert check[name]==after
assert all(check[n]==parent[n]for n in check if n!=name)
assert file_hash(game)==p['sha256']
(out/'rin_nana.cue').write_bytes((ROOT/p['cue']).read_bytes())
(out/name).write_bytes(after);(out/'recipe.json').write_bytes((candidate/'recipe.json').read_bytes());write(out/'sector_changes.json',result)
manifest={'project':'ver_rin_nana','task':'rin_hunter_proportions','parent_cue':p['cue'],'parent_sha256':p['sha256'],'modified_bin':{k:v for k,v in result.items()if k!='changed_sectors'},'changed_resources':[name],'changed_entries':[0x10102,10],'changed_sectors':len(actual),'full_disc_sectors_compared':result['size']//2352,'EDC_ECC_verified':True,'readback_verified':True,'all_other_disc_data_preserved':True,'palette_exe_audio_title_gameplay_sprites_preserved':True,'runtime_verified':False,'user_accepted':False}
write(out/'manifest.json',manifest);write(W/'build.json',{'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),'sha256':result['sha256'],'manifest':(out/'manifest.json').relative_to(ROOT).as_posix()});print(json.dumps({'cue':str(out/'rin_nana.cue'),'sha256':result['sha256'],'changed_sectors':len(actual)}))
