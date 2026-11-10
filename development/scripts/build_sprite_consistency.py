"""Apply reviewed fixed-length sprite resources to new, hash-bound BIN copies."""
import argparse, json, hashlib, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc, require
from scripts.discover_inputs import psx_arc
from scripts.project import working_cue
from src.psx_disc import file_hash, write_archive_copies
from src.psx_sector import validate_checks

WORK=ROOT/'work/sprite_consistency_20261105'
ALLOWED={'PL00_U.ARC':{2,3},'PL01_U.ARC':{2,3},'PL02_U.ARC':{2,3},'LOAD_U.ARC':{0x10008}}

def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')

def check_resource(name, old, new):
    require(len(old)==len(new),'Resource length changed')
    if name=='MOJIPAT.ARC':
        # Explicit save UI preparation carries its frame/palette protection proof.
        # This generic boundary check additionally freezes its palette directory.
        import struct
        palette=struct.unpack_from('<I',old,4)[0]
        parts=struct.unpack_from('<I',old,8)[0]
        require(old[:16]==new[:16] and old[palette:parts]==new[palette:parts], 'Menu directory/palette changed')
    else:
        require(name in ALLOWED,'Unexpected sprite resource')
        entries=psx_arc(old)
        layout=lambda es:[(e['type'],e['offset'],e['size'])for e in es]
        require(layout(entries)==layout(psx_arc(new)),'ARC layout changed')
        permitted=bytearray(len(old))
        for e in entries:
            if int(e['type'],16) in ALLOWED[name]:permitted[e['offset']:e['offset']+e['size']]=bytes([1])*e['size']
        require(all(a==b or permitted[i] for i,(a,b)in enumerate(zip(old,new))),'Non-sprite/audio/palette data changed')
    return {'before':sha(old),'after':sha(new),'size':len(new),'changed_bytes':sum(a!=b for a,b in zip(old,new))}

def build(plan_path):
    plan_path=plan_path.resolve();require(plan_path.is_relative_to(WORK.resolve()),'Plan outside review workspace')
    plan=json.loads(plan_path.read_text('utf8'));mode=plan['project'];require(mode in ('ver_buki_riko','ver_rin_nana'),'Unknown mode')
    source=(ROOT/plan['source_bin']).resolve();require(source.is_relative_to((ROOT/'out'/mode).resolve()),'Source must be working copy')
    require(file_hash(source)==plan['source_sha256'],'Parent hash mismatch')
    output=(ROOT/plan['output']).resolve();require(output.is_relative_to((ROOT/'out'/mode).resolve())and not output.exists(),'New mode output required')
    names=list(plan['resources']);old,records=read_disc(source,tuple(names)+('SLUS_005.61',));replacements={};checks={}
    for name,q in plan['resources'].items():
        path=(ROOT/q['path']).resolve();require(path.is_relative_to(WORK.resolve()),'Prepared resource outside workspace')
        new=path.read_bytes();require(sha(old[name])==q['before'] and sha(new)==q['after'],'Prepared resource hash mismatch')
        checks[name]=check_resource(name,old[name],new);replacements[name]=new
    output.mkdir(parents=True);stem=source.stem;target=output/(stem+'.bin')
    result=write_archive_copies(source,target,[({**records[n],'sha256':sha(old[n])},replacements[n])for n in names],plan['source_sha256'])
    changed={s['lba'] for s in result['changed_sectors']};sectors=0
    with source.open('rb')as a,target.open('rb')as b:
        while before:=a.read(2352):
            after=b.read(2352);require((before!=after)==(sectors in changed),'Undeclared sector difference')
            if sectors in changed:validate_checks(after)
            sectors+=1
        require(not b.read(1),'Disc length changed')
    actual,_=read_disc(target,tuple(names)+('SLUS_005.61',))
    require(all(actual[n]==replacements[n]for n in names),'Disc readback mismatch')
    require(actual['SLUS_005.61']==old['SLUS_005.61'],'Executable changed')
    require(file_hash(source)==plan['source_sha256'],'Parent changed')
    (output/(stem+'.cue')).write_text(working_cue(source.with_suffix('.cue').read_text('ascii'),stem+'.bin'),'ascii')
    report={'task':'sprite_consistency_review','project':mode,'parent_bin':plan['source_bin'],'parent_sha256':plan['source_sha256'],
      'modified_bin':result,'resources':checks,'review_plan':plan_path.relative_to(ROOT).as_posix(),
      'all_disc_sectors_compared':sectors,'unchanged_sectors_identical':True,'changed_EDC_ECC_valid':True,'disc_readback_verified':True,
      'executable_sha256':sha(actual['SLUS_005.61']),'gameplay_timing_code_palettes_audio_preserved':True,
      'runtime_verified':False,'user_accepted':False,'active_pointer_changed':False,'save_data_written':False}
    save(output/'manifest.json',report)
    print(json.dumps({'project':mode,'sha256':result['sha256'],'changed_sectors':len(changed),'output':str(output)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('plan',type=Path);a=p.parse_args();build(a.plan)
