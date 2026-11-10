"""수용된 최종 BIN을 고정하고, 해시 검증 후 과거 BIN만 복구 가능한 차이 ZIP으로 정리한다."""
import argparse,json,hashlib,shutil,sys,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.compact_builds import compact,reconstruct,safe_path,digest,SOURCE_HASH
from scripts.discover_inputs import DiscReader,psx_arc
from scripts.project import working_cue
FINAL_SHA='8f130c5e807690e24204cee986717e9f7148e02960bf270359cfe0dae12dc25a'
ACCEPTED='out/ver_buki_riko/cliche_title_voice_20261028T071319364977Z'
ROLLBACK='out/ver_buki_riko/shibuki_voice_mute_20261028T064914983985Z'
RELEASE='out/ver_buki_riko/final_v1_0_0'
D=ROOT/'work/maintenance/final_20261028'
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf-8')
def seed():
    source=ROOT/'MegaMan X4.bin';accepted=ROOT/ACCEPTED
    assert digest(source)==SOURCE_HASH and digest(accepted/'shibuki_riko.bin')==FINAL_SHA
    dest=ROOT/RELEASE;dest.mkdir(exist_ok=True);game=dest/'game';game.mkdir(exist_ok=True)
    for name in ['shibuki_riko.bin','manifest.json','cliche_title_preview.wav']:
        if (game/name).exists():
            assert digest(game/name)==digest(accepted/name),f'Existing release differs: {name}'
        else:shutil.copy2(accepted/name,game/name)
    (game/'shibuki_riko.cue').write_text(working_cue((accepted/'shibuki_riko.cue').read_text('ascii'),'shibuki_riko.bin'),'ascii')
    assert digest(game/'shibuki_riko.bin')==FINAL_SHA
    if (dest/'recovery.json').exists():
        recovery=json.loads((dest/'recovery.json').read_text('utf-8'))
        reconstruct(ROOT,game/'shibuki_riko.bin.delta.zip')
    else:
        recovery=compact(ROOT,(game/'shibuki_riko.bin').relative_to(ROOT).as_posix(),FINAL_SHA,remove_full=False)
        save(dest/'recovery.json',recovery)
    resources=dest/'resources';resources.mkdir(exist_ok=True);records=[]
    with (accepted/'shibuki_riko.bin').open('rb') as f,source.open('rb') as g:
        final=DiscReader(f,source.stat().st_size);original=DiscReader(g,source.stat().st_size)
        disc=final.inspect()
        save(resources/'disc_inventory.json',disc)
        for rec in disc['files']:
            if not (rec['path'].endswith('.ARC;1') or rec['path']=='/SLUS_005.61;1'):continue
            a=original.read(rec['lba'],rec['size']);b=final.read(rec['lba'],rec['size'])
            changed=a!=b
            row={**rec,'source_sha256':hashlib.sha256(a).hexdigest(),'final_sha256':hashlib.sha256(b).hexdigest(),'changed':changed}
            if changed or rec['path'] in ['/ARC/PL00_U.ARC;1','/ARC/PL01_U.ARC;1','/ARC/PL02_U.ARC;1']:
                name=rec['path'].split('/')[-1].split(';')[0];(resources/name).write_bytes(b);row['exported']=name
                if name.endswith('.ARC'):
                    try:row['entries']=psx_arc(b)
                    except ValueError as e:row['parse_note']='비표준 ARC 구조: 원시 파일 보존';row['parse_error']=str(e)
            records.append(row)
    save(resources/'resource_manifest.json',{'source_sha256':SOURCE_HASH,'final_sha256':FINAL_SHA,'resources':records})
    # Freeze original/source-owned inputs and every save/card before cleanup.
    listed=json.loads((D/'files_before.json').read_text('utf-8'));protected=[]
    for item in listed:
        p=ROOT/item['path'];rel=item['path'];suffix=p.suffix.lower()
        if rel.startswith('character/') or suffix in ['.mcr','.state','.000','.001','.002','.pic'] or rel in ['MegaMan X4.bin','MegaMan X4.cue','Rockman X4.bin','Rockman X4.cue','error_face.png','ePSXe2018.zip'] or rel.startswith('ePSXe2018/') or ('/baseline/' in rel and suffix in ['.bin','.exe','.dll']):
            if not p.is_symlink():protected.append({'path':rel,'size':p.stat().st_size,'sha256':digest(p)})
    save(D/'protected_before.json',protected)
    print(json.dumps({'release':RELEASE,'resources':sum('exported' in x for x in records),'protected_files':len(protected),'recovery_bytes':recovery['archive_bytes']}))
def plan():
    keep={ACCEPTED,ROLLBACK,RELEASE+'/game'};targets=[]
    for p in sorted((ROOT/'out/ver_buki_riko').rglob('*.bin')):
        if p.stat().st_size<500000000:continue
        rel=p.relative_to(ROOT).as_posix();safe_path(ROOT,rel,output=True)
        if p.parent.relative_to(ROOT).as_posix() in keep:continue
        m=json.loads((p.parent/'manifest.json').read_text('utf-8'))
        assert m['source_sha256']==SOURCE_HASH
        info=m['roundtrip'] if p.name=='roundtrip.bin' else m['modified_bin']
        targets.append({'path':rel,'sha256':info['sha256'],'size':p.stat().st_size})
    result={'source_sha256':SOURCE_HASH,'final_sha256':FINAL_SHA,'keep':sorted(keep),'targets':targets,'bytes_before':sum(t['size'] for t in targets)}
    p=D/'compact_plan.json'
    with p.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps({'count':len(targets),'GiB':result['bytes_before']/1024**3,'keep':result['keep']}))
def execute():
    from scripts.emulator_session import working_instances
    assert not working_instances(include_original=True),'Emulator is running; no deletion'
    p=json.loads((D/'compact_plan.json').read_text('utf-8'))
    assert digest(ROOT/RELEASE/'game/shibuki_riko.bin')==FINAL_SHA
    results=[]
    with (D/'compact_results.jsonl').open('x',encoding='utf-8') as log:
        for i,t in enumerate(p['targets'],1):
            assert str(Path(t['path']).parent).replace('\\','/') not in p['keep']
            result=compact(ROOT,t['path'],t['sha256']);results.append(result)
            log.write(json.dumps(result)+'\n');log.flush();os.fsync(log.fileno())
            if i%5==0 or i==len(p['targets']):print(f'{i}/{len(p["targets"])} verified and compacted',flush=True)
    save(D/'compact_summary.json',{'count':len(results),'before':sum(x['original_bytes'] for x in results),'after':sum(x['archive_bytes'] for x in results),'all_restored_hashes_verified':all(x['restored_hash_verified'] for x in results)})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['seed','plan','compact']);a=p.parse_args()
    {'seed':seed,'plan':plan,'compact':execute}[a.action]()
