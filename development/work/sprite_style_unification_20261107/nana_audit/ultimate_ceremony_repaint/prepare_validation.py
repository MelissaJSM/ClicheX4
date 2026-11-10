"""등장10 후보 입력 잠금과 원MIPS 격리 검사 계획."""
from pathlib import Path
import sys,json
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(D)]
from preview_restore import digest,write,need
from pack_native import BEFORE,PARENT
def main():
 out=D/'packed_arrival_candidate_v1';final=digest(out/'PL02_U.ARC');need(final=='c721ddee3292a88f6d1dbffb49bc79d1a82e08b3d6913cb501dc406800aa23c9','최종후보');need(not(out/'INPUT_FROZEN.json').exists(),'새입력잠금')
 folders=['first_inputs_v1','first_v1','first_registered_v2','second_inputs_v1','second_v1','second_registered_v1','costume_pair_probe_v3','settle_inputs_v1','settle_v1','settle_registered_v1','raised138_inputs_v1','raised138_v1','raised138_registered_v1','raised138_local_probe_v1','settle_pair_probe_v1','pistol_hands_a_inputs_v1','pistol_hands_a_v1','pistol_hands_b_inputs_v1','pistol_hands_b_v1','pistol_hands_registered_v1','canonical_cases_probe_v2','common_hands_probe_v1','settle_legs_inputs_v1','settle_legs_v1','settle_legs_registered_v1','arrival_targets_probe_v2']
 files=[p for folder in folders for p in(D/folder).rglob('*')if p.is_file()and p.suffix in('.png','.json','.txt')]
 files.extend(D/name for name in['register_first.py','register_second.py','register_costume_pairs.py','register_settle.py','register_raised138_local.py','prepare_settle_pair.py','register_pistol_hands.py','register_canonical_cases.py','prepare_common_hands.py','register_settle_legs.py','prepare_arrival_targets.py','pack_native.py'])
 files.extend(ROOT/p for p in['scripts/overhaul_sprites_costume_pack.py','scripts/prepare_shibuki_ultimate_production.py','scripts/prepare_riko_ui.py','scripts/discover_inputs.py','src/psx_player.py','work/overhaul_20261105/sprites/ver_rin_nana/baseline/PL02_U.ARC','work/ver_rin_nana/nana_art/arrival_v1/production02/frame_133.png'])
 files.extend(N/p for p in['native_restore/preview_restore.py','base_run_repaint/register_page.py','base_run_repaint/pack_cycle.py']);files.append(PARENT)
 for folder in('nana_ultimate_ceremony_sources01','nana_ultimate_ceremony_sources02','nana_ultimate_ceremony_sources03','nana_ultimate_ceremony_pistol_sources01','nana_arrival141_dust01'):
  fd=N.parent/'zero_audit'/folder;files.extend(fd.glob('*.json'));files.extend(fd.glob('*.npy'))
 lock=[{'path':p.relative_to(ROOT).as_posix(),'size':p.stat().st_size,'sha256':digest(p)}for p in sorted(set(files))]
 write(out/'INPUT_FROZEN.json',{'candidate_sha256':final,'parent_sha256':BEFORE,'input_fixed':True,'files':lock,'scope':'등장5새몸체·새손/권총/138하체 국소원화 및5파생참조50층의입력고정. 미술검토/독립/원MIPS/실기별도.'})
 write(D/'native_components_v1.json',{'project':'ver_rin_nana','source_bin':'out/ver_rin_nana/sprite_style_unification_20261107_v19/rin_nana.bin','source_sha256':'383cd66528a25abf1bef08b4791824d52d3ae676b8e09af567fcae36447cea7c','resources':{'PL02_U.ARC':{'path':(out/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':BEFORE,'after':final}},'checkpoint_only':True,'scope':'RN19 원MIPS 해독/조립/GPU 격리검사. 디스크/저장/실제실행 프로세스 변경없음.'});print(json.dumps({'sha256':final,'inputs':len(lock),'lock_sha256':digest(out/'INPUT_FROZEN.json')}))
if __name__=='__main__':main()
