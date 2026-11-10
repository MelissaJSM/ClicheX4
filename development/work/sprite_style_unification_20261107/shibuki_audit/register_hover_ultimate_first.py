"""호버 첫4를 전체192격자로 등록한다. 원화에서 개별포즈 확대/축소 없음."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
def main():
    s=H/'hover_ultimate_inputs01';d=H/'hover_ultimate_native01';need(not d.exists(),'기존등록보호');m=json.loads((s/'input.json').read_text('utf8'));g=s/'generated_v1.png';a=Archive((ROOT/m['parent']['path']).read_bytes());need(sha(a.data)==m['parent']['sha256'],'부모변경')
    for name,h in m['files'].items():need(sha((s/name).read_bytes())==h,'입력변경')
    im=Image.open(g).convert('RGBA');need(im.width==im.height,'정사각전체캔버스');whole=np.array(im.resize((192,192),Image.Resampling.NEAREST));d.mkdir();rows=[];ims=[]
    write(s/'generation.json',{'tool':'builtin imagegen','default_saved_path':'<LOCAL_PATH>','workspace_path':g.relative_to(ROOT).as_posix(),'sha256':sha(g.read_bytes()),'actual_size':list(im.size),'prompt_sha256':sha((s/'prompt.txt').read_bytes()),'asset_saved':True,'accepted':False})
    rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[:16]],np.int32)
    for f in m['frames']:
        i=f['cell'];n=f['ref'];cell=whole[i//2*96:(i//2+1)*96,i%2*96:(i%2+1)*96];ind=(1+((cell[:,:,:3].astype(np.int32)[:,:,None]-rgb[None,None,1:])**2).sum(3).argmin(2)).astype(np.uint8);ind[cell[:,:,3]<128]=0;need(not(ind[0].any()or ind[-1].any()or ind[:,0].any()or ind[:,-1].any()),'셀경계')
        z=np.zeros((384,384),np.uint8);z[112:208,112:208]=ind;show=a.rgba(z);Image.fromarray(z).save(d/f'{n:03}_indices.png');Image.fromarray(cell).save(d/f'{n:03}_sample.png');show.save(d/f'{n:03}.png');labs,_=label(ind>0,np.ones((3,3)));sizes=sorted(np.bincount(labs.ravel())[1:].tolist(),reverse=True);old=a.composite(n,15)[0];ims.extend([(f'{n} old',old),(f'{n} new fixed',show)]);rows.append({'ref':n,'source_cell':i,'old_metrics':metrics(old),'new_metrics':metrics(show),'components':sizes,'alpha_1_127_samples':int(((cell[:,:,3]>0)&(cell[:,:,3]<128)).sum()),'indexed_sha256':sha(z.tobytes())})
    for k in range(2):page(ims[k*4:(k+1)*4],a.composite(0,0)[0],d/f'comparison_{k:02}.png',cols=2,scale=5)
    write(d/'registration.json',{'source_sha256':sha(g.read_bytes()),'source_size':list(im.size),'whole_canvas_native':[192,192],'fixed_native_cell':[96,96],'alpha_cutoff':128,'sprite_specific_scaling':False,'pixel_deletion':False,'frames':rows,'native_palette':0,'lower_layer_palette16_assignment_pending':True,'jet_contacts_pending':True,'art_accepted':False,'files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in[s/'input.json',g,s/'generation.json',Path(__file__),*d.glob('*.png')]}})
    print(json.dumps({'frames':rows,'report':sha((d/'registration.json').read_bytes())}))
if __name__=='__main__':main()
