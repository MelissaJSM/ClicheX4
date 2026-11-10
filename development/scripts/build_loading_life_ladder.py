"""Build approved sprite fixes; loading display data requires explicit approval."""
import argparse,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest,working_cue
from scripts.discover_inputs import DiscReader,sha256
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

def main(candidate,repro,approved_loading_data=False):
    candidate=candidate.resolve();repro=repro.resolve()
    if any(not p.is_relative_to(ROOT/'work/ver_buki_riko') for p in (candidate,repro)):raise ValueError('Isolated candidates required')
    recipe=json.loads((candidate/'recipe.json').read_text())
    if recipe['kind']!='loading_life_ladder_fix' or set(recipe['files'])!={'PL00_U.ARC','PL01_U.ARC','PL02_U.ARC','LOAD_U.ARC','MOJIPAT.ARC','SLUS_005.61'}:raise ValueError('Wrong candidate')
    from scripts.verify_loading_life_ladder import verify
    verify(candidate,repro)
    selected=set(recipe['files']) if approved_loading_data else {'PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'}
    parent=(ROOT/recipe['parent']).resolve();source=parent/'shibuki_riko.bin';original=ROOT/'MegaMan X4.bin'
    original_hash='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
    if not parent.is_relative_to(ROOT/'out/ver_buki_riko') or digest(source)!=recipe['parent_sha256'] or digest(original)!=original_hash:raise ValueError('Changed input')
    updates=[]
    with source.open('rb') as stream:
        reader=DiscReader(stream,source.stat().st_size)
        for name,meta in recipe['files'].items():
            if name not in selected:continue
            r=recipe['records'][name];before=reader.read(r['lba'],r['size']);after=(candidate/name).read_bytes()
            if sha256(before)!=meta['before'] or sha256(after)!=meta['after'] or after!=(repro/name).read_bytes() or len(after)!=len(before):raise ValueError('Hash/size/reproduction failure')
            updates.append(({**r,'sha256':meta['before']},after))
    out=ROOT/'out/ver_buki_riko'/(('loading_life_ladder_fix_' if approved_loading_data else 'life_ladder_fix_')+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    target=out/'shibuki_riko.bin';result=write_archive_copies(source,target,updates,recipe['parent_sha256']);declared={x['lba'] for x in result['changed_sectors']};actual=set()
    with source.open('rb') as a,target.open('rb') as b:
        for lba in range(result['size']//2352):
            old,new=a.read(2352),b.read(2352)
            if old==new:continue
            hits=[(r,data) for r,data in updates if r['lba']<=lba<r['lba']+(r['size']+2047)//2048]
            if lba not in declared or len(hits)!=1 or old[:24]!=new[:24]:raise ValueError('Unexpected sector edit')
            r,data=hits[0];offset=(lba-r['lba'])*2048;chunk=data[offset:offset+2048]
            if new[24:24+len(chunk)]!=chunk or new[24+len(chunk):2072]!=old[24+len(chunk):2072]:raise ValueError('Unexpected sector payload')
            validate_checks(new);actual.add(lba)
    if actual!=declared:raise ValueError('Incomplete sector validation')
    with target.open('rb') as stream:
        reader=DiscReader(stream,target.stat().st_size)
        for r,data in updates:
            if reader.read(r['lba'],r['size'])!=data:raise ValueError('Readback failure')
    if digest(source)!=recipe['parent_sha256'] or digest(original)!=original_hash:raise ValueError('Protected source changed')
    for name in selected:shutil.copyfile(candidate/name,out/name)
    shutil.copyfile(candidate/'recipe.json',out/'proposal_recipe.json')
    applied={**recipe,'files':{n:v for n,v in recipe['files'].items() if n in selected},'applied_resources':sorted(selected),'loading_change_applied':approved_loading_data}
    (out/'recipe.json').write_text(json.dumps(applied,indent=2))
    (out/'shibuki_riko.cue').write_text(working_cue((parent/'shibuki_riko.cue').read_text('ascii'),'shibuki_riko.bin'),encoding='ascii')
    manifest={'project':'ver_buki_riko','task':'ultimate_armor_shibuki','kind':recipe['kind'] if approved_loading_data else 'life_ladder_fix','source_sha256':original_hash,'parent_build':recipe['parent'],'parent_bin_sha256':recipe['parent_sha256'],'modified_bin':{k:v for k,v in result.items() if k!='changed_sectors'},'modified_archive_sha256':digest(out/'PL02_U.ARC'),'changed_resources':sorted(selected),'changed_sectors':len(actual),'full_disc_sectors_compared':result['size']//2352,'same_resource_sizes_lbas':True,'exe_changed':approved_loading_data,'loading_data_approval_received':approved_loading_data,'loading_change_applied':approved_loading_data,'timing_changed':False,'runtime_verified':False}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2));(out/'sector_changes.json').write_text(json.dumps(result,indent=2));print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(actual)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--repro',type=Path,required=True);p.add_argument('--approved-loading-data',action='store_true');a=p.parse_args();main(a.candidate,a.repro,a.approved_loading_data)
