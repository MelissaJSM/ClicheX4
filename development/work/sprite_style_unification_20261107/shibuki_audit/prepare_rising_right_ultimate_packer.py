"""고정 Ultimate 부모 위 새103/104만 반영하는 재현 패커 생성."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[2]))
from native_pose_pack import need,sha,write
def main():
    d=H/'rising_right_ultimate_shared02';p=H/'pack_rising_right_ultimate01.py';need(not p.exists(),'New producer only')
    source_files=['prepare_rising_right_ultimate_shared01.py','register_ultimate_right_hand02.py','rising_ultimate_prepare103/generated.png','rising_ultimate_right_retry02/generated.png']
    source_files+=[f'{folder}/{form}_{n}_indices.png'for folder,n in[('rising_ultimate_prepare103_native01',103),('rising_ultimate_right_native02',104)]for form in('before','after')]
    write(d/'LOCK.json',{'files':{f.name:sha(f.read_bytes())for f in sorted(d.glob('*_indices.png'))},'source_files':{name:sha((H/name).read_bytes())for name in source_files},'scope':'103/104를 새 오른손 준비/발사 자세로 교정. 103 전체(0,+1) 등록,104 새맨팔 외곽1점만재킷에정확공유.'})
    digest=sha((d/'LOCK.json').read_bytes());s=(H/'pack_rising_ultimate_probe.py').read_text('utf8')
    replacements={
      "PARENT_SHA='dd6416c8840a1a0e5fd7ff4c73fe33b6ebd90e69b5f86f9be5f9671cc4d53c1d'":"PARENT_SHA='71d02fe6d965c1fb42cc786766bad62372c792ccd8ecf6d5bc1e40dc8deb8597'",
      "LOCK_SHA='0d714b748498c92efe3d6848867829d791d6bffab6dc2a9a503a484c2b74b3a2'":f"LOCK_SHA='{digest}'",
      'REFS=(100,101,102,103,104,231,232)':'REFS=(103,104)',
      "default='rising_ultimate_pack_probe01'":"default='rising_right_ultimate_pack01'",
      "'prepared_double_cyclone_ultimate01/PL02_U.ARC'":"'prepared_rising_fire_ultimate01/PL02_U.ARC'",
      "'rising_ultimate_shared02'":"'rising_right_ultimate_shared02'",
      "    for form in('before','after'):images[232,form]=np.roll(images[232,form],1,0)\n":"",
      "'new_costume_displays':14":"'new_costume_displays':4",
      "'derived232':'accepted Shibuki231 translated (0,+1); not original US pose equivalence'":"'derived232':'unchanged from frozen parent'"}
    for a,b in replacements.items():need(s.count(a)==1,'Unexpected source token '+a);s=s.replace(a,b)
    p.write_text(s,'utf8');print(json.dumps({'lock':digest,'producer':str(p)}))
if __name__=='__main__':main()
