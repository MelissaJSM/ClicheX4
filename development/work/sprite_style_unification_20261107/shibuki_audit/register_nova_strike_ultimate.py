"""Ultimate217 신규몸체 전체128격자 고정 등록. 포즈별 크기변형 없음."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
def main():
    s=H/'nova_strike_ultimate_inputs01';d=H/'nova_strike_ultimate_native01';need(not d.exists(),'새 등록');m=json.loads((s/'input.json').read_text('utf8'));g=s/'generated_v1.png';receipt=json.loads((s/'generation.json').read_text('utf8'));need(sha(g.read_bytes())==receipt['sha256'],'원화 변경')
    for name,h in m['files'].items():need(sha((s/name).read_bytes())==h,'입력 변경')
    a=Archive((ROOT/m['parent']['path']).read_bytes());need(sha(a.data)==m['parent']['sha256'],'부모 변경');original=Image.open(g).convert('RGBA');need(original.width==original.height,'정사각 전체캔버스');cell=np.array(original.resize((128,128),Image.Resampling.NEAREST))
    rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[:16]],np.int32);ind=(1+((cell[:,:,:3].astype(np.int32)[:,:,None]-rgb[None,None,1:])**2).sum(3).argmin(2)).astype(np.uint8);ind[cell[:,:,3]<128]=0
    need(not(ind[0].any()or ind[-1].any()or ind[:,0].any()or ind[:,-1].any()),'셀 경계');z=np.zeros((384,384),np.uint8);z[96:224,96:224]=ind;im=a.rgba(z,0);labs,_=label(ind>0,np.ones((3,3)));sizes=sorted(np.bincount(labs.ravel())[1:].tolist(),reverse=True)
    old=a.composite(217,15)[0];d.mkdir();Image.fromarray(z).save(d/'217_indices.png');im.save(d/'217.png');Image.fromarray(cell).save(d/'sample_rgba.png')
    page([('현재 강제15 옛재킷몸',old),('새 after 의상 고정등록',im)],a.composite(0,0)[0],d/'comparison.png',cols=2,scale=6)
    yy,xx=np.nonzero((z==7)&(np.indices(z.shape)[1]<160));gold=list(zip((xx-160).tolist(),(yy-160).tolist()))
    write(d/'registration.json',{'source_sha256':sha(g.read_bytes()),'source_size':list(original.size),'whole_canvas_native':[128,128],'alpha_cutoff':128,'sprite_specific_scaling':False,'pixel_deletion':False,'old_metrics':metrics(old),'new_metrics':metrics(im),'components':sizes,'left_gold_samples':gold,'low_alpha_samples':int(((cell[:,:,3]>0)&(cell[:,:,3]<128)).sum()),'indexed_sha256':sha(z.tobytes()),'files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in[s/'input.json',g,s/'generation.json',Path(__file__),*d.glob('*.png')]},'new_art_accepted':False,'policy':'단일새몸은 강제mask15에 표시할after의상 신규 제작. 원217 흰재킷의의상을보존했다는뜻아님. 새효과/최종접점/실기는별도.'})
    print(json.dumps({'old':metrics(old),'new':metrics(im),'components':sizes,'low_alpha':int(((cell[:,:,3]>0)&(cell[:,:,3]<128)).sum()),'gold':gold}))
if __name__=='__main__':main()
