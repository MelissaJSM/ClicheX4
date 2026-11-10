"""새95/97 공통부와 후폼 머리끝1셀을 보존하여15층을 만든다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,same_rgba
from scripts.export_x_consistency import Archive,page
from prepare_lowhp_final import compose
P=H/'prepared_ultimate_return01/PL02_U.ARC'
PARENT='f40f33969d488af9db8c7d99b6bf4a78ad6e5542883bff63116fa26778de4cdc'
PBS=(0,5,6,7,8);REFS=(95,96,97)

def main():
    o=H/'ultimate_special_targets01';need(not o.exists(),'Fresh target folder');o.mkdir()
    need(sha(P.read_bytes())==PARENT,'Wrong parent');a=Archive(P.read_bytes());s=H/'ultimate_special_common_probe01'
    rgb=np.array([[(int(w)>>k&31)*255//31 for k in (0,5,10)] for w in a.words],np.int32)
    inverse=np.r_[0,1+((rgb[1:16,None]-rgb[None,17:32])**2).sum(2).argmin(1)].astype(np.uint8)
    forms={};source_change=[]
    for ref in (95,97):
        pair={f:np.array(Image.open(s/f'{f}_{ref:03}_indices.png')) for f in ('before','after')}
        addition=np.zeros((384,384),bool)
        if ref==97:
            # 새 후폼의 뒤머리 안쪽 보라색1셀을 같은 머리로 공유한다.
            py,px=164,165
            need(pair['before'][py,px]==0 and pair['after'][py,px]==8,'Hair-point source changed')
            pair['before'][py,px]=inverse[8];addition[py,px]=True
            need(int(inverse[8])==8,'Unexpected hair palette correspondence')
            source_change.append({'ref':97,'world':[5,4],'source_form':'new_after','source_index':8,'target_before_index':8,
                                  'meaning':'팔 뒤의 새 뒤머리 안쪽1셀. 후폼 새 원화 픽셀을 두 의상 공통머리에 포함한다.'})
        need(not ((pair['after']>0)&(pair['before']==0)).any(),'After silhouette outside jacket')
        forms[ref]=pair;Image.fromarray(addition.astype(np.uint8)*255).save(o/f'{ref:03}_shared_hair_addition_mask.png')
    forms[96]={f:np.roll(v,1,axis=1) for f,v in forms[95].items()}
    targets={};rows=[]
    for ref,pair in sorted(forms.items()):
        before,after=pair['before'],pair['after']
        layers={0:after,5:np.where(same_rgba(a,before,after),0,before).astype('uint8'),
                **{b:np.zeros_like(after) for b in (6,7,8)}}
        targets[str(ref)]={}
        for b,v in layers.items():
            Image.fromarray(v).save(o/f'{ref:03}_bank{b}_indices.png');targets[str(ref)][str(b)]=sha(v.tobytes())
        for f,v in pair.items():
            Image.fromarray(v).save(o/f'{f}_{ref:03}_indices.png');im=a.rgba(v,16 if f=='before' else 0);im.save(o/f'{f}_{ref:03}.png')
            need(compose(a,layers,15 if f=='before' else 0).tobytes()==im.tobytes(),'Layer composition does not reproduce new form')
        rows.append({'ref':ref,'layer_pixels':{str(b):int((v>0).sum()) for b,v in layers.items()},'after_outside_before':0})
        if ref!=96:page([(f'{ref} mask{mask:X}',compose(a,layers,mask)) for mask in range(16)],a.composite(0,15)[0],o/f'partial_{ref:03}.png',cols=4,scale=4)
    for f,mask in (('before',15),('after',0)):
        page([(f'{n} old',a.composite(n,mask)[0]) for n in REFS]+[(f'{n} new',Image.open(o/f'{f}_{n:03}.png')) for n in REFS],a.composite(0,mask)[0],o/f'{f}_comparison.png',cols=3,scale=4)
    sources={}
    for folder in ('ultimate_special_inputs01','ultimate_special_native01','ultimate_special_common_probe01'):
        for p in sorted((H/folder).iterdir()):
            if p.is_file():sources[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for name in ('prepare_ultimate_special_inputs.py','register_ultimate_special.py','probe_ultimate_special_common.py','prepare_ultimate_special_targets.py'):
        p=H/name;sources[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    rel=H.parent/'zero_audit/shibuki_standing_special_relations01/report.json'
    sources[rel.relative_to(ROOT).as_posix()]=sha(rel.read_bytes())
    write(o/'manifest.json',{'parent':P.relative_to(ROOT).as_posix(),'parent_sha256':PARENT,'refs':list(REFS),
        'parts_banks':list(PBS),'targets':targets,'rows':rows,'source_files':sources,'source_shared_hair':source_change,
        'new96_policy':'새95를 x+1 이동한다. 원US의5층 동형을 참고한 새 제작정책이며, 현재Ultimate95/96의160/201px 차이를 원래부터 동일했다고 기록하지 않는다.',
        'fixed_scale':192/1254,'old_body_copied':False,'accepted_idle_modified':False,
        'arc_written':False,'visual_review_pending':True,'runtime_verified':False})
    print(json.dumps({'rows':rows,'source_change':source_change,'manifest_sha256':sha((o/'manifest.json').read_bytes())}))

if __name__=='__main__':main()
