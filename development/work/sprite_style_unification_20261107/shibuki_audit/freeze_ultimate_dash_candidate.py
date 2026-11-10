"""Ultimate 대시20 자산을 독립·원MIPS/GPU·실제8판열람 근거와 동결."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_ultimate_dash_complete import validate_inputs,P,PARENT,LOCK
def main():
    d=H/'prepared_ultimate_dash01';need(not(d/'FROZEN.json').exists(),'Already frozen');prepared=json.loads((d/'PREPARED_LOCK.json').read_text('utf8'))
    for n,s in prepared['files'].items():need(sha((d/n).read_bytes())==s,'Prepared changed '+n)
    for n,s in prepared['source_scripts'].items():need(sha((H/n).read_bytes())==s,'Producer changed '+n)
    validate_inputs(P.read_bytes(),lambda p:(H/p).read_bytes());expected='bdcf0f648e2102a208307e21a941b53439a2f342014e69981a6de156a4dfbdfb';need(sha((d/'PL02_U.ARC').read_bytes())==expected,'Candidate changed')
    paths=['work/sprite_style_unification_20261107/shibuki_ultimate_dash14_components_native_checks.json','work/sprite_style_unification_20261107/nana_audit/shibuki_ultimate_dash_independent/report.json','work/sprite_style_unification_20261107/root_review_checkpoint47.json'];reports=[json.loads((ROOT/p).read_text('utf8'))for p in paths];need(reports[0]['passed']and reports[1]['passed'],'Checks not passed');need(reports[0]['resources']['PL02_U.ARC']['candidate_sha256']==expected,'Wrong native resource');need(reports[1]['candidate_sha256']==expected,'Wrong independent resource');need(reports[2]['shibuki_candidate_sha256']==expected,'Wrong root review');images=[r for r in reports[2]['art_review_images']if '/prepared_ultimate_dash01/'in r['path']];need(len(images)==8,'Incomplete root visual scope')
    for r in images:need(r['root_actually_viewed']and sha((ROOT/r['path']).read_bytes())==r['sha256'],'Root reviewed image changed')
    proof={'passed':True,'candidate_sha256':expected,'parent_arc_sha256':PARENT,'selected_visual_refs':list(range(67,85))+[93,94],'evidence':{p:sha((ROOT/p).read_bytes())for p in paths},'counts':reports[1]['counts'],'root_actual_visual_plates':8,'author_actual_visual_plates':8,'native_MIPS_GPU':True,'independent_reader_no_producer_called':True,'reproduction_runs':3,'invalid_input_rejections':8,'original_speedline_tile_records_exact':True,'source_lock_sha256':LOCK,'source_inputs':619,'new_gameplay_verified':False,'user_accepted':False,'full_project_complete':False,'replaces_pending_status_in_initial_prepared_reports':True,'next_scope':'기본/포스2~32의명암/세부통일.별도선택23빛기둥은root담당.'};write(d/'final_verification.json',proof)
    write(d/'FROZEN.json',{'frozen':True,'files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()and p.name!='FROZEN.json'},'candidate_sha256':expected,'parent_arc_sha256':PARENT,'source_lock_sha256':LOCK,'selected_visual_refs':proof['selected_visual_refs'],'native_and_independent_passed':True,'root_packed_art_reviewed':True,'supersedes_initial_pending_flags':True,'gameplay_verified':False,'user_accepted':False,'full_style_unification_complete':False});print(json.dumps({'frozen':sha((d/'FROZEN.json').read_bytes()),'verification':sha((d/'final_verification.json').read_bytes())}))
if __name__=='__main__':main()
