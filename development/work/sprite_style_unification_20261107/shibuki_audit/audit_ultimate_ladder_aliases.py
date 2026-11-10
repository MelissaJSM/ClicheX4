"""최신 Ultimate 사다리의 반전/공동스트림을 실제 레이어로 확인한다."""
from pathlib import Path
import sys,json
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from native_pose_pack import sha,need,write
from probe_ladder_capacity import mirror

def main():
    d=H/'ultimate_ladder_alias_audit01';need(not d.exists(),'Fresh audit');d.mkdir();p=H/'prepared_ultimate_dash01/PL02_U.ARC';need(sha(p.read_bytes())=='bdcf0f648e2102a208307e21a941b53439a2f342014e69981a6de156a4dfbdfb','Changed parent');a=Archive(p.read_bytes());refs=list(range(143,156))+[183];rows=[]
    for n in refs:
        f=a.banks[0]['frames'][n];matching=[]
        for key in refs:
            if key==n:continue
            for delta in(-1,0,1):
                checks={b:bool(np.array_equal(a.layer(n,b)[0],mirror(a.layer(key,b)[0],delta)))for b in(0,5,6,7,8)}
                if all(checks.values()):matching.append({'key':key,'mirror_world_delta':delta,'all_five_layers_exact':True})
        rows.append({'ref':n,'offset':f['offset'],'tile_count':f['tile_count'],'same_raw_slot_refs':[m for m in range(len(a.banks[0]['frames']))if a.banks[0]['frames'][m]['offset']==f['offset']],'exact_mirrors':matching})
    write(d/'report.json',{'source':p.relative_to(ROOT).as_posix(),'source_sha256':sha(p.read_bytes()),'rows':rows,'scope':'원자원5층 실제 픽셀 반전관계 조사. 원화/게임 변경 없음.','known_new_base_alias_recipe':{'145':[144,-1],'147':[146,0],'148':[149,0],'152':[151,0]},'not_assumed_for_ultimate_until_row_check':True,'source_modified':False})
    print(json.dumps(rows))
if __name__=='__main__':main()
