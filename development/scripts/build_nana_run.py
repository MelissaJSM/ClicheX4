"""수용 나나 대기판에 이동/사격32참조를 누적하고 전체 디스크 변경을 검사한다."""
import argparse,json,shutil,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_idle_shot import PILOT,write
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks
PARENT=ROOT/'out/ver_rin_nana/nana_idle_shot_20261029T055257544069Z'
PARENT_SHA='02f8c18047c5705ea247a9f880f7c50a5b1866922a2c68c877a497af6962a3a4'
SCOPE='run'
FRAME_IDS=list(range(1,33))
RECIPE_SCOPE='base_run_and_shoot_32'

def configure_scope(scope):
    global PARENT,PARENT_SHA,SCOPE,FRAME_IDS,RECIPE_SCOPE
    if scope=='air':
        PARENT=ROOT/'out/ver_rin_nana/nana_run_icon_20261029T063639488649Z'
        PARENT_SHA='ecc139fdb7e4521bf0f4ad6167f24efc431749881f128378d64f8d203f59f3f2'
        SCOPE='air';FRAME_IDS=list(range(33,55));RECIPE_SCOPE='base_air_22'
    elif scope=='dash':
        PARENT=ROOT/'out/ver_rin_nana/nana_air_20261029T070014731019Z'
        PARENT_SHA='be23eefed6fa5e0257d56429a37d96429a628eac72d9ddacc80166a11e6ed8f3'
        SCOPE='dash';FRAME_IDS=list(range(67,85));RECIPE_SCOPE='base_dash_18'
    elif scope=='wall':
        PARENT=ROOT/'out/ver_rin_nana/nana_dash_20261029T072609070724Z'
        PARENT_SHA='3d0ca518ba91895215069ac4c54867574c7c5b66bc99f0d719078d178c24e6d9'
        SCOPE='wall';FRAME_IDS=list(range(55,67));RECIPE_SCOPE='base_wall_12'
    elif scope=='hurt':
        PARENT=ROOT/'out/ver_rin_nana/nana_wall_20261029T224356693137Z'
        PARENT_SHA='6385e1e5ae99e57601a1e8af784a9e22cb509a2cb07542d2b2b00785bc0ef2ab'
        SCOPE='hurt';FRAME_IDS=list(range(106,115));RECIPE_SCOPE='base_hurt_9'
    elif scope=='fall_legs':
        PARENT=ROOT/'out/ver_rin_nana/nana_hurt_20261029T225358832150Z'
        PARENT_SHA='ad17b9c369636a1aab2695be00b1e4f304b405e6b296741ad6db9418de2e0dd5'
        SCOPE='fall_legs';FRAME_IDS=list(range(43,49));RECIPE_SCOPE='fall_legs_revision_6'
    elif scope=='ladder':
        PARENT=ROOT/'out/ver_rin_nana/nana_fall_legs_20261029T230758381002Z'
        PARENT_SHA='8addc7ebcddc359b8fc828296d684f8909b771df7549bea40f3c8ea16d22adf2'
        SCOPE='ladder';FRAME_IDS=list(range(143,156))+[183];RECIPE_SCOPE='base_ladder_14'
    elif scope=='low_hp':
        PARENT=ROOT/'out/ver_rin_nana/nana_ladder_20261029T232724676396Z'
        PARENT_SHA='a4c100125a08e9ed4715c1cf8d757444f897f6e22e73efd01a8b1fe951da228c'
        SCOPE='low_hp';FRAME_IDS=list(range(120,126));RECIPE_SCOPE='base_low_hp_6'
    elif scope=='arrival':
        PARENT=ROOT/'out/ver_rin_nana/nana_low_hp_20261029T233800161474Z'
        PARENT_SHA='04eb92e3a509ebf34d87ca58145ce48041da18d30d09525c605d10d6d25ff521'
        SCOPE='arrival';FRAME_IDS=list(range(126,143));RECIPE_SCOPE='base_nana_arrival_17'
    elif scope=='victory':
        PARENT=ROOT/'out/ver_rin_nana/nana_arrival_20261029T235340020385Z'
        PARENT_SHA='30e4ee72fc00b3917b754687bb7e1c94d865bc7d583cbe5d70a5c0bc01b35879'
        SCOPE='victory';FRAME_IDS=list(range(156,162))+list(range(204,208));RECIPE_SCOPE='base_nana_victory_return_10'
    elif scope=='special':
        PARENT=ROOT/'out/ver_rin_nana/nana_victory_20261030T002449610350Z'
        PARENT_SHA='a225875d841e211d490b147779431af999315079fb30a8b4e9e6ed47f9b62c20'
        SCOPE='special';FRAME_IDS=[88,89,90,91,97,98,99];RECIPE_SCOPE='base_nana_special_7'
    elif scope=='special_remaining':
        PARENT=ROOT/'out/ver_rin_nana/nana_special_20261030T004646283984Z'
        PARENT_SHA='796238e5366d63d22228fb9995be563d8bebd3437855ae0bb65e5e1dbc2c09cb'
        SCOPE='special_remaining';FRAME_IDS=[95,96,100,101,102,103,104,231,232];RECIPE_SCOPE='base_nana_special_remaining_9'
    elif scope=='air_clone':
        PARENT=ROOT/'out/ver_rin_nana/nana_special_remaining_20261030T010327624138Z'
        PARENT_SHA='1521ce5112d92445c369867e7e62560868be2de32b275d80d00e8d6ff3360eb0'
        SCOPE='air_clone';FRAME_IDS=[93,94,*range(208,213),*range(221,231)];RECIPE_SCOPE='base_nana_air_clone_17'
    elif scope=='vehicle_hurt':
        PARENT=ROOT/'out/ver_rin_nana/nana_air_clone_20261030T012148509868Z'
        PARENT_SHA='4f82fba9883df2f209699620fa007f3f071c2072d150d717ab2c8e604f11edb2'
        SCOPE='vehicle_hurt';FRAME_IDS=[*range(162,175),*range(184,204),*range(233,237)];RECIPE_SCOPE='base_nana_vehicle_hurt_37'
    elif scope!='run' or SCOPE!='run':raise ValueError('Scope is immutable per build process')

