"""HUD 마감 수정의 F3 시험/활성 포인터 적용. 게임 진행과 이전 자료를 보존한다."""
import argparse,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.hud_frame_fix import SOURCES,WORK,require
FINAL={'ver_buki_riko':'d426ac48b7e8efa7e3e5b879d391efab89fe19993d22b7cb98ae2c08eaff85fd',
       'ver_rin_nana':'2c3cf873615cab8c84fd7a5dc8a6260d95e6bea26b84de5c87d08651e6ce53dc'}
OLD_STATE='57977106f9bf2a8fae08834c94225fdcdf477d895e82256510e7a745f5259440'
NEW_STATE='43a5eda05884a844154383ad1c86efaa20ddfc11d01e17d50b431b84cae17aa5'
CLONE=WORK/'checkpoint/nana_final_v1/SLUS_005.61.000'
LIVE=ROOT/'work/overhaul_20261105/hud_frame_followup/live_progress'
ACTIVE=ROOT/'work/ver_rin_nana/emulator/sstates/SLUS_005.61.000'
BUILD_FOLDER='hud_frame_fix_20261105_v1'
RUNTIME_SCOPE='Nana actual HUD; all six resources and 540 digit/frame combinations independently checked'

def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
def trial(session):
    session=session.resolve();require(session.is_relative_to(ROOT/'work/ver_rin_nana/emulator_sessions'),'Unexpected session')
    rec=json.loads((session/'session.local.json').read_text('utf8'))
    require(rec['bin_sha256']==FINAL['ver_rin_nana']and digest(Path(rec['cue']).with_suffix('.bin'))==FINAL['ver_rin_nana'],'Unexpected mounted BIN')
    require(digest(ACTIVE)==OLD_STATE and digest(CLONE)==NEW_STATE,'Unexpected user/clone F1')
    dest=WORK/'application'
    if dest.exists():
        require(not(dest/'trial.json').exists()and not(dest/'applied.json').exists(),'Trial already completed')
        for p in(ACTIVE,ACTIVE.with_suffix('.000.pic')):require(digest(p)==digest(dest/p.name),'Interrupted trial backup differs')
    else:
        dest.mkdir()
        for p in(ACTIVE,ACTIVE.with_suffix('.000.pic')):shutil.copyfile(p,dest/p.name)
    cards=[]
    for project in SOURCES:
        settings=ROOT/'projects'/project
        for name in('project.json','current_build.json'):
            p=settings/name;target=dest/project;target.mkdir(exist_ok=True);shutil.copyfile(p,target/name)
        emulator=ROOT/'work/ver_rin_nana/emulator'if project=='ver_rin_nana'else ROOT/'work/ver_buki_riko/baseline/20261023T054951214649Z/emulator'
        for p in(emulator/'memcards').glob('*.mcr'):cards.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=digest(p)))
    write(dest/'cards.json',cards);events=[]
    try:
        shutil.copyfile(CLONE,ACTIVE);shutil.copyfile(LIVE/'SLUS_005.61.000.pic',ACTIVE.with_suffix('.000.pic'))
        for scan in('0x3d','0x35'):
            result=subprocess.run([sys.executable,str(ROOT/'scripts/korean_runtime_control.py'),'--project','ver_rin_nana','key','--session',str(session),'--scan',scan],capture_output=True,text=True,check=True)
            events.append(json.loads(result.stdout));time.sleep(.7)
    finally:
        for p in(ACTIVE,ACTIVE.with_suffix('.000.pic')):shutil.copyfile(dest/p.name,p)
        require(digest(ACTIVE)==OLD_STATE,'User F1 restore failed')
    write(dest/'trial.json',dict(session=session.relative_to(ROOT).as_posix(),clone_sha256=NEW_STATE,original_F1_restored=True,events=events))
    print(json.dumps(events))

def activate(session):
    dest=WORK/'application';require(not(dest/'applied.json').exists(),'Already applied')
    require(json.loads((dest/'runtime.json').read_text('utf8'))['passed'],'Actual HUD verification required')
    require(digest(ACTIVE)==OLD_STATE and digest(CLONE)==NEW_STATE,'User F1 changed')
    for card in json.loads((dest/'cards.json').read_text('utf8')):require(digest(ROOT/card['path'])==card['sha256'],'User memory card changed')
    prepared=[]
    for project,(stem,old_sha)in SOURCES.items():
        folder=ROOT/'projects'/project;build=ROOT/'out'/project/BUILD_FOLDER
        require(digest(build/(stem+'.bin'))==FINAL[project],'Final BIN differs')
        for name in('project.json','current_build.json'):require(digest(folder/name)==digest(dest/project/name),'User pointer changed')
        current=json.loads((folder/'current_build.json').read_text('utf8'));require(current['sha256']==old_sha,'Unexpected active build')
        current.update(build=build.relative_to(ROOT).as_posix(),cue=(build/(stem+'.cue')).relative_to(ROOT).as_posix(),sha256=FINAL[project],
            task='hud_frame_fix',stage='HUD_FRAME_REVIEW',user_accepted=False,hud_frame_fix_report='docs/HUD_FRAME_FIX.md',
            runtime_verification_scope=RUNTIME_SCOPE)
        if project=='ver_rin_nana':current.update(current_session=session.as_posix(),current_runtime_state='HUD_review_at_preserved_user_position',active_checkpoint_sha256=NEW_STATE,original_checkpoint=(LIVE/'SLUS_005.61.000').relative_to(ROOT).as_posix(),original_checkpoint_sha256=digest(LIVE/'SLUS_005.61.000'))
        settings=json.loads((folder/'project.json').read_text('utf8'));settings.update(active_task='hud_frame_fix',active_substage='HUD_FRAME_REVIEW',latest_integrated_build=build.relative_to(ROOT).as_posix(),latest_integrated_bin_sha256=FINAL[project])
        prepared.append((folder,current,settings))
    shutil.copyfile(CLONE,ACTIVE);shutil.copyfile(LIVE/'SLUS_005.61.000.pic',ACTIVE.with_suffix('.000.pic'))
    require(digest(ACTIVE)==NEW_STATE,'Installed F1 differs')
    for folder,current,settings in prepared:write(folder/'current_build.json',current);write(folder/'project.json',settings)
    write(dest/'applied.json',dict(final_builds=FINAL,checkpoint_sha256=NEW_STATE,cards_preserved=True,original_games_written=False,previous_F1_backed_up=True))
    print(json.dumps({'applied':FINAL,'checkpoint_sha256':NEW_STATE}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['trial','activate']);p.add_argument('--session',type=Path,required=True);a=p.parse_args()
    (trial if a.action=='trial'else activate)(a.session)
