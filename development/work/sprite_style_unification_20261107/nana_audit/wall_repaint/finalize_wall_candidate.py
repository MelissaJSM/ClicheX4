"""동결 후보 재현/거부 검사와 출처를 기록. BIN·활성 포인터는 쓰지 않는다."""
from pathlib import Path
import sys,json,copy
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D))
from pack_wall_native import validate_source,validate_targets,validate_output,PBS,REFS,sha,write,need,digest,ROOT
def main():
    out=D/'packed_wall_candidate_v4';td=D/'joint_layers_probe_v4';manifest=json.loads((td/'manifest.json').read_text('utf8'));targets={(n,pb):np.array(Image.open(td/f'layer{pb}_{n:03}.png'))for n in REFS for pb in PBS};expected='03ebbfa01fa63772a61888b7a0022323090807b07b87f36bfa524cc755cf750d';need(digest(out/'PL00_U.ARC')==expected,'Candidate SHA');need(digest(D/'packed_wall_reproduction_v4/PL00_U.ARC')==expected,'Reproduction SHA');validate_targets(targets,manifest);checks=[]
    def reject(name,fn):
        try:fn()
        except (ValueError,KeyError):checks.append(name);return
        raise ValueError('Invalid input accepted '+name)
    reject('wrong_source_hash',lambda:validate_source(b'wrong'))
    missing=targets.copy();missing.pop((55,0));reject('missing_target',lambda:validate_targets(missing,manifest))
    unexpected=targets.copy();unexpected[67,0]=targets[55,0];reject('unexpected_ref',lambda:validate_targets(unexpected,manifest))
    for name,arr in [('shape',np.zeros((383,384),np.uint8)),('dtype',targets[55,0].astype(np.int16)),('range',np.full((384,384),16,np.uint8)),('hash',np.zeros((384,384),np.uint8))]:
        bad=targets.copy();bad[55,0]=arr;reject('target_'+name,lambda bad=bad:validate_targets(bad,manifest))
    badmeta=copy.deepcopy(manifest);badmeta['source_arc_sha256']='0'*64;reject('target_parent',lambda:validate_targets(targets,badmeta))
    reject('existing_output',lambda:validate_output(out));reject('outside_output',lambda:validate_output(ROOT/'not_created_by_wall_test'))
    component=json.loads((out/'component_probe.json').read_text('utf8'));need(not component,'Disconnected component remains')
    verification=json.loads((out/'verification.json').read_text('utf8'));masks=json.loads((out/'mask_verification.json').read_text('utf8'));need(verification['passed']and masks['passed'],'Required checks');write(out/'reproduction.json',{'passed':True,'after_sha256':expected,'reproduced_sha256':digest(D/'packed_wall_reproduction_v4/PL00_U.ARC'),'rejections':checks,'source_parent_unchanged':digest(D.parent/'base_run_repaint/packed_joint_v2/PL00_U.ARC')==verification['before'],'new_art_source_files':{str(p.relative_to(ROOT)):digest(p)for p in[D/'fourth_keys_v1/generated.png',D/'fourth_remaining_v1/generated.png',D/'basic_keys_v2/generated.png',D/'basic_remaining_v1/generated.png',D/'basic_firing_reach_v2/generated.png',D/'basic_remaining_reach_v2/generated.png']},'source_preservation_note':'게임/BIN/포인터/F1/카드에 쓰지 않음. 원화는 별도 신규 PNG로 생성했다.','runtime_verified':False})
    proposal=json.loads((out/'proposal.json').read_text('utf8'));proposal.update({'frozen_candidate':True,'candidate_only':True,'changed_refs':list(REFS),'required_parent_contains':'new run/fire32 + shin50 native restore','verification':str((out/'verification.json').relative_to(ROOT)),'regression':str((out/'mask_verification.json').relative_to(ROOT)),'art_scope':'기본/포스 벽6몸체+사격6, 전신새원화. Ultimate 및 다른모션 미변경.','runtime_verified':False});write(out/'proposal.json',proposal)
    print(json.dumps({'passed':True,'sha':expected,'rejections':len(checks)}))
if __name__=='__main__':main()
