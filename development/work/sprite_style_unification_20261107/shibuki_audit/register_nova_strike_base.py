"""Nova217 두 의상 전체 캔버스 고정배율 등록. 몸체별 확대/축소 없음."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics

def main():
    s=H/'nova_strike_base_inputs01';d=H/'nova_strike_base_native01';need(not d.exists(),'새 등록');d.mkdir()
    m=json.loads((s/'input.json').read_text('utf8'));src=Path(sys.argv[1]);g=s/'generated.png';need(not g.exists(),'원화 보호');shutil.copy2(src,g)
    original=Image.open(g).convert('RGBA');need(original.width*2==original.height*3,'전체 캔버스 비율1.5')
    a=Archive((ROOT/m['parent']['path']).read_bytes());need(sha(a.data)==m['parent']['sha256'],'부모 변경')
    for name,h in m['files'].items():need(sha((s/name).read_bytes())==h,'입력 변경')
    write(s/'generation_receipt.json',{'tool':'builtin image_gen','default_output':str(src),'sha256':sha(g.read_bytes()),'size':list(original.size),'prompt_sha256':sha((s/'prompt.txt').read_bytes()),'input_roles':['현재217 몸체/효과 분리 타깃','해당 의상 실제 대기0','해당 의상 새대시71 상세 참조'],'original_preserved':True,'generated_art_accepted':False})
    sample=np.array(original.resize((192,128),Image.Resampling.NEAREST));rows=[]
    for col,(form,mask,pal)in enumerate((('base',0,0),('fourth',15,16))):
        cell=sample[:,96*col:96*(col+1)];rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[pal:pal+16]],np.int32)
        ind=(1+((cell[:,:,:3].astype(np.int32)[:,:,None]-rgb[None,None,1:])**2).sum(3).argmin(2)).astype(np.uint8);ind[cell[:,:,3]<128]=0
        need(not(ind[0].any()or ind[-1].any()or ind[:,0].any()or ind[:,-1].any()),'셀 경계')
        z=np.zeros((384,384),np.uint8);z[96:224,112:208]=ind;im=a.rgba(z,pal)
        old=Image.open(H/f'nova_strike_base_sources01/{form}_217_body.png').convert('RGBA')
        Image.fromarray(z).save(d/f'{form}_217_indices.png');im.save(d/f'{form}_217.png');Image.fromarray(cell).save(d/f'{form}_217_sample_rgba.png')
        labs,_=label(ind>0,np.ones((3,3)));sizes=sorted(np.bincount(labs.ravel())[1:].tolist(),reverse=True)
        page([('현재 효과 분리 몸',old),('새 원화 고정 등록',im)],a.composite(0,mask)[0],d/f'{form}_comparison.png',cols=2,scale=6)
        yy,xx=np.nonzero((ind==7)&(np.indices(ind.shape)[1]<48));eyes=list(zip((xx-48).tolist(),(yy-64).tolist()))
        rows.append({'form':form,'palette_start':pal,'old_metrics':metrics(old),'new_metrics':metrics(im),'components':sizes,'gold_samples_left':eyes,'low_alpha_samples':int(((cell[:,:,3]>0)&(cell[:,:,3]<128)).sum()),'indexed_sha256':sha(z.tobytes())})
    write(d/'registration.json',{'source_sha256':sha(g.read_bytes()),'source_size':list(original.size),'whole_canvas_native':[192,128],'alpha_cutoff':128,'sprite_specific_scaling':False,'pixel_deletion':False,'rows':rows,'files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in[s/'input.json',s/'generated.png',s/'generation_receipt.json',Path(__file__),*d.glob('*.png')]},'new_art_accepted':False});print(json.dumps({'generated':sha(g.read_bytes()),'rows':rows},ensure_ascii=False))
if __name__=='__main__':main()
