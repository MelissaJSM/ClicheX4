"""검증된 부모 빌드 위에 Shibuki 동작 ARC를 넣고 전체 디스크 차이를 검사한다."""
import argparse,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import write_json,working_cue,validate_bin,inspect_references,load_project
from scripts.discover_inputs import sha256
from src.psx_disc import write_archive_copy
from src.psx_sector import validate_checks

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--recipe',type=Path,required=True);args=parser.parse_args()
    path=args.recipe.resolve()
    recipe=json.loads(path.read_text(encoding='utf-8'))
    scopes={'base_run_16_with_shared_shoot_references':'shibuki_run','base_standing_buster_4':'shibuki_standing','base_air_22':'shibuki_air','base_dash_18':'shibuki_dash','base_wall_12':'shibuki_wall','base_hurt_9':'shibuki_hurt'}
    scopes['base_ladder_14']='shibuki_ladder'
    scopes['base_low_hp_6']='shibuki_low_hp'
    scopes['base_remaining_105']='shibuki_remaining'
    scopes['base_weapon_body_palettes']='shibuki_weapon_palette'
    scopes['base_special_style_7']='shibuki_special_style'
    scopes['base_arrival_victory_style_11']='shibuki_arrival_victory_style'
    scopes['fourth_armor_idle_6']='shibuki_fourth_idle'
    scopes['fourth_armor_run_32']='shibuki_fourth_run'
    scopes['fourth_armor_remaining_189']='shibuki_fourth_remaining'
    scopes['fourth_armor_hover_alignment_4']='shibuki_fourth_hover_alignment'
    group=scopes.get(recipe['scope'])
    expected_task='fourth_armor_shibuki' if recipe['scope'].startswith('fourth_armor_') else 'x_shibuki'
    if recipe['task']!=expected_task or group is None:raise ValueError('Unsupported recipe')
    if not path.is_relative_to(ROOT/'work/ver_buki_riko'/group):raise ValueError('Expected isolated sprite recipe')
    cfg=json.loads((ROOT/'config/shibuki_x_us.json').read_text(encoding='utf-8'))
    if recipe['original_arc_sha256']!=cfg['archive']['sha256']:raise ValueError('Unsupported original ARC')
    parentdir=(ROOT/recipe['parent_build']).resolve()
    if not parentdir.is_relative_to(ROOT/'out/ver_buki_riko'):raise ValueError('Invalid parent build')
    parent=parentdir/'shibuki_riko.bin';pm=json.loads((parentdir/'manifest.json').read_text(encoding='utf-8'))
    if pm['modified_bin']['sha256']!=recipe['parent_bin_sha256'] or sha256((parentdir/'modified.arc').read_bytes())!=recipe['parent_arc_sha256']:raise ValueError('Parent changed')
    arc=(path.parent/'modified.arc').read_bytes()
    if sha256(arc)!=recipe['modified_arc_sha256']:raise ValueError('Prepared ARC changed')
    project=load_project(ROOT,'ver_buki_riko');inspect_references(ROOT,project)
    validate_bin(ROOT/project['source_bin'],cfg['source_sha256']);validate_bin(parent,recipe['parent_bin_sha256'])
    out=ROOT/'out/ver_buki_riko'/(group+'_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(exist_ok=False)
    parent_archive={**cfg['archive'],'sha256':recipe['parent_arc_sha256']}
    target=out/'shibuki_riko.bin';result=write_archive_copy(parent,target,parent_archive,arc,recipe['parent_bin_sha256'])
    (out/'shibuki_riko.cue').write_text(working_cue((parentdir/'shibuki_riko.cue').read_text(encoding='ascii'),'shibuki_riko.bin'),encoding='ascii')
    (out/'modified.arc').write_bytes(arc);shutil.copyfile(path,out/'recipe.json')
    expected={r['lba'] for r in result['changed_sectors']};actual=[]
    with parent.open('rb') as a,target.open('rb') as b:
        for sector in range(result['size']//2352):
            before,after=a.read(2352),b.read(2352)
            if before==after:continue
            if sector not in expected or before[:24]!=after[:24]:raise ValueError('Unexpected raw sector difference')
            validate_checks(after);actual.append(sector);start=(sector-cfg['archive']['lba'])*2048
            if after[24:2072]!=arc[start:start+2048]:raise ValueError('Sector differs from expected ARC')
    if set(actual)!=expected:raise ValueError('Sector accounting mismatch')
    validate_bin(parent,recipe['parent_bin_sha256']);validate_bin(ROOT/project['source_bin'],cfg['source_sha256']);inspect_references(ROOT,project)
    manifest={'project':'ver_buki_riko','task':recipe['task'],'stage':'EXPANSION','kind':group+'_candidate',
        'parent_build':recipe['parent_build'],'parent_bin_sha256':recipe['parent_bin_sha256'],'source_sha256':cfg['source_sha256'],
        'modified_bin':result,'modified_archive_sha256':sha256(arc),'archive':cfg['archive'],'recipe':str(path.relative_to(ROOT)),
        'riko_preserved_byte_for_byte':True,'only_X_archive_and_checks_changed':True,'full_disc_sectors_compared':result['size']//2352,
        'idle_frames_preserved':True,'run_frames_preserved':recipe.get('run_frames_preserved',False),'runtime_verified':False,'new_animation_user_review_pending':True,
        'shooting_body_uses_same_run_pose':recipe['shooting_body_uses_same_run_pose'],'shooting_arm_art_pending':recipe['shooting_arm_art_pending'],'unedited_X_actions_recolored':True,'armor_not_implemented':True,'text_not_changed':True}
    if recipe['scope'] in ('base_special_style_7','base_arrival_victory_style_11'):manifest.update(unedited_X_actions_recolored=False,base_sprite_references_applied=228,style_revision_frames=recipe['edited_frame_references'])
    if recipe.get('resources_relocated_within_bank'):manifest.update(resources_relocated_within_bank=True,repack=recipe['repack'],archive_size_and_lba_preserved=True,repack_approval=recipe['approval'])
    if recipe['scope']=='fourth_armor_idle_6':manifest.update(armor_not_implemented=False,armor_full_animation_complete=False,armor_idle_frames=recipe['edited_frame_references'],base_sprite_references_preserved=228,base_idle_rasters_preserved=True,unedited_X_actions_recolored=False,armor_palette_rows=recipe['palette_rows'],unimplemented_armor_frames_use_original_bitmap_with_candidate_palette=True,resources_relocated_within_bank=recipe['resources_relocated_within_bank'],archive_size_and_lba_preserved=True)
    if recipe['scope']=='fourth_armor_run_32':manifest.update(armor_not_implemented=False,armor_full_animation_complete=False,armor_idle_frames=pm['armor_idle_frames'],armor_frames_cumulative=recipe['armor_frames_cumulative'],base_sprite_references_preserved=228,base_idle_rasters_preserved=True,unedited_X_actions_recolored=False,armor_palette_rows=pm['armor_palette_rows'],unimplemented_armor_frames_use_original_bitmap_with_candidate_palette=True,resources_relocated_within_bank=recipe['resources_relocated_within_bank'],archive_size_and_lba_preserved=True)
    if recipe['scope']=='fourth_armor_remaining_189':manifest.update(armor_not_implemented=False,armor_full_animation_complete=recipe['armor_full_animation_complete'],armor_idle_frames=pm['armor_idle_frames'],armor_frames_cumulative=recipe['armor_frames_cumulative'],base_sprite_references_preserved=228,base_idle_rasters_preserved=True,unedited_X_actions_recolored=False,armor_palette_rows=pm['armor_palette_rows'],unimplemented_armor_frames_use_original_bitmap_with_candidate_palette=False,resources_relocated_within_bank=recipe['resources_relocated_within_bank'],archive_size_and_lba_preserved=True)
    if recipe['scope']=='fourth_armor_hover_alignment_4':manifest.update(armor_not_implemented=False,armor_full_animation_complete=False,armor_idle_frames=pm['armor_idle_frames'],armor_frames_cumulative=recipe['armor_frames_cumulative'],unedited_X_actions_recolored=False,armor_palette_rows=pm['armor_palette_rows'],unimplemented_armor_frames_use_original_bitmap_with_candidate_palette=False,resources_relocated_within_bank=False,archive_size_and_lba_preserved=True,hover_alignment_frames=recipe['edited_frame_references'],upper_body_rasters_preserved=True,other_frames_and_armor_layers_preserved=True,graphics_scope_complete=True)
    write_json(out/'manifest.json',manifest);print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':actual,'full_disc_verified':True}))

if __name__=='__main__':main()
