"""동결 제안과 원화·입력거부·최종 시각검토 출처를 묶는다."""
from pathlib import Path
import sys,json,copy,shutil
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(Path(__file__).parent),str(Path(__file__).parent.parent/'native_restore')]
from preview_restore import Archive,sha,digest,write,helper,need
from pack_joint_cycle import validate_targets,validate_output,OUTPUT,PBS
from register_cycle import PAGES
from PIL import Image
import numpy as np
D=Path(__file__).parent;O=D/'packed_joint_v2'
def main():
    targets={(n,pb):np.array(Image.open(D/'joint_layers_v1'/f'layer{pb}_{n:03}.png'))for n in range(1,33)for pb in PBS};m=json.loads((D/'joint_layers_v1/manifest.json').read_text('utf8'));validate_targets(targets,m)
    tests=[]
    def reject(name,fn):
        try:fn()
        except ValueError as e:tests.append({'case':name,'rejected':True,'reason':str(e)})
        else:raise AssertionError(f'Accepted invalid input: {name}')
    for kind in('missing','extra','shape','dtype','palette','pixel'):
        t=dict(targets)
        if kind=='missing':del t[1,0]
        if kind=='extra':t[33,0]=targets[1,0]
        if kind=='shape':t[1,0]=t[1,0][:383]
        if kind=='dtype':t[1,0]=t[1,0].astype(np.int16)
        if kind in('palette','pixel'):
            t[1,0]=t[1,0].copy();t[1,0][0,0]=16 if kind=='palette'else 1
        reject(kind,lambda t=t:validate_targets(t,m))
    reject('existing_output',lambda:validate_output(O));reject('outside_scope',lambda:validate_output(ROOT/'out/not_allowed'))
    need((O/'PL00_U.ARC').read_bytes()==(D/'packed_joint_reproduction_v1/PL00_U.ARC').read_bytes(),'Reproduction differs')
    write(O/'reproduction.json',{'passed':True,'after_sha256':OUTPUT,'reproduced_bytes_identical':True,'reproduction_path':str((D/'packed_joint_reproduction_v1/PL00_U.ARC').relative_to(ROOT)).replace('\\','/'),'rejected_inputs':tests})
    a=Archive((O/'PL00_U.ARC').read_bytes())
    for page,refs in enumerate(((1,7,13,19),(17,23,25,27)),1):
        helper.grid([(f'ref {n}',[(f'mask {mask:X}',a.composite(n,mask)[0])for mask in(1,2,4,8)])for n in refs],O/f'partial_detail_{page}.png',6)
    prior=json.loads((D.parent/'native_restore/prepared_v1/proposal.json').read_text('utf8'));f=copy.deepcopy(prior['files']['PL00_U.ARC']);f.update(path=(O/'PL00_U.ARC').relative_to(ROOT).as_posix(),after=OUTPUT)
    f['changes']={'new_native_refs':list(range(1,33)),'composition_banks':[0,5,6,7,8],'graphics_bank':0,'tile_count':32,'stream_split_pairs':[[17,18],[19,20],[31,32]],'included_previous_ladder_restore':True,'palette_audio_other_entries_unchanged':True}
    proposal={k:prior[k]for k in('project','baseline','baseline_sha256')};proposal.update(files={'PL00_U.ARC':f},candidate_only=True,runtime_verified=False,new_art_generated=True)
    write(O/'proposal.json',proposal)
    sources=[]
    for folder,refs in PAGES:
        p=D/folder/'generated.png';sources.append({'kind':'basic_run','refs':refs,'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)})
    for page in range(1,5):
        for kind,folder in(('moving_fire',f'shot_page{page}_v2'),('fourth_run',f'fourth_page{page}_v1')):
            p=D/folder/'generated.png';sources.append({'kind':kind,'page':page,'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)})
    write(O/'source_provenance.json',{'sources':sources,'generated_with':'builtin image_gen','input_manifest':'joint_layers_v1/manifest.json','old_art_overpaint':False,'no_bulk_material_fill':True,'registration_scripts':['register_cycle.py','register_shot_pairs.py','register_fourth_body_scale.py','align_fourth_foot_contacts.py','common_silhouette_registered.py','prepare_joint_layers.py'],'all_native_targets_hash_bound':True})
    print(json.dumps({'proposal':str(O/'proposal.json'),'sha256':OUTPUT,'rejects':len(tests),'sources':len(sources)}))
if __name__=='__main__':main()
