"""귀환3 후보의 입력 잠금 및 RN23 원MIPS 격리 검사 계획."""
from pathlib import Path
import sys,json
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(D)]
from preview_restore import digest,write,need
from pack_native import PARENT,BEFORE
FINAL='493bf2706aae33b64c4ffe70be1576a7ed63b0a4f62c54e89ca5876131392e29'

def main():
 out=D/'packed_return_candidate_v1';need(digest(out/'PL02_U.ARC')==FINAL,'후보');need(not(out/'INPUT_FROZEN.json').exists(),'새 잠금')
 folders=['body_inputs_v1','body_v1','body_registered_v1','costume_edit_inputs_v1','costume_edit_v1','costume_pair_probe_v2','final_targets_v1']
 files=[p for folder in folders for p in(D/folder).rglob('*')if p.is_file()and p.suffix in('.png','.json','.txt')]
 files.extend(D/name for name in['prepare_inputs.py','prepare_costume_edit.py','register_body.py','prepare_costume_pair.py','prepare_targets.py','pack_native.py'])
 files.extend(ROOT/p for p in['scripts/overhaul_sprites_costume_pack.py','scripts/prepare_shibuki_ultimate_production.py','scripts/prepare_riko_ui.py','scripts/discover_inputs.py','src/psx_player.py','work/ver_rin_nana/nana_ultimate_armor/ceremony_v1/generated_first.png','work/overhaul_20261105/sprites/ver_rin_nana/baseline/PL02_U.ARC'])
 files.extend(N/p for p in['native_restore/preview_restore.py','base_run_repaint/register_page.py','base_run_repaint/pack_cycle.py','ultimate_victory_repaint/register_page.py']);files.extend([PARENT,PARENT.parent/'FROZEN.json'])
 files.append(N.parent/'zero_audit/nana_ultimate_ceremony_sources01/report.json')
 lock=[{'path':p.relative_to(ROOT).as_posix(),'size':p.stat().st_size,'sha256':digest(p)}for p in sorted(set(files))]
 write(out/'INPUT_FROZEN.json',{'candidate_sha256':FINAL,'parent_sha256':BEFORE,'input_fixed':True,'files':lock,'scope':'귀환156 새몸×2의상·국소 하의1셀원화 및157/158파생15층 고정. 원화 전체 재양자화·독립·원MIPS·실기와 구분.'})
 src=ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v23/rin_nana.bin';need(digest(src)=='fe225d3fee86aaa9a26e47e855d661265eefcdef229bdc5c8801a6521dccaa98','RN23부모')
 write(D/'native_components_v1.json',{'project':'ver_rin_nana','source_bin':src.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'resources':{'PL02_U.ARC':{'path':(out/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':BEFORE,'after':FINAL}},'checkpoint_only':True,'scope':'RN23 부모 원MIPS 해독/조립/GPU 격리검사. 게임디스크/프로세스/저장 변경 없음.'});print(json.dumps({'inputs':len(lock),'lock_sha256':digest(out/'INPUT_FROZEN.json'),'asset':FINAL}))
if __name__=='__main__':main()
