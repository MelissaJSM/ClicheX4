"""새 사다리 발사팔만 등록하고 새 머리/몸과 원 배럴은 보존한다."""
from pathlib import Path
import sys,struct
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_run_cycle import quantize
from native_pose_pack import need,sha,write
from register_ladder_parts import poly,compose

def main():
    a=Archive((H/'prepared_wall_front01/PL00_U.ARC').read_bytes());inputs=H/'ladder_shot_inputs01';out=H/'ladder_shots_registered01';need(not out.exists(),'Output exists');out.mkdir()
    path=inputs/'generated.png';source_sha='a3c0819c10f5a7c97e1b2e343fedcd59ec48f5a511518abd2bc3bbce7f29af0c';need(sha(path.read_bytes())==source_sha,'Art changed');im=Image.open(path).convert('RGBA');need(im.size==(1254,1254),'Fixed cell layout changed')
    body={b:np.array(Image.open(H/f'ladder_parts04/149_bank{b}_indices.png'))for b in(0,5,6,7,8)};owner=np.array(Image.open(H/'ladder_parts04/149_owner.png'));yy,xx=np.indices(owner.shape);x=xx-160;y=yy-160
    head=(owner==5)&(body[0]>0);rows=[];sheets={0:[],15:[]}
    for col,ref in enumerate((150,155)):
        rect={150:(-25,-12,-15,-4),155:(-22,-16,-12,-8)}[ref];x0,y0,x1,y1=rect;barrel_rect=np.zeros_like(head);barrel_rect[160+y0:160+y1,160+x0:160+x1]=True
        barrel=np.zeros_like(body[0]);barrel[barrel_rect]=a.layer(ref)[0][barrel_rect]
        new_region=poly([(x1-2,y0-2),(-6,-11),(-1,-3),(-2,6),(-12,6),(x1-3,y1+3)])
        old_region=(owner==7)&(x<0)&(y>-14)
        edit=(new_region|old_region)&~head
        generated={}
        for row,start in((0,0),(1,16)):
            rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in struct.unpack_from('<16H',a.p,start*2)],np.int32)
            cell=im.crop((col*627,row*627,(col+1)*627,(row+1)*627));v=quantize(cell,(64,64),rgb,128);new=np.zeros((384,384),np.uint8);new[128:192,128:192]=v;generated[start]=new
        target={b:v.copy()for b,v in body.items()};target[0][edit]=generated[0][edit];target[0][barrel_rect]=barrel[barrel_rect]
        for b in(5,6,7,8):target[b][edit|barrel_rect]=0
        target[7][edit&~barrel_rect]=generated[16][edit&~barrel_rect]
        outside=edit&~barrel_rect&(target[0]>0)&(target[7]==0)
        rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:32]],np.int32);mapping={i:int(np.argmin(((rgb[17:32]-rgb[i])**2).sum(1)))+1 for i in range(1,16)};mapping.update({1:2,4:11,10:10,11:11,12:9,13:9,15:1})
        for py,px in zip(*np.nonzero(outside)):target[7][py,px]=mapping[int(target[0][py,px])]
        for b in body:need(np.array_equal(target[b][~(edit|barrel_rect)],body[b][~(edit|barrel_rect)]),'New nonarm pixels changed')
        for b,v in target.items():Image.fromarray(v).save(out/f'{ref:03}_bank{b}_indices.png')
        Image.fromarray(edit.astype(np.uint8)*255).save(out/f'{ref:03}_arm_mask.png');Image.fromarray(head.astype(np.uint8)*255).save(out/f'{ref:03}_head_protected.png')
        for mask,name in((0,'base'),(15,'fourth')):
            pic=compose(a,target,mask);need(np.array_equal(np.array(pic)[barrel_rect],np.array(a.composite(ref,mask)[0])[barrel_rect]),'Original barrel RGBA changed');pic.save(out/f'{ref:03}_{name}.png');sheets[mask].extend([(f'{name} body149',compose(a,body,mask)),(f'{name} shot{ref}',pic)])
        rows.append({'ref':ref,'body_ref':149,'barrel_rect':rect,'barrel_rgba_exact':True,'head_and_nonarm_body_exact':True,'original_body_not_used':True,'generated_arm_scale':64/627,'edge_material_pixels':int(outside.sum()),'arm_resize':False})
    for mask,name in((0,'base'),(15,'fourth')):page(sheets[mask],a.composite(0,mask)[0],out/f'{name}_comparison.png',cols=2,scale=4)
    write(out/'registration.json',{'source_sha256':source_sha,'rows':rows,'candidate_not_packed':True,'visual_review_pending':True,'game_runtime_verified':False})
    print(rows)

if __name__=='__main__':main()
