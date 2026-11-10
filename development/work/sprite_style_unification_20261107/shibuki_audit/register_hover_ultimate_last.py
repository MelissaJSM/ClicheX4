"""호버229 단독 원화를 전체128격자로 고정 등록하고 실제 두 팔레트를 분리한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from prepare_lowhp_final import compose
def main():
    s=H/'hover_ultimate_inputs02';d=H/'hover_ultimate_native02';need(not d.exists(),'기존등록보호');m=json.loads((s/'input.json').read_text('utf8'));g=s/'generated_v1.png';a=Archive((ROOT/m['parent']['path']).read_bytes());need(sha(a.data)==m['parent']['sha256'],'부모변경')
    for n,h in m['files'].items():need(sha((s/n).read_bytes())==h,'입력변경')
    im=Image.open(g).convert('RGBA');need(im.width==im.height,'정사각전체캔버스');cell=np.array(im.resize((128,128),Image.Resampling.NEAREST));need(not any(np.any(cell[e,:,-1]>=128)for e in(0,-1)),'캔버스끝');d.mkdir();layers={b:np.zeros((384,384),np.uint8)for b in(0,5,6,7,8)}
    for b,pal in((0,0),(5,16)):
        rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[pal:pal+16]],np.int32);z=(1+((cell[:,:,:3].astype(np.int32)[:,:,None]-rgb[None,None,1:])**2).sum(3).argmin(2)).astype(np.uint8);z[cell[:,:,3]<128]=0;layers[b][96:224,96:224]=z
    layers[0][165:]=0;layers[5][:165]=0;actual=compose(a,layers,15);labs,_=label(np.array(actual)[:,:,3]>0,np.ones((3,3)));sizes=sorted(np.bincount(labs.ravel())[1:].tolist(),reverse=True);need(len(sizes)==1,'단일몸체연결');actual.save(d/'229.png');Image.fromarray(cell).save(d/'229_sample.png')
    for b,z in layers.items():Image.fromarray(z).save(d/f'229_bank{b}_indices.png')
    page([('229 old actual15',a.composite(229,15)[0]),('229 new actual15',actual)],a.composite(0,0)[0],d/'comparison.png',cols=2,scale=6)
    write(s/'generation.json',{'tool':'builtin imagegen','default_saved_path':'<LOCAL_PATH>','workspace_path':g.relative_to(ROOT).as_posix(),'sha256':sha(g.read_bytes()),'actual_size':list(im.size),'prompt_sha256':sha((s/'prompt.txt').read_bytes()),'asset_saved':True,'accepted':False})
    report={'parent':m['parent'],'ref':229,'source_sha256':sha(g.read_bytes()),'source_size':list(im.size),'whole_canvas_native':[128,128],'fixed_origin':[64,64],'alpha_cutoff':128,'sprite_specific_scaling':False,'pixel_deletion':False,'cut_world_y':5,'palettes':{'0':0,'5':16},'old_metrics':metrics(a.composite(229,15)[0]),'new_metrics':metrics(actual),'components':sizes,'alpha_1_127_samples':int(((cell[:,:,3]>0)&(cell[:,:,3]<128)).sum()),'target_hashes':{str(b):sha(z.tobytes())for b,z in layers.items()},'jet_contacts_pending':True,'art_accepted':False,'files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in[s/'input.json',g,s/'generation.json',Path(__file__),*d.glob('*.png')]}}
    write(d/'registration.json',report);print(json.dumps({k:v for k,v in report.items()if k!='files'}))
if __name__=='__main__':main()
