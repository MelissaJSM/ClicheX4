"""검토된 원화/정합자료를 해시 고정한다. 아트 수정 없음."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
from native_pose_pack import need,sha,write
def main():
    common=['prepare_rising_fire_inputs.py','register_rising_fire_probe.py','prepare_rising_common_layers.py','rising_fire_inputs01/structure.json']
    for typ,d,parents,dirs,scripts in[
        ('base','rising_common_layers01',['rising_fire_inputs01/page01','rising_fire_inputs01/page02','rising104_arm_correction01'],['rising_fire_native01','rising_fire_native02','rising104_arm_native02'],['register_rising104_arm.py','prepare_rising104_correction.py']),
        ('ultimate','rising_ultimate_shared02',['rising_ultimate_costume01/page01','rising_ultimate_costume01/page02'],['rising_ultimate_native01','rising_ultimate_native02'],['prepare_rising_ultimate_costume.py','prepare_rising_ultimate_shared.py'])]:
        folder=H/d;path=folder/'LOCK.json';need(not path.exists(),'Lock already exists');source=set(common+scripts)
        for p in parents:
            source.update(q.relative_to(H).as_posix()for q in (H/p).iterdir()if q.is_file()and q.suffix in('.png','.txt','.json'))
        for p in dirs:source.update(q.relative_to(H).as_posix()for q in (H/p).glob('*_indices.png'))
        files={p.name:sha(p.read_bytes())for p in sorted(folder.iterdir())if p.is_file()and(p.name.endswith('_indices.png')or p.name.endswith('_mask.png')or p.name.endswith('_owner.png')or p.name=='report.json')}
        write(path,{'scope':typ,'target_refs':[100,101,102,103,104,231,232],'files':files,'source_files':{p:sha((H/p).read_bytes())for p in sorted(source)},'derived232':[0,1],'derived232_basis':'현재 수용된 시부키231→232 관계, 원작 US 자세 동일성 주장 아님','old_coarse_head_or_body_copied':False,'runtime_verified':False})
        print(typ,sha(path.read_bytes()),len(files),len(source))
if __name__=='__main__':main()
