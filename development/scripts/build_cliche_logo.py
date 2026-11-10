"""Build fixed-size logo replacements and audit every raw disc sector."""
import argparse,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest,working_cue
from scripts.discover_inputs import DiscReader,sha256
from scripts.inventory_cliche_logo import PARENT,SOURCE_HASH
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

def main(candidate,repro):
    kind=json.loads((candidate/'recipe.json').read_text())['kind']
    if kind=='cliche_logo_v4':from scripts.verify_cliche_logo_v4 import verify
    elif kind=='cliche_logo_v3':from scripts.verify_cliche_logo_v3 import verify
    else:raise ValueError('Unsupported logo recipe')
    recipe=verify(candidate,repro);source=PARENT/'shibuki_riko.bin';updates=[]
    with source.open('rb') as stream:
        reader=DiscReader(stream,source.stat().st_size)
        for name,meta in recipe['files'].items():
            r=recipe['records'][name];before=reader.read(r['lba'],r['size']);after=(candidate/name).read_bytes()
            if sha256(before)!=meta['before'] or sha256(after)!=meta['after'] or len(after)!=len(before):raise ValueError('Changed resource')
            updates.append(({**r,'sha256':meta['before']},after))
    out=ROOT/'out/ver_buki_riko'/('cliche_logo_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    target=out/'shibuki_riko.bin';result=write_archive_copies(source,target,updates,recipe['parent_sha256']);declared={x['lba'] for x in result['changed_sectors']};actual=set()
    with source.open('rb') as a,target.open('rb') as b:
        for lba in range(result['size']//2352):
            old,new=a.read(2352),b.read(2352)
            if old==new:continue
            hits=[(r,data) for r,data in updates if r['lba']<=lba<r['lba']+(r['size']+2047)//2048]
            if lba not in declared or len(hits)!=1 or old[:24]!=new[:24]:raise ValueError('Unexpected sector edit')
            r,data=hits[0];offset=(lba-r['lba'])*2048;chunk=data[offset:offset+2048]
            if new[24:24+len(chunk)]!=chunk or new[24+len(chunk):2072]!=old[24+len(chunk):2072]:raise ValueError('Unexpected payload')
            validate_checks(new);actual.add(lba)
    if actual!=declared:raise ValueError('Incomplete sector validation')
    with target.open('rb') as stream:
        reader=DiscReader(stream,target.stat().st_size)
        for r,data in updates:
            if reader.read(r['lba'],r['size'])!=data:raise ValueError('Readback failure')
    if digest(source)!=recipe['parent_sha256'] or digest(ROOT/'MegaMan X4.bin')!=SOURCE_HASH:raise ValueError('Protected source changed')
    for name in recipe['files']:shutil.copyfile(candidate/name,out/name)
    for name in ('recipe.json','verification.json'):shutil.copyfile(candidate/name,out/name)
    (out/'shibuki_riko.cue').write_text(working_cue((PARENT/'shibuki_riko.cue').read_text('ascii'),'shibuki_riko.bin'),encoding='ascii')
    manifest={'project':'ver_buki_riko','task':'cliche_logo','kind':recipe['kind'],'source_sha256':SOURCE_HASH,'parent_build':recipe['parent'],'parent_bin_sha256':recipe['parent_sha256'],'bin_file':'shibuki_riko.bin','modified_bin':{k:v for k,v in result.items() if k!='changed_sectors'},'changed_resources':list(recipe['files']),'changed_sectors':len(actual),'full_disc_sectors_compared':result['size']//2352,'same_resource_sizes_lbas':True,'exe_changed':'SLUS_005.61' in recipe['files'],'exe_scope':recipe['checks'].get('loading_position'),'logic_changed':False,'timing_changed':False,'runtime_verified':False}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2));(out/'sector_changes.json').write_text(json.dumps(result,indent=2));print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(actual)}));return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--repro',type=Path,required=True);a=p.parse_args();main(a.candidate,a.repro)
