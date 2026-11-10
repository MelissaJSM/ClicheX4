"""통합 수정 제안들을 기준 BIN에 대조·병합해 새 작업용 BIN/CUE를 만든다."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.overhaul_dialogue import BASES
from scripts.project import digest,working_cue
from scripts.prepare_rin_common import read_disc
from scripts.discover_inputs import sha256
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks
from src.psx_xa_audio import validate_audio_sector

def checked_path(relative,allowed):
    p=(ROOT/relative).resolve()
    if not any(p.is_relative_to(ROOT/a) for a in allowed):raise ValueError('Path outside approved workspace area')
    return p

def merge_bytes(original,current,proposal,resource,owners,owner):
    if len(original)!=len(current) or len(original)!=len(proposal):raise ValueError('Resource length changed')
    changed=[]
    for i,(a,b) in enumerate(zip(original,proposal)):
        if a==b:continue
        if current[i]!=a and current[i]!=b:
            raise ValueError(f'Conflicting patches: {resource}+{i:#x}: {owners.get(i)} / {owner}')
        current[i]=b;owners[i]=owner;changed.append(i)
    return changed

def integrate(project,proposals,output,raw_patches=()):
    source_path,source_sha,_=BASES[project];source=ROOT/source_path
    output=output.resolve()
    if not output.is_relative_to(ROOT/'out'/project) or output.exists():raise ValueError('Fresh variant output directory required')
    if digest(source)!=source_sha:raise ValueError('Unsupported baseline BIN')
    parsed=[];names=set()
    for p in proposals:
        p=p.resolve()
        if not p.is_relative_to(ROOT/'work/overhaul_20261105'):raise ValueError('Unexpected patch location')
        j=json.loads(p.read_text('utf8'))
        if j['project']!=project or j['baseline']!=source_path or j['baseline_sha256']!=source_sha:raise ValueError('Mixed variant or baseline')
        names.update(j['files']);parsed.append((p,j))
    old,records=read_disc(source,sorted(names));merged={n:bytearray(a) for n,a in old.items()};owners={n:{} for n in names};contributions=[]
    for p,j in parsed:
        for name,f in j['files'].items():
            record=f.get('record',records[name]);new=checked_path(f['path'],['work/overhaul_20261105']).read_bytes()
            if sha256(old[name])!=f['before'] or sha256(new)!=f['after'] or len(new)!=f['size']:raise ValueError('Patch resource identity mismatch')
            if any(record[k]!=records[name][k] for k in ('lba','size','path')):raise ValueError('Disc record changed')
            changed=merge_bytes(old[name],merged[name],new,name,owners[name],p.relative_to(ROOT).as_posix())
            contributions.append(dict(proposal=p.relative_to(ROOT).as_posix(),resource=name,changed_bytes=len(changed)))
    raw={};raw_sources=[]
    with source.open('rb') as stream:
        for p in raw_patches:
            p=p.resolve()
            if not p.is_relative_to(ROOT/'work/overhaul_20261105'):raise ValueError('Unexpected raw patch location')
            j=json.loads(p.read_text('utf8'))
            if j['project']!=project or j['baseline_sha256']!=source_sha:raise ValueError('Raw patch baseline differs')
            rows=j.get('sectors',j.get('raw_sectors'))
            if not isinstance(rows,list) or not rows:raise ValueError('Raw patch has no sectors')
            for row in rows:
                lba=row['lba']
                if not 226570<=lba<226570+1544 or (lba-226570)%8:raise ValueError('Raw patch escaped title voice channel')
                data=checked_path(row['path'],['work/overhaul_20261105']).read_bytes();stream.seek(lba*2352);before=stream.read(2352)
                if sha256(before)!=row['before_sha256'] or sha256(data)!=row['after_sha256']:raise ValueError('Raw sector identity mismatch')
                validate_audio_sector(before);validate_audio_sector(data,allow_absent_edc=False)
                if data[:24]!=before[:24] or data[2328:2348]!=before[2328:2348]:raise ValueError('XA header/padding changed')
                if lba in raw and raw[lba]!=data:raise ValueError('Conflicting raw patch')
                if data!=before:raw[lba]=data
            raw_sources.append(p.relative_to(ROOT).as_posix())
    changes=[]
    for name,data in merged.items():
        if data!=old[name]:changes.append(({**records[name],'sha256':sha256(old[name])},bytes(data)))
    # Exact resource ranges must stay separate from any Form2 audio edits.
    arc_lbas={i for rec,_ in changes for i in range(rec['lba'],rec['lba']+(rec['size']+2047)//2048)}
    if arc_lbas&raw.keys():raise ValueError('Resource/raw sector overlap')
    output.mkdir(parents=True);stem='shibuki_riko' if project=='ver_buki_riko' else 'rin_nana';target=output/(stem+'.bin')
    result=write_archive_copies(source,target,changes,source_sha)
    arc_changes={r['lba'] for r in result['changed_sectors']}
    if raw:
        with target.open('r+b') as stream:
            for lba,data in sorted(raw.items()):stream.seek(lba*2352);stream.write(data)
    changed_lbas=arc_changes|raw.keys();checked=0
    with source.open('rb') as a,target.open('rb') as b:
        while True:
            old_sector,new_sector=a.read(2352),b.read(2352)
            if not old_sector:
                if new_sector:raise ValueError('Output size changed')
                break
            if (old_sector!=new_sector)!=(checked in changed_lbas):raise ValueError('Undeclared sector change')
            if checked in raw:
                if new_sector!=raw[checked]:raise ValueError('XA readback differs')
                validate_audio_sector(new_sector,allow_absent_edc=False)
            elif checked in arc_changes:validate_checks(new_sector)
            checked+=1
    actual,_=read_disc(target,sorted(merged))
    if any(actual[n]!=bytes(v) for n,v in merged.items()):raise ValueError('Resource readback differs')
    if digest(source)!=source_sha:raise ValueError('Baseline modified')
    result['sha256']=digest(target);result['raw_audio_changed_lbas']=sorted(raw)
    cue=source.with_suffix('.cue');(output/(stem+'.cue')).write_text(working_cue(cue.read_text('ascii'),stem+'.bin'),'ascii')
    assets=output/'resources';assets.mkdir()
    for name,data in merged.items():(assets/name).write_bytes(data)
    parent=json.loads((source.parent/'manifest.json').read_text('utf8'))
    report=dict(project=project,task='integration_overhaul',kind='issues_20261105_integration',stage='EXPANSION',
        parent=source.parent.relative_to(ROOT).as_posix(),parent_sha256=source_sha,
        source_sha256='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b',modified_bin=result,
        changed_resources={n:dict(before=sha256(old[n]),after=sha256(bytes(v)),size=len(v)) for n,v in merged.items() if bytes(v)!=old[n]},
        contributions=contributions,raw_audio_proposals=raw_sources,all_disc_sectors_compared=checked,
        all_changes_declared=True,edc_ecc_verified=True,resource_readback_verified=True,baseline_preserved=True,
        original_timing_and_collision_code_preserved=True,runtime_verified=False,user_accepted=False)
    manifest={**parent,**report}
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf8')
    (output/'integration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
    print(json.dumps({'project':project,'output':str(output),'sha256':result['sha256'],'resources':len(changes),'arc_sectors':len(arc_changes),'audio_sectors':len(raw),'sectors_checked':checked}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project',choices=BASES,required=True);p.add_argument('--proposal',type=Path,action='append',required=True);p.add_argument('--raw-patch',type=Path,action='append',default=[]);p.add_argument('--output',type=Path,required=True);a=p.parse_args();integrate(a.project,a.proposal,a.output,a.raw_patch)
