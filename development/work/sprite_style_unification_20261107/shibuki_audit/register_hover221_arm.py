"""221 오른팔 국소 원화의 고정128격자 표본과 의미영역 조합 후보."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation,label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from prepare_hover_ultimate_inputs import P,PARENT
def main():
    s=H/'hover221_arm_inputs01';d=H/'hover221_arm_native01';need(not d.exists(),'기존등록보호');m=json.loads((s/'input.json').read_text('utf8'));a=Archive(P.read_bytes());need(sha(a.data)==PARENT,'부모변경')
    for n,h in m['files'].items():need(sha((s/n).read_bytes())==h,'입력변경')
    g=s/'generated_v1.png';im=Image.open(g).convert('RGBA');need(im.width==im.height,'전체정사각격자');pix=np.array(im.resize((128,128),Image.Resampling.NEAREST));pal=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[:16]],np.int32);ind=(1+((pix[:,:,:3].astype(np.int32)[:,:,None]-pal[None,None,1:])**2).sum(3).argmin(2)).astype(np.uint8);ind[pix[:,:,3]<128]=0;donor=np.zeros((384,384),np.uint8);donor[96:224,96:224]=ind
    z=np.array(Image.open(ROOT/m['source_new_body']['path']));need(sha((ROOT/m['source_new_body']['path']).read_bytes())==m['source_new_body']['sha256'],'새원몸변경');yy,xx=np.indices(z.shape);x=xx-160;y=yy-160;roi=(x>=1)&(x<=10)&(y>=-30)&(y<=-4);skin=np.isin(donor,[10,11,12,13])&roi;arm=binary_dilation(skin,np.ones((3,3)))&((x>=0)&(x<=11)&(y>=-31)&(y<=-3));waist=(x>=-1)&(x<=9)&(y>=-5)&(y<=5);mask=arm|waist;out=z.copy();out[mask]=donor[mask];need(np.array_equal(out[~mask],z[~mask]),'보호외부변경');d.mkdir()
    for name,v in [('donor_indices',donor),('221_indices',out),('arm_semantic_mask',arm.astype(np.uint8)*255),('old_waist_arm_mask',waist.astype(np.uint8)*255),('changed_mask',(out!=z).astype(np.uint8)*255)]:Image.fromarray(v).save(d/f'{name}.png')
    Image.fromarray(pix).save(d/'sample_rgba.png');page([('원호버221',a.composite(221,15)[0]),('첫새몸 팔오류',a.rgba(z)),('국소새원화',a.rgba(donor)),('팔의미영역 조합',a.rgba(out))],a.composite(0,0)[0],d/'comparison.png',cols=2,scale=6)
    sy,sx=np.nonzero(skin);labs,_=label(out>0,np.ones((3,3)));sizes=sorted(np.bincount(labs.ravel())[1:].tolist(),reverse=True)
    write(s/'generation.json',{'tool':'builtin imagegen','default_saved_path':'<LOCAL_PATH>','workspace_path':g.relative_to(ROOT).as_posix(),'sha256':sha(g.read_bytes()),'actual_size':list(im.size),'prompt_sha256':sha((s/'prompt.txt').read_bytes()),'asset_saved':True,'accepted':False})
    write(d/'registration.json',{'source_sha256':sha(g.read_bytes()),'actual_size':list(im.size),'fixed_canvas':[128,128],'alpha_cutoff':128,'sprite_specific_scaling':False,'body_protected_outside_semantic_mask':True,'new_arm_skin_points':list(zip((sx-160).tolist(),(sy-160).tolist())),'new_arm_skin_pixels':int(skin.sum()),'copied_mask_cells':int(mask.sum()),'changed_cells':int((out!=z).sum()),'metrics':metrics(a.rgba(out)),'components':sizes,'art_accepted':False,'files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in[s/'input.json',g,s/'generation.json',Path(__file__),*d.glob('*.png')]}});print(json.dumps({'changed':int((out!=z).sum()),'skin_bounds':None if not len(sx)else[int(sx.min()-160),int(sy.min()-160),int(sx.max()-159),int(sy.max()-159)],'components':sizes,'metrics':metrics(a.rgba(out))}))
if __name__=='__main__':main()
