"""현재 기본형 수정 BIN에 두 저장 UI 자원만 같은 크기로 삽입한다."""
import json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.analyze_shibuki_ultimate import D,SOURCE_SHA
from scripts.project import digest,working_cue
from scripts.discover_inputs import DiscReader,sha256
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

def main():
    parent=ROOT/'out/ver_buki_riko/shibuki_ultimate_base_fix_20261027T105534656587Z';candidate=D/'save_ui_fix01';repro=D/'save_ui_fix02_repro';recipe=json.loads((candidate/'recipe.json').read_text());records=json.loads((D/'save_ui_observed01/records.json').read_text())
    source=parent/'shibuki_riko.bin'
    if digest(source)!=recipe['parent_bin_sha256'] or digest(ROOT/'MegaMan X4.bin')!=SOURCE_SHA:raise ValueError('Wrong game input')
    updates=[]
    with source.open('rb') as f:
        reader=DiscReader(f,source.stat().st_size)
        for name,meta in recipe['files'].items():
            before=reader.read(records[name]['lba'],records[name]['size']);after=(candidate/name).read_bytes()
            if sha256(before)!=meta['before'] or sha256(after)!=meta['after'] or after!=(repro/name).read_bytes() or len(after)!=len(before) or len(after)!=meta['size']:raise ValueError('Candidate hash/length/reproduction mismatch')
            updates.append(({**records[name],'sha256':meta['before']},after))
    out=ROOT/'out/ver_buki_riko'/('shibuki_ultimate_save_fix_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    target=out/'shibuki_riko.bin';result=write_archive_copies(source,target,updates,recipe['parent_bin_sha256']);changed={x['lba'] for x in result['changed_sectors']};actual=set()
    with source.open('rb') as a,target.open('rb') as b:
        for lba in range(result['size']//2352):
            old,new=a.read(2352),b.read(2352)
            if old==new:continue
            if lba not in changed or old[:24]!=new[:24]:raise ValueError('Unexpected sector change')
            candidates=[(r,d) for r,d in updates if r['lba']<=lba<r['lba']+(r['size']+2047)//2048]
            if len(candidates)!=1:raise ValueError('Change outside selected file')
            r,data=candidates[0];off=(lba-r['lba'])*2048;chunk=data[off:off+2048]
            if new[24:24+len(chunk)]!=chunk or new[24+len(chunk):2072]!=old[24+len(chunk):2072]:raise ValueError('Wrong sector payload')
            validate_checks(new);actual.add(lba)
    if actual!=changed:raise ValueError('Incomplete changed-sector check')
    with target.open('rb') as f:
        reader=DiscReader(f,target.stat().st_size)
        for r,data in updates:
            if reader.read(r['lba'],r['size'])!=data:raise ValueError('Disc readback mismatch')
    if digest(source)!=recipe['parent_bin_sha256'] or digest(ROOT/'MegaMan X4.bin')!=SOURCE_SHA:raise ValueError('Protected game changed')
    (out/'shibuki_riko.cue').write_text(working_cue((parent/'shibuki_riko.cue').read_text('ascii'),'shibuki_riko.bin'),encoding='ascii')
    for name in (*recipe['files'],'review.png','recipe.json'):shutil.copyfile(candidate/name,out/name)
    for name in ('PL02_U.ARC','regression.json'):shutil.copyfile(parent/name,out/name)
    manifest={'project':'ver_buki_riko','task':'ultimate_armor_shibuki','kind':'ultimate_pre_capsule_and_save_ui_fix','source_sha256':SOURCE_SHA,'parent_build':str(parent.relative_to(ROOT)),'parent_bin_sha256':recipe['parent_bin_sha256'],'modified_bin':{k:v for k,v in result.items() if k!='changed_sectors'},'modified_archive_sha256':digest(out/'PL02_U.ARC'),'changed_resources':list(recipe['files']),'changed_sectors':len(actual),'full_disc_sectors_compared':result['size']//2352,'archive_sizes_lbas_preserved':True,'player_graphics_preserved_from_parent':True,'exe_changed':False,'runtime_new_ui_verified':False,'full_ultimate_complete':False,'ultimate_outfit_still_standing_pilot':True}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2));(out/'sector_changes.json').write_text(json.dumps(result,indent=2));print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(actual),'full_disc_sectors_compared':result['size']//2352}))

if __name__=='__main__':main()
