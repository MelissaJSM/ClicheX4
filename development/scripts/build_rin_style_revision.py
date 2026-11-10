"""현재 대기를 고정한 린 전체 질감 수정본을 별도 BIN으로 제작·검증한다."""
import argparse,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.assemble_rin_style_revision import prepare,DEST,OUT,PARENT
from scripts.project import load_project,inspect_references,digest,working_cue
from scripts.build_rin_idle import sha
from src.psx_disc import write_archive_copy
from src.psx_sector import validate_checks

def main():
    global OUT,DEST
    ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,default=OUT);args=ap.parse_args();OUT=args.work.resolve();DEST=OUT/'assembled'
    project=load_project(ROOT,'ver_rin_nana');inspect_references(ROOT,project)
    pm=json.loads((PARENT/'manifest.json').read_text('utf-8'))
    if digest(PARENT/'rin_nana.bin')!=pm['modified_bin']['sha256']:raise ValueError('Parent BIN changed')
    arc,report=prepare(OUT);again,_=prepare(OUT)
    if arc!=again:raise ValueError('Repeated assembly differs')
    out=ROOT/'out/ver_rin_nana'/('rin_style_revision_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    profile=json.loads((ROOT/'config/ps1_us_slus00561.json').read_text('utf-8'));source=ROOT/project['source_bin'];target=out/'rin_nana.bin'
    result=write_archive_copy(source,target,profile['zero_archive'],arc,project['source_sha256'])
    (out/'rin_nana.cue').write_text(working_cue((ROOT/project['source_cue']).read_text('utf-8-sig'),'rin_nana.bin'),'ascii',newline='')
    (out/'modified.arc').write_bytes(arc)
    changed={v['lba'] for v in result['changed_sectors']};rec=profile['zero_archive'];readback=bytearray();count=0
    with source.open('rb') as a,target.open('rb') as b:
        while True:
            x=a.read(2352);y=b.read(2352)
            if not x:
                if y:raise ValueError('Output longer than source')
                break
            if len(x)!=len(y) or (x!=y)!=(count in changed):raise ValueError('Unexpected disc difference')
            if count in changed:validate_checks(y)
            if rec['lba']<=count<rec['lba']+(rec['size']+2047)//2048:readback.extend(y[24:2072])
            count+=1
    if readback[:len(arc)]!=arc:raise ValueError('BIN archive readback differs')
    report.update({'repeat_arc_identical':True,'all_disc_sectors_compared':count,'changed_sectors':len(changed),'edc_ecc_checked':True,'reextracted_arc_equal':True})
    manifest={'project':'ver_rin_nana','task':'zero_rin','kind':'all_motion_idle_master_revision','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':pm['modified_bin']['sha256'],'source_sha256':project['source_sha256'],'modified_bin':result,'modified_archive_sha256':sha(arc),'art_recipe':(DEST/'verification.json').relative_to(ROOT).as_posix(),'art_master':(OUT/'master.json').relative_to(ROOT).as_posix(),'verification':report,'cumulative_frames':pm['cumulative_frames'],'cumulative_bank1_frames':pm['cumulative_bank1_frames'],'bank1_frame_inputs':dict(pm['bank1_frame_inputs']),'runtime_verified':False}
    for n in report['body_frames']['1']:
        p=DEST/f'bank1_{n:03d}.png';manifest['bank1_frame_inputs'][str(n)]={'path':str(p),'sha256':digest(p)}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf-8')
    # Check protected user inputs against the preceding handoff, without
    # overwriting cards, states, reference art or the first completed version.
    previous=json.loads((ROOT/'out/ver_rin_nana/rin_ice_20261028T204000812726Z/preservation_handoff.json').read_text('utf-8'))
    checked=[]
    for q in previous['files']:
        actual=digest(ROOT/q['path']);checked.append({'path':q['path'],'expected_sha256':q['expected_sha256'],'actual_sha256':actual,'unchanged':actual==q['expected_sha256']})
    (out/'preservation.json').write_text(json.dumps({'files':checked},ensure_ascii=False,indent=2)+'\n','utf-8')
    if not all(q['unchanged'] for q in checked):raise ValueError('Protected input differs from prior handoff; review before promotion')
    pointer={'project':'ver_rin_nana','task':'zero_rin','build':out.relative_to(ROOT).as_posix(),'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),'sha256':result['sha256'],'frames':pm['cumulative_frames'],'bank1_frames':pm['cumulative_bank1_frames'],'runtime_verified':False}
    (ROOT/'projects/ver_rin_nana/current_build.json').write_text(json.dumps(pointer,indent=2)+'\n','utf-8')
    print(json.dumps({'output':str(out),'sha256':result['sha256'],'revised_refs':sum(map(len,report['body_frames'].values())),'fixed_idle_refs':10,'changed_sectors':len(changed),'protected_files':len(checked)}))

if __name__=='__main__':main()
