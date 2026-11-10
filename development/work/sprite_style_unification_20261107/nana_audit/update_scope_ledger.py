"""Emit explicit per-reference production status without inferring completion."""
from pathlib import Path
import sys,json,collections
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent
sys.path[:0]=[str(ROOT),str(D/'native_restore')]
from preview_restore import write,digest

def group(n):
    for label,refs in [('reference_idle',{0,115,116,117,118,119,141,142}),('run_fire',set(range(1,33))),('air',set(range(33,55))|{93,94}),('wall',set(range(55,67))),('dash',set(range(67,85))),('standing_fire',set(range(85,93))),('weapon_pose',set(range(95,105))|{231,232}),('hurt',set(range(106,115))),('low_hp',set(range(120,126))|set(range(233,237))),('arrival_return',set(range(126,141))),('ladder',set(range(143,156))|{183}),('victory',set(range(156,162))),('vehicle',set(range(162,175))|set(range(184,204))),('special_flight_nova',set(range(213,231)))]:
        if n in refs:return label
    return 'other_requires_event_classification'

def main():
    blank={105,*range(175,183)};accepted={0,115,116,117,118,119,141,142};forms={};sums={}
    for form in ('base','fourth','ultimate_before_jacket','ultimate_after_swim'):
        items=[]
        for n in range(237):
            state='not_redrawn';detail=None
            if n in blank:state='reserved_placeholder'
            elif n in accepted:state='accepted_style_reference_preserved'
            elif form in ('base','fourth')and 1<=n<=32:state='new_full_art_frozen_native';detail='packed_joint_v2'
            elif form=='fourth'and n in {*range(144,153),155}:state='limited_existing_source_detail_restore';detail='50 shin shade pixels total; not full style remake'
            elif form.startswith('ultimate')and 67<=n<=84:state='limited_existing_source_detail_restore';detail='hair source detail only; not full style remake'
            elif form.startswith('ultimate')and n in(217,218,220):state='limited_existing_source_detail_restore';detail='101 changed hair pixels per ref from dash73; full art/effects not redrawn'
            elif form in('base','fourth')and 55<=n<=66:state='new_full_art_frozen_candidate';detail='packed_wall_candidate_v4: all 12 refs, paired new firing sleeves and Fourth veil; 7296 masks and authored front boot restoration verified; awaiting integration/native CPU/runtime'
            elif form in('base','fourth')and n in range(33,55):state='new_full_art_frozen_candidate';detail='packed_air_candidate_v1 SHA721457a5: all22 new bodies/firing pairs, accepted fold_C39/40;7296 partial combinations,352 exact original gun windows, reproduction and11 rejection checks passed. Awaiting independent/root native MIPS and gameplay verification; not whole-character style completion.'
            elif form in ('base','fourth')and n in {*range(67,85),93,94}:state='new_full_art_frozen_candidate';detail='packed_dash_candidate_v1 SHAcbe69967: 20 refs, new native body/costume/sleeve art,73/74 separate54px effects;7296 RGBA masks,288 original gun windows,10 input rejection guards and exact reproduction passed. Producer frozen; independent readback/root MIPS and gameplay are separate.'
            items.append({'ref':n,'group':group(n),'status':state,'detail':detail})
        forms[form]=items;sums[form]=dict(collections.Counter(q['status']for q in items))
    files={
        'frozen_PL00':D/'base_run_repaint/packed_joint_v2/PL00_U.ARC',
        'frozen_PL02':D/'native_restore/nova_sync_v1/PL02_U.ARC',
        'wall_source_v2':D/'wall_repaint/basic_keys_v2/generated.png',
        'wall_native_probe':D/'wall_repaint/basic_contacts_probe_v3/registration.json',
        'wall_native_candidate':D/'wall_repaint/packed_wall_candidate_v4/PL00_U.ARC',
        'air_first_keys':D/'air_repaint/basic_registered_v2/registration.json',
        'air_middle_keys':D/'air_repaint/basic_middle_registered_v2/registration.json',
        'air_landing_keys':D/'air_repaint/basic_landing_registered_v5/registration.json',
        'air_firing_a':D/'air_repaint/firing_a_joint_probe_v1/manifest.json',
        'air_firing_b':D/'air_repaint/firing_b_joint_probe_v2/manifest.json',
        'air_landing_firing_reach':D/'air_repaint/landing_reach_joint_v1/manifest.json',
        'air_landing_firing_54':D/'air_repaint/landing54_probe_v2/manifest.json',
        'air_fourth_51_knee_source':D/'air_repaint/fourth51_knee_v1/generated.png',
        'air_joint_candidate':D/'air_repaint/joint_layers_probe_v6/manifest.json',
        'air_native_diagnostic':D/'air_repaint/packed_air_diagnostic_v1/verification.json',
        'air_fold39_art_review':D/'air_repaint/fold39_detail_probe_v1/manifest.json',
        'air_frozen_targets':D/'air_repaint/joint_layers_final_v1/manifest.json',
        'air_frozen_candidate':D/'air_repaint/packed_air_candidate_v1/PL00_U.ARC',
        'air_frozen_proposal':D/'air_repaint/packed_air_candidate_v1/proposal.json',
        'air_regression':D/'air_repaint/packed_air_candidate_v1/mask_verification.json',
        'air_reproduction':D/'air_repaint/packed_air_candidate_v1/reproduction.json',
        'dash_first_native':D/'dash_repaint/basic_contacts_v2/registration.json',
        'dash_71_boots':D/'dash_repaint/dash71_boots_registered_v1/registration.json',
        'dash_second_native':D/'dash_repaint/basic_second_contacts_v4/registration.json',
        'dash_last_native':D/'dash_repaint/basic_last_registered_v2/registration.json',
        'dash_effects':D/'dash_repaint/effects/manifest.json',
        'dash_next_inputs':D/'dash_repaint/next_guides_v1/manifest.json',
        'dash_frozen_candidate':D/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC',
        'dash_frozen_proposal':D/'dash_repaint/packed_dash_candidate_v1/proposal.json',
        'dash_regression':D/'dash_repaint/packed_dash_candidate_v1/mask_verification.json',
        'dash_reproduction':D/'dash_repaint/packed_dash_candidate_v1/reproduction_and_guards.json',
        'dash_offline_playback':D/'dash_repaint/native_cycle_v1/verification.json',
        'remaining_visual_inventory':D/'remaining_review_v1/manifest.json',
    }
    write(D/'scope_ledger.json',{'scope':'Nana player bank0 render references 0..236, four visible forms. Not a count of unique animations or every bank/UI asset.','parent_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','parent_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','files':{k:{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}for k,p in files.items()},'summary':sums,'forms':forms,'full_style_complete':False,'other_banks_and_ui':'No new artwork in this bundle; independently preserve/review after player poses.','gameplay_by_this_agent':False})
    print(json.dumps(sums))
if __name__=='__main__':main()
