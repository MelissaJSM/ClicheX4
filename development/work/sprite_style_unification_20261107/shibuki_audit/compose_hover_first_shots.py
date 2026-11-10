"""222/224의 새팔 표본만 새몸에 등록하고 정본총열/하체를 보호한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation,label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from prepare_lowhp_final import compose
from prepare_hover_ultimate_inputs import P,PARENT
def main():
    d=H/'hover_ultimate_shot_composed01';need(not d.exists(),'새합성');a=Archive(P.read_bytes());need(sha(a.data)==PARENT,'부모변경');d.mkdir();rows=[];ims=[]
    for n in(222,224):
        bs=H/'hover_ultimate_body_layers01';base={b:np.array(Image.open(bs/f'{n-1:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)};donorp=H/('hover222_cleanup_native01/222_indices.png'if n==222 else'hover_ultimate_shot_page01_registered01/224_indices.png');donor=np.array(Image.open(donorp));old=base[0];yy,xx=np.indices(old.shape);x=xx-160;y=yy-160
        upperROI=(x>=-18)&(x<=-9)&(y>=(-28 if n==222 else-21))&(y<=-7);oldskin=upperROI&np.isin(old,[10,11,12,13]);remove=binary_dilation(oldskin,np.ones((3,3)))&upperROI
        armROI=(x>=-31)&(x<=-7)&(y>=-14)&(y<=0);newskin=armROI&np.isin(donor,[10,11,12,13]);arm=binary_dilation(newskin,np.ones((3,3)))&armROI;shoulder=(x>=-8)&(x<=-4)&(y>=-4)&(y<=0)
        if n==222:remove|=(x>=-17)&(x<=-8)&(y>=-27)&(y<=-11)
        mask=remove|arm|shoulder;out=old.copy();out[mask]=donor[mask];gd=H/'hover_ultimate_shot_inputs01';gun=np.array(Image.open(gd/f'{n:03}_barrel_indices.png'));guard=np.array(Image.open(gd/f'{n:03}_barrel_mask.png'))>0;out[guard]=gun[guard];mask|=guard;need(np.array_equal(out[~mask],old[~mask]),'신체보호');layers={**base,0:out};new=compose(a,layers,15);lab,_=label(np.array(new)[:,:,3]>0,np.ones((3,3)));sizes=sorted(np.bincount(lab.ravel())[1:].tolist(),reverse=True);touch=binary_dilation(gun>0,np.array([[0,1,0],[1,1,1],[0,1,0]]))&(out>0)&~guard;need(touch.any(),'총팔접점')
        for b,z in layers.items():Image.fromarray(z).save(d/f'{n:03}_bank{b}_indices.png')
        Image.fromarray(mask.astype(np.uint8)*255).save(d/f'{n:03}_semantic_mask.png');new.save(d/f'actual_{n}.png');ims.extend([(f'{n-1} new body',compose(a,base,15)),(f'{n} new shot trial',new)]);rows.append({'ref':n,'body_ref':n-1,'donor':donorp.relative_to(ROOT).as_posix(),'donor_sha256':sha(donorp.read_bytes()),'changed_cells':int((old!=out).sum()),'outside_arm_mask_exact':True,'lower_exact':True,'canonical_guard_exact':True,'cannon_contact_cells':int(touch.sum()),'components':sizes,'metrics':metrics(new)})
    page(ims,a.composite(0,0)[0],d/'comparison.png',cols=2,scale=6);write(d/'registration.json',{'parent_sha256':PARENT,'frames':rows,'art_final':False,'native_packed':False,'source_art_preserved_except_explicit_new_arm_region':True,'files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in[Path(__file__),*d.glob('*.png')]}});print(json.dumps(rows))
if __name__=='__main__':main()
