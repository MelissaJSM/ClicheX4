"""Ultimate 피격 후보의 최종 경로와 입력을 고정하고 원MIPS 계획을 작성한다."""
from pathlib import Path
import sys,json,shutil
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path.insert(0,str(N/'native_restore'))
from preview_restore import digest,write,need
FINAL='c9e68442829a7f149ae86317c88172e27dbce545e454687b98310fad28ef83a5'
PARENT='4132738ac872750507538cd8d150e13a510422df81cea99b502e7371b6753cd9'
def main():
    source=D/'packed_hurt_diagnostic_v1';out=D/'packed_hurt_candidate_v1'
    need(not out.exists(),'새 최종 경로 필요');need(digest(source/'PL02_U.ARC')==FINAL,'진단 자원 해시')
    out.mkdir()
    for name in ['PL02_U.ARC','verification.json',*[f'readback_{i}.png' for i in range(1,6)]]:shutil.copyfile(source/name,out/name)
    p=json.loads((source/'proposal.json').read_text('utf8'));p['files']['PL02_U.ARC']['path']=(out/'PL02_U.ARC').relative_to(ROOT).as_posix();write(out/'proposal.json',p)
    folders=['first_inputs_v1','extra_inputs_v1','first_v1','extra_v1','first_registered_v1','extra_registered_v1','costume_pair_probe_v4','body_layers_probe_v1','effect_probe_v1','aura_contact_probe_v2','final_targets_v1']
    files=[p for folder in folders for p in(D/folder).rglob('*')if p.is_file()and p.suffix in('.png','.json','.txt')]
    files.extend(D/name for name in ['register_first.py','register_costume_pairs.py','prepare_body_layers.py','prepare_effect_probe.py','register_aura_components.py','prepare_final_targets.py','pack_native.py'])
    files.extend(ROOT/name for name in ['scripts/overhaul_sprites_costume_pack.py','scripts/prepare_shibuki_ultimate_production.py','src/psx_player.py','scripts/prepare_riko_ui.py','scripts/discover_inputs.py'])
    files.extend(N/name for name in ['native_restore/preview_restore.py','base_run_repaint/pack_cycle.py','base_run_repaint/register_page.py','rising_repaint/packed_ultimate_candidate_v1/PL02_U.ARC'])
    audit=N.parent/'zero_audit/nana_ultimate_hurt_relations01'
    files.append(audit/'report.json');files.extend(audit.glob('*.npy'))
    files.append(ROOT/'work/overhaul_20261105/sprites/ver_rin_nana/baseline/PL02_U.ARC')
    lock=[{'path':p.relative_to(ROOT).as_posix(),'size':p.stat().st_size,'sha256':digest(p)}for p in sorted(set(files))]
    write(out/'INPUT_FROZEN.json',{'candidate_sha256':FINAL,'parent_sha256':PARENT,'input_fixed':True,'files':lock,'scope':'Ultimate 피격13의 원화2장·고정셀8·의상/손/신발 정합·효과 포함65목표층·원효과 및 오라 출처 입력잠금. 최종수용/실기/FROZEN과 구분.'})
    write(D/'native_components_v1.json',{'project':'ver_rin_nana','source_bin':'out/ver_rin_nana/sprite_style_unification_20261107_v18/rin_nana.bin','source_sha256':'0f40463b883e00a7e3acf268fd45052b905d0454440d8c5436ce24fe80f58c95','resources':{'PL02_U.ARC':{'path':(out/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':PARENT,'after':FINAL}},'checkpoint_only':True,'scope':'RN18 원MIPS 해독/조립/GPU 격리 검사. 실제게임·디스크·포인터·저장 쓰기 없음.'})
    print(json.dumps({'sha256':FINAL,'inputs':len(lock),'lock_sha256':digest(out/'INPUT_FROZEN.json')}))
if __name__=='__main__':main()
