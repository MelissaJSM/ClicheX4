"""Build isolated Black UI BINs; no original, progress, or emulator changes."""
import json,struct,sys
from pathlib import Path
import numpy as np
from black_ui import ROOT,H,START,END,TABLE,HOOK,off,sha,proposal,CHANGES
from scripts.c01_audio_build import read_disc
from src.psx_disc import file_hash,write_archive_copies
from src.psx_sector import validate_checks

def load(p):return json.loads(p.read_text('utf8'))
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
original_protected=load(ROOT/'work/armor_dialogue_20261108/protection_before.json')['files']
snapshot={name:{'size':(ROOT/name).stat().st_size,'sha256':file_hash(ROOT/name)}for name in original_protected}
write(H/'protection_before_black.json',{'files':snapshot})
results=[]
for mode in CHANGES:
    d=H/mode; ptr=load(d/'source.json')['pointer']; assert load(ROOT/'projects'/mode/'current_build.json')==ptr
    source=ROOT/Path(ptr['cue']).with_suffix('.bin'); assert file_hash(source)==ptr['sha256']
    exe,pr=proposal(mode); cpu=load(d/'black_proposal/cpu_verification.json');assert cpu['passed'] and cpu['target_exe_sha256']==sha(exe)
    origexe=(d/'originals/SLUS_005.61').read_bytes();allowed=bytearray(len(exe))
    for a,b in [(START,END),(TABLE,TABLE+4),(HOOK,HOOK+12)]:allowed[off(a):off(b)]=b'\xff'*(b-a)
    assert len(exe)==len(origexe) and all(a==b or allowed[i] for i,(a,b)in enumerate(zip(exe,origexe)))
    replacement={'SLUS_005.61':exe};static=None
    if mode=='ver_buki_riko':
        pre=d/'prepared_assets_v2'; static=load(pre/'verification.json');assert static['pointer']==ptr
        for q in static['files']:
            raw=(pre/q['file']).read_bytes();assert sha(raw)==q['after'];replacement[q['file']]=raw
    originals,records=read_disc(source,list(replacement));assert originals['SLUS_005.61']==origexe
    if static:
        for q in static['files']:assert sha(originals[q['file']])==q['before']
    stem='rin_nana' if mode=='ver_rin_nana' else 'shibuki_riko'
    out=ROOT/'out'/mode/'black_illustrations_20261108_v1';out.mkdir(exist_ok=False);target=out/(stem+'.bin')
    result=write_archive_copies(source,target,[({**records[name],'sha256':sha(originals[name])},data)for name,data in replacement.items()],ptr['sha256'])
    declared={q['lba']for q in result['changed_sectors']};actual=set()
    permitted={lba for q in records.values()for lba in range(q['lba'],q['lba']+(q['size']+2047)//2048)}
    with source.open('rb')as f,target.open('rb')as g:
        for lba in range(result['size']//2352):
            a,b=f.read(2352),g.read(2352)
            if a!=b:
                assert lba in declared and lba in permitted and a[:24]==b[:24];validate_checks(b);actual.add(lba)
    assert actual==declared and read_disc(target,list(replacement))[0]==replacement and file_hash(source)==ptr['sha256']
    (out/(stem+'.cue')).write_bytes((ROOT/ptr['cue']).read_bytes())
    write(out/'sector_changes.json',result)
    manifest={'project':mode,'task':'black_illustrations_20261108','parent_cue':ptr['cue'],'parent_sha256':ptr['sha256'],'modified_bin':{k:v for k,v in result.items()if k!='changed_sectors'},'changed_files':list(replacement),'changed_sectors':len(actual),'all_disc_sectors_compared':result['size']//2352,'EDC_ECC_checked':True,'readback_exact':True,'all_other_sectors_preserved':True,'gameplay_resources_unchanged':True,'exe_ranges':[[hex(a),hex(b)]for a,b in [(START,END),(TABLE,TABLE+4),(HOOK,HOOK+12)]],'cpu_verification':cpu,'normal_rin_bitmaps_palettes_exact':mode=='ver_rin_nana','riko_normal_color_reindexing':static['poses'] if static else None,'x_hunter_armor_outfits_implemented':False,'runtime_verified':False,'user_accepted':False}
    write(out/'manifest.json',manifest);resultptr={'mode':mode,'cue':(out/(stem+'.cue')).relative_to(ROOT).as_posix(),'sha256':result['sha256'],'manifest':(out/'manifest.json').relative_to(ROOT).as_posix()};results.append(resultptr)
    print(json.dumps(resultptr),flush=True)
for name,q in snapshot.items():assert file_hash(ROOT/name)==q['sha256'],name
write(H/'black_builds.json',results)
