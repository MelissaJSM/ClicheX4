"""Activate verified review discs; preserve accepted discs and user saves."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import digest,write
from scripts.c01_audio_build import require
import scripts.emulator_session as session_control

def main():
    w=ROOT/'work/sprite_consistency_20261105';app=w/'application'
    require(not app.exists(),'Application already recorded')
    protection=json.loads((w/'protection_before.json').read_text('utf8'))
    protected={p:{'sha256':digest(ROOT/p),'size':(ROOT/p).stat().st_size} for p in protection}
    require(protected==protection,'Protected original/reference/save file changed; inspect before activation')
    gallery=w/'zero/gallery_validation/verification.json';g=json.loads(gallery.read_text('utf8'))
    require(g['passed'] and digest(ROOT/'out/sprite_consistency_20261105/index.html')==g['html_sha256'],'Latest gallery was not verified')
    require(json.loads((w/'build_guard_checks.json').read_text('utf8'))['passed'],'Build guards not checked')
    rows=[]
    for mode in ('ver_buki_riko','ver_rin_nana'):
        plan=json.loads((w/(mode+'_plan.json')).read_text('utf8'));native=json.loads((w/(mode+'_plan_native_checks.json')).read_text('utf8'))
        require(native['passed'],'Native verification failed')
        for n,q in native['resources'].items():require(q['candidate_sha256']==plan['resources'][n]['after'],'Stale native proof')
        folder=ROOT/plan['output'];manifest=json.loads((folder/'manifest.json').read_text('utf8'));stem=Path(plan['source_bin']).stem
        require(digest(folder/(stem+'.bin'))==manifest['modified_bin']['sha256'],'Build hash mismatch')
        for n,q in plan['resources'].items():require(manifest['resources'][n]['after']==q['after'],'Stale build resource')
        require(digest(ROOT/plan['source_bin'])==plan['source_sha256'],'Accepted parent changed')
        pp=ROOT/'projects'/mode/'current_build.json';pj=pp.with_name('project.json');pointer=json.loads(pp.read_text('utf8'));project=json.loads(pj.read_text('utf8'))
        require(pointer['sha256']==plan['source_sha256'],'Concurrent pointer change')
        rows.append((mode,plan,folder,manifest,stem,pp,pj,pointer,project))
    app.mkdir(parents=True)
    runtime=ROOT/'work/ver_rin_nana/emulator_sessions/20261105T102945242982Z';r=json.loads((runtime/'session.local.json').read_text('utf8'))
    session_control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
    live=r['pid'] in session_control.working_instances()
    applied=[]
    for mode,plan,folder,manifest,stem,pp,pj,pointer,project in rows:
        back=app/mode;back.mkdir();(back/'current_build.json').write_bytes(pp.read_bytes());(back/'project.json').write_bytes(pj.read_bytes())
        pointer.update(task='sprite_consistency_review',stage='SPRITE_CONSISTENCY_APPLIED_REVIEW',build=plan['output'],cue=f"{plan['output']}/{stem}.cue",sha256=manifest['modified_bin']['sha256'],
          previous_pointer=(back/'current_build.json').relative_to(ROOT).as_posix(),status_report='docs/SPRITE_CONSISTENCY_REVIEW.md',art_review='docs/SPRITE_CONSISTENCY_REVIEW.md',
          sprite_collection='out/sprite_consistency_20261105/index.html',sprite_consistency_static_verified=True,sprite_consistency_runtime_verified=False,sprite_consistency_user_accepted=False,user_accepted=False,
          runtime_verification_scope='Nana fresh process intro FMV observed read-only; no changed player sprite runtime verification',
          next_action='Review changed sprites in gallery and fresh-disc gameplay; old F3 caches are not proof of this build',
          current_session=runtime.relative_to(ROOT).as_posix() if mode=='ver_rin_nana' and live else None,
          running_bin_sha256=manifest['modified_bin']['sha256'] if mode=='ver_rin_nana' and live else None,
          current_runtime_state='Review build intro FMV observed; no keys/F1/F3 sent' if mode=='ver_rin_nana' and live else 'No running session observed')
        project.update(active_task='sprite_consistency_review',active_substage='SPRITE_CONSISTENCY_APPLIED_REVIEW',latest_integrated_build=plan['output'],latest_integrated_bin_sha256=manifest['modified_bin']['sha256'],latest_sprite_collection='out/sprite_consistency_20261105')
        write(pp,pointer);write(pj,project)
        manifest['active_pointer_changed']=True;manifest['application_record']=(app/'applied.json').relative_to(ROOT).as_posix();write(folder/'manifest.json',manifest)
        applied.append({'project':mode,'cue':pointer['cue'],'sha256':pointer['sha256'],'current_session':pointer['current_session']})
    write(app/'applied.json',{'applied':applied,'protected_files':protected,'protected_file_count':len(protected),'save_data_written':False,'emulator_inputs_sent':False,'game_code_changed':False,'runtime_all_sprites_verified':False,'user_accepted':False})
    print(json.dumps({'applied':applied,'protected_files':len(protected)}))

if __name__=='__main__':main()
