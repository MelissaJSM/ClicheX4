"""재현이 확인된 공통 한글/로고 자원을 린 사본 BIN에 적용한다."""
import argparse,json,shutil,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_common import PARENT,PARENT_SHA,DONOR,DONOR_SHA,SOURCE_SHA
from scripts.prepare_hud_emblems import require
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

def build(candidate,reproduced):
    for p in (candidate,reproduced):require(p.resolve().is_relative_to(ROOT/'work/ver_rin_nana'),'Wrong variant path')
    recipe=json.loads((candidate/'proposal.json').read_text('utf8'));again=json.loads((reproduced/'proposal.json').read_text('utf8'))
    require(recipe['kind']=='rin_common_localization' and recipe['parent_sha256']==PARENT_SHA and recipe['donor_sha256']==DONOR_SHA,'Proposal identity differs')
    require(recipe['files']==again['files'],'Independent reproduction differs')
    require((candidate/'native_cpu_verification.json').exists(),'Native CPU verification required')
    preservation=json.loads((PARENT/'preservation.json').read_text('utf8'))
    def protect():
        for q in preservation['files']:require(digest(ROOT/q['path'])==q['expected_sha256'],'Protected input changed '+q['path'])
        require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(DONOR)==DONOR_SHA and digest(ROOT/'MegaMan X4.bin')==SOURCE_SHA,'Protected game changed')
    protect();changes=[]
    with (PARENT/'rin_nana.bin').open('rb') as f:
        d=DiscReader(f,(PARENT/'rin_nana.bin').stat().st_size)
        for name,meta in recipe['files'].items():
            rec=recipe['records'][name];old=d.read(rec['lba'],rec['size']);new=(candidate/name).read_bytes()
            require(sha256(old)==meta['before'] and sha256(new)==meta['after'] and len(new)==len(old),'Resource identity changed')
            require(new==(reproduced/name).read_bytes(),'Resource reproduction differs')
            changes.append(({**rec,'sha256':meta['before']},new))
    out=ROOT/'out/ver_rin_nana'/('rin_common_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    result=write_archive_copies(PARENT/'rin_nana.bin',out/'rin_nana.bin',changes,PARENT_SHA);changed={r['lba'] for r in result['changed_sectors']};count=0
    with (PARENT/'rin_nana.bin').open('rb') as f,(out/'rin_nana.bin').open('rb') as g:
        while True:
            a,b=f.read(2352),g.read(2352)
            if not a:require(not b,'Output grew');break
            require(len(a)==len(b) and (a!=b)==(count in changed),'Undeclared sector difference')
            if count in changed:validate_checks(b)
            count+=1
    with (out/'rin_nana.bin').open('rb') as f:
        d=DiscReader(f,result['size'])
        for rec,data in changes:require(d.read(rec['lba'],rec['size'])==data,'Resource readback differs')
    protect();shutil.copyfile(PARENT/'rin_nana.cue',out/'rin_nana.cue');shutil.copyfile(candidate/'PL01_U.ARC',out/'modified.arc')
    shutil.copytree(candidate,out/'common')
    for folder in ('ui','portrait','hunter','dialogue','pause','weapon_get','hud_theme','life_item','effect_colors'):shutil.copytree(PARENT/folder,out/folder)
    parent=json.loads((PARENT/'manifest.json').read_text('utf8'))
    v={'all_disc_sectors_compared':count,'changed_sectors':len(changed),'reproduced_resources':len(changes),'readback_equal':True,'edc_ecc_checked':True,
       'protected_files':len(preservation['files']),'embedded_static_bodies':parent['verification']['embedded_static_bodies'],'runtime_verified':False,
       'native_cpu_verification':'common/native_cpu_verification.json','resource_proofs':'common/proposal.json','player_combat_and_art_preserved':True}
    manifest={**parent,'kind':'rin_common_localization','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'modified_bin':result,
       'modified_archive_sha256':digest(out/'modified.arc'),'verification':v,'inherited_verification':parent['verification'],'runtime_verified':False,
       'localization_overlay':{'recipe':'common/proposal.json','names':recipe['names'],'mode_label':recipe['mode_label'],'nana_art_produced':False,'voice_policy_changed':False}}
    for name,data in [('manifest.json',manifest),('verification.json',v),('preservation.json',preservation)]:(out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
    pointer={'project':'ver_rin_nana','task':'zero_rin','build':out.relative_to(ROOT).as_posix(),'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),'sha256':result['sha256'],
             'frames':parent['cumulative_frames'],'bank1_frames':parent['cumulative_bank1_frames'],'runtime_verified':False}
    (ROOT/'projects/ver_rin_nana/current_build.json').write_text(json.dumps(pointer,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(changed)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--reproduced',type=Path,required=True);a=p.parse_args();build(a.candidate,a.reproduced)
