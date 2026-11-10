"""승리4 후보의 입력을 고정하고 원MIPS 격리 검사 계획을 만든다."""
from pathlib import Path
import sys,json
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(D)]
from preview_restore import digest,write,need
from pack_native import PARENT,BEFORE
FINAL='b7dcf46dba35084265e8b32529d7a4d072108ed201a60ba4f17fcc71494aa1c5'
def main():
 out=D/'packed_victory_candidate_v1';need(digest(out/'PL02_U.ARC')==FINAL,'후보');need(not(out/'INPUT_FROZEN.json').exists(),'새 잠금')
 folders=['a_inputs_v1','a_v1','a_registered_v1','b_inputs_v1','b_v1','b_registered_v1','costume_pair_probe_v2','canonical_weapon_probe_v1','final_targets_v1']
 files=[p for folder in folders for p in(D/folder).rglob('*')if p.is_file()and p.suffix in('.png','.json','.txt')]
 files.extend(D/name for name in['prepare_inputs.py','register_page.py','semantic_grids.py','prepare_costume_pairs.py','prepare_canonical_weapon.py','prepare_targets.py','pack_native.py'])
 files.extend(ROOT/p for p in['scripts/overhaul_sprites_costume_pack.py','scripts/prepare_shibuki_ultimate_production.py','scripts/prepare_riko_ui.py','scripts/discover_inputs.py','src/psx_player.py','work/ver_rin_nana/nana_ultimate_armor/ceremony_v1/generated_first.png'])
 files.extend(N/p for p in['native_restore/preview_restore.py','base_run_repaint/register_page.py','base_run_repaint/pack_cycle.py']);files.extend([PARENT,PARENT.parent/'FROZEN.json'])
 files.extend((N.parent/'zero_audit/nana_ultimate_victory_relations01').glob('*.json'))
 lock=[{'path':p.relative_to(ROOT).as_posix(),'size':p.stat().st_size,'sha256':digest(p)}for p in sorted(set(files))]
 write(out/'INPUT_FROZEN.json',{'candidate_sha256':FINAL,'parent_sha256':BEFORE,'input_fixed':True,'files':lock,'scope':'승리4×양의상 원화2장8고정셀 및20층 입력고정.204/205 빈손,206/207 새손/정본권총.독립/최종미술/원MIPS/실기 별도.'})
 write(D/'native_components_v1.json',{'project':'ver_rin_nana','source_bin':'out/ver_rin_nana/sprite_style_unification_20261107_v21/rin_nana.bin','source_sha256':'c5608887658797cad4e034870882ad4aa3c47f5993afaac28aa6a2328674a0e3','resources':{'PL02_U.ARC':{'path':(out/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':BEFORE,'after':FINAL}},'checkpoint_only':True,'scope':'RN21 부모 원MIPS 해독/조립/GPU 격리검사.게임디스크/저장/프로세스 변경 없음.'});print(json.dumps({'inputs':len(lock),'lock_sha256':digest(out/'INPUT_FROZEN.json'),'asset':FINAL}))
if __name__=='__main__':main()