def validate(a,b):
    for p in (a,b):
        if not p.resolve().is_relative_to(ROOT/'work/ver_rin_nana'/('nana_'+SCOPE)):raise ValueError('Expected isolated Nana preparation')
    r=json.loads((a/'recipe.json').read_text('utf8'));s=json.loads((b/'recipe.json').read_text('utf8'))
    if r!=s or r['task']!='x_nana' or r['scope']!=RECIPE_SCOPE or r['parent_bin_sha256']!=PARENT_SHA or Path(r['parent_build'])!=PARENT.relative_to(ROOT):raise ValueError('Recipe identity or parent mismatch')
    if r['changed_bitmap_references']!=[[0,n] for n in FRAME_IDS]:raise ValueError('Unexpected frame references')
    if any(not r[k] for k in ('idle_palette_preserved','idle_frames_preserved','standing_frames_preserved','armor_tiles_preserved','other_compositions_preserved','other_decoded_bitmaps_preserved')) or r['timing_changed'] or r['resources_relocated']:raise ValueError('Preservation invariant failed')
    if SCOPE in ('air','dash','wall','hurt','fall_legs','ladder','low_hp','arrival','victory') and not r['run_frames_preserved']:raise ValueError('Accepted running must be preserved')
    if SCOPE=='victory' and not all(r[k]for k in ('air_frames_preserved','dash_frames_preserved','wall_frames_preserved','hurt_frames_preserved','ladder_frames_preserved','low_hp_frames_preserved','arrival_frames_preserved','accepted140_frames_preserved','special98_frames_preserved')):raise ValueError('Accepted actions changed')
    if SCOPE=='special' and not all(r[k]for k in ('run_frames_preserved','air_frames_preserved','dash_frames_preserved','wall_frames_preserved','hurt_frames_preserved','ladder_frames_preserved','low_hp_frames_preserved','arrival_frames_preserved','victory_return_frames_preserved','accepted150_frames_preserved','separate_effect_tiles_preserved','effect_and_armor_palette_rows_preserved')):raise ValueError('Accepted actions or effects changed')
    if SCOPE=='special_remaining' and not all(r[k]for k in ('run_frames_preserved','air_frames_preserved','dash_frames_preserved','wall_frames_preserved','hurt_frames_preserved','ladder_frames_preserved','low_hp_frames_preserved','arrival_frames_preserved','victory_return_frames_preserved','accepted157_frames_preserved','charge_cyclone_frames_preserved','separate_effect_tiles_preserved','palette_preserved')):raise ValueError('Accepted actions, effects or palettes changed')
    if SCOPE=='air_clone' and not all(r[k]for k in ('run_frames_preserved','air_frames_preserved','dash_frames_preserved','wall_frames_preserved','hurt_frames_preserved','ladder_frames_preserved','low_hp_frames_preserved','arrival_frames_preserved','victory_return_frames_preserved','accepted166_frames_preserved','charge_cyclone_frames_preserved','frost_fire_frames_preserved','separate_attack_effects_preserved','palette_preserved','nova_strike_preserved','armor_costumes_unchanged')):raise ValueError('Accepted actions, attack effects, armor or palettes changed')
    if SCOPE=='vehicle_hurt' and not all(r[k]for k in ('run_frames_preserved','air_frames_preserved','dash_frames_preserved','wall_frames_preserved','hurt_frames_preserved','ladder_frames_preserved','low_hp_frames_preserved','arrival_frames_preserved','victory_return_frames_preserved','existing183_frames_preserved','charge_cyclone_frames_preserved','frost_fire_frames_preserved','extra_air_clone_frames_preserved','separate_attack_effects_preserved','palette_preserved','nova_strike_preserved','armor_costumes_unchanged','blank198_display_preserved')):raise ValueError('Existing actions, blank198, attack effects, armor or palettes changed')
    if SCOPE=='arrival' and not all(r[k] for k in ('air_frames_preserved','dash_frames_preserved','wall_frames_preserved','hurt_frames_preserved','ladder_frames_preserved','low_hp_frames_preserved','arrival_endpoint_equals_idle')):raise ValueError('Arrival endpoint or accepted actions changed')
    if SCOPE=='low_hp' and not all(r[k] for k in ('air_frames_preserved','dash_frames_preserved','wall_frames_preserved','hurt_frames_preserved','ladder_frames_preserved','mouth_overlay_verified','ground_contact_preserved')):raise ValueError('Low HP preservation or mouth/feet validation failed')
    if SCOPE=='ladder' and not all(r[k] for k in ('air_frames_preserved','dash_frames_preserved','wall_frames_preserved','hurt_frames_preserved')):raise ValueError('Existing actions changed')
    if SCOPE=='dash' and not all(r[k] for k in ('air_frames_preserved','dash_speed_streak_tile_preserved')):raise ValueError('Air or dash speed streak preservation failed')
    if SCOPE=='wall' and not all(r[k] for k in ('air_frames_preserved','dash_frames_preserved')):raise ValueError('Air or dash preservation failed')
    if SCOPE=='hurt' and not all(r[k] for k in ('air_frames_preserved','dash_frames_preserved','wall_frames_preserved','shared_effect_tiles_parts_preserved')):raise ValueError('Accepted motions or native effects changed')
    if SCOPE=='fall_legs' and not all(r[k] for k in ('rise_and_landing_preserved','dash_frames_preserved','wall_frames_preserved','hurt_frames_preserved','upper_body_gun_and_registration_preserved','only_legs_changed')):raise ValueError('Leg revision escaped requested scope')
    if digest(PILOT/'nana_000_indexed.png')!=r['master_sha256'] or digest(PILOT/'palette.bin')!=r['palette_sha256']:raise ValueError('Approved style changed')
    arc=(a/'modified.arc').read_bytes()
    if sha256(arc)!=r['modified_arc_sha256'] or arc!=(b/'modified.arc').read_bytes():raise ValueError('Archive reproduction differs')
    for n,h in r['frame_sha256'].items():
        if digest(a/f'frame_{int(n):03d}.png')!=h or digest(b/f'frame_{int(n):03d}.png')!=h:raise ValueError('Frame reproduction differs')
    if digest(PARENT/'rin_nana.bin')!=PARENT_SHA or digest(PARENT/'modified.arc')!=r['parent_arc_sha256']:raise ValueError('Parent changed')
    rec=json.loads((PARENT/'manifest.json').read_text('utf8'))['archive'];rec={**rec,'sha256':r['parent_arc_sha256']}
    with (PARENT/'rin_nana.bin').open('rb') as f:
        if DiscReader(f,(PARENT/'rin_nana.bin').stat().st_size).read(rec['lba'],rec['size'])!=(PARENT/'modified.arc').read_bytes():raise ValueError('Parent ARC readback differs')
    return r,arc,rec

