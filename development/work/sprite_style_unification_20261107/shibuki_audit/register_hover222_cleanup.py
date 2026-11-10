"""생성 국소표본만 세번째 팔에 등록하고 원발사팔/다른몸체 보존."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from prepare_hover_ultimate_inputs import P,PARENT
def main():
    s=H/'hover222_cleanup_inputs01';d=H/'hover222_cleanup_native01';need(not d.exists(),'새등록');m=json.loads((s/'input.json').read_text('utf8'));a=Archive(P.read_bytes());need(sha(a.data)==PARENT,'부모변경')
    for n,h in m['files'].items():need(sha((s/n).read_bytes())==h,'입력변경')
    g=s/'generated_v1.png';im=Image.open(g).convert('RGBA');cell=np.array(im.resize((128,128),Image.Resampling.NEAREST));rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[:16]],np.int32);z=(1+((cell[:,:,:3].astype(np.int32)[:,:,None]-rgb[None,None,1:])**2).sum(3).argmin(2)).astype(np.uint8);z[cell[:,:,3]<128]=0;donor=np.zeros((384,384),np.uint8);donor[96:224,96:224]=z;old=np.array(Image.open(ROOT/m['source']['path']));yy,xx=np.indices(old.shape);mask=(xx>=143)&(xx<=152)&(yy>=133)&(yy<=149);new=old.copy();new[mask]=donor[mask];need(np.array_equal(new[~mask],old[~mask]),'국소밖변경');d.mkdir();Image.fromarray(donor).save(d/'donor_indices.png');Image.fromarray(new).save(d/'222_indices.png');Image.fromarray(mask.astype(np.uint8)*255).save(d/'semantic_mask.png');a.rgba(new).save(d/'222.png');page([('222 rejected 3 arms',a.rgba(old)),('222 local donor',a.rgba(donor)),('222 corrected local',a.rgba(new))],a.composite(0,0)[0],d/'comparison.png',cols=3,scale=6)
    write(s/'generation.json',{'tool':'builtin imagegen','default_saved_path':'<LOCAL_PATH>','workspace_path':g.relative_to(ROOT).as_posix(),'sha256':sha(g.read_bytes()),'actual_size':list(im.size),'asset_saved':True,'accepted':False})
    write(d/'registration.json',{'source_sha256':sha(g.read_bytes()),'source_size':list(im.size),'fixed_whole_grid':[128,128],'alpha_cutoff':128,'local_world_rectangle':[-17,-27,-7,-10],'changed_cells':int((new!=old).sum()),'outside_mask_exact':True,'body_cannon_other_arm_exact':True,'final_body_composition_pending':True,'files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in[s/'input.json',s/'generation.json',g,ROOT/m['source']['path'],Path(__file__),*d.glob('*.png')]}});print(int((new!=old).sum()))
if __name__=='__main__':main()
