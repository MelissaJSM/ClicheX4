"""공중 22참조 후보의 재현·거부·총구 보존을 확인하고 동결한다."""
from pathlib import Path
import sys,json,copy
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D))
from pack_air_native import validate_source,validate_targets,validate_output,PBS,REFS,sha,write,need,digest,ROOT,Archive

EXPECTED='721457a50ea48e76c1ac592eec21db274b43c5863cc5b3df310ac981d5890dca'
def main():
    out=D/'packed_air_candidate_v1';td=D/'joint_layers_final_v1';parent=D.parent/'wall_repaint/packed_wall_candidate_v4/PL00_U.ARC'
    manifest=json.loads((td/'manifest.json').read_text('utf8'))
    targets={(n,pb):np.array(Image.open(td/f'layer{pb}_{n:03}.png'))for n in REFS for pb in PBS}
    need(digest(out/'PL00_U.ARC')==EXPECTED,'Candidate SHA')
    need(digest(D/'packed_air_reproduction_v1/PL00_U.ARC')==EXPECTED,'Reproduction SHA')
    validate_targets(targets,manifest);checks=[]
    def reject(name,fn):
        try:fn()
        except (ValueError,KeyError):checks.append(name);return
        raise ValueError('Invalid input accepted '+name)
    reject('wrong_source_hash',lambda:validate_source(b'wrong'))
    missing=targets.copy();missing.pop((33,0));reject('missing_target',lambda:validate_targets(missing,manifest))
    unexpected=targets.copy();unexpected[55,0]=targets[33,0];reject('unexpected_ref',lambda:validate_targets(unexpected,manifest))
    for name,arr in [('shape',np.zeros((383,384),np.uint8)),('dtype',targets[33,0].astype(np.int16)),('range',np.full((384,384),16,np.uint8)),('hash',np.zeros((384,384),np.uint8))]:
        bad=targets.copy();bad[33,0]=arr;reject('target_'+name,lambda bad=bad:validate_targets(bad,manifest))
    badmeta=copy.deepcopy(manifest);badmeta['source_arc_sha256']='0'*64;reject('target_parent',lambda:validate_targets(targets,badmeta))
    badmeta=copy.deepcopy(manifest);badmeta['frames'][-1]=copy.deepcopy(badmeta['frames'][0]);reject('duplicate_manifest_ref',lambda:validate_targets(targets,badmeta))
    reject('existing_output',lambda:validate_output(out));reject('outside_output',lambda:validate_output(ROOT/'not_created_by_air_test'))
    a=validate_source(parent.read_bytes());b=Archive((out/'PL00_U.ARC').read_bytes());gun=[]
    for q in json.loads((D/'fire_constraints/manifest.json').read_text('utf8'))['frames']:
        n=q['ref'];x0,y0,x1,y1=q['gun_window'];need(x1-x0==8,'Original gun width')
        for mask in range(16):
            for arm in (1,2):
                before=np.array(a.composite(n,mask,arm)[0])[y0+160:y1+160,x0+160:x1+160]
                after=np.array(b.composite(n,mask,arm)[0])[y0+160:y1+160,x0+160:x1+160]
                need(np.array_equal(before,after),f'Original gun RGBA window {n}/{mask}/{arm}')
                gun.append({'ref':n,'mask':mask,'arm':arm,'window':[x0,y0,x1,y1],'before_after_rgba_sha256':sha(after.tobytes())})
    verify=json.loads((out/'verification.json').read_text('utf8'));masks=json.loads((out/'mask_verification.json').read_text('utf8'))
    need(verify['passed']and masks['passed'],'Required checks')
    # Every current generated source remains a separate input, never a game source file.
    source_names=['basic_keys_v1','basic_middle_v1','basic_landing_v1','basic_firing_a_v1','basic_firing_b_v1','basic_firing_c_v1','landing_reach_generated_v1','fourth_air_a_v1','fourth_air_b_v1','fourth_air_c_v1','fourth_joint_edits_v1','fourth51_knee_v1']
    sources={str((D/n/'generated.png').relative_to(ROOT)):digest(D/n/'generated.png')for n in source_names}
    write(out/'reproduction.json',{'passed':True,'after_sha256':EXPECTED,'reproduced_sha256':digest(D/'packed_air_reproduction_v1/PL00_U.ARC'),'rejections':checks,'source_parent_unchanged':digest(parent)==verify['before'],'generated_source_files':sources,'original_gun_rgba_checks':len(gun),'gun_windows':gun,'runtime_verified':False,'protection_note':'원본 게임·설정화·BIN·포인터·F1·카드는 변경하지 않았다. 별도 준비 ARC만 작성했다.'})
    proposal=json.loads((out/'proposal.json').read_text('utf8'))
    proposal.update({'frozen_candidate':True,'candidate_only':True,'changed_refs':list(REFS),'required_parent_contains':'new run/fire32 + shin50 native restore + wall12 v4','verification':str((out/'verification.json').relative_to(ROOT)),'regression':str((out/'mask_verification.json').relative_to(ROOT)),'reproduction':str((out/'reproduction.json').relative_to(ROOT)),'art_scope':'기본/포스 공중 11몸체+사격11. 새 원화·접점 정합. 39/40은 수용된 fold_C 원화 명암을 반영. 다른 참조와 Ultimate는 그대로.','art_static_review':'root가 v6와 fold_C 방향을 직접 열람·수용했고 제작자가 native readback4장 및 부분소유8장을 직접 열람했다.','runtime_verified':False,'native_mips_verified_by_this_script':False})
    write(out/'proposal.json',proposal)
    print(json.dumps({'passed':True,'sha':EXPECTED,'rejections':len(checks),'original_gun_checks':len(gun)}))
if __name__=='__main__':main()