def build(a,b):
    r,arc,rec=validate(a,b);protection=json.loads((PARENT/'preservation.json').read_text('utf8'))
    def protect():
        for q in protection['files']:
            if digest(ROOT/q['path'])!=q['expected_sha256']:raise ValueError('Protected file changed: '+q['path'])
        if digest(PARENT/'rin_nana.bin')!=PARENT_SHA:raise ValueError('Parent changed')
    protect();out=ROOT/'out/ver_rin_nana'/('nana_'+SCOPE+'_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    result=write_archive_copies(PARENT/'rin_nana.bin',out/'rin_nana.bin',[(rec,arc)],PARENT_SHA);changes={q['lba'] for q in result['changed_sectors']};count=0
    with (PARENT/'rin_nana.bin').open('rb') as x,(out/'rin_nana.bin').open('rb') as y:
        while True:
            p,q=x.read(2352),y.read(2352)
            if not p:
                if q:raise ValueError('Disc size increased')
                break
            if len(p)!=len(q) or (p!=q)!=(count in changes):raise ValueError('Undeclared sector change')
            if count in changes:
                if p[:24]!=q[:24] or not rec['lba']<=count<rec['lba']+(rec['size']+2047)//2048:raise ValueError('Change outside PL00')
                validate_checks(q)
            count+=1
    with (out/'rin_nana.bin').open('rb') as f:
        if DiscReader(f,result['size']).read(rec['lba'],rec['size'])!=arc:raise ValueError('Output ARC readback differs')
    protect();shutil.copyfile(PARENT/'rin_nana.cue',out/'rin_nana.cue');shutil.copyfile(PARENT/'PL01_U.ARC',out/'PL01_U.ARC');(out/'modified.arc').write_bytes(arc);shutil.copytree(a,out/'art')
    if SCOPE in ('air','dash','wall','hurt','fall_legs','ladder','low_hp','arrival','victory','special','special_remaining','air_clone','vehicle_hurt'):
        shutil.copyfile(PARENT/'PL02_U.ARC',out/'PL02_U.ARC');shutil.copytree(PARENT/'menu_icon',out/'menu_icon')
    if SCOPE not in ('hurt','ladder','low_hp','arrival','victory','special','special_remaining','air_clone','vehicle_hurt'):
        pairs=ROOT/r['paired_art'];shutil.copyfile(pairs/'paired_4x.png',out/'art/paired_4x.png')
    v={'all_disc_sectors_compared':count,'changed_sectors':len(changes),'edc_ecc_checked':True,'readback_equal':True,'protected_files':len(protection['files']),'independent_arc_reproduction':True,'checked_bitmap_references':r['checked_bitmap_references'],'changed_frames':FRAME_IDS,'rin_and_common_assets_preserved':True,'idle_and_standing_preserved':True,'only_X_archive_changed':True,'runtime_verified':False}
    m={'project':'ver_rin_nana','task':'x_nana','kind':'nana_run_and_moving_fire','stage':'EXPANSION','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'modified_bin':result,'modified_archive_sha256':sha256(arc),'archive':rec,'frames':list(range(1,33)),'art':'art','verification':v,'inherited_manifest':(PARENT/'manifest.json').relative_to(ROOT).as_posix(),'style_basis_approved':True,'new_animation_user_accepted':False,'runtime_verified':False,'known_limit':'Only base X idle/standing/run replaced; other motions and armor still native'}
    if SCOPE=='air':
        v.update(run_frames_preserved=True,sarangi_menu_icon_preserved=True)
        m.update(kind='nana_air_and_shooting',frames=FRAME_IDS,known_limit='Base idle/standing/run/air replaced; remaining motions and armor native')
    if SCOPE=='dash':
        v.update(run_frames_preserved=True,air_frames_preserved=True,dash_speed_streak_tile_preserved=True,sarangi_menu_icon_preserved=True)
        m.update(kind='nana_dash_and_shooting',frames=FRAME_IDS,known_limit='Base idle/standing/run/air/dash replaced; remaining motions and armor native')
    if SCOPE=='wall':
        v.update(run_frames_preserved=True,air_frames_preserved=True,dash_frames_preserved=True,sarangi_menu_icon_preserved=True)
        m.update(kind='nana_wall_and_shooting',frames=FRAME_IDS,known_limit='Base idle/standing/run/air/dash/wall replaced; remaining motions and armor native')
    if SCOPE=='hurt':
        v.update(run_frames_preserved=True,air_frames_preserved=True,dash_frames_preserved=True,wall_frames_preserved=True,shared_effect_tiles_parts_preserved=True,sarangi_menu_icon_preserved=True)
        m.update(kind='nana_hurt',frames=FRAME_IDS,known_limit='Base hurt 106..114 added; special hurt 233..236, remaining motions and armor still native')
    if SCOPE=='fall_legs':
        v.update(only_legs_changed=True,upper_body_gun_and_registration_preserved=True,rise_and_landing_preserved=True,existing97_frames_preserved=True,sarangi_menu_icon_preserved=True)
        m.update(kind='nana_fall_leg_revision',frames=FRAME_IDS,known_limit='Only falling legs 43..48 revised; cumulative103 base references, remaining motions and armor native')
    if SCOPE=='ladder':
        v.update(existing103_frames_preserved=True,sarangi_menu_icon_preserved=True)
        m.update(kind='nana_ladder',frames=FRAME_IDS,cumulative_base_references=117,known_limit='Ladder14 added; remaining base actions and armor still native')
    if SCOPE=='low_hp':
        v.update(existing117_frames_preserved=True,mouth_overlay_verified=True,ground_contact_preserved=True,sarangi_menu_icon_preserved=True)
        m.update(kind='nana_low_hp',frames=FRAME_IDS,cumulative_base_references=123,known_limit='Low HP6 added; remaining base actions and armor still native')
    if SCOPE=='arrival':
        v.update(existing123_frames_preserved=True,arrival_endpoint_equals_idle=True,sarangi_menu_icon_preserved=True)
        m.update(kind='nana_arrival',frames=FRAME_IDS,cumulative_base_references=140,known_limit='Arrival17 added; shared raised-pistol poses in special animations95/96 also changed. Other special, victory and armor actions remain native')
    if SCOPE=='victory':
        v.update(existing140_frames_preserved=True,arrival_frames_preserved=True,special98_frames_preserved=True,sarangi_menu_icon_preserved=True)
        m.update(kind='nana_victory_return',frames=FRAME_IDS,cumulative_base_references=150,known_limit='Victory4 and return6 added; other special, vehicle, extra damage and armor actions remain native')
    if SCOPE=='special':
        v.update(existing150_frames_preserved=True,separate_effect_tiles_preserved=True,effect_and_armor_palette_rows_preserved=True,sarangi_menu_icon_preserved=True,body_palette_rows=sorted(map(int,r['body_palette_rows'])))
        m.update(kind='nana_special_charge_cyclone',frames=FRAME_IDS,cumulative_base_references=157,known_limit='Charge linkage4 and cyclone3 added; remaining special, vehicle, extra damage and armor actions remain native')
    if SCOPE=='special_remaining':
        v.update(existing157_frames_preserved=True,all_palette_rows_preserved=True,separate_effect_tiles_preserved=True,sarangi_menu_icon_preserved=True)
        m.update(kind='nana_special_frost_fire',frames=FRAME_IDS,cumulative_base_references=166,known_limit='Frost/Soul Body shared2 and Rising Fire7 added; extra air, clone effects, vehicle, extra damage and armor actions remain native')
    if SCOPE=='air_clone':
        v.update(existing166_frames_preserved=True,all_palette_rows_preserved=True,separate_attack_effects_preserved=True,clone_disappearance_changed=True,sarangi_menu_icon_preserved=True,nova_strike_preserved=True,armor_costumes_unchanged=True)
        m.update(kind='nana_air_clone',frames=FRAME_IDS,cumulative_base_references=183,known_limit='Additional air12 and clone disappearance5 prepared; armor-conditioned activation not proven by static checks. Vehicle, extra damage, Nova and armor costumes remain native')
    if SCOPE=='vehicle_hurt':
        v.update(existing183_frames_preserved=True,all_palette_rows_preserved=True,separate_attack_effects_preserved=True,sarangi_menu_icon_preserved=True,nova_strike_preserved=True,armor_costumes_unchanged=True,blank198_display_preserved=True)
        m.update(kind='nana_vehicle_extra_hurt',frames=FRAME_IDS,cumulative_base_references=220,new_visible_references=36,shared_blank_reference=198,known_limit='Chaser13, ride heads19 and damage4 added; shared blank198 preserved. Vehicle/special damage actual scene testing pending. Nova8 and armor costumes still native; placeholders9 retained')
    for name,d in [('manifest.json',m),('verification.json',v),('preservation.json',protection)]:write(out/name,d)
    write(ROOT/'projects/ver_rin_nana/current_build.json',{'project':'ver_rin_nana','task':'x_nana','build':out.relative_to(ROOT).as_posix(),'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),'sha256':result['sha256'],'frames':FRAME_IDS,'art':(out/'art').relative_to(ROOT).as_posix(),'inherited_from':PARENT.relative_to(ROOT).as_posix(),'runtime_verified':False})
    print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(changes),'protected':len(protection['files'])}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--reproduced',type=Path,required=True);p.add_argument('--scope',choices=('run','air','dash','wall','hurt','fall_legs','ladder','low_hp','arrival','victory','special','special_remaining','air_clone','vehicle_hurt'),default='run');a=p.parse_args();configure_scope(a.scope);build(a.candidate.resolve(),a.reproduced.resolve())
