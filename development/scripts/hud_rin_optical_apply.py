"""린 정렬 수정본을 다음 실행 대상으로 연결하며 현재 나나 실행/저장을 보존한다."""
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.hud_frame_fix import require

WORK=ROOT/'work/hud_frame_fix_20261105/rin_optical_v9'
OLD='2ed8c388fafe4122aee301bf932632f1fef4ca80fff9cb8c93ea93ffc99bc29f'
NEW='8b70dbca936c2ad4d72eade207cf44f9095fb9ae05beb4e2e4943a7ba6e19768'


def write(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def main():
    require(json.loads((WORK/'independent.json').read_text('utf8'))['passed'],'Independent verification required')
    runtime=json.loads((WORK/'runtime.json').read_text('utf8'))
    require(runtime['passed'] and runtime['mounted_bin_sha256']==NEW,'Actual Rin verification required')
    folder=ROOT/'projects/ver_rin_nana'
    current=json.loads((folder/'current_build.json').read_text('utf8'))
    settings=json.loads((folder/'project.json').read_text('utf8'))
    require(current['sha256']==OLD and settings['latest_integrated_bin_sha256']==OLD,'Current project changed')
    build=ROOT/'out/ver_rin_nana/hud_rin_optical_20261105_v9'
    require(digest(build/'rin_nana.bin')==NEW,'Final BIN differs')
    require(digest((ROOT/current['cue']).with_suffix('.bin'))==OLD,'Source BIN differs')
    dest=WORK/'application';require(not dest.exists(),'Already applied or unexpected application directory')
    protected=[ROOT/'projects/ver_buki_riko/current_build.json',ROOT/'projects/ver_buki_riko/project.json']
    for emulator in (ROOT/'work/ver_rin_nana/emulator',ROOT/'work/ver_buki_riko/baseline/20261023T054951214649Z/emulator'):
        protected.extend((emulator/'memcards').glob('*.mcr'))
        protected.extend((emulator/'sstates').glob('*'))
    protected=[p for p in protected if p.is_file()]
    hashes={p.relative_to(ROOT).as_posix():digest(p) for p in protected}
    dest.mkdir()
    for name in ('current_build.json','project.json'):
        shutil.copyfile(folder/name,dest/name)
    current.update(build=build.relative_to(ROOT).as_posix(),cue=(build/'rin_nana.cue').relative_to(ROOT).as_posix(),
        sha256=NEW,task='rin_hud_alignment',stage='HUD_FRAME_REVIEW',user_accepted=False,
        running_bin_sha256=None,current_runtime_state='Previous Nana process was found closed during isolated verification; protected F1 and memory cards retained; next launch uses v9',
        runtime_verification_scope='Rin v9 isolated fresh-game HUD; 9 shifted frames and 90 digit combinations; Nana PL00/PL02 byte-identical',
        rin_optical_alignment_report='docs/RIN_HUD_OPTICAL_ALIGNMENT.md')
    settings.update(active_task='rin_hud_alignment',active_substage='HUD_FRAME_REVIEW',
        latest_integrated_build=build.relative_to(ROOT).as_posix(),latest_integrated_bin_sha256=NEW)
    write(folder/'current_build.json',current);write(folder/'project.json',settings)
    for p,h in hashes.items():require(digest(ROOT/p)==h,'Protected state changed: '+p)
    write(dest/'applied.json',dict(passed=True,source_sha256=OLD,target_sha256=NEW,
        protected_hashes=hashes,first_project_unchanged=True,F1_written=False,memory_cards_written=False,
        current_nana_restarted=False,rin_runtime_verified=True))
    print(json.dumps({'applied':NEW,'protected_files':len(hashes),'saved_nana_progress_preserved':True,'previous_nana_process_closed':True}))


if __name__=='__main__':main()
