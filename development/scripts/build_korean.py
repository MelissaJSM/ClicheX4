"""Apply a reviewed Korean proposal to a new fixed-layout BIN.

Execution requires the user's approval for the new dialogue renderer under
AGENTS.md section4. Preparation alone is not approval; this script was not run
while that request was pending.
"""
import argparse,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest,working_cue
from scripts.discover_inputs import DiscReader,sha256
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

def main(candidate):
    recipe=json.loads((candidate/'proposal.json').read_text('utf-8'))
    if recipe['kind']!='korean_localization_integrated_proposal':raise ValueError('Wrong proposal')
    source=ROOT/recipe['parent']/'shibuki_riko.bin'
    if digest(source)!=recipe['parent_sha256'] or digest(ROOT/'MegaMan X4.bin')!=recipe['source_sha256']:raise ValueError('Protected input changed')
    updates=[]
    with source.open('rb') as f:
        reader=DiscReader(f,source.stat().st_size)
        for name,meta in recipe['files'].items():
            r=recipe['records'][name];old=reader.read(r['lba'],r['size']);new=(candidate/name).read_bytes()
            if sha256(old)!=meta['before'] or sha256(new)!=meta['after'] or len(old)!=len(new):raise ValueError('Candidate input changed')
            updates.append(({**r,'sha256':meta['before']},new))
    output=ROOT/'out/ver_buki_riko'/('korean_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));output.mkdir()
    target=output/'shibuki_riko.bin';result=write_archive_copies(source,target,updates,recipe['parent_sha256']);declared={v['lba'] for v in result['changed_sectors']};actual=set()
    with source.open('rb') as a,target.open('rb') as b:
        for lba in range(result['size']//2352):
            old,new=a.read(2352),b.read(2352)
            if old==new:continue
            hits=[(r,data) for r,data in updates if r['lba']<=lba<r['lba']+(r['size']+2047)//2048]
            if len(hits)!=1 or lba not in declared or old[:24]!=new[:24]:raise ValueError('Unexpected sector mutation')
            r,data=hits[0];off=(lba-r['lba'])*2048;chunk=data[off:off+2048]
            if new[24:24+len(chunk)]!=chunk or new[24+len(chunk):2072]!=old[24+len(chunk):2072]:raise ValueError('Unexpected sector payload')
            validate_checks(new);actual.add(lba)
    if actual!=declared:raise ValueError('Sector verification incomplete')
    with target.open('rb') as f:
        reader=DiscReader(f,target.stat().st_size)
        for r,data in updates:
            if reader.read(r['lba'],r['size'])!=data:raise ValueError('Disc resource readback differs')
    for name in recipe['files']:shutil.copyfile(candidate/name,output/name)
    (output/'shibuki_riko.cue').write_text(working_cue((source.parent/'shibuki_riko.cue').read_text('ascii'),'shibuki_riko.bin'),encoding='ascii')
    manifest={'task':'korean_localization','source_sha256':recipe['source_sha256'],'parent_build':recipe['parent'],'parent_bin_sha256':recipe['parent_sha256'],'bin_file':'shibuki_riko.bin','modified_bin':{k:v for k,v in result.items() if k!='changed_sectors'},'changed_resources':list(recipe['files']),'changed_sectors':len(actual),'full_disc_sectors_compared':result['size']//2352,'resource_sizes_lbas_preserved':True,'text_renderer_changed':True,'gameplay_logic_changed':False,'runtime_verified':False,'coverage':recipe['coverage']}
    if digest(source)!=recipe['parent_sha256'] or digest(ROOT/'MegaMan X4.bin')!=recipe['source_sha256']:raise ValueError('Protected input changed after build')
    shutil.copyfile(candidate/'proposal.json',output/'proposal.json');(output/'manifest.json').write_text(json.dumps(manifest,indent=2));(output/'sector_changes.json').write_text(json.dumps(result,indent=2));print(json.dumps({'output':str(output),'sha256':result['sha256']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);a=p.parse_args();main(a.candidate)
