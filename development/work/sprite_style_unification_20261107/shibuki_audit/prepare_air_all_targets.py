"""공중 몸체와 사격을 동일한 새 파츠 소유 규칙으로 합성한다. ARC는 쓰지 않는다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image
import numpy as np
from scripts.export_x_consistency import Archive,page
from native_pose_pack import need,sha,write
from inspect_air_layers import P,REFS
from prepare_lowhp_final import compose
from register_air_shot_arms import arm_masks

def main():
    o=H/'air_targets_probe02';need(not o.exists(),'Fresh output required');o.mkdir();a=Archive(P.read_bytes());d=H/'air_head_ownership03';s=H/'air_shot_arms_registered06';rows=[];pics=[];yy,xx=np.indices((384,384))
    for n in sorted(REFS):
        body={b:np.array(Image.open(d/f'{n:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)};shot={b:v.copy()for b,v in body.items()};shot[0]=np.array(Image.open(s/f'base_{n+1:03}_indices.png'))
        patch=np.array(Image.open(s/f'fourth_{n+1:03}_patch_mask.png'))>0;gm=np.array(Image.open(H/f'air_barrel_guard02/{n+1:03}_mask.png'))>0
        source=np.array(Image.open(H/f'air_shot_native_probe02/fourth_{n+1:03}_source_indices.png'));remove,add=arm_masks(n)
        # Uncovered new hair in the removed raised-arm region uses the same
        # new basic artwork. Clothing stays on the foreground Arm part.
        reveal=remove&~add&(yy<160+({37:-6,39:-9,41:-9,43:-9}.get(n,-99)))
        for b in(5,6,7,8):shot[b][patch|gm]=0
        clothing=patch&~reveal&~gm;shot[7][clothing]=source[clothing]
        outside=clothing&(shot[0]>0)&(shot[7]==0)
        marks=[]
        for py,px in zip(*np.nonzero(outside)):
            ix=int(shot[0][py,px]);dst={1:2,2:1,4:11,5:4,6:3,7:10,8:3,9:4,10:10,11:11,12:9,13:9,14:4,15:1}.get(ix,1)
            shot[7][py,px]=dst;marks.append([int(px)-160,int(py)-160,ix,dst])
        # No basic sleeve may leak through a transparent Fourth arm texel.
        need(not np.any(clothing&(shot[0]>0)&(shot[7]==0)),'Uncovered basic sleeve')
        guard=np.array(a.rgba(np.array(Image.open(H/f'air_barrel_guard02/{n+1:03}_indices.png'))))
        for mask in range(16):
            for arm in(1,2):need(np.array_equal(np.array(compose(a,shot,mask,arm))[gm],guard[gm]),'A partial overlay changed the native barrel')
        for ref,layers in((n,body),(n+1,shot)):
            for b,v in layers.items():Image.fromarray(v).save(o/f'{ref:03}_bank{b}_indices.png')
            for mask,name in((0,'base'),(15,'fourth')):compose(a,layers,mask).save(o/f'{name}_{ref:03}.png')
        oldhead=body[5];unchanged=~(patch|gm);need(np.array_equal(shot[5][unchanged],oldhead[unchanged]),'Head outside firing area changed')
        rows.append({'body_ref':n,'shot_ref':n+1,'edge_material_registration':marks,'revealed_hair_pixels':int(np.count_nonzero(shot[0][reveal])),'shot_head_layer_preserved_outside_arm':True,'fullmask_basic_sleeve_alpha_leak':0,'source_only_registration':True})
        for name,mask in(('base',0),('fourth',15)):
            pics.append((name,n,compose(a,body,mask),compose(a,shot,mask)))
        if n in(33,39,41,43,49,53):page([(f'{n+1} mask{mask:X}',compose(a,shot,mask))for mask in range(16)],a.composite(0,15)[0],o/f'partial_{n+1:03}.png',cols=4,scale=3)
    for name,mask in(('base',0),('fourth',15)):
        pairs=[p for p in pics if p[0]==name]
        for start in range(0,len(pairs),4):
            items=[]
            for _,n,b,s in pairs[start:start+4]:items.extend([(f'{n} nonfiring',b),(f'{n+1} firing',s)])
            page(items,a.composite(0,mask)[0],o/f'{name}_pairs_{start//4:02}.png',cols=2,scale=4)
    write(o/'targets.json',{'candidate_only':True,'parent_sha256':sha(P.read_bytes()),'refs':list(range(33,55)),'rows':rows,'source_body_layers':'air_head_ownership03','source_shot_registration':'air_shot_arms_registered06','full_partial_regression_pending':True,'resource_written':False})
    print(json.dumps([{'ref':r['shot_ref'],'edge_pixels':len(r['edge_material_registration']),'revealed_hair_pixels':r['revealed_hair_pixels']}for r in rows]))
if __name__=='__main__':main()
