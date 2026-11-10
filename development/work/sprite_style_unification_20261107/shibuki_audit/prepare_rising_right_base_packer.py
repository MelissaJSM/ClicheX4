"""현재 동결본 위103/104만 교체하는 좁은 재현 패커를 별도로 생성한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[2]))
from native_pose_pack import need,sha,write
def main():
    d=H/'rising_right_base_layers01';p=H/'pack_rising_right_base01.py';need(not p.exists(),'New producer only')
    source_files=['prepare_rising_right_base_layers01.py','register_rising_right_hand_probe.py','rising_air_hand_fix_inputs01/page01/generated_rejected104.png','rising104_height_edit01/generated.png','rising_right_hand_native04/report.json']
    source_files += [f'rising_right_hand_native04/{form}_{n}_indices.png'for form in('base','fourth')for n in(103,104)]
    write(d/'LOCK.json',{'files':{f.name:sha(f.read_bytes())for f in sorted(d.glob('*_indices.png'))},'source_files':{name:sha((H/name).read_bytes())for name in source_files},'scope':'기존 새103/104의 잘못된 발사손을 원US 공중 불꽃이 있는 오른쪽 손으로 교정. 100..102/231232 불변.'})
    digest=sha((d/'LOCK.json').read_bytes());s=(H/'pack_rising_base_v2.py').read_text('utf8')
    replacements={
      "PARENT_SHA='61495a2aaf002efc32492a4e12c3724a77c82b3f42464538ae1e2cc855da74c0'":"PARENT_SHA='008eb1df4809fe6f8e7002604f98abbe58c885265cfa63a688105f9acf4d29ce'",
      "LOCK_SHA='06e27b8d005770dd4b473aaaaf1aaee14cb149dbe649d0995a13db2f247e107a'":f"LOCK_SHA='{digest}'",
      'REFS=(100,101,102,103,104,231,232)':'REFS=(103,104)',
      "default='rising_base_pack_probe02'":"default='rising_right_base_pack01'",
      "'prepared_double_cyclone_base01/PL00_U.ARC'":"'prepared_rising_fire_base02/PL00_U.ARC'",
      "'rising_common_layers02'":"'rising_right_base_layers01'",
      '    targets[232]={b:np.roll(v,1,0)for b,v in targets[232].items()};changes={b:{}for b in BANKS};raws={};packmeta=[]':'    changes={b:{}for b in BANKS};raws={};packmeta=[]',
      "'derived232':'accepted Shibuki231 translated (0,+1); not claimed as original US pose equivalence'":"'derived232':'unchanged from frozen parent'"}
    for a,b in replacements.items():need(s.count(a)==1,'Unexpected source token '+a);s=s.replace(a,b)
    p.write_text(s,'utf8');print(json.dumps({'lock':digest,'producer':str(p)}))
if __name__=='__main__':main()
